#!/usr/bin/env node
/**
 * NFL Fields — image shrinker + page data builder.
 *
 * Reads your "NFL field schedule YYYY" folders, makes web-sized copies of every
 * field image, and writes the list the NFL Fields page reads. Your originals are
 * never changed.
 *
 * One-time setup, in your site folder (logos-site):
 *   npm install sharp
 *   echo node_modules >> .gitignore        # keeps the image library out of GitHub
 *
 * The site only ever uses the copies this script saves in images/fields/, never the
 * originals in iCloud.
 *
 * Usage:
 *   node build-fields.mjs "/Users/luke/Library/Mobile Documents/com~apple~CloudDocs/Sports/Fields:Courts/NFL"
 *   node build-fields.mjs "<same folder>" --year 2025      # just one year
 *
 * Output (inside your site folder):
 *   images/fields/2025/arizona-cardinals.webp       full size, shown when you click
 *   images/fields/2025/arizona-cardinals-sm.webp    small preview for the page
 *   data/fields.js                                  the list the page reads
 *
 * Re-running is quick: images that are already up to date are skipped, and their originals
 * aren't even opened, so it doesn't matter if iCloud has offloaded them. New or changed
 * images that iCloud has offloaded are downloaded automatically first.
 */

import { readdir, stat, mkdir, writeFile, readFile } from 'node:fs/promises';
import { join, dirname, resolve, extname, basename } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFile } from 'node:child_process';

let sharp;
try { sharp = (await import('sharp')).default; }
catch {
  console.error('This needs the "sharp" image library. In this folder, run:  npm install sharp');
  process.exit(1);
}

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT_IMAGES = resolve(HERE, 'images/fields');
const OUT_DATA = resolve(HERE, 'data/fields.js');
const FULL_WIDTH = 1600;    // full-size copy, shown when a field is clicked
const THUMB_WIDTH = 640;    // preview on the page (sharp on high-resolution screens)
const QUALITY = 82;         // WebP quality (0-100)
// Only folders named exactly like "NFL field schedule 2024" are used (capital letters don't matter).
// Anything else in the NFL folder, like "NFL Fields 2014" with Illustrator files, is ignored.
const SEASON_FOLDER = /^NFL field schedule ((?:19|20)\d{2})$/i;
const IMAGE_TYPES = new Set(['.png', '.jpg', '.jpeg', '.gif', '.webp', '.tif', '.tiff']);

// Every team name used since 2013, longest first so "Los Angeles Chargers" wins over shorter matches.
const TEAMS = [
  'Arizona Cardinals', 'Atlanta Falcons', 'Baltimore Ravens', 'Buffalo Bills', 'Carolina Panthers',
  'Chicago Bears', 'Cincinnati Bengals', 'Cleveland Browns', 'Dallas Cowboys', 'Denver Broncos',
  'Detroit Lions', 'Green Bay Packers', 'Houston Texans', 'Indianapolis Colts', 'Jacksonville Jaguars',
  'Kansas City Chiefs', 'Las Vegas Raiders', 'Oakland Raiders', 'Los Angeles Chargers', 'San Diego Chargers',
  'Los Angeles Rams', 'St. Louis Rams', 'St Louis Rams', 'Miami Dolphins', 'Minnesota Vikings',
  'New England Patriots', 'New Orleans Saints', 'New York Giants', 'New York Jets', 'Philadelphia Eagles',
  'Pittsburgh Steelers', 'San Francisco 49ers', 'Seattle Seahawks', 'Tampa Bay Buccaneers', 'Tennessee Titans',
  'Washington Commanders', 'Washington Football Team', 'Washington Redskins',
].sort((a, b) => b.length - a.length);

/** "Atlanta Falcons throwback Atlanta end zones" → { team: "Atlanta Falcons", label: "Throwback Atlanta end zones" } */
function parseName(name) {
  const team = TEAMS.find(t => name.toLowerCase() === t.toLowerCase() || name.toLowerCase().startsWith(t.toLowerCase() + ' '));
  if (!team) return { team: null, label: name };
  const rest = name.slice(team.length).trim();
  return { team, label: rest ? rest[0].toUpperCase() + rest.slice(1) : 'Base' };
}

const slug = s => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
  .replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');

async function newer(src, out) {
  try { return (await stat(out)).mtimeMs >= (await stat(src)).mtimeMs; } catch { return false; }
}

/**
 * Read an original image. If iCloud has offloaded it from this Mac, ask iCloud to
 * download it (brctl is built into macOS) and wait up to 2 minutes for it to arrive.
 */
async function readOriginal(src) {
  try {
    const buf = await readFile(src);
    if (buf.length) return buf;
  } catch {}
  if (process.platform !== 'darwin') throw new Error('file could not be read');
  process.stdout.write(`  downloading from iCloud: ${basename(src)} … `);
  await new Promise(done => execFile('brctl', ['download', src], () => done()));
  for (let waited = 0; waited < 300; waited += 2) {   // big files (like large GIFs) can take a while
    await new Promise(r => setTimeout(r, 2000));
    try {
      const buf = await readFile(src);
      if (buf.length) { console.log('done'); return buf; }
    } catch {}
  }
  console.log('gave up');
  throw new Error("iCloud didn't download it within 5 minutes; run the script again to retry");
}

