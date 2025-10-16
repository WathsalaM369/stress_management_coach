// Configuration
const API_BASE = 'http://localhost:5001/api';
let currentUserId = null;
let currentUsername = null;
let selectionStartTime = Date.now();
let historyChart = null;
let eventListenersSetup = false;

// Enhanced assessment data structure
let assessmentData = {
    physicalSymptoms: [],
    emotionalState: [],
    cognitiveSymptoms: [],
    lifestyleImpact: {
        sleep: null,
        appetite: null,
        social: null,
        functioning: null
    },
    copingMechanisms: [],
    duration: null,
    stressSource: null,
    initialMood: null
};

// Debug logging
console.log('🚀 Frontend initialized');
console.log('API Base:', API_BASE);

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    console.log('📄 DOM loaded, initializing app...');
    checkAuthentication();
    setupAssessmentListeners();
    injectStatsStyles();
});

// Enhanced Authentication Functions
// Enhanced Authentication Functions
async function checkAuthentication() {
    try {
        console.log('🔐 Checking authentication...');
        const response = await fetch(`${API_BASE}/current-user`, {
            credentials: 'include',
            cache: 'no-cache'
        });
        
        console.log('🔐 Auth check response status:', response.status);
        
        if (response.ok) {
            const userData = await response.json();
            console.log('📋 User data:', userData);
            
            if (userData.logged_in) {
                currentUserId = userData.user_id;
                currentUsername = userData.username;
                console.log('✅ User authenticated:', currentUsername);
                
                // Add small delay to ensure DOM is fully ready
                setTimeout(() => {
                    showMainApp();
                    showNotification('✅ Welcome back!', 'success');
                }, 100);
            } else {
                console.log('❌ No active session');
                showAuthSection();
            }
        } else {
            console.log('❌ Auth check failed');
            showAuthSection();
        }
    } catch (error) {
        console.error('❌ Auth check failed:', error);
        showAuthSection();
    }
}

function showAuthSection() {
    document.getElementById('authSection').style.display = 'block';
    document.getElementById('mainContent').style.display = 'none';
    document.getElementById('userInfo').style.display = 'none';
    document.getElementById('comprehensiveAssessment').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'none';
}

function showMainApp() {
    console.log('🎮 Showing main app for user:', currentUsername);
    
    // First hide all sections
    document.getElementById('authSection').style.display = 'none';
    document.getElementById('mainContent').style.display = 'none';
    document.getElementById('comprehensiveAssessment').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'none';
    
    // Then show the main content with a small delay to ensure DOM is ready
    setTimeout(() => {
        document.getElementById('mainContent').style.display = 'block';
        document.getElementById('gameSection').style.display = 'block';
        document.getElementById('quickSelection').style.display = 'block';
        
        if (currentUsername) {
            document.getElementById('usernameDisplay').textContent = `Welcome, ${currentUsername}`;
            document.getElementById('userInfo').style.display = 'block';
        }
        
        // Reset the event listeners flag when showing main app
        eventListenersSetup = false;
        
        // Initialize the app components
        testBackendConnection();
        createBubbleGame();
        setupEventListeners();
        
        // Load user data after everything is initialized
        setTimeout(() => {
            loadRealHistoryChart();
            loadUserStats();
        }, 500);
        
        console.log('✅ Main app initialized for user:', currentUserId);
    }, 100);
}

function showAuthTab(tab) {
    document.getElementById('loginForm').style.display = 'none';
    document.getElementById('registerForm').style.display = 'none';
    
    document.querySelectorAll('.auth-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    if (tab === 'login') {
        document.getElementById('loginForm').style.display = 'block';
        document.querySelectorAll('.auth-tab')[0].classList.add('active');
    } else {
        document.getElementById('registerForm').style.display = 'block';
        document.querySelectorAll('.auth-tab')[1].classList.add('active');
    }
}

async function login(event) {
    event.preventDefault();
    
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    
    if (!username || !password) {
        showNotification('❌ Please fill in all fields', 'error');
        return;
    }
    
    showLoading('Logging in...');
    
    try {
        const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            credentials: 'include',
            body: JSON.stringify({ username, password })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            currentUserId = result.user_id;
            currentUsername = result.username;
            showNotification('✅ Login successful!', 'success');
            showMainApp();
        } else {
            showNotification(`❌ ${result.error}`, 'error');
        }
    } catch (error) {
        showNotification('❌ Login failed. Please try again.', 'error');
    } finally {
        hideLoading();
    }
}

async function register(event) {
    event.preventDefault();
    
    const username = document.getElementById('registerUsername').value;
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    
    if (!username || !password) {
        showNotification('❌ Please fill in all required fields', 'error');
        return;
    }
    
    showLoading('Creating account...');
    
    try {
        const response = await fetch(`${API_BASE}/register`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            credentials: 'include',
            body: JSON.stringify({ username, email, password })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            currentUserId = result.user_id;
            currentUsername = result.username;
            showNotification('✅ Registration successful!', 'success');
            
            // Wait a moment before showing main app to ensure session is set
            setTimeout(() => {
                showMainApp();
            }, 500);
            
        } else {
            showNotification(`❌ ${result.error}`, 'error');
        }
    } catch (error) {
        showNotification('❌ Registration failed. Please try again.', 'error');
    } finally {
        hideLoading();
    }
}

async function logout() {
    try {
        await fetch(`${API_BASE}/logout`, {
            method: 'POST',
            credentials: 'include'
        });
    } catch (error) {
        console.error('Logout error:', error);
    }
    
    currentUserId = null;
    currentUsername = null;
    showAuthSection();
    showNotification('👋 Logged out successfully', 'info');
}

function continueAsGuest() {
    currentUserId = 'guest_' + Date.now();
    currentUsername = 'Guest';
    showMainApp();
    showNotification('🚀 Continuing as guest. Your data will be saved temporarily.', 'info');
}

function hideLoading() {
    document.body.style.cursor = 'default';
    const loader = document.querySelector('.loading-indicator');
    if (loader) loader.remove();
}

