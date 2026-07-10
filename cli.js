#!/usr/bin/env node

/**
 * CLI shim for api-contract-guardian
 * Delegates to the Python implementation
 */

const { spawn } = require('child_process');
const path = require('path');

// Find the Python package directory
const packageDir = path.join(__dirname, 'src', 'api_contract_guardian');

// Run the Python CLI
const python = spawn('python', ['-m', 'api_contract_guardian', ...process.argv.slice(2)], {
  cwd: __dirname,
  stdio: 'inherit',
  env: {
    ...process.env,
    PYTHONPATH: path.join(__dirname, 'src')
  }
});

python.on('close', (code) => {
  // code is null when the child was killed by a signal — treat as failure,
  // not success (code || 0 would report exit 0 to CI).
  process.exit(code === null ? 1 : code);
});

python.on('error', (err) => {
  console.error('Failed to start Python:', err.message);
  process.exit(1);
});
