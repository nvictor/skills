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
  const input = JSON.parse(fs.readFileSync(0, 'utf-8'));
  const sessionId = input.session_id || 'default';
  const tmpFile = path.join(os.tmpdir(), `gemini_task_${sessionId}_start.txt`);

  fs.writeFileSync(tmpFile, Date.now().toString());
} catch (e) {
  console.error('Error in before-agent hook:', e.message);
}

console.log(JSON.stringify({}));
