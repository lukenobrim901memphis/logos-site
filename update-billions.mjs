#!/usr/bin/env node
/**
 * Billions tracker — nightly updater.
 *
 * Pulls NBA scoreboards from ESPN, opens the box score of every finished game,
 * and records every player line that qualifies as a "billion". Results are kept
 * in data/billions.json, which billions.html reads.
 *
 * Usage (Node 18+, no npm packages needed):
 *   node update-billions.mjs                      # yesterday and the day before
 *   node update-billions.mjs --date 20261020      # one specific day
 *   node update-billions.mjs --from 20261020 --to 20261031   # backfill a range
 *   node update-billions.mjs --from 20121030 --to 20161024   # add 2012-13 through 2015-16
 *   node update-billions.mjs --from 20121030 --to 20161024 --retry-broken   # retry games skipped as broken
 *
 * The script is safe to run as often as you like: games that were already
 * processed are skipped, and games that aren't final yet are retried next run.
 */

import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

// ---------------------------------------------------------------------------
// The billion rule. Edit here if you ever tweak the stat.
//   under: the player must have LESS THAN this number
//   zero:  the player must have exactly 0
// (Players listed as "did not play" are never counted.)
// ---------------------------------------------------------------------------
export const BILLION_RULE = {
  under: { min: 10, reb: 2, ast: 2, stl: 2, blk: 2 },
  zero: ['pts', 'fgm', 'fga', 'ftm', 'fta'],
};

const ESPN_BASE = process.env.ESPN_BASE ||
  'https://site.api.espn.com/apis/site/v2/sports/basketball/nba';
const HERE = dirname(fileURLToPath(import.meta.url));
const DATA_FILE = resolve(HERE, process.env.BILLIONS_FILE || 'data/billions.json');
const TIME_ZONE = 'America/New_York';   // NBA schedule days are Eastern time
const LOOKBACK_DAYS = 2;                // nightly run checks this many days: yesterday and the day before
const COUNT_PRESEASON = false;          // season type 1 = preseason
const FIRST_SEASON = 2013;              // earliest season tracked (2013 = 2012-13)
const CHECK_SEASONS_THROUGH = 2016;     // games through 2015-16 are checked first; broken box scores are skipped
const NBA_FALLBACK = true;              // when ESPN's box score is broken, try the same game on NBA.com
const NBA_BASE = process.env.NBA_BASE || 'https://www.nba.com';
const CONCURRENCY = 4;                  // box scores fetched at the same time (be polite to ESPN)

// ---------------------------------------------------------------------------

function ymdInZone(date, tz = TIME_ZONE) {
  const p = Object.fromEntries(
    new Intl.DateTimeFormat('en-US', { timeZone: tz, year: 'numeric', month: '2-digit', day: '2-digit' })
      .formatToParts(date).map(x => [x.type, x.value]));
  return `${p.year}${p.month}${p.day}`;
}

function shiftYmd(ymd, days) {
  const d = new Date(Date.UTC(+ymd.slice(0, 4), +ymd.slice(4, 6) - 1, +ymd.slice(6, 8) + days));
  return d.toISOString().slice(0, 10).replace(/-/g, '');
}

function rangeYmd(from, to) {
  const out = [];
  for (let d = from; d <= to; d = shiftYmd(d, 1)) out.push(d);
  return out;
}

const toIso = ymd => `${ymd.slice(0, 4)}-${ymd.slice(4, 6)}-${ymd.slice(6, 8)}`;

async function getJson(url, tries = 3) {
  for (let i = 1; ; i++) {
    try {
      const res = await fetch(url, { headers: { 'User-Agent': 'billions-tracker/1.0' } });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      if (i >= tries) throw new Error(`${url}: ${err.message}`);
      await new Promise(r => setTimeout(r, 1000 * i));
    }
  }
}

// "3-7" -> [3, 7]
const madeAtt = s => {
  const [m, a] = String(s ?? '').split('-').map(n => parseInt(n, 10));
  return [Number.isFinite(m) ? m : 0, Number.isFinite(a) ? a : 0];
};
const num = s => {
  const n = parseInt(String(s ?? '').replace('+', ''), 10);
  return Number.isFinite(n) ? n : 0;
};