// Backend Connection Test
async function testBackendConnection() {
    try {
        const response = await fetch(API_BASE + '/health');
        if (response.ok) {
            const data = await response.json();
            console.log('✅ Backend connection successful');
            console.log('🤖 LLM Status:', data.llm_enabled ? 'Enabled' : 'Disabled');
           if (data.llm_enabled) {
                showNotification('🤖 Gemini AI Analysis Enabled', 'success');
            }
        }
    } catch (error) {
        console.error('❌ Backend connection failed:', error.message);
        showNotification('❌ Backend connection failed', 'error');
    }
}

// Show notification
function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 10px;
        color: white;
        font-weight: bold;
        z-index: 10000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        animation: slideIn 0.3s ease;
    `;
    
    const colors = {
        'success': '#4caf50',
        'warning': '#ff9800',
        'error': '#f44336',
        'info': '#2196f3'
    };
    
    notification.style.background = colors[type] || '#2196f3';
    document.body.appendChild(notification);
    
    setTimeout(() => notification.remove(), 4000);
}

// Add CSS animation for notification
if (!document.querySelector('#notification-styles')) {
    const style = document.createElement('style');
    style.id = 'notification-styles';
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
    `;
    document.head.appendChild(style);
}

// Bubble Game Implementation
function createBubbleGame() {
    const container = document.getElementById('bubbleGame');
    if (!container) return;
    
    container.innerHTML = '';
    
    const moodBubbles = [
        { type: 'calm', stress: 2, label: 'Calm', size: 120 },
        { type: 'okay', stress: 4, label: 'Okay', size: 100 },
        { type: 'uneasy', stress: 6, label: 'Uneasy', size: 110 },
        { type: 'stressed', stress: 8, label: 'Stressed', size: 130 },
        { type: 'overwhelmed', stress: 9.5, label: 'Overwhelmed', size: 140 }
    ];
    
    moodBubbles.forEach((mood) => {
        const bubble = document.createElement('div');
        bubble.className = `bubble ${mood.type}`;
        bubble.textContent = mood.label;
        
        const x = Math.random() * 70 + 15;
        const y = Math.random() * 60 + 20;
        
        bubble.style.width = `${mood.size}px`;
        bubble.style.height = `${mood.size}px`;
        bubble.style.left = `${x}%`;
        bubble.style.top = `${y}%`;
        bubble.style.animationDelay = `${Math.random() * 5}s`;
        
        bubble.addEventListener('click', function() {
            const timeTaken = (Date.now() - selectionStartTime) / 1000;
            selectBubble(mood.type, mood.label, timeTaken);
            
            this.style.transform = 'scale(1.8)';
            this.style.opacity = '0';
            this.style.transition = 'all 0.4s ease';
            
            setTimeout(() => {
                this.remove();
                setTimeout(createBubbleGame, 1000);
            }, 400);
        });
        
        container.appendChild(bubble);
    });
}

function selectBubble(bubbleType, label, timeTaken) {
    console.log('🎯 Bubble selected:', { bubbleType, label, timeTaken });
    
    const analysisData = {
        input_method: 'bubble_game',
        bubble_type: bubbleType,
        time_taken: timeTaken,
        user_id: currentUserId,
        timestamp: new Date().toISOString()
    };
    
    // Show comprehensive assessment instead of immediate results
    showComprehensiveAssessment(analysisData);
}

// Event Listeners for Quick Selection
function setupEventListeners() {
    if (eventListenersSetup) {
        console.log('🔗 Event listeners already setup, skipping...');
        return;
    }
    
    console.log('🔗 Setting up event listeners...');
    
    // Remove any existing event listeners first
    removeEventListeners();
    
    // Emoji selection
    document.querySelectorAll('.emoji-option').forEach(option => {
        option.addEventListener('click', function() {
            const emoji = this.getAttribute('data-emoji');
            console.log('😊 Emoji selected:', emoji);
            
            const analysisData = {
                input_method: 'emoji_selection',
                emoji: emoji,
                user_id: currentUserId
            };
            // Show comprehensive assessment instead of immediate results
            showComprehensiveAssessment(analysisData);
        });
    });
    
    // Scene selection
    document.querySelectorAll('.scene-option').forEach(option => {
        option.addEventListener('click', function() {
            const scene = this.getAttribute('data-scene');
            console.log('🏝️ Scene selected:', scene);
            
            const analysisData = {
                input_method: 'scene_selection',
                scene: scene,
                user_id: currentUserId
            };
            // Show comprehensive assessment instead of immediate results
            showComprehensiveAssessment(analysisData);
        });
    });
    
    // Color selection
    document.querySelectorAll('.color-option').forEach(option => {
        option.addEventListener('click', function() {
            const color = this.getAttribute('data-color');
            console.log('🎨 Color selected:', color);
            
            const analysisData = {
                input_method: 'color_wheel',
                color: color,
                user_id: currentUserId
            };
            // Show comprehensive assessment instead of immediate results
            showComprehensiveAssessment(analysisData);
        });
    });
    
    eventListenersSetup = true;
    console.log('✅ Event listeners setup complete');
}

function removeEventListeners() {
    console.log('🗑️ Removing existing event listeners...');
    
    // Emoji selection
    document.querySelectorAll('.emoji-option').forEach(option => {
        option.replaceWith(option.cloneNode(true));
    });
    
    // Scene selection
    document.querySelectorAll('.scene-option').forEach(option => {
        option.replaceWith(option.cloneNode(true));
    });
    
    // Color selection
    document.querySelectorAll('.color-option').forEach(option => {
        option.replaceWith(option.cloneNode(true));
    });
    
    eventListenersSetup = false;
}

