#!/usr/bin/env node
const fs = require('fs');
const os = require('os');

try {
  const input = JSON.parse(fs.readFileSync(0, 'utf-8'));
  const tmpFile = `${os.tmpdir()}/copilot_task_start.json`;

  fs.writeFileSync(tmpFile, JSON.stringify({
    startTime: Date.now(),
    prompt: input.initialPrompt || ''
  }));
} catch (e) {
  // Fail silently — hooks must not interrupt the agent
}

console.log(JSON.stringify({}));