/** Turn ESPN's parallel keys/stats arrays into a named stat line. */
export function parseStatLine(keys, stats) {
  const v = Object.fromEntries(keys.map((k, i) => [k, stats[i]]));
  const [fgm, fga] = madeAtt(v['fieldGoalsMade-fieldGoalsAttempted']);
  const [tpm, tpa] = madeAtt(v['threePointFieldGoalsMade-threePointFieldGoalsAttempted']);
  const [ftm, fta] = madeAtt(v['freeThrowsMade-freeThrowsAttempted']);
  return {
    min: num(String(v.minutes ?? '').split(':')[0]),
    pts: num(v.points), fgm, fga, tpm, tpa, ftm, fta,
    reb: num(v.rebounds), ast: num(v.assists), to: num(v.turnovers),
    stl: num(v.steals), blk: num(v.blocks),
    oreb: num(v.offensiveRebounds), dreb: num(v.defensiveRebounds),
    pf: num(v.fouls), pm: num(v.plusMinus),
  };
}

export function isBillion(line, rule = BILLION_RULE) {
  return Object.entries(rule.under).every(([k, n]) => line[k] < n) &&
         rule.zero.every(k => line[k] === 0);
}

// ---------------------------------------------------------------------------
// Historical team names. ESPN shows today's name on old games, so swap in the
// name the team actually had that season. `through` is the last season (by its
// ending year) the old name was used: 2013 = 2012-13, 2014 = 2013-14.
// ---------------------------------------------------------------------------
const OLD_TEAM_NAMES = [
  { abbrs: ['NO', 'NOP', 'NOH'], through: 2013, abbr: 'NOH', name: 'Hornets' }, // New Orleans Hornets → Pelicans in 2013-14
  { abbrs: ['CHA', 'CHO'],       through: 2014, abbr: 'CHA', name: 'Bobcats' }, // Charlotte Bobcats → Hornets in 2014-15
];

// Player names ESPN shows with a middle name. Add more as "Name ESPN shows": "Name to use".
const NAME_FIXES = {
  'Robbie John Hummel': 'Robbie Hummel',
  'Vince Shamar Hunter': 'Vince Hunter',
  'Jerome Adolphus Jordan': 'Jerome Jordan',
  'Omari Rasulala Spellman': 'Omari Spellman',
  'Pierre Deshawn Jackson': 'Pierre Jackson',
  'Gustavo Alfonso Ayon': 'Gustavo Ayon',
};

// Matches the names above even if ESPN's version has accents (Ayón), odd spaces or different capitals.
const fixKey = s => String(s ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/\s+/g, ' ').trim().toLowerCase();
const NAME_FIX_LOOKUP = new Map(Object.entries(NAME_FIXES).map(([from, to]) => [fixKey(from), to]));
const fixName = name => NAME_FIX_LOOKUP.get(fixKey(name)) ?? name;

function eraTeam(abbr, name, season) {
  const old = OLD_TEAM_NAMES.find(t => t.abbrs.includes(abbr) && season <= t.through);
  return old ? { abbr: old.abbr, name: old.name } : { abbr, name };
}

const eraMatchup = (matchup, season) =>
  matchup.split('@').map(a => eraTeam(a, '', season).abbr).join('@');

/** Apply historical team names to a saved billion (safe to run repeatedly). */
function applyEraNames(b) {
  const t = eraTeam(b.teamAbbr, b.team, b.season);
  b.teamAbbr = t.abbr;
  b.team = t.name;
  b.matchup = eraMatchup(b.matchup, b.season);
  return b;
}

/**
 * Sanity-check an older box score. Returns a list of problems (empty = looks fine).
 * Same checks as check-old-seasons.mjs.
 */
export function boxScoreProblems(summary, finalScores) {
  const problems = new Set();
  const teams = summary?.boxscore?.players ?? [];
  if (!teams.length) return ['NO_BOXSCORE'];
  for (const teamBlock of teams) {
    const group = teamBlock.statistics?.[0];
    const keys = group?.keys ?? [];
    const rows = (group?.athletes ?? []).filter(r => !r.didNotPlay);
    if (!rows.length) { problems.add('NO_PLAYERS'); continue; }
    const minIdx = keys.indexOf('minutes');
    if (minIdx < 0) { problems.add('NO_MINUTES'); continue; }
    let pts = 0, mins = 0;
    for (const r of rows) {
      if (!r.stats?.length || !/^\d+/.test(String(r.stats[minIdx] ?? '').trim())) { problems.add('BLANK_ROWS'); continue; }
      const line = parseStatLine(keys, r.stats);
      pts += line.pts;
      mins += line.min;
    }
    const final = finalScores.get(String(teamBlock.team?.id));
    if (final != null && pts !== final) problems.add('POINTS_MISMATCH');
    if (mins < 230) problems.add('LOW_MINUTES');
  }
  return [...problems];
}

