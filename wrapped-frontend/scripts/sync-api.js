const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Use env var or default to localhost
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
const OPENAPI_URL = `${API_BASE}/openapi.json`;
const OUTPUT_DIR = path.resolve(__dirname, '../src/lib');
const OUTPUT_NAME = 'api-client.js';

console.log(`[Sync] Fetching OpenAPI spec from: ${OPENAPI_URL}`);

try {
  // We use the CLI tool to generate the JS client. 
  // -p: path/url to spec
  // -o: output directory
  // -n: output filename
  // --js: generate JavaScript instead of TypeScript
  // --module-api: generate a modular API client
  
  const command = `npx swagger-typescript-api generate -p ${OPENAPI_URL} -o ${OUTPUT_DIR} -n ${OUTPUT_NAME} --js --module-api`;
  
  console.log(`[Sync] Executing: ${command}`);
  execSync(command, { stdio: 'inherit' });
  
  console.log(`\n[Sync] Success! API client generated at ${path.join(OUTPUT_DIR, OUTPUT_NAME)}`);
} catch (error) {
  console.error('\n[Sync] Error generating API client:');
  console.error(error.message);
  console.log('\nTip: Make sure the backend server is running and accessible at ' + OPENAPI_URL);
  process.exit(1);
}
