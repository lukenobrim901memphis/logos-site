#!/usr/bin/env node
/**
 * MLB guessing game — data builder.
 *
 * Downloads every team's season roster from MLB's public stats service
 * (statsapi.mlb.com) and saves the players the game picks from.
 *
 * Usage (Node 18+, no npm packages needed), from the same folder as mlb-guess.html:
 *   node build-mlb-guess.mjs --test        # check one team (2015 Padres) and print it
 *   node build-mlb-guess.mjs               # build everything, 2012 to last season
 *   node build-mlb-guess.mjs --from 2020   # rebuild from 2020 on (e.g. to add a new season)
 *
 * Output: data/mlb-guess.js (what the game page loads) and data/mlb-guess.json.
 * Each team-season is cached in data/mlb-cache/, so re-running is quick and an
 * interrupted build picks up where it left off.
 *
 * Difficulty mixes two things, each ranked against every other player-season:
 *   - playing time that season (plate appearances, or batters faced for pitchers)
 *   - career length (years from MLB debut to last MLB game)
 * The top third of the combined score is "easy", the middle third "medium", the bottom third "hard".
 */

import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const API = process.env.MLB_API || 'https://statsapi.mlb.com/api/v1';
const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(HERE, 'data/mlb-guess.json');
const CACHE = resolve(HERE, 'data/mlb-cache');
const FIRST_SEASON = 2012;
const CONCURRENCY = 4;

const args = process.argv.slice(2);
const arg = n => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : null; };
const TEST = args.includes('--test');
const now = new Date();
// The latest finished season: this year once October is over, otherwise last year.
const LAST_SEASON = +(arg('--to') || (now.getMonth() >= 10 ? now.getFullYear() : now.getFullYear() - 1));
const FROM = +(arg('--from') || FIRST_SEASON);

async function getJson(url, tries = 3) {
  for (let i = 1; ; i++) {
    try {
      const res = await fetch(url, { headers: { 'User-Agent': 'mlb-guess/1.0' }, signal: AbortSignal.timeout(30000) });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      if (i >= tries) throw new Error(`${url}: ${err.message}`);
      await new Promise(r => setTimeout(r, 1500 * i));
    }
  }
}

async function pool(items, limit, fn) {
  let next = 0;
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, async () => {
    while (next < items.length) await fn(items[next++]);
  }));
}

const POSITIONS = {
  C: 'Catcher', '1B': 'First base', '2B': 'Second base', '3B': 'Third base', SS: 'Shortstop',
  LF: 'Left field', CF: 'Center field', RF: 'Right field', OF: 'Outfield', DH: 'Designated hitter',
  SP: 'Starting pitcher', RP: 'Relief pitcher', TWP: 'Two-way player', IF: 'Infield', UT: 'Utility',
};
const HANDS = { R: 'Right', L: 'Left', S: 'Switch' };

/** Age on June 30 of the season (the usual baseball "season age"). */
function seasonAge(birthDate, season) {
  if (!birthDate) return null;
  const [y, m, d] = birthDate.split('-').map(Number);
  let age = season - y;
  if (m > 6 || (m === 6 && d > 30)) age--;
  return age;
}

/** Find this team's split for a stat group (traded players have one split per team). */
function seasonStat(person, group, teamId) {
  const block = (person.stats ?? []).find(s =>
    s.group?.displayName === group && /season/i.test(s.type?.displayName ?? ''));
  const splits = block?.splits ?? [];
  return (splits.find(s => s.team?.id === teamId) ?? (splits.length === 1 ? splits[0] : null))?.stat ?? null;
}