// ---------------------------------------------------------------------------
// NBA.com fallback. NBA.com game pages carry the full box score in a hidden
// data block (__NEXT_DATA__); its scoreboard page lists each date's game IDs.
// ---------------------------------------------------------------------------
const BROWSER_HEADERS = {
  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36',
  'Accept': 'text/html,application/xhtml+xml',
  'Accept-Language': 'en-US,en;q=0.9',
};

async function getNextData(url, tries = 3) {
  for (let i = 1; ; i++) {
    try {
      const res = await fetch(url, { headers: BROWSER_HEADERS, signal: AbortSignal.timeout(30000) });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const m = (await res.text()).match(/<script id="__NEXT_DATA__"[^>]*>([\s\S]*?)<\/script>/);
      if (!m) throw new Error('no data block on page');
      return JSON.parse(m[1]);
    } catch (err) {
      if (i >= tries) throw new Error(`${url}: ${err.message}`);
      await new Promise(r => setTimeout(r, 1500 * i));
    }
  }
}

// ESPN team codes → NBA.com team codes, where they differ.
const NBA_CODES = { GS: 'GSW', NY: 'NYK', NO: 'NOP', NOH: 'NOH', SA: 'SAS', UTAH: 'UTA', WSH: 'WAS' };
const nbaCode = espn => NBA_CODES[espn] || espn;
const sameTeam = (espn, nba) => nbaCode(espn) === nba || (espn === 'NO' && nba === 'NOH') || (espn === 'CHA' && nba === 'CHO');

const nbaDateCache = new Map();
/** Every game on NBA.com's scoreboard for a date (YYYY-MM-DD): [{ gameId, home, away }] */
function nbaGamesOn(date) {
  if (!nbaDateCache.has(date)) {
    nbaDateCache.set(date, getNextData(`${NBA_BASE}/games?date=${date}`).then(data => {
      const games = [];
      (function walk(n) {
        if (Array.isArray(n)) n.forEach(walk);
        else if (n && typeof n === 'object') {
          if (/^00\d{8}$/.test(n.gameId ?? '') && n.homeTeam?.teamTricode) {
            games.push({
              gameId: n.gameId,
              home: { code: n.homeTeam.teamTricode, score: Number(n.homeTeam.score) },
              away: { code: n.awayTeam?.teamTricode, score: Number(n.awayTeam?.score) },
            });
          }
          Object.values(n).forEach(walk);
        }
      })(data);
      return games;
    }));
  }
  return nbaDateCache.get(date);
}

/** Find the NBA.com game ID for an ESPN game: same date, same final score (team codes as a backup). */
async function findNbaGameId(date, home, away) {
  const games = await nbaGamesOn(date);
  const byScore = games.filter(g => g.home.score === home.score && g.away.score === away.score);
  if (byScore.length === 1) return byScore[0].gameId;
  const byTeam = games.filter(g => sameTeam(home.code, g.home.code) && sameTeam(away.code, g.away.code));
  return byTeam.length === 1 ? byTeam[0].gameId : null;
}

