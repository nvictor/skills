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
  const file = statePath(input.session_id);

  ensureStateDir();
  fs.writeFileSync(
    file,
    JSON.stringify({
      prompt: input.prompt || 'Unknown task',
      startedAt: Date.now(),
      sessionId: input.session_id || null,
      transcriptPath: input.transcript_path || null,
    }),
  );
} catch (_error) {
  // Hooks should fail open.
}

writeHookSuccess({});
