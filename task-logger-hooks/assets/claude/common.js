#!/usr/bin/env node
const fs = require('fs');
const os = require('os');
const path = require('path');

const LOG_FILE = path.join(os.homedir(), 'Developer/design/active/TaskLog.md');
const STATE_DIR = path.join(os.tmpdir(), 'claude-code-task-logger');
const DESCRIPTION_LIMIT = 120;

const CANONICAL_CATEGORIES = new Set([
  'Feature',
  'Bugfix',
  'Misc',
  'Investigation',
  'Documentation',
  'Testing',
]);

const SKIPPED_PROMPT_PATTERNS = [
  /^you are an expert at upholding safety and compliance standards for codex ambient suggestions\.?$/i,
  /^#\s*system\b/i,
  /^<system(?:\s|>)/i,
  /^you are codex\b/i,
  /^you are an ai\b/i,
  /^knowledge cutoff:/i,
];

function ensureStateDir() {
  fs.mkdirSync(STATE_DIR, { recursive: true });
}

function safeKey(value, fallback) {
  return String(value || fallback).replace(/[^a-zA-Z0-9_-]/g, '_');
}

function statePath(sessionId) {
  return path.join(STATE_DIR, `${safeKey(sessionId, 'unknown-session')}.json`);
}

function readJsonStdin() {
  const raw = fs.readFileSync(0, 'utf8').trim();
  return raw ? JSON.parse(raw) : {};
}

function writeHookSuccess(payload = {}) {
  process.stdout.write(JSON.stringify(payload));
}

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

function normalizeCategory(category) {
  return CANONICAL_CATEGORIES.has(category) ? category : 'Misc';
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

function ensureLogFile() {
  fs.mkdirSync(path.dirname(LOG_FILE), { recursive: true });
  if (!fs.existsSync(LOG_FILE)) {
    fs.writeFileSync(LOG_FILE, '# Task Log\n\n');
  }
}

function appendLogEntry({ prompt, startedAt }) {
  if (shouldSkipPrompt(prompt)) {
    return;
  }

  ensureLogFile();

  const durationSec = startedAt > 0 ? Math.max(0, Math.round((Date.now() - startedAt) / 1000)) : 0;
  const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
  const category = normalizeCategory(inferCategory(prompt));
  const entry = `- **[${category}]** (${durationSec}s) - ${timestamp}: ${truncateDescription(prompt)}\n`;

  fs.appendFileSync(LOG_FILE, entry);
}

module.exports = {
  appendLogEntry,
  ensureStateDir,
  readJsonStdin,
  statePath,
  writeHookSuccess,
};
