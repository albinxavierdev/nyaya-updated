const axios = require('axios');

// Configuration
const BASE_URL = 'http://localhost:8000';
const FRONTEND_URL = 'http://localhost:3001';

// Test data
const testUser = {
    first_name: 'Test',
    last_name: 'User',
    email: 'test' + Date.now() + '@example.com',
    password: 'test123456'
};

let authToken = '';
let conversationId = '';

// Utility functions
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

// Test functions
async function testBackendHealth() {
    log('Testing backend health...');
    try {
        const response = await axios.get(`${BASE_URL}/docs`, { timeout: 5000 });
        logResponse(response, 'Backend Health');
        return true;
    } catch (error) {
        log(`Backend health failed: ${error.message}`, 'ERROR');
        return false;
    }
}

async function testUserCreation() {
    log('Testing user creation...');
    try {
        // Test registration (signup)
        const registerResponse = await axios.post(`${BASE_URL}/api/auth/signup`, {
            email: testUser.email,
            first_name: testUser.first_name,
            last_name: testUser.last_name,
            password: testUser.password
        });
        logResponse(registerResponse, 'User Registration');
        
        // Test login with form data (OAuth2PasswordRequestForm expects username=email)
        const formData = new FormData();
        formData.append('username', testUser.email);  // OAuth2PasswordRequestForm uses username field for email
        formData.append('password', testUser.password);
        
        const loginResponse = await axios.post(`${BASE_URL}/api/auth/login`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });
        logResponse(loginResponse, 'User Login');
        
        authToken = loginResponse.data.access_token;  // Backend returns access_token field
        log('Authentication token obtained');
        return true;
    } catch (error) {
        log(`User creation failed: ${error.message}`, 'ERROR');
        if (error.response) {
            console.log('Error response:', error.response.data);
        }
        return false;
    }
}

async function testConversationCreation() {
    log('Testing conversation creation...');
    try {
        // Backend uses GET /api/conversation to create new conversation
        const response = await axios.get(`${BASE_URL}/api/conversation`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        logResponse(response, 'Conversation Creation');
        
        conversationId = response.data.conversation_id;
        log(`Conversation ID: ${conversationId}`);
        return true;
    } catch (error) {
        log(`Conversation creation failed: ${error.message}`, 'ERROR');
        if (error.response) {
            console.log('Error response:', error.response.data);
        }
        return false;
    }
}

async function testLegalChat() {
    log('Testing legal chat with RAG...');
    try {
        const legalQuery = {
            messages: [{
                role: "user",
                content: "What is section 420 of the Indian Penal Code?"
            }]
        };
        
        const response = await axios.post(`${BASE_URL}/api/legal`, legalQuery, {
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            params: {
                conversation_id: conversationId
            }
        });
        
        logResponse(response, 'Legal Chat (RAG Test)');
        
        // Analyze response for RAG indicators (streaming response)
        if (response.data) {
            log('=== RAG Analysis ===');
            log('Response type:', typeof response.data);
            log('Response keys:', Object.keys(response.data));
            
            // Legal chat may return streaming data or structured response
            if (response.data.response) {
                const responseText = response.data.response;
                log('Response length:', responseText.length);
                log('Contains legal citations:', responseText.includes('section') || responseText.includes('IPC'));
                log('Contains sources:', !!response.data.sources);
                
                if (response.data.sources) {
                    log('Sources found:', response.data.sources.length);
                    response.data.sources.forEach((source, index) => {
                        log(`Source ${index + 1}: ${source.title || source.metadata?.title || 'Unknown'}`);
                    });
                }
            } else {
                log('Response data:', JSON.stringify(response.data, null, 2));
            }
        }
        
        return true;
    } catch (error) {
        log(`Legal chat failed: ${error.message}`, 'ERROR');
        if (error.response) {
            console.log('Error response:', error.response.data);
        }
        return false;
    }
}

async function testGeneralChat() {
    log('Testing general chat with OpenAI...');
    try {
        const generalQuery = {
            messages: [{
                role: "user",
                content: "What is artificial intelligence? Explain in simple terms."
            }]
        };
        
        const response = await axios.post(`${BASE_URL}/api/chat`, generalQuery, {
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            params: {
                conversation_id: conversationId
            }
        });
        
        logResponse(response, 'General Chat (OpenAI Test)');
        
        // Analyze response for LLM indicators (streaming response)
        if (response.data) {
            log('=== OpenAI Analysis ===');
            log('Response type:', typeof response.data);
            log('Response keys:', Object.keys(response.data));
            
            if (response.data.response) {
                const responseText = response.data.response;
                log('Response length:', responseText.length);
                log('Contains AI explanation:', responseText.toLowerCase().includes('artificial intelligence') || responseText.toLowerCase().includes('ai'));
                log('Response coherence:', responseText.length > 100);
            } else {
                log('Response data:', JSON.stringify(response.data, null, 2));
            }
        }
        
        return true;
    } catch (error) {
        log(`General chat failed: ${error.message}`, 'ERROR');
        if (error.response) {
            console.log('Error response:', error.response.data);
        }
        return false;
    }
}

async function testFrontend() {
    log('Testing frontend...');
    try {
        const response = await axios.get(FRONTEND_URL, { timeout: 5000 });
        logResponse(response, 'Frontend Health');
        return true;
    } catch (error) {
        log(`Frontend test failed: ${error.message}`, 'ERROR');
        return false;
    }
}

async function testChatConfig() {
    log('Testing chat config endpoint...');
    try {
        const response = await axios.get(`${BASE_URL}/api/chat/config`);
        logResponse(response, 'Chat Config');
        
        // Check for OpenAI configuration
        if (response.data) {
            log('=== Configuration Analysis ===');
            log('Has model info:', !!response.data.model);
            log('Has provider info:', !!response.data.provider);
            if (response.data.model) {
                log('Model:', response.data.model);
            }
        }
        
        return true;
    } catch (error) {
        log(`Chat config test failed: ${error.message}`, 'ERROR');
        return false;
    }
}

// Main test runner
async function runTests() {
    log('Starting comprehensive OpenAI migration tests...');
    log('========================================');
    
    const results = {
        backendHealth: await testBackendHealth(),
        chatConfig: await testChatConfig(),
        userCreation: await testUserCreation(),
        conversationCreation: await testConversationCreation(),
        legalChat: await testLegalChat(),
        generalChat: await testGeneralChat(),
        frontend: await testFrontend()
    };
    
    log('\n========================================');
    log('TEST RESULTS SUMMARY:');
    log('========================================');
    
    Object.entries(results).forEach(([test, passed]) => {
        log(`${test}: ${passed ? '✅ PASSED' : '❌ FAILED'}`);
    });
    
    const passedTests = Object.values(results).filter(Boolean).length;
    const totalTests = Object.keys(results).length;
    
    log(`\nOverall: ${passedTests}/${totalTests} tests passed`);
    
    if (passedTests === totalTests) {
        log('🎉 All tests passed! OpenAI migration successful!', 'SUCCESS');
    } else {
        log('⚠️  Some tests failed. Check the logs above.', 'WARNING');
    }
    
    log('\nTest user created:');
    log(`Name: ${testUser.first_name} ${testUser.last_name}`);
    log(`Email: ${testUser.email}`);
    log(`Password: ${testUser.password}`);
    if (conversationId) {
        log(`Conversation ID: ${conversationId}`);
    }
}

// Run the tests
runTests().catch(error => {
    log(`Test suite failed: ${error.message}`, 'ERROR');
    console.error(error);
});