// Enhanced Comprehensive Assessment Functions
function setupAssessmentListeners() {
    // Physical symptoms
    document.querySelectorAll('.symptom-option').forEach(option => {
        option.addEventListener('click', function() {
            this.classList.toggle('selected');
            const symptom = this.getAttribute('data-symptom');
            const weight = parseInt(this.getAttribute('data-weight'));
            
            if (this.classList.contains('selected')) {
                assessmentData.physicalSymptoms.push({ symptom, weight });
            } else {
                assessmentData.physicalSymptoms = assessmentData.physicalSymptoms.filter(s => s.symptom !== symptom);
            }
            console.log('Physical symptoms:', assessmentData.physicalSymptoms);
        });
    });
    
    // Emotional state
    document.querySelectorAll('.emotion-option').forEach(option => {
        option.addEventListener('click', function() {
            this.classList.toggle('selected');
            const emotion = this.getAttribute('data-emotion');
            const weight = parseInt(this.getAttribute('data-weight'));
            
            if (this.classList.contains('selected')) {
                assessmentData.emotionalState.push({ emotion, weight });
            } else {
                assessmentData.emotionalState = assessmentData.emotionalState.filter(e => e.emotion !== emotion);
            }
            console.log('Emotional state:', assessmentData.emotionalState);
        });
    });
    
    // Cognitive symptoms
    document.querySelectorAll('.cognitive-option').forEach(option => {
        option.addEventListener('click', function() {
            this.classList.toggle('selected');
            const cognitive = this.getAttribute('data-cognitive');
            const weight = parseInt(this.getAttribute('data-weight'));
            
            if (this.classList.contains('selected')) {
                assessmentData.cognitiveSymptoms.push({ cognitive, weight });
            } else {
                assessmentData.cognitiveSymptoms = assessmentData.cognitiveSymptoms.filter(c => c.cognitive !== cognitive);
            }
            console.log('Cognitive symptoms:', assessmentData.cognitiveSymptoms);
        });
    });
    
    // Lifestyle impact (single selection per category)
    document.querySelectorAll('.lifestyle-option').forEach(option => {
        option.addEventListener('click', function() {
            const category = this.getAttribute('data-category');
            const value = this.getAttribute('data-value');
            const weight = parseInt(this.getAttribute('data-weight'));
            
            // Remove other selections in same category
            document.querySelectorAll(`.lifestyle-option[data-category="${category}"]`).forEach(opt => {
                opt.classList.remove('selected');
            });
            
            this.classList.add('selected');
            assessmentData.lifestyleImpact[category] = { value, weight };
            console.log('Lifestyle impact:', assessmentData.lifestyleImpact);
        });
    });
    
    // Coping mechanisms
    document.querySelectorAll('.coping-option').forEach(option => {
        option.addEventListener('click', function() {
            this.classList.toggle('selected');
            const coping = this.getAttribute('data-coping');
            const weight = parseInt(this.getAttribute('data-weight'));
            
            if (this.classList.contains('selected')) {
                assessmentData.copingMechanisms.push({ coping, weight });
            } else {
                assessmentData.copingMechanisms = assessmentData.copingMechanisms.filter(c => c.coping !== coping);
            }
            console.log('Coping mechanisms:', assessmentData.copingMechanisms);
        });
    });
    
    // Duration (single selection)
    document.querySelectorAll('.duration-option').forEach(option => {
        option.addEventListener('click', function() {
            document.querySelectorAll('.duration-option').forEach(opt => opt.classList.remove('selected'));
            this.classList.add('selected');
            assessmentData.duration = {
                duration: this.getAttribute('data-duration'),
                weight: parseInt(this.getAttribute('data-weight'))
            };
            console.log('Duration:', assessmentData.duration);
        });
    });
    
    // Stress source (single selection)
    document.querySelectorAll('.source-option').forEach(option => {
        option.addEventListener('click', function() {
            document.querySelectorAll('.source-option').forEach(opt => opt.classList.remove('selected'));
            this.classList.add('selected');
            assessmentData.stressSource = {
                source: this.getAttribute('data-source'),
                weight: parseInt(this.getAttribute('data-weight'))
            };
            console.log('Stress source:', assessmentData.stressSource);
        });
    });
}

function showComprehensiveAssessment(initialMoodData) {
    console.log('🎯 Starting comprehensive assessment with:', initialMoodData);
    
    // Store initial mood data
    assessmentData.initialMood = initialMoodData;
    
    // Show assessment, hide other sections
    document.getElementById('comprehensiveAssessment').style.display = 'block';
    document.getElementById('gameSection').style.display = 'none';
    document.getElementById('quickSelection').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'none';
    
    // Reset assessment data (keep initialMood)
    assessmentData.physicalSymptoms = [];
    assessmentData.emotionalState = [];
    assessmentData.cognitiveSymptoms = [];
    assessmentData.lifestyleImpact = {
        sleep: null,
        appetite: null,
        social: null,
        functioning: null
    };
    assessmentData.copingMechanisms = [];
    assessmentData.duration = null;
    assessmentData.stressSource = null;
    
    // Reset all selections
    document.querySelectorAll('.symptom-option, .emotion-option, .cognitive-option, .lifestyle-option, .coping-option, .duration-option, .source-option').forEach(option => {
        option.classList.remove('selected');
    });
    
    // Show first section
    document.querySelectorAll('.assessment-section').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById('sectionPhysical').classList.add('active');
    
    updateProgress(1);
}

function nextSection(currentId, nextId) {
    document.getElementById(currentId).classList.remove('active');
    document.getElementById(nextId).classList.add('active');
    
    const sectionNumber = parseInt(nextId.replace('section', '').charAt(0));
    updateProgress(sectionNumber);
}

function prevSection(currentId, prevId) {
    document.getElementById(currentId).classList.remove('active');
    document.getElementById(prevId).classList.add('active');
    
    const sectionNumber = parseInt(prevId.replace('section', '').charAt(0));
    updateProgress(sectionNumber);
}

function updateProgress(sectionNumber) {
    const progress = (sectionNumber / 5) * 100; // Now 5 sections
    document.getElementById('progressFill').style.width = `${progress}%`;
    document.getElementById('progressText').textContent = `${sectionNumber}/5`;
}

// Enhanced Comprehensive Score Calculation with LLM ONLY
function calculateComprehensiveScore() {
    console.log('🧠 Calculating comprehensive score with LLM ONLY...');
    console.log('Assessment data:', assessmentData);
    
    showLoading('🤖 AI is analyzing your comprehensive stress profile...');
    
    // Send directly to LLM - no local calculations
    generateLLMExplanation(assessmentData);
}