async function makeCopies(src, outBase) {
  const full = `${outBase}.webp`, thumb = `${outBase}-sm.webp`;
  const animated = extname(src).toLowerCase() === '.gif';
  // Only open the original when a copy is missing or out of date. Once both copies exist,
  // the site never needs the original again, even if iCloud offloads it from this Mac.
  const needFull = !(await newer(src, full)), needThumb = !(await newer(src, thumb));
  if (needFull || needThumb) {
    const original = await readOriginal(src);
    if (animated && original.length > 5e6) console.log(`  big animated GIF: ${basename(src)} (${(original.length / 1e6).toFixed(1)} MB), this one takes a minute…`);
    // limitInputPixels: false — animated GIFs count every frame, which can trip the library's size safety limit.
    if (needFull) {
      await sharp(original, { animated, limitInputPixels: false })
        .resize({ width: FULL_WIDTH, withoutEnlargement: true }).webp({ quality: QUALITY, effort: 4 }).toFile(full);
    }
    // The preview on the page uses the first frame only, so the page stays light.
    // Clicking the field shows the full animation.
    if (needThumb) {
      await sharp(original, { animated: false, limitInputPixels: false })
        .resize({ width: THUMB_WIDTH, withoutEnlargement: true }).webp({ quality: QUALITY }).toFile(thumb);
    }
  }
  const meta = await sharp(thumb, { limitInputPixels: false }).metadata();
  return { w: meta.width, h: meta.pageHeight || meta.height };
}

async function main() {
  const args = process.argv.slice(2);
  const root = args.find(a => !a.startsWith('--'));
  const only = args.includes('--year') ? args[args.indexOf('--year') + 1] : null;
  if (!root) {
    console.log('Tell me where your field folders are, e.g.:\n  node build-fields.mjs "/Users/luke/Library/Mobile Documents/com~apple~CloudDocs/Sports/Fields:Courts/NFL"');
    process.exit(1);
  }

  // Keep years already built when only rebuilding one.
  let data = { years: {} };
  try {
    const old = await readFile(OUT_DATA, 'utf8');
    data = JSON.parse(old.slice(old.indexOf('{'), old.lastIndexOf('}') + 1));
  } catch {}

  const folders = (await readdir(root, { withFileTypes: true }))
    .filter(d => d.isDirectory() && SEASON_FOLDER.test(d.name.trim()))
    .map(d => ({ path: join(root, d.name), year: d.name.trim().match(SEASON_FOLDER)[1] }))
    .filter(f => !only || f.year === only)
    .sort((a, b) => a.year.localeCompare(b.year));
  if (!folders.length) { console.log(`No year folders found in ${root}`); process.exit(1); }

  let beforeBytes = 0, afterBytes = 0;
  for (const { path, year } of folders) {
    const files = (await readdir(path)).filter(f => IMAGE_TYPES.has(extname(f).toLowerCase()) && !f.startsWith('.')).sort();
    await mkdir(join(OUT_IMAGES, year), { recursive: true });
    const fields = [], unmatched = [], used = new Set();
    for (const file of files) {
      const src = join(path, file);
      const name = basename(file, extname(file)).normalize('NFC').trim();
      const { team, label } = parseName(name);
      if (!team) unmatched.push(file);
      let id = slug(name) || 'field';
      while (used.has(id)) id += '-2';
      used.add(id);
      try {
        const size = await makeCopies(src, join(OUT_IMAGES, year, id));
        beforeBytes += (await stat(src)).size;
        afterBytes += (await stat(join(OUT_IMAGES, year, `${id}-sm.webp`))).size;
        fields.push({ team: team ?? 'Other fields', label: team ? label : name, img: `images/fields/${year}/${id}.webp`, thumb: `images/fields/${year}/${id}-sm.webp`, ...size });
      } catch (err) {
        console.error(`  ${year}: skipped "${file}" (${err.message}).`);
      }
    }
    // Teams A–Z, "Base" first within each team, then the rest A–Z.
    fields.sort((a, b) =>
      (a.team === 'Other fields') - (b.team === 'Other fields') || a.team.localeCompare(b.team) ||
      (b.label === 'Base') - (a.label === 'Base') || a.label.localeCompare(b.label));
    data.years[year] = fields;
    const teams = new Set(fields.map(f => f.team)).size;
    console.log(`${year}: ${fields.length} fields, ${teams} teams` + (unmatched.length ? `  (no team name found: ${unmatched.join(', ')})` : ''));
  }

  data.built = new Date().toISOString();
  await mkdir(dirname(OUT_DATA), { recursive: true });
  await writeFile(OUT_DATA, `window.FIELDS_DATA = ${JSON.stringify(data)};\n`);
  const size = n => n >= 1e6 ? `${(n / 1e6).toFixed(1)} MB` : `${Math.round(n / 1e3)} KB`;
  if (beforeBytes) {
    console.log(`\nPage previews: ${size(afterBytes)} total, down from ${size(beforeBytes)} of originals (${Math.round(100 - afterBytes / beforeBytes * 100)}% smaller).`);
  }
  console.log(`Saved ${OUT_DATA}`);
}

main();
