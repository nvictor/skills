#!/usr/bin/env node
const fs = require('fs');
const os = require('os');
const path = require('path');

const DESCRIPTION_LIMIT = 120;
const SKIPPED_PROMPT_PATTERNS = [
  /^you are an expert at upholding safety and compliance standards for codex ambient suggestions\.?$/i,
  /^#\s*system\b/i,
  /^<system(?:\s|>)/i,
  /^you are codex\b/i,
  /^you are an ai\b/i,
  /^knowledge cutoff:/i,
];

function normalizePrompt(prompt) {
  return String(prompt || '').replace(/\r\n/g, '\n').trim();
}

function shouldSkipPrompt(prompt) {
  const firstLine = normalizePrompt(prompt)
    .split('\n')
    .map((line) => line.trim())
    .find(Boolean) || '';

  return SKIPPED_PROMPT_PATTERNS.some((pattern) => pattern.test(firstLine));
}

function truncateDescription(prompt) {
  const firstLine = normalizePrompt(prompt || 'Unknown task')
    .split('\n')
    .map((line) => line.trim())
    .find(Boolean) || 'Unknown task';
  const description = firstLine.replace(/\s+/g, ' ');

  if (description.length <= DESCRIPTION_LIMIT) return description;
  return description.slice(0, DESCRIPTION_LIMIT - 3).trimEnd() + '...';
}

function inferCategory(prompt) {
  const lower = String(prompt || '').toLowerCase();

  if (lower.includes('bug') || lower.includes('fix') || lower.includes('error') || lower.includes('issue')) {
    return 'Bugfix';
  }
  if (lower.includes('test') || lower.includes('mock') || lower.includes('assert')) {
    return 'Testing';
  }
  if (lower.includes('doc') || lower.includes('readme') || lower.includes('comment') || lower.includes('explain')) {
    return 'Documentation';
  }
  if (lower.includes('investigate') || lower.includes('search') || lower.includes('find') || lower.includes('look')) {
    return 'Investigation';
  }
  if (
    lower.includes('refactor') ||
    lower.includes('clean') ||
    lower.includes('create') ||
    lower.includes('add') ||
    lower.includes('new') ||
    lower.includes('build') ||
    lower.includes('implement') ||
    lower.includes('setup') ||
    lower.includes('hook')
  ) {
    return 'Feature';
  }

  return 'Misc';
}

try {
  const tmpFile = `${os.tmpdir()}/copilot_task_start.json`;

  let startTime = 0;
  let prompt = 'Unknown task';

  if (fs.existsSync(tmpFile)) {
    const saved = JSON.parse(fs.readFileSync(tmpFile, 'utf-8'));
    startTime = saved.startTime || 0;
    prompt = saved.prompt || 'Unknown task';
    fs.unlinkSync(tmpFile);
  }

  const durationSec = startTime > 0 ? Math.round((Date.now() - startTime) / 1000) : 0;
  if (shouldSkipPrompt(prompt)) {
    console.log(JSON.stringify({ skipped: true }));
    process.exit(0);
  }

  const logFile = path.join(os.homedir(), 'Developer/design/active', 'TaskLog.md');
  const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
  const entry = `- **[${inferCategory(prompt)}]** (${durationSec}s) - ${timestamp}: ${truncateDescription(prompt)}\n`;

  if (!fs.existsSync(logFile)) fs.writeFileSync(logFile, '# Task Log\n\n');
  fs.appendFileSync(logFile, entry);
} catch (e) {
  // Fail silently — hooks must not interrupt the agent
}

console.log(JSON.stringify({}));