// Enhanced LLM explanation generation with proper API endpoint
async function generateLLMExplanation(assessmentData) {
    try {
        console.log('🤖 Sending comprehensive data to LLM for analysis...');
        
        const requestData = {
            assessment_data: assessmentData,
            user_id: currentUserId,
            timestamp: new Date().toISOString()
        };
        
        console.log('📤 Sending to LLM:', requestData);

        const response = await fetch(API_BASE + '/analyze-comprehensive', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            credentials: 'include',
            body: JSON.stringify(requestData)
        });

        console.log('📨 LLM Response status:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('❌ LLM analysis failed:', errorText);
            throw new Error(`LLM analysis failed: ${response.status} - ${errorText}`);
        }
        
        const result = await response.json();
        console.log('✅ LLM analysis successful:', result);
        
        // Use the LLM result completely
        displayEnhancedResults(result);
        
    } catch (error) {
        console.error('❌ LLM analysis failed:', error);
        showNotification('❌ AI analysis failed. Please try again.', 'error');
        // Don't fallback to rule-based - show error
        hideLoading();
    }
}

// Force refresh user data
async function forceRefreshUserData() {
    console.log('🔄 Force refreshing user data...');
    
    try {
        // Add delay to ensure database operations complete
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Load updated chart and stats
        await loadRealHistoryChart();
        await loadUserStats();
        
        console.log('✅ User data refresh complete');
    } catch (error) {
        console.error('❌ Error refreshing user data:', error);
    }
}

// Enhanced results display with detailed analysis
async function displayEnhancedResults(data) {
    console.log('📊 Displaying enhanced results:', data);
    
    // Hide input sections, show results
    document.getElementById('gameSection').style.display = 'none';
    document.getElementById('quickSelection').style.display = 'none';
    document.getElementById('comprehensiveAssessment').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'block';
    
    // Update basic results
    document.getElementById('stressScore').textContent = data.stress_score;
    
    const levelBadge = document.getElementById('levelBadge');
    levelBadge.textContent = data.stress_level;
    
    // Handle all possible stress levels
    const levelClass = data.stress_level.toLowerCase().replace(/ /g, '-').replace('very-', 'very-').replace('chronic-', 'chronic-');
    levelBadge.className = `level-badge level-${levelClass}`;
    
    // Build detailed analysis HTML
    const explanationHTML = buildDetailedAnalysisHTML(data);
    document.getElementById('explanationText').innerHTML = explanationHTML;
    
    document.getElementById('inputMethod').textContent = 'AI Comprehensive Assessment 🤖';
    
    // Get mood label from initial selection
    const moodLabel = getMoodLabel(assessmentData.initialMood);
    document.getElementById('moodLabel').textContent = moodLabel;
    
    // Show AI analysis indicator
    const trendItem = document.getElementById('trendItem');
    const trendValue = document.getElementById('trendValue');
    
    if (data.analysis_metadata?.llm_used) {
        trendItem.style.display = 'block';
        trendValue.textContent = 'AI Analysis';
        trendValue.className = 'trend-ai';
    }
    
    // Show trend if available
    if (data.trend && data.trend !== 'no_data' && data.trend !== 'insufficient_data') {
        trendItem.style.display = 'block';
        trendValue.textContent = data.trend;
        trendValue.className = `trend-${data.trend}`;
    }
    
    // Force reload history and stats
    setTimeout(async () => {
        await loadRealHistoryChart();
        await loadUserStats();
    }, 1000);
    
    // Hide loading
    hideLoading();
}

function buildDetailedAnalysisHTML(data) {
    let html = '';
    
    // Detailed Analysis Section
    html += `
        <div class="detailed-analysis-section">
            <h3>🔍 Detailed Analysis</h3>
            <div class="analysis-content">
                <p>${data.detailed_analysis || 'Analysis completed based on your reported symptoms and patterns.'}</p>
            </div>
        </div>
    `;
    
    // Symptom Breakdown Section
    if (data.symptom_breakdown) {
        html += `
            <div class="symptom-breakdown-section">
                <h3>🧩 Symptom Impact Analysis</h3>
                <div class="breakdown-grid">
        `;
        
        if (data.symptom_breakdown.physical_impact && !data.symptom_breakdown.physical_impact.includes('No significant')) {
            html += `<div class="breakdown-item physical">
                <h4>💪 Physical Impact</h4>
                <p>${data.symptom_breakdown.physical_impact}</p>
            </div>`;
        }
        
        if (data.symptom_breakdown.emotional_impact && !data.symptom_breakdown.emotional_impact.includes('within normal')) {
            html += `<div class="breakdown-item emotional">
                <h4>💖 Emotional Impact</h4>
                <p>${data.symptom_breakdown.emotional_impact}</p>
            </div>`;
        }
        
        if (data.symptom_breakdown.cognitive_impact && !data.symptom_breakdown.cognitive_impact.includes('unaffected')) {
            html += `<div class="breakdown-item cognitive">
                <h4>🧠 Cognitive Impact</h4>
                <p>${data.symptom_breakdown.cognitive_impact}</p>
            </div>`;
        }
        
        if (data.symptom_breakdown.lifestyle_impact && !data.symptom_breakdown.lifestyle_impact.includes('Minimal disruption')) {
            html += `<div class="breakdown-item lifestyle">
                <h4>📊 Lifestyle Impact</h4>
                <p>${data.symptom_breakdown.lifestyle_impact}</p>
            </div>`;
        }
        
        html += `</div></div>`;
    }
    
    // Key Findings Section
    if (data.key_findings && data.key_findings.length > 0) {
        html += `
            <div class="key-findings-section">
                <h3>🎯 Key Findings</h3>
                <ul class="findings-list">
                    ${data.key_findings.map(finding => `<li>${finding}</li>`).join('')}
                </ul>
            </div>
        `;
    }
    
    // Score Explanation Section
    if (data.score_explanation) {
        html += `
            <div class="score-explanation-section">
                <h3>📈 Score Analysis</h3>
                <div class="score-content">
                    <p>Your ${data.stress_score}/10 score indicates <strong>${data.stress_level} stress levels</strong>.</p>
                    <p>${data.score_explanation}</p>
                </div>
            </div>
        `;
    }
    
    // Analysis Metadata
    if (data.analysis_metadata) {
        html += `
            <div class="analysis-metadata">
                <small>
                    Analyzed ${data.analysis_metadata.symptoms_analyzed || 0} symptoms using 
                    ${data.analysis_metadata.llm_used ? 'AI analysis' : 'rule-based analysis'}
                </small>
            </div>
        `;
    }
    
    return html;
}