/** One team-season → list of players (from cache when possible). */
async function teamSeason(team, season) {
  const file = resolve(CACHE, `${season}-${team.id}.json`);
  try { return JSON.parse(await readFile(file, 'utf8')); } catch {}

  const url = `${API}/teams/${team.id}/roster?rosterType=fullSeason&season=${season}` +
    `&hydrate=person(stats(type=season,season=${season},group=[hitting,pitching]))`;
  const roster = (await getJson(url)).roster ?? [];
  const players = [];
  for (const r of roster) {
    const p = r.person ?? {};
    const pos = r.position?.abbreviation || p.primaryPosition?.abbreviation || '';
    const isPitcher = pos === 'P' || (pos === 'TWP' ? false : p.primaryPosition?.type === 'Pitcher');
    const hit = seasonStat(p, 'hitting', team.id);
    const pit = seasonStat(p, 'pitching', team.id);

    let position, games, usage, hand;
    if (isPitcher) {
      if (!pit) continue;
      games = pit.gamesPitched ?? pit.gamesPlayed ?? 0;
      position = (pit.gamesStarted ?? 0) * 2 >= games && games > 0 ? 'SP' : 'RP';
      usage = pit.battersFaced ?? Math.round(parseFloat(pit.inningsPitched ?? 0) * 4.3);
      hand = p.pitchHand?.code;
    } else if (pos === 'TWP') {
      games = Math.max(hit?.gamesPlayed ?? 0, pit?.gamesPitched ?? 0);
      position = 'TWP';
      usage = (hit?.plateAppearances ?? 0) + (pit?.battersFaced ?? 0);
      hand = p.batSide?.code;
    } else {
      if (!hit) continue;
      games = hit.gamesPlayed ?? 0;
      position = POSITIONS[pos] ? pos : (p.primaryPosition?.abbreviation ?? pos);
      usage = hit.plateAppearances ?? hit.atBats ?? 0;
      hand = p.batSide?.code;
    }
    if (!games) continue;

    const first = p.useName || p.firstName || (p.fullName ?? '').split(' ')[0];
    const last = p.useLastName || p.lastName || (p.fullName ?? '').split(' ').slice(-1)[0];
    const debut = +(p.mlbDebutDate ?? '').slice(0, 4) || season;
    const lastYear = +(p.lastPlayedDate ?? '').slice(0, 4) || (p.active ? LAST_SEASON : season);
    players.push({
      id: p.id,
      name: p.fullName || `${first} ${last}`,
      first, last,
      position,
      role: isPitcher ? 'P' : 'H',
      hand: hand || '',
      bats: p.batSide?.code || '',
      throws: p.pitchHand?.code || '',
      age: seasonAge(p.birthDate, season),
      games,
      usage,
      careerYears: Math.max(1, Math.max(lastYear, season) - Math.min(debut, season) + 1),
    });
  }
  await mkdir(CACHE, { recursive: true });
  await writeFile(file, JSON.stringify(players));
  return players;
}

async function teamsFor(season) {
  const data = await getJson(`${API}/teams?sportId=1&season=${season}`);
  return (data.teams ?? []).filter(t => t.sport?.id === 1 || !t.sport).map(t => ({
    id: t.id, name: t.teamName || t.clubName || t.name, abbr: t.abbreviation, full: t.name,
  }));
}

async function test() {
  console.log('Test: 2015 San Diego Padres\n');
  const teams = await teamsFor(2015);
  const padres = teams.find(t => t.id === 135) ?? teams.find(t => /padres/i.test(t.full));
  if (!padres) { console.log(`Couldn't find the Padres. Teams found: ${teams.map(t => t.name).join(', ')}`); return; }
  const players = await teamSeason(padres, 2015);
  console.log(`${players.length} players who appeared for the ${padres.full}:\n`);
  for (const p of players.sort((a, b) => b.usage - a.usage)) {
    const initials = `${p.first[0]}${p.last[0]}`;
    console.log(`  ${initials.padEnd(3)} ${p.name.padEnd(22)} ${(POSITIONS[p.position] ?? p.position).padEnd(18)} ` +
      `${(HANDS[p.hand] ?? p.hand).padEnd(7)} age ${String(p.age).padEnd(3)} ${String(p.games).padStart(3)} G   ` +
      `usage ${String(p.usage).padStart(4)}   career ${p.careerYears} yrs`);
  }
  const mm = players.find(p => /mateo/i.test(p.last));
  console.log(mm ? `\nMarcos Mateo check: ${POSITIONS[mm.position]}, ${HANDS[mm.hand]}, ${mm.games} games, age ${mm.age}`
                 : '\nMarcos Mateo not found on this roster.');
}

