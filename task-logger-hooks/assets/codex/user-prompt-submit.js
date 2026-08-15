#!/usr/bin/env node
const fs = require('fs');

const {
  ensureStateDir,
  readJsonStdin,
  statePath,
  writeHookSuccess,
} = require('./common');

try {
  const input = readJsonStdin();
  const file = statePath(input.session_id, input.turn_id);

  ensureStateDir();
  fs.writeFileSync(
    file,
    JSON.stringify({
      prompt: input.prompt || 'Unknown task',
      startedAt: Date.now(),
      turnId: input.turn_id || null,
      sessionId: input.session_id || null,
    }),
  );
} catch (_error) {
  // Hooks should fail open.
}

writeHookSuccess({});
