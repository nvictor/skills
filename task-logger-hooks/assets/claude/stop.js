#!/usr/bin/env node
const fs = require('fs');

const {
  appendLogEntry,
  readJsonStdin,
  statePath,
  writeHookSuccess,
} = require('./common');

try {
  const input = readJsonStdin();
  const file = statePath(input.session_id);

  if (fs.existsSync(file)) {
    const saved = JSON.parse(fs.readFileSync(file, 'utf8'));
    appendLogEntry({
      prompt: saved.prompt || 'Unknown task',
      startedAt: saved.startedAt || 0,
    });
    fs.unlinkSync(file);
  }
} catch (_error) {
  // Hooks should fail open.
}

writeHookSuccess({});
