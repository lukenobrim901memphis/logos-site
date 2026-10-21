#!/usr/bin/env node
/**
 * Billions tracker — nightly updater.
 *
 * Pulls NBA scoreboards from ESPN, opens the box score of every finished game,
 * and records every player line that qualifies as a "billion". Results are kept
 * in data/billions.json, which billions.html reads.
 *
 * Usage (Node 18+, no npm packages needed):
 *   node update-billions.mjs                      # yesterday (plus a short look-back for late games)
 *   node update-billions.mjs --date 20261020      # one specific day
 *   node update-billions.mjs --from 20261020 --to 20261031   # backfill a range
 *   node update-billions.mjs --from 20161025                 # everything since the 2016-17 opener
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
const LOOKBACK_DAYS = 3;                // always re-check at least this many recent days
const COUNT_PRESEASON = false;          // season type 1 = preseason
const FIRST_SEASON = 2017;              // earliest season tracked (2017 = 2016-17); older ESPN box scores are unreliable
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
  const blank = { updated: null, lastGameDate: null, processedEvents: {}, billions: [] };
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
  let newOnes = 0, pending = 0, done = 0, skipped = 0;
  const todo = [];

  for (const ev of events) {
    if (data.processedEvents[ev.id]) { done++; continue; }
    const seasonType = ev.season?.type ?? board.leagues?.[0]?.season?.type?.type;
    const season = ev.season?.year ?? board.leagues?.[0]?.season?.year;
    if (season < FIRST_SEASON) { skipped++; continue; }
    if ((!COUNT_PRESEASON && seasonType === 1) || EXHIBITION.test(`${ev.name} | ${ev.shortName}`)) { skipped++; continue; }
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
      (skipped ? `, ${skipped} skipped (preseason/All-Star/before 2016-17)` : '') +
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
    // Normal nightly run: check yesterday, plus every day since the last run
    // (so nights when the computer was off or asleep get filled in automatically).
    const lastRun = data.lastCheckedDay?.replace(/-/g, '');
    let start = shiftYmd(yesterday, -(LOOKBACK_DAYS - 1));
    if (lastRun && lastRun < start) start = shiftYmd(lastRun, -1);
    days = rangeYmd(start, yesterday);
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