/** Rank each value against the rest: 0 = lowest, 1 = highest. */
function percentiles(values) {
  const sorted = [...values].sort((a, b) => a - b);
  const n = sorted.length;
  return values.map(v => {
    let lo = 0, hi = n;
    while (lo < hi) { const mid = (lo + hi) >> 1; if (sorted[mid] < v) lo = mid + 1; else hi = mid; }
    let hi2 = lo; while (hi2 < n && sorted[hi2] === v) hi2++;
    return n > 1 ? ((lo + hi2 - 1) / 2) / (n - 1) : 0.5;
  });
}

async function build() {
  // Start from what's already built so --from only redoes later seasons.
  let existing = { seasons: {} };
  try { existing = JSON.parse(await readFile(OUT, 'utf8')); } catch {}

  const rows = [];
  const teamNames = {};
  for (let season = FIRST_SEASON; season <= LAST_SEASON; season++) {
    const keep = season < FROM && existing.seasons?.[season];
    if (keep) {
      teamNames[season] = existing.teamNames[season];
      for (const r of existing.raw[season]) rows.push({ ...r, season });
      console.log(`${season}: kept from last build`);
      continue;
    }
    const teams = await teamsFor(season);
    teamNames[season] = Object.fromEntries(teams.map(t => [t.id, { name: t.name, abbr: t.abbr, full: t.full }]));
    let count = 0, failed = 0;
    await pool(teams, CONCURRENCY, async team => {
      try {
        const players = await teamSeason(team, season);
        for (const p of players) rows.push({ ...p, season, team: team.id });
        count += players.length;
      } catch (err) {
        failed++;
        console.error(`  ${season} ${team.full}: ${err.message}`);
      }
    });
    console.log(`${season}: ${teams.length} teams, ${count} players` + (failed ? ` (${failed} teams failed, run again to retry)` : ''));
  }

  // Difficulty: average of playing-time rank (within hitters / within pitchers) and career-length rank.
  const scores = new Array(rows.length).fill(0);
  for (const role of ['H', 'P']) {
    const idx = rows.map((r, i) => (r.role === role ? i : -1)).filter(i => i >= 0);
    const pct = percentiles(idx.map(i => rows[i].usage));
    idx.forEach((i, k) => { scores[i] += pct[k] / 2; });
  }
  const careerPct = percentiles(rows.map(r => r.careerYears));
  rows.forEach((r, i) => { scores[i] += careerPct[i] / 2; });
  const cut = percentiles(scores);
  rows.forEach((r, i) => { r.tier = cut[i] >= 2 / 3 ? 'E' : cut[i] >= 1 / 3 ? 'M' : 'H'; });

  // Compact output for the page: one array per player-season.
  const fields = ['season', 'team', 'name', 'first', 'last', 'position', 'hand', 'age', 'games', 'tier', 'bats', 'throws'];
  const raw = {};
  for (const r of rows) {
    const { season, ...rest } = r;
    (raw[season] ??= []).push(rest);
  }
  const out = {
    built: new Date().toISOString(),
    seasons: Object.fromEntries(Object.keys(raw).map(s => [s, raw[s].length])),
    teamNames,
    fields,
    players: rows.map(r => fields.map(f => r[f])),
    raw,   // kept so the next build can reuse finished seasons
  };
  await mkdir(dirname(OUT), { recursive: true });
  await writeFile(OUT, JSON.stringify(out));
  const { raw: _, ...forPage } = out;
  await writeFile(OUT.replace(/\.json$/, '.js'), `window.MLB_GUESS_DATA = ${JSON.stringify(forPage)};\n`);

  const tiers = rows.reduce((t, r) => ((t[r.tier] = (t[r.tier] || 0) + 1), t), {});
  console.log(`\nSaved ${rows.length} player-seasons (easy ${tiers.E || 0}, medium ${tiers.M || 0}, hard ${tiers.H || 0}).`);
  console.log(`Game data: ${OUT.replace(/\.json$/, '.js')}`);
}

(TEST ? test() : build()).catch(err => { console.error(err.message); process.exitCode = 1; });
