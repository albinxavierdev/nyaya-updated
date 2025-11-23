// frontend-flow-test.js
const axios = require('axios');

const BASE_URL = process.env.BACKEND_BASE || 'http://localhost:8000';
const FRONTEND_BASE = process.env.FRONTEND_BASE || 'http://localhost:3001';

// Test user
const testUser = {
  first_name: 'FE',
  last_name: 'FlowUser',
  email: 'fe-flow-' + Date.now() + '@example.com',
  password: 'test123456',
};

let authToken = '';
let conversationId = '';

function log(message, type = 'INFO') {
  console.log(`[${type}] ${message}`);
}

function logResponse(response, label) {
  console.log(`\n=== ${label} ===`);
  console.log('Status:', response.status);
  if (response.data) {
    console.log('Response:', JSON.stringify(response.data, null, 2));
  }
}

// 1) Backend: health
async function testBackendHealth() {
  log('Testing backend health (/docs)...');
  const res = await axios.get(`${BASE_URL}/docs`, { timeout: 5000 });
  logResponse(res, 'Backend Health');
}

// 2) Backend: chat config
async function testChatConfig() {
  log('Testing chat config endpoint (/api/chat/config)...');
  const res = await axios.get(`${BASE_URL}/api/chat/config`);
  logResponse(res, 'Chat Config');
  if (res.data) {
    log('=== Configuration Analysis ===');
    log('Has model info:', !!res.data.model);
    log('Has provider info:', !!res.data.provider);
  }
}

// 3) Backend: user signup + login
async function createUserAndLogin() {
  log('Creating test user via backend /api/auth/signup ...');
  const reg = await axios.post(`${BASE_URL}/api/auth/signup`, {
    email: testUser.email,
    first_name: testUser.first_name,
    last_name: testUser.last_name,
    password: testUser.password,
  });
  logResponse(reg, 'User Registration');

  log('Logging in via backend /api/auth/login ...');
  const formData = new FormData();
  formData.append('username', testUser.email);
  formData.append('password', testUser.password);

  const login = await axios.post(`${BASE_URL}/api/auth/login`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  logResponse(login, 'User Login');

  authToken = login.data.access_token;
  log('Auth token acquired');
}

// 4) Backend: conversation creation
async function createConversation() {
  log('Creating conversation via backend /api/conversation ...');
  const res = await axios.get(`${BASE_URL}/api/conversation`, {
    headers: { Authorization: `Bearer ${authToken}` },
  });
  logResponse(res, 'Conversation Creation');
  conversationId = res.data.conversation_id;
  log(`Conversation ID: ${conversationId}`);
}

// 5) Backend: legal chat (RAG) via /api/legal
async function testLegalChat() {
  log('Testing legal chat with RAG (/api/legal)...');
  const legalQuery = {
    messages: [
      {
        role: 'user',
        content: 'What is section 420 of the Indian Penal Code?',
      },
    ],
  };

  const res = await axios.post(`${BASE_URL}/api/legal`, legalQuery, {
    headers: {
      Authorization: `Bearer ${authToken}`,
      'Content-Type': 'application/json',
    },
    params: {
      conversation_id: conversationId,
    },
  });

  logResponse(res, 'Legal Chat (RAG Test)');

  if (res.data && res.data.response) {
    log('=== RAG Analysis ===');
    const text = res.data.response;
    log('Response length:', text.length);
    log(
      'Contains legal citations:',
      text.includes('section') || text.includes('IPC')
    );
    log('Contains sources:', !!res.data.sources || !!res.data.source_nodes);
  }
}

// 6) Backend: general AI chat via /api/chat
async function testGeneralChat() {
  log('Testing general chat with OpenAI (/api/chat)...');
  const generalQuery = {
    messages: [
      {
        role: 'user',
        content: 'What is artificial intelligence? Explain in simple terms.',
      },
    ],
  };

  const res = await axios.post(`${BASE_URL}/api/chat`, generalQuery, {
    headers: {
      Authorization: `Bearer ${authToken}`,
      'Content-Type': 'application/json',
    },
    params: {
      conversation_id: conversationId,
    },
  });

  logResponse(res, 'General Chat (OpenAI Test)');

  if (res.data && res.data.response) {
    log('=== OpenAI Analysis ===');
    const text = res.data.response;
    log('Response length:', text.length);
    log(
      'Contains AI explanation:',
      text.toLowerCase().includes('artificial intelligence') ||
        text.toLowerCase().includes('ai')
    );
  }
}

// 7) Frontend: core routes
async function testFrontendRoutes() {
  async function check(path, name) {
    const url = `${FRONTEND_BASE}${path}`;
    const res = await axios.get(url, { validateStatus: () => true });
    console.log(`\n=== Frontend ${name} (${path}) ===`);
    console.log('URL:', url);
    console.log('Status:', res.status);
    console.log(
      'Body snippet:',
      String(res.data).slice(0, 200).replace(/\s+/g, ' ')
    );
  }

  log('Testing frontend routes (/ , /signin, /signup, /chat)...');
  await check('/', 'Root');
  await check('/signin', 'Signin');
  await check('/signup', 'Signup');
  await check('/chat', 'Chat');
}

// 8) Frontend: chat page with conversation & query
async function testFrontendChatWithConversation() {
  if (!conversationId) throw new Error('No conversationId set');
  const query = encodeURIComponent('What is Section 420 IPC?');
  const url = `${FRONTEND_BASE}/chat?conversation_id=${conversationId}&query=${query}`;

  log('Testing frontend /chat with conversation_id & query ...');
  const res = await axios.get(url, { validateStatus: () => true });
  console.log('\n=== Frontend Chat Page with Data ===');
  console.log('URL:', url);
  console.log('Status:', res.status);
  console.log(
    'Body snippet:',
    String(res.data).slice(0, 200).replace(/\s+/g, ' ')
  );
}

// Main runner
async function main() {
  log('Starting full frontend–backend flow tests...');
  log(`Backend:  ${BASE_URL}`);
  log(`Frontend: ${FRONTEND_BASE}`);

  await testBackendHealth();
  await testChatConfig();
  await createUserAndLogin();
  await createConversation();
  await testLegalChat();
  await testGeneralChat();
  await testFrontendRoutes();
  await testFrontendChatWithConversation();

  log('\n[RESULT] All flow tests completed.');
  log(`Test user: ${testUser.email} / ${testUser.password}`);
  log(`Conversation ID: ${conversationId}`);
}

main().catch((err) => {
  log(`Test failed: ${err.message}`, 'ERROR');
  if (err.response) {
    console.error('Error response:', err.response.data);
  } else {
    console.error(err);
  }
  process.exit(1);
});