// Helper function to get mood label
function getMoodLabel(moodData) {
    if (!moodData) return 'Comprehensive Assessment';
    
    const inputMethod = moodData.input_method;
    
    if (inputMethod === 'bubble_game') {
        return moodData.bubble_type;
    } else if (inputMethod === 'emoji_selection') {
        return moodData.emoji;
    } else if (inputMethod === 'scene_selection') {
        return moodData.scene;
    } else if (inputMethod === 'color_wheel') {
        return moodData.color;
    }
    
    return 'Comprehensive Assessment';
}

// Enhanced REAL HISTORY CHART with better data handling
async function loadRealHistoryChart() {
    if (!currentUserId) {
        console.log('No user ID available for chart');
        showSampleChart('No user session');
        return;
    }
    
    console.log('📈 Loading real history chart for user:', currentUserId);
    showChartLoading();
    
    try {
        const response = await fetch(`${API_BASE}/chart-data/${currentUserId}`, {
            credentials: 'include',
            cache: 'no-cache' // Prevent caching
        });
        
        console.log('📊 Chart API response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`Failed to fetch chart data: ${response.status}`);
        }
        
        const chartData = await response.json();
        console.log('📈 Chart data received:', chartData);
        
        if (chartData.error) {
            throw new Error(chartData.error);
        }
        
        if (chartData.has_data && !chartData.is_sample) {
            // Show REAL user data
            console.log('✅ Creating chart with real user data');
            console.log('📊 Chart data points:', chartData.labels.length);
            console.log('📊 Scores:', chartData.scores);
            createHistoryChart(chartData, 'Your Stress History 📊');
        } else if (chartData.sample_data) {
            // Show sample data with message
            console.log('📋 Creating chart with sample data');
            createHistoryChart(chartData.sample_data, 'Sample Data - Complete an assessment to see your history!');
        } else {
            // Fallback to sample data
            console.log('🔄 Creating fallback sample chart');
            showSampleChart('No data available yet');
        }
        
    } catch (error) {
        console.error('❌ Error loading real history chart:', error);
        showSampleChart('Error loading history');
    }
}

// Enhanced user statistics loading
async function loadUserStats() {
    if (!currentUserId) {
        console.log('No user ID available for stats');
        updateStatsDisplay({
            has_data: false,
            total_entries: 0,
            average_stress: 0,
            trend: 'no_data'
        });
        return;
    }
    
    try {
        console.log('📊 Loading user stats for:', currentUserId);
        const response = await fetch(`${API_BASE}/stats/${currentUserId}`, {
            credentials: 'include',
            cache: 'no-cache'
        });
        
        if (response.ok) {
            const stats = await response.json();
            console.log('📊 User stats received:', stats);
            
            updateStatsDisplay(stats);
        } else {
            console.error('❌ Stats API error:', response.status);
            updateStatsDisplay({
                has_data: false,
                total_entries: 0,
                average_stress: 0,
                trend: 'error'
            });
        }
    } catch (error) {
        console.error('❌ Error loading stats:', error);
        updateStatsDisplay({
            has_data: false,
            total_entries: 0,
            average_stress: 0,
            trend: 'error'
        });
    }
}

// Enhanced chart creation with better data validation
function createHistoryChart(data, title) {
    console.log('🎨 Creating chart with data:', data);
    
    // Hide loading, show chart
    hideChartLoading();
    
    // Destroy existing chart if it exists
    if (historyChart) {
        console.log('🗑️ Destroying existing chart');
        historyChart.destroy();
    }
    
    const ctx = document.getElementById('historyChart');
    if (!ctx) {
        console.error('❌ Chart canvas not found');
        return;
    }
    
    const isSampleData = data.is_sample || title.includes('Sample');
    
    console.log('📊 Chart data validation:', {
        labels: data.labels?.length || 0,
        scores: data.scores?.length || 0,
        isSample: isSampleData
    });
    
    try {
        historyChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: isSampleData ? 'Sample Stress Level' : 'Your Stress Level',
                    data: data.scores || [],
                    borderColor: isSampleData ? '#cccccc' : '#4facfe',
                    backgroundColor: isSampleData ? 'rgba(204, 204, 204, 0.1)' : 'rgba(79, 172, 254, 0.1)',
                    borderWidth: isSampleData ? 2 : 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: isSampleData ? '#999' : '#4facfe',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 10,
                        title: {
                            display: true,
                            text: 'Stress Score',
                            font: {
                                weight: 'bold'
                            }
                        },
                        ticks: {
                            stepSize: 1,
                            font: {
                                weight: 'bold'
                            }
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Time',
                            font: {
                                weight: 'bold'
                            }
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: title,
                        color: isSampleData ? '#666' : '#333',
                        font: {
                            size: 16,
                            weight: 'bold'
                        },
                        padding: 20
                    },
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            color: '#333',
                            font: {
                                weight: 'bold',
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        titleFont: {
                            weight: 'bold'
                        },
                        bodyFont: {
                            weight: 'bold'
                        },
                        callbacks: {
                            label: function(context) {
                                return `Stress: ${context.parsed.y}/10`;
                            }
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                animation: {
                    duration: 1000,
                    easing: 'easeOutQuart'
                }
            }
        });
        
        console.log('✅ Chart created successfully with', (data.scores?.length || 0), 'data points');
        
    } catch (error) {
        console.error('❌ Error creating chart:', error);
        showSampleChart('Chart creation failed');
    }
}

function showSampleChart(message) {
    console.log('📋 Showing sample chart:', message);
    
    const sampleData = {
        labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        scores: [4.2, 5.1, 3.8, 6.2, 7.5, 4.0, 3.5],
        is_sample: true
    };
    
    createHistoryChart(sampleData, `${message} - Complete an assessment!`);
}

function showChartLoading() {
    const chartLoading = document.getElementById('chartLoading');
    const chartWrapper = document.querySelector('.chart-wrapper');
    
    if (chartLoading && chartWrapper) {
        console.log('⏳ Showing chart loading state');
        chartLoading.style.display = 'flex';
        chartWrapper.style.display = 'none';
    }
}

