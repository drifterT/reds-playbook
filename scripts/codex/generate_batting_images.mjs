#!/usr/bin/env node

/**
 * Generate or edit the batting-slide raster assets described in
 * batting-image-jobs.json.
 *
 * Requirements:
 *   - Node.js 20 or newer
 *   - OPENAI_API_KEY
 *
 * Examples:
 *   node scripts/codex/generate_batting_images.mjs --list
 *   node scripts/codex/generate_batting_images.mjs --job slide3-mobility-v2 --dry-run
 *   node scripts/codex/generate_batting_images.mjs --job slide3-mobility-v2
 *   node scripts/codex/generate_batting_images.mjs --all
 */

import crypto from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import {fileURLToPath} from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(scriptDir, '../..');
const defaultManifestPath = path.join(scriptDir, 'batting-image-jobs.json');

function parseArgs(argv) {
  const options = {
    all: false,
    dryRun: false,
    force: false,
    list: false,
    jobIds: [],
    manifestPath: defaultManifestPath,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === '--all') options.all = true;
    else if (arg === '--dry-run') options.dryRun = true;
    else if (arg === '--force') options.force = true;
    else if (arg === '--list') options.list = true;
    else if (arg === '--job') options.jobIds.push(argv[++index]);
    else if (arg === '--manifest') options.manifestPath = path.resolve(argv[++index]);
    else if (arg === '--help' || arg === '-h') options.help = true;
    else throw new Error(`Unknown argument: ${arg}`);
  }
  return options;
}

function printHelp() {
  console.log(`Usage:
  generate_batting_images.mjs --list
  generate_batting_images.mjs --job <id> [--job <id> ...] [--dry-run] [--force]
  generate_batting_images.mjs --all [--dry-run] [--force]

Options:
  --list             List available jobs without calling the API.
  --job <id>         Run one named job. Repeat to run several jobs.
  --all              Run every job whose enabled field is true.
  --dry-run          Print the resolved request without calling the API.
  --force            Overwrite an existing output file.
  --manifest <path>  Use a different jobs manifest.
`);
}

async function readJson(filePath) {
  return JSON.parse(await fs.readFile(filePath, 'utf8'));
}

function absoluteRepoPath(relativePath) {
  const resolved = path.resolve(repoRoot, relativePath);
  if (!resolved.startsWith(`${repoRoot}${path.sep}`)) {
    throw new Error(`Path escapes repository root: ${relativePath}`);
  }
  return resolved;
}

function contentTypeFor(filePath) {
  const extension = path.extname(filePath).toLowerCase();
  if (extension === '.png') return 'image/png';
  if (extension === '.jpg' || extension === '.jpeg') return 'image/jpeg';
  if (extension === '.webp') return 'image/webp';
  throw new Error(`Unsupported reference-image type: ${filePath}`);
}

function requestSummary(job, defaults) {
  return {
    id: job.id,
    mode: job.mode,
    endpoint: job.mode === 'edit' ? '/v1/images/edits' : '/v1/images/generations',
    model: job.model ?? defaults.model,
    size: job.size ?? defaults.size,
    quality: job.quality ?? defaults.quality,
    outputFormat: job.outputFormat ?? defaults.outputFormat,
    references: job.references ?? [],
    output: job.output,
    prompt: job.prompt,
  };
}

async function callGenerate(job, defaults, apiKey) {
  const body = {
    model: job.model ?? defaults.model,
    prompt: job.prompt,
    size: job.size ?? defaults.size,
    quality: job.quality ?? defaults.quality,
    output_format: job.outputFormat ?? defaults.outputFormat,
    n: 1,
  };

  return fetch('https://api.openai.com/v1/images/generations', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });
}

async function callEdit(job, defaults, apiKey) {
  if (!job.references?.length) {
    throw new Error(`Edit job ${job.id} has no reference images.`);
  }

  const form = new FormData();
  form.append('model', job.model ?? defaults.model);
  form.append('prompt', job.prompt);
  form.append('size', job.size ?? defaults.size);
  form.append('quality', job.quality ?? defaults.quality);
  form.append('output_format', job.outputFormat ?? defaults.outputFormat);

  for (const relativePath of job.references) {
    const filePath = absoluteRepoPath(relativePath);
    const bytes = await fs.readFile(filePath);
    form.append('image[]', new Blob([bytes], {type: contentTypeFor(filePath)}), path.basename(filePath));
  }

  return fetch('https://api.openai.com/v1/images/edits', {
    method: 'POST',
    headers: {Authorization: `Bearer ${apiKey}`},
    body: form,
  });
}

async function runJob(job, defaults, options) {
  const summary = requestSummary(job, defaults);
  console.log(JSON.stringify(summary, null, 2));
  if (options.dryRun) return;

  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) throw new Error('OPENAI_API_KEY is required unless --dry-run is used.');

  const outputPath = absoluteRepoPath(job.output);
  try {
    await fs.access(outputPath);
    if (!options.force) {
      throw new Error(`Output already exists: ${job.output}. Use --force to replace it.`);
    }
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
  }

  const response = job.mode === 'edit'
    ? await callEdit(job, defaults, apiKey)
    : await callGenerate(job, defaults, apiKey);
  const requestId = response.headers.get('x-request-id');
  const payload = await response.json();

  if (!response.ok) {
    throw new Error(`OpenAI image request failed (${response.status}, request ${requestId ?? 'unknown'}):\n${JSON.stringify(payload, null, 2)}`);
  }

  const encoded = payload.data?.[0]?.b64_json;
  if (!encoded) throw new Error(`No base64 image returned for ${job.id}.`);

  await fs.mkdir(path.dirname(outputPath), {recursive: true});
  await fs.writeFile(outputPath, Buffer.from(encoded, 'base64'));

  const metadata = {
    generatedAt: new Date().toISOString(),
    requestId,
    job: summary,
    promptSha256: crypto.createHash('sha256').update(job.prompt).digest('hex'),
    usage: payload.usage ?? null,
  };
  await fs.writeFile(`${outputPath}.json`, `${JSON.stringify(metadata, null, 2)}\n`);
  console.log(`Saved ${path.relative(repoRoot, outputPath)}`);
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) {
    printHelp();
    return;
  }

  const manifest = await readJson(options.manifestPath);
  const jobs = manifest.jobs ?? [];

  if (options.list) {
    for (const job of jobs) {
      console.log(`${job.id}\t${job.enabled === false ? 'disabled' : 'enabled'}\t${job.mode}\t${job.output}`);
    }
    return;
  }

  const selected = options.all
    ? jobs.filter((job) => job.enabled !== false)
    : jobs.filter((job) => options.jobIds.includes(job.id));

  if (!selected.length) {
    printHelp();
    throw new Error('Select at least one job with --job <id>, or use --all.');
  }

  for (const job of selected) {
    await runJob(job, manifest.defaults, options);
  }
}

main().catch((error) => {
  console.error(error.stack ?? error.message);
  process.exitCode = 1;
});
