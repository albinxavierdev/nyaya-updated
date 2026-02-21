// frontend-test.js
const axios = require('axios');

const FRONTEND_BASE =
  process.env.FRONTEND_BASE || 'http://localhost:3001';

async function check(path, name) {
  const url = `${FRONTEND_BASE}${path}`;
  try {
    const res = await axios.get(url, { validateStatus: () => true });
    console.log(`\n=== ${name} (${path}) ===`);
    console.log('URL:', url);
    console.log('Status:', res.status);
    console.log(
      'Body snippet:',
      String(res.data).slice(0, 200).replace(/\\s+/g, ' ')
    );
  } catch (err) {
    console.log(`\n=== ${name} (${path}) ===`);
    console.log('URL:', url);
    console.log('ERROR:', err.message);
  }
}

async function main() {
  console.log('[INFO] Starting frontend health tests...');
  console.log('[INFO] FRONTEND_BASE =', FRONTEND_BASE);

  await check('/', 'Root');
  await check('/signin', 'Signin page');
  await check('/signup', 'Signup page');
  await check('/chat', 'Chat page');

  console.log('\\n[INFO] Frontend tests finished.');
}

main().catch(err => {
  console.error('Unexpected error:', err);
  process.exit(1);
});