function hideChartLoading() {
    const chartLoading = document.getElementById('chartLoading');
    const chartWrapper = document.querySelector('.chart-wrapper');
    
    if (chartLoading && chartWrapper) {
        console.log('✅ Hiding chart loading state');
        chartLoading.style.display = 'none';
        chartWrapper.style.display = 'block';
    }
}

function showLoading(message = 'Loading...') {
    console.log('⏳ Showing loading state...');
    document.body.style.cursor = 'wait';
    
    const existingLoader = document.querySelector('.loading-indicator');
    if (existingLoader) existingLoader.remove();
    
    const loader = document.createElement('div');
    loader.className = 'loading-indicator';
    loader.innerHTML = `🔄 ${message}`;
    loader.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #4facfe;
        color: white;
        padding: 12px 18px;
        border-radius: 20px;
        z-index: 1000;
        font-weight: bold;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    `;
    document.body.appendChild(loader);
}

function showError(message) {
    console.error('🚨 Showing error:', message);
    hideLoading();
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-modal';
    errorDiv.innerHTML = `
        <div class="error-content">
            <div class="error-icon">🚨</div>
            <h3>Connection Issue</h3>
            <div class="error-message">${message}</div>
            <div class="error-actions">
                <button onclick="testBackendConnection()" class="btn-test">Test Connection</button>
                <button onclick="resetAnalysis()" class="btn-retry">Try Again</button>
                <button onclick="this.parentElement.parentElement.parentElement.remove()" class="btn-close">Close</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(errorDiv);
}

// Enhanced stats display with better formatting
function updateStatsDisplay(stats) {
    const statsContainer = document.getElementById('statsContainer');
    if (!statsContainer) {
        console.error('❌ Stats container not found');
        return;
    }
    
    console.log('📊 Updating stats display:', stats);
    
    if (!stats.has_data || stats.total_entries === 0) {
        statsContainer.innerHTML = `
            <div class="no-stats">
                <p>📊 No statistics available yet</p>
                <p><small>Complete an assessment to see your trends!</small></p>
            </div>
        `;
        statsContainer.style.display = 'block';
        return;
    }
    
    // Build level distribution string
    let levelDistributionText = '';
    const distributionEntries = Object.entries(stats.level_distribution || {});
    
    if (distributionEntries.length > 0) {
        levelDistributionText = distributionEntries.map(([level, count]) => 
            `<span class="level-tag level-${level.toLowerCase().replace(/ /g, '-')}">${level}: ${count}</span>`
        ).join(' ');
    } else {
        levelDistributionText = '<span class="no-data">No level data</span>';
    }
    
    statsContainer.innerHTML = `
        <div class="stats-header">
            <h3>📈 Your Statistics</h3>
        </div>
        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-value">${stats.total_entries}</div>
                <div class="stat-label">Total Entries</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${stats.average_stress}/10</div>
                <div class="stat-label">Average Stress</div>
            </div>
            <div class="stat-item">
                <div class="stat-value trend-${stats.trend}">${stats.trend}</div>
                <div class="stat-label">Trend</div>
            </div>
        </div>
        <div class="level-distribution">
            <div class="distribution-header">Level Distribution:</div>
            <div class="distribution-tags">${levelDistributionText}</div>
        </div>
    `;
    statsContainer.style.display = 'block';
}

// Enhanced reset function to properly clear everything
function resetAnalysis() {
    console.log('🔄 Resetting analysis...');
    
    const errorModal = document.querySelector('.error-modal');
    if (errorModal) errorModal.remove();
    
    hideLoading();
    
    // Show input sections, hide results
    document.getElementById('gameSection').style.display = 'block';
    document.getElementById('quickSelection').style.display = 'block';
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('comprehensiveAssessment').style.display = 'none';
    
    // Reset assessment data completely
    assessmentData = {
        physicalSymptoms: [],
        emotionalState: [],
        cognitiveSymptoms: [],
        lifestyleImpact: {
            sleep: null,
            appetite: null,
            social: null,
            functioning: null
        },
        copingMechanisms: [],
        duration: null,
        stressSource: null,
        initialMood: null
    };
    
    // Reset all UI selections
    document.querySelectorAll('.symptom-option, .emotion-option, .cognitive-option, .lifestyle-option, .coping-option, .duration-option, .source-option').forEach(option => {
        option.classList.remove('selected');
    });
    
    // Hide stats and clear chart
    const statsContainer = document.getElementById('statsContainer');
    if (statsContainer) {
        statsContainer.style.display = 'none';
    }
    
    // Destroy existing chart
    if (historyChart) {
        historyChart.destroy();
        historyChart = null;
    }
    
    // Reset bubble game
    selectionStartTime = Date.now();
    document.body.style.cursor = 'default';
    
    createBubbleGame();
    
    console.log('✅ Analysis reset complete');
    showNotification('🔄 Analysis reset. Ready for new assessment!', 'info');
}

// Add CSS for stats
function injectStatsStyles() {
    if (!document.querySelector('#stats-styles')) {
        const style = document.createElement('style');
        style.id = 'stats-styles';
        style.textContent = `
            .stats-header h3 {
                margin-bottom: 15px;
                color: #495057;
                text-align: center;
                font-size: 1.2em;
            }
            
            .level-distribution {
                margin-top: 20px;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 10px;
                border: 1px solid #e9ecef;
            }
            
            .distribution-header {
                font-weight: bold;
                margin-bottom: 10px;
                color: #495057;
                text-align: center;
            }
            
            .distribution-tags {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                justify-content: center;
            }
            
            .level-tag {
                padding: 6px 12px;
                border-radius: 15px;
                font-size: 0.8em;
                font-weight: bold;
                color: white;
            }
            
            .level-tag.level-low { background: #4caf50; }
            .level-tag.level-medium { background: #ff9800; }
            .level-tag.level-high { background: #f44336; }
            .level-tag.level-very-high { background: #d32f2f; }
            .level-tag.level-chronic-high { background: #b71c1c; }
            .level-tag.level-low-medium { background: #8bc34a; }
            
            .no-stats {
                text-align: center;
                padding: 30px 20px;
                color: #6c757d;
                background: #f8f9fa;
                border-radius: 10px;
                border: 2px dashed #dee2e6;
            }
            
            .no-stats p {
                margin: 5px 0;
            }
            
            .no-data {
                color: #6c757d;
                font-style: italic;
            }
            
            .trend-increasing { color: #f44336; font-weight: bold; }
            .trend-decreasing { color: #4caf50; font-weight: bold; }
            .trend-stable { color: #ff9800; font-weight: bold; }
            .trend-ai { color: #2196f3; font-weight: bold; }
            .trend-rule-based { color: #6c757d; font-weight: bold; }
        `;
        document.head.appendChild(style);
    }
}