// "Luka Dončić Jr." → "luka doncic"
const nameKey = s => String(s ?? '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
  .replace(/[.'’]/g, '').replace(/-/g, ' ').replace(/\b(jr|sr|ii|iii|iv)\b/g, '').replace(/\s+/g, ' ').trim();

/** Turn an NBA.com player's statistics into the same stat line ESPN rows produce. */
function nbaStatLine(st) {
  const [mm, ss] = String(st.minutes ?? '').split(':').map(Number);
  return {
    min: Math.floor(((mm || 0) * 60 + (ss || 0)) / 60),
    pts: st.points ?? 0, fgm: st.fieldGoalsMade ?? 0, fga: st.fieldGoalsAttempted ?? 0,
    tpm: st.threePointersMade ?? 0, tpa: st.threePointersAttempted ?? 0,
    ftm: st.freeThrowsMade ?? 0, fta: st.freeThrowsAttempted ?? 0,
    reb: st.reboundsTotal ?? 0, ast: st.assists ?? 0, to: st.turnovers ?? 0,
    stl: st.steals ?? 0, blk: st.blocks ?? 0,
    oreb: st.reboundsOffensive ?? 0, dreb: st.reboundsDefensive ?? 0,
    pf: st.foulsPersonal ?? 0, pm: Math.round(st.plusMinusPoints ?? 0),
  };
}

/**
 * Try one broken ESPN game on NBA.com. Returns { billions, nbaGameId } if NBA.com's
 * box score passes the same checks, or { problems } if it can't be used.
 */
async function nbaFallback(ctx, comp, espnSummary, data) {
  const side = h => comp.competitors?.find(c => c.homeAway === h);
  const espn = { home: side('home'), away: side('away') };
  const ref = h => ({ code: espn[h]?.team?.abbreviation, score: parseInt(espn[h]?.score, 10) });

  const nbaGameId = await findNbaGameId(ctx.date, ref('home'), ref('away'));
  if (!nbaGameId) return { problems: ['NBA_NO_MATCH'] };
  const page = await getNextData(`${NBA_BASE}/game/${nbaGameId}/box-score`);
  const game = page?.props?.pageProps?.game;
  if (!game?.homeTeam?.players || !game?.awayTeam?.players) return { problems: ['NBA_NO_BOXSCORE'] };

  // ESPN's player IDs, by name, so NBA.com billions count under the same player.
  const espnIds = new Map();
  for (const t of espnSummary?.boxscore?.players ?? []) {
    for (const g of t.statistics ?? []) {
    for (const r of g.athletes ?? []) if (r.athlete?.id) espnIds.set(nameKey(fixName(r.athlete.displayName)), String(r.athlete.id));
    }
  }
  for (const b of data.billions) if (!espnIds.has(nameKey(b.name))) espnIds.set(nameKey(b.name), b.athleteId);

  const problems = new Set();
  const found = [];
  for (const h of ['home', 'away']) {
    const team = espn[h]?.team ?? {};
    const rows = game[`${h}Team`].players.filter(p => !String(p.comment ?? '').trim());   // a comment means DNP/DND/NWT
    if (!rows.length) { problems.add('NBA_NO_PLAYERS'); continue; }
    let pts = 0, secs = 0;
    for (const p of rows) {
      if (!/^\d+:\d{2}$/.test(String(p.statistics?.minutes ?? ''))) { problems.add('NBA_BLANK_ROWS'); continue; }
      const line = nbaStatLine(p.statistics);
      const [mm, ss] = p.statistics.minutes.split(':').map(Number);
      pts += line.pts;
      secs += mm * 60 + ss;
      if (!isBillion(line)) continue;
      const name = [p.firstName, p.familyName].filter(Boolean).join(' ') || p.nameI;
      found.push({
        date: ctx.date, eventId: ctx.eventId, season: ctx.season, seasonType: ctx.seasonType, matchup: ctx.matchup,
        athleteId: espnIds.get(nameKey(name)) ?? `nba-${p.personId}`,
        name,
        teamAbbr: team.abbreviation ?? '',
        team: team.name ?? team.shortDisplayName ?? '',
        stats: line,
        source: 'nba.com',
      });
    }
    if (pts !== ref(h).score) problems.add('NBA_POINTS_MISMATCH');
    if (secs < 230 * 60) problems.add('NBA_LOW_MINUTES');
  }
  return problems.size ? { problems: [...problems] } : { billions: found, nbaGameId };
}

/** Find every billion in one game summary. */
export function billionsInSummary(summary, ctx) {
  const found = [];
  for (const teamBlock of summary?.boxscore?.players ?? []) {
    const team = teamBlock.team ?? {};
    for (const group of teamBlock.statistics ?? []) {
      const keys = group.keys ?? [];
      for (const row of group.athletes ?? []) {
        if (row.didNotPlay || !row.stats?.length) continue;
        // Skip rows with no real stats (ESPN shows "--" or blanks when a box score is missing)
        const minIdx = keys.indexOf('minutes');
        if (minIdx < 0 || !/^\d+/.test(String(row.stats[minIdx] ?? '').trim())) continue;
        const line = parseStatLine(keys, row.stats);
        if (!isBillion(line)) continue;
        found.push({
          date: ctx.date,
          eventId: ctx.eventId,
          season: ctx.season,
          seasonType: ctx.seasonType,
          matchup: ctx.matchup,
          athleteId: String(row.athlete?.id ?? row.athlete?.displayName),
          name: row.athlete?.displayName ?? 'Unknown',
          teamAbbr: team.abbreviation ?? '',
          team: team.name ?? team.shortDisplayName ?? team.displayName ?? '',
          stats: line,
        });
      }
    }
  }
  return found;
}

// All-Star weekend and other showcase games aren't real games.
const EXHIBITION = /all-?star|rising stars|celebrity|team (lebron|giannis|durant|stephen|curry|chuck|shaq|kenny|candace)|\b(east|west)\b.*\b(east|west)\b|world vs|usa vs/i;

async function loadData() {
  const blank = { updated: null, lastGameDate: null, processedEvents: {}, badGames: {}, nbaFilled: {}, billions: [] };
  try {
    return { ...blank, ...JSON.parse(await readFile(DATA_FILE, 'utf8')) };
  } catch {
    return blank;
  }
}

async function saveData(data) {
  // Keep the file tidy: chronological, no duplicates.
  const seen = new Set();
  for (const [id, date] of Object.entries(data.processedEvents)) {
    if (date < `${FIRST_SEASON - 1}-08-01`) delete data.processedEvents[id];
  }
    data.billions = data.billions
    .filter(b => b.season >= FIRST_SEASON)
    .map(applyEraNames)
    .map(b => { b.name = fixName(b.name); return b; });

  // Billions filled in from NBA.com whose player couldn't be matched to ESPN get an "nba-" ID.
  // If an ESPN ID exists for the same name, move them under it so the player isn't listed twice.
  const espnIdByName = new Map();
  for (const b of data.billions) {
    if (!String(b.athleteId).startsWith('nba-') && !espnIdByName.has(nameKey(b.name))) espnIdByName.set(nameKey(b.name), b.athleteId);
  }
  for (const b of data.billions) {
    if (String(b.athleteId).startsWith('nba-') && espnIdByName.has(nameKey(b.name))) b.athleteId = espnIdByName.get(nameKey(b.name));
  }

  data.billions = data.billions
    .filter(b => { const k = `${b.eventId}:${b.athleteId}`; if (seen.has(k)) return false; seen.add(k); return true; })
    .sort((a, b) => a.date.localeCompare(b.date) || a.eventId.localeCompare(b.eventId) || a.name.localeCompare(b.name));
  data.rule = BILLION_RULE;
  data.updated = new Date().toISOString();

  await mkdir(dirname(DATA_FILE), { recursive: true });
  const json = JSON.stringify(data);
  await writeFile(DATA_FILE, json + '\n');
  // Same data as a script file, so billions.html also works when opened
  // straight from your folder (browsers block reading .json files that way).
  await writeFile(DATA_FILE.replace(/\.json$/, '.js'), `window.BILLIONS_DATA = ${json};\n`);
}

/** Run fn over items with at most `limit` running at once. */
async function pool(items, limit, fn) {
  let next = 0;
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, async () => {
    while (next < items.length) await fn(items[next++]);
  }));
}

async function processDay(ymd, data) {
  const board = await getJson(`${ESPN_BASE}/scoreboard?dates=${ymd}`);
  const events = board.events ?? [];
  let newOnes = 0, pending = 0, done = 0, skipped = 0, broken = 0, filled = 0;
  const todo = [];

  for (const ev of events) {
    if (data.processedEvents[ev.id]) { done++; continue; }
    const seasonType = ev.season?.type ?? board.leagues?.[0]?.season?.type?.type;
    const season = ev.season?.year ?? board.leagues?.[0]?.season?.year;
    if (season < FIRST_SEASON) { skipped++; continue; }
    if ((!COUNT_PRESEASON && seasonType === 1) || EXHIBITION.test(`${ev.name} | ${ev.shortName}`)) { skipped++; continue; }
    if (/POSTPONED|CANCELED|CANCELLED/.test(ev.status?.type?.name ?? '')) { skipped++; continue; }
    if (!ev.status?.type?.completed) { pending++; continue; }
    todo.push({ ev, seasonType });
  }

  await pool(todo, CONCURRENCY, async ({ ev, seasonType }) => {
    const comp = ev.competitions?.[0] ?? {};
    const away = comp.competitors?.find(c => c.homeAway === 'away')?.team?.abbreviation ?? '?';
    const home = comp.competitors?.find(c => c.homeAway === 'home')?.team?.abbreviation ?? '?';
    const ctx = {
      date: toIso(ymd),
      eventId: String(ev.id),
      season: ev.season?.year ?? board.leagues?.[0]?.season?.year,
      seasonType,
      matchup: `${away}@${home}`,
    };
    const summary = await getJson(`${ESPN_BASE}/summary?event=${ev.id}`);

    // Older seasons: skip games whose box score is broken, so bad data can't create fake billions.
    if (ctx.season <= CHECK_SEASONS_THROUGH) {
      const finalScores = new Map((comp.competitors ?? []).map(c => [String(c.team?.id), parseInt(c.score, 10)]));
      const problems = boxScoreProblems(summary, finalScores);
      if (problems.length && NBA_FALLBACK) {
        let nba;
        try { nba = await nbaFallback(ctx, comp, summary, data); }
        catch (err) { nba = { problems: ['NBA_FETCH_FAILED'] }; console.error(`  NBA.com: ${err.message}`); }
        if (nba.billions) {
          data.billions.push(...nba.billions);
          data.nbaFilled[ev.id] = nba.nbaGameId;
          delete data.badGames[ev.id];
          data.processedEvents[ev.id] = ctx.date;
          newOnes += nba.billions.length;
          filled++;
          done++;
          for (const b of nba.billions) console.log(`  BILLION (from NBA.com): ${b.name} (${b.teamAbbr}) ${b.matchup}`);
          return;
        }
        problems.push(...nba.problems);
      }
      if (problems.length) {
        data.badGames[ev.id] = { date: ctx.date, game: ctx.matchup, problems };
        data.processedEvents[ev.id] = ctx.date;
        broken++;
        done++;
        return;
      }
    }

    const found = billionsInSummary(summary, ctx);
    data.billions.push(...found);
    data.processedEvents[ev.id] = ctx.date;
    newOnes += found.length;
    done++;
    for (const b of found) console.log(`  BILLION: ${b.name} (${b.teamAbbr}) ${b.matchup}`);
  });

  if (done > 0 && (!data.lastGameDate || toIso(ymd) > data.lastGameDate)) {
    data.lastGameDate = toIso(ymd);
  }
  if (events.length) {
    console.log(`${toIso(ymd)}: ${events.length} games, ${newOnes} new billions` +
      (skipped ? `, ${skipped} skipped (preseason/All-Star/postponed/too old)` : '') +
      (filled ? `, ${filled} filled in from NBA.com` : '') +
      (broken ? `, ${broken} broken box score${broken === 1 ? '' : 's'} not counted` : '') +
      (pending ? `, ${pending} not final yet (will retry next run)` : ''));
  }
  return pending === 0;
}

async function main() {
  const args = process.argv.slice(2);
  const arg = name => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : null; };
  const yesterday = shiftYmd(ymdInZone(new Date()), -1);
  const data = await loadData();

  let days;
  if (arg('--date')) days = [arg('--date')];
  else if (arg('--from')) days = rangeYmd(arg('--from'), arg('--to') || yesterday);
  else {
    // Normal nightly run: only the last LOOKBACK_DAYS days (yesterday and the day before).
    days = rangeYmd(shiftYmd(yesterday, -(LOOKBACK_DAYS - 1)), yesterday);
  }
  // --retry-broken: give games that were skipped as broken another try (e.g. via NBA.com).
  if (args.includes('--retry-broken')) {
    const first = toIso(days[0]), last = toIso(days[days.length - 1]);
    let n = 0;
    for (const [id, g] of Object.entries(data.badGames)) {
      if (g.date >= first && g.date <= last) { delete data.processedEvents[id]; n++; }
    }
    console.log(`Retrying ${n} broken game${n === 1 ? '' : 's'} between ${first} and ${last}.`);
  }
  if (days.length > 30) console.log(`Checking ${days.length} days — this can take a while. Progress is saved as it goes; if it stops, run the same command again to pick up where it left off.`);

  let allOk = true, lastSave = Date.now();
  for (const d of days) {
    let ok;
    try { ok = await processDay(d, data); }
    catch (err) { console.error(`${toIso(d)}: failed — ${err.message}`); process.exitCode = 1; ok = false; }
    // The nightly run resumes from the last day that fully finished.
    if (ok && allOk && (!data.lastCheckedDay || toIso(d) > data.lastCheckedDay)) data.lastCheckedDay = toIso(d);
    if (!ok) allOk = false;
    if (Date.now() - lastSave > 30_000) { await saveData(data); lastSave = Date.now(); }
  }

  await saveData(data);
  console.log(`Saved ${data.billions.length} billions (${Object.keys(data.processedEvents).length} games checked) to ${DATA_FILE}`);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