// Add global function for testing
window.testBackendConnection = testBackendConnection;
window.showAuthTab = showAuthTab;
window.login = login;
window.register = register;
window.logout = logout;
window.continueAsGuest = continueAsGuest;
window.resetAnalysis = resetAnalysis;
window.nextSection = nextSection;
window.prevSection = prevSection;
window.calculateComprehensiveScore = calculateComprehensiveScore;

// Debug function to check current state
window.debugState = function() {
    console.log('🔍 DEBUG STATE:');
    console.log('User ID:', currentUserId);
    console.log('Username:', currentUsername);
    console.log('Assessment Data:', assessmentData);
    console.log('History Chart:', historyChart);
    
    // Test backend connection
    testBackendConnection();
    
    // Force reload data
    loadRealHistoryChart();
    loadUserStats();
};

// Debug authentication
window.debugAuth = function() {
    console.log('🔍 DEBUG AUTH:');
    console.log('Current User ID:', currentUserId);
    console.log('Current Username:', currentUsername);
    
    fetch(`${API_BASE}/debug/session`, {credentials: 'include'})
        .then(r => r.json())
        .then(console.log);
    
    fetch(`${API_BASE}/debug/users`, {credentials: 'include'})
        .then(r => r.json())
        .then(console.log);
};

//Vinusha
// Motivation functionality
let currentMotivationData = null;
let audioElement = null;
let isAudioPlaying = false;

function showMotivationPage() {
    // Hide results and show motivation section
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('motivationSection').style.display = 'block';
    
    // Get stress data from results
    const stressScore = parseFloat(document.getElementById('stressScore').textContent);
    const stressLevel = document.getElementById('levelBadge').textContent;
    
    // Update motivation section with stress data
    document.getElementById('motivationStressLevel').textContent = stressScore;
    
    // Generate motivational message
    generateMotivationalMessage(stressScore, stressLevel);
}

function goBackToResults() {
    document.getElementById('motivationSection').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'block';
}

async function generateMotivationalMessage(stressScore, stressLevel) {
    const typingIndicator = document.getElementById('typingIndicator');
    const motivationText = document.getElementById('motivationText');
    const playButton = document.getElementById('playButton');
    
    // Show typing indicator
    typingIndicator.style.display = 'block';
    motivationText.style.display = 'none';
    playButton.disabled = true;
    
    try {
        const response = await fetch('/api/generate-motivation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                stress_level: stressScore,
                stress_category: stressLevel,
                user_message: '',
                generate_audio: true,
                play_audio: false
            })
        });
        
        const data = await response.json();
        currentMotivationData = data;
        
        // Display message
        typingIndicator.style.display = 'none';
        motivationText.style.display = 'block';
        motivationText.textContent = data.motivational_message;
        
        // Enable audio if available
        if (data.audio_file_path) {
            playButton.disabled = false;
        }
        
    } catch (error) {
        console.error('Error generating motivation:', error);
        typingIndicator.style.display = 'none';
        motivationText.style.display = 'block';
        motivationText.textContent = "I'm here to support you through this challenging time. Remember that every small step forward counts, and you're doing better than you think.";
    }
}

async function toggleAudio() {
    if (!currentMotivationData || !currentMotivationData.audio_file_path) {
        console.log("No audio file available");
        return;
    }

    initAudioElement();

    const playButton = document.getElementById('playButton');
    const playIcon = document.getElementById('playIcon');
    const playText = document.getElementById('playText');

    if (!isAudioPlaying) {
        // PLAY
        try {
            console.log("Playing audio:", currentMotivationData.audio_file_path);
            
            // Set the audio source if it changed
            if (audioElement.src !== currentMotivationData.audio_file_path) {
                audioElement.src = currentMotivationData.audio_file_path;
            }

            // Play the audio
            await audioElement.play();
            isAudioPlaying = true;

            // Update UI
            playIcon.textContent = '⏸️';
            playText.textContent = 'Pause';
            playButton.classList.add('playing');

        } catch (error) {
            console.error('Error playing audio:', error);
            alert('Could not play audio. Please try again.');
            isAudioPlaying = false;
            resetAudioControls();
        }

    } else {
        // PAUSE
        audioElement.pause();
        isAudioPlaying = false;

        // Update UI
        playIcon.textContent = '▶️';
        playText.textContent = 'Play Message';
        playButton.classList.remove('playing');
    }
}

function initAudioElement() {
    if (!audioElement) {
        audioElement = new Audio();
        audioElement.addEventListener('ended', () => {
            isAudioPlaying = false;
            resetAudioControls();
        });
        audioElement.addEventListener('play', () => {
            isAudioPlaying = true;
            updatePlayButtonUI();
        });
        audioElement.addEventListener('pause', () => {
            isAudioPlaying = false;
            updatePlayButtonUI();
        });
        audioElement.addEventListener('timeupdate', updateProgressBar);
        audioElement.addEventListener('loadedmetadata', updateDuration);
    }
}

function updatePlayButtonUI() {
    const playButton = document.getElementById('playButton');
    const playIcon = document.getElementById('playIcon');
    const playText = document.getElementById('playText');

    if (isAudioPlaying) {
        playIcon.textContent = '⏸️';
        playText.textContent = 'Pause';
        playButton.classList.add('playing');
    } else {
        playIcon.textContent = '▶️';
        playText.textContent = 'Play Message';
        playButton.classList.remove('playing');
    }
}

function updateProgressBar() {
    if (!audioElement || !audioElement.duration) return;

    const progressBarFill = document.getElementById('progressBarFill');
    const progressBarHandle = document.getElementById('progressBarHandle');
    const currentTimeEl = document.getElementById('currentTime');

    const percentage = (audioElement.currentTime / audioElement.duration) * 100;

    if (progressBarFill) progressBarFill.style.width = percentage + '%';
    if (progressBarHandle) progressBarHandle.style.left = percentage + '%';
    if (currentTimeEl) currentTimeEl.textContent = formatTime(audioElement.currentTime);
}

function updateDuration() {
    const durationEl = document.getElementById('durationTime');
    if (durationEl && audioElement && audioElement.duration) {
        durationEl.textContent = formatTime(audioElement.duration);
    }
}

function formatTime(seconds) {
    if (isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
}

function enableAudioPlayback(audioUrl) {
    console.log("🎵 Enabling audio playback for:", audioUrl);
    
    // Ensure audio element exists
    initAudioElement();
    
    // Update the audio element's source
    audioElement.src = audioUrl;
    console.log("📝 Audio element src set to:", audioElement.src);
    
    // Store in currentMotivationData
    currentMotivationData = currentMotivationData || {};
    currentMotivationData.audio_file_path = audioUrl;

    const playButton = document.getElementById('playButton');
    if (playButton) {
        playButton.disabled = false;
        console.log("✅ Play button enabled");
    }

    resetAudioControls();
}

function setupProgressBarClick() {
    const progressBarContainer = document.getElementById('progressBarContainer');
    
    if (!progressBarContainer) return;

    progressBarContainer.addEventListener('click', (e) => {
        if (!audioElement || !audioElement.duration) return;

        const rect = progressBarContainer.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const percentage = clickX / rect.width;
        audioElement.currentTime = percentage * audioElement.duration;
    });
}

function animateAudioWave(audioWave) {
    let progress = 0;
    const interval = setInterval(() => {
        progress += 2;
        audioWave.style.width = progress + '%';
        
        if (progress >= 100) {
            clearInterval(interval);
            setTimeout(() => {
                resetAudioControls();
            }, 500);
        }
    }, 100);
}

function resetAudioControls() {
    const playButton = document.getElementById('playButton');
    const playText = document.getElementById('playText');
    const audioWave = document.getElementById('audioWave');
    
    if (playButton) playButton.classList.remove('playing');
    if (playText) playText.textContent = 'Play Message';
    if (audioWave) audioWave.style.width = '0%';  // Only set if element exists
    isAudioPlaying = false;
}

function startBreathingExercise() {
    document.getElementById('breathingExercise').style.display = 'block';
}

function stopBreathingExercise() {
    document.getElementById('breathingExercise').style.display = 'none';
    showTemporaryMessage("Great job! Taking deep breaths can really help reduce stress. 🎉");
}

function showAffirmations() {
    const affirmations = [
        "You are capable of amazing things.",
        "Your feelings are valid and important.",
        "Progress, not perfection, is what matters.",
        "You've survived 100% of your bad days so far.",
        "This moment is just a moment, and it will pass."
    ];
    
    const randomAffirmation = affirmations[Math.floor(Math.random() * affirmations.length)];
    document.getElementById('motivationText').textContent = `💝 ${randomAffirmation}`;
}

function saveMotivation() {
    if (currentMotivationData) {
        // In a real app, you'd save to localStorage or send to backend
        showTemporaryMessage("Motivation saved to your favorites! 💾");
    }
}

async function generateNewMotivation() {
    try {
        console.log("Generating new motivation...");
        
        const scoreElement = document.getElementById('stressScore');
        const levelElement = document.getElementById('levelBadge');
        
        if (!scoreElement || !levelElement) {
            console.error("Could not find stress score elements");
            showNotification('❌ Could not find stress data', 'error');
            return;
        }

        const stressLevel = parseFloat(scoreElement.textContent);
        const stressCategory = levelElement.textContent;

        console.log("Stress data:", { stressLevel, stressCategory });

        // Show loading indicator
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) typingIndicator.style.display = 'block';

        const motivationText = document.getElementById('motivationText');
        if (motivationText) motivationText.innerHTML = '';

        // Disable play button while generating
        const playButton = document.getElementById('playButton');
        if (playButton) playButton.disabled = true;

        // Call backend to generate motivation
        const response = await fetch('/api/generate-motivation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                stress_level: stressLevel,
                stress_category: stressCategory,
                user_message: `I'm feeling ${stressCategory.toLowerCase()} stress`,
                generate_audio: true,
                voice_gender: 'female'
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log("Motivation response:", data);

        // Hide loading indicator FIRST
        if (typingIndicator) typingIndicator.style.display = 'none';

        // Display message IMMEDIATELY
        if (motivationText && data.motivational_message) {
            motivationText.textContent = data.motivational_message;
            motivationText.style.display = 'block';
        }

        // Handle audio separately - no blocking
        if (data.audio_file_path) {
            console.log("✅ Audio URL received:", data.audio_file_path);
            // Audio path is already a full URL like /api/audio-stream/uuid
            enableAudioPlayback(data.audio_file_path);
            showNotification('✅ New motivation generated!', 'success');
        } else {
            console.warn("⚠️ No audio file in response");
            if (playButton) playButton.disabled = true;
            showNotification('✅ Motivation generated (audio unavailable)', 'info');
        }

    } catch (error) {
        console.error("❌ Error generating motivation:", error);
        console.error("Full error object:", error);
        
        // Hide loading
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) typingIndicator.style.display = 'none';
        
        // Show specific error message
        showNotification(`❌ Error: ${error.message}`, 'error');
        
        // Display fallback text
        const motivationText = document.getElementById('motivationText');
        if (motivationText) {
            motivationText.textContent = "I'm here for you. Take a deep breath. You've got this.";
            motivationText.style.display = 'block';
        }
    }
}

function showTemporaryMessage(message) {
    const motivationText = document.getElementById('motivationText');
    const originalText = motivationText.textContent;
    
    motivationText.textContent = message;
    
    setTimeout(() => {
        motivationText.textContent = originalText;
    }, 3000);
    
}