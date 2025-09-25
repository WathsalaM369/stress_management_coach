// Stress Management Coach - JavaScript Module

class StressCoachApp {
    constructor() {
        this.selectedMood = 'focused';
        this.stressLevel = 5;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.updateStressDisplay();
    }

    setupEventListeners() {
        // Mood selector
        document.querySelectorAll('.mood-option').forEach(option => {
            option.addEventListener('click', (e) => {
                document.querySelectorAll('.mood-option').forEach(opt => opt.classList.remove('active'));
                e.target.classList.add('active');
                this.selectedMood = e.target.dataset.mood;
            });
        });

        // Stress level slider
        const stressSlider = document.getElementById('stressLevel');
        if (stressSlider) {
            stressSlider.addEventListener('input', (e) => {
                this.stressLevel = parseInt(e.target.value);
                this.updateStressDisplay();
            });
        }
    }

    updateStressDisplay() {
        const display = document.getElementById('stressDisplay');
        if (display) {
            display.textContent = `Stress Level: ${this.stressLevel}/10`;
        }
    }

    showMessage(message, type = 'error') {
        const messagesContainer = document.getElementById('messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.textContent = message;
        
        messagesContainer.appendChild(messageDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.parentNode.removeChild(messageDiv);
            }
        }, 5000);
    }

    parseTasksInput(tasksText) {
        if (!tasksText.trim()) return [];
        
        return tasksText.split('\n')
            .filter(line => line.trim())
            .map((task, index) => ({
                id: `task_${Date.now()}_${index}`,
                title: task.trim(),
                description: '',
                priority: 'medium',
                category: 'work',
                estimated_duration: 60,
                deadline: null,
                is_flexible: true
            }));
    }

    parseTimeSlots(slotsText) {
        if (!slotsText.trim()) return [];
        
        return slotsText.split('\n')
            .filter(line => line.trim())
            .map((slot, index) => {
                try {
                    const parts = slot.trim().split(' ');
                    const timeRange = parts[0];
                    const label = parts.slice(1).join(' ') || `Time slot ${index + 1}`;
                    
                    if (!timeRange.includes('-')) {
                        throw new Error('Invalid time format');
                    }
                    
                    const [start, end] = timeRange.split('-');
                    const today = new Date().toISOString().split('T')[0];
                    
                    return {
                        start_time: `${today}T${start}:00`,
                        end_time: `${today}T${end}:00`,
                        is_available: true,
                        label: label
                    };
                } catch (error) {
                    console.warn(`Invalid time slot format: ${slot}`);
                    return null;
                }
            })
            .filter(slot => slot !== null);
    }

    validateInputs(tasks, timeSlots) {
        if (!tasks.length) {
            this.showMessage('Please enter at least one task');
            return false;
        }
        
        if (!timeSlots.length) {
            this.showMessage('Please enter at least one time slot in format "09:00-11:00 Morning work"');
            return false;
        }
        
        return true;
    }

    showLoading() {
        const loading = document.getElementById('loading');
        const results = document.getElementById('results');
        
        if (loading) loading.classList.add('show');
        if (results) results.classList.remove('show');
    }

    hideLoading() {
        const loading = document.getElementById('loading');
        if (loading) loading.classList.remove('show');
    }

    async analyzeAndSchedule() {
        const userText = document.getElementById('userText')?.value.trim() || '';
        const tasksText = document.getElementById('tasksInput')?.value.trim() || '';
        const timeSlotsText = document.getElementById('timeSlots')?.value.trim() || '';

        const tasks = this.parseTasksInput(tasksText);
        const timeSlots = this.parseTimeSlots(timeSlotsText);

        if (!this.validateInputs(tasks, timeSlots)) {
            return;
        }

        this.showLoading();

        try {
            const requestData = {
                tasks: tasks,
                mood: this.selectedMood,
                available_blocks: timeSlots
            };

            // Use stress estimation if text provided, otherwise manual level
            if (userText) {
                requestData.user_text = userText;
            } else {
                requestData.user_stress_level = this.stressLevel;
            }

            const response = await fetch('/api/schedule', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            this.displayResults(result);
            this.showMessage('Schedule generated successfully!', 'success');

        } catch (error) {
            console.error('Error:', error);
            this.showMessage(`Failed to generate schedule: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }

    displayResults(result) {
        const results = document.getElementById('results');
        if (results) {
            results.classList.add('show');
            results.scrollIntoView({ behavior: 'smooth' });
        }

        this.displayStressAnalysis(result);
        this.displaySchedule(result);
        this.displayRecommendations(result);
    }

    displayStressAnalysis(result) {
        const container = document.getElementById('stressResults');
        if (!container) return;

        const stressLevel = result.stress_analysis?.level || 'N/A';
        const stressImpact = result.stress_analysis?.impact || 'No impact analysis available';
        const stressActions = result.stress_analysis?.recommended_actions || [];

        container.innerHTML = `
            <div class="stress-summary">
                <p><strong>Detected Stress Level:</strong> ${stressLevel}/10</p>
                <p><strong>Impact Assessment:</strong> ${stressImpact}</p>
                ${stressActions.length > 0 ? `
                    <div class="stress-actions">
                        <strong>Recommended Actions:</strong>
                        <div class="action-tags">
                            ${stressActions.map(action => 
                                `<span class="action-tag">${action.replace('_', ' ')}</span>`
                            ).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }

    displaySchedule(result) {
        const container = document.getElementById('scheduleItems');
        if (!container) return;

        if (!result.optimized_schedule || result.optimized_schedule.length === 0) {
            container.innerHTML = '<p class="no-schedule">No schedule items generated</p>';
            return;
        }

        let scheduleHtml = '';
        result.optimized_schedule.forEach(item => {
            const startTime = this.formatTime(item.time_block.start_time);
            const endTime = this.formatTime(item.time_block.end_time);
            
            scheduleHtml += `
                <div class="schedule-item">
                    <div class="time">${startTime} - ${endTime}</div>
                    <h4>${item.task.title}</h4>
                    ${item.task.description ? `<div class="description">${item.task.description}</div>` : ''}
                    <div class="meta">
                        <span>Priority: ${item.task.priority.toUpperCase()}</span>
                        <span>Duration: ${item.task.estimated_duration} mins</span>
                        <span>Category: ${item.task.category}</span>
                        ${item.task.analysis ? `<span>Score: ${(item.task.analysis.overall_priority || 0).toFixed(2)}</span>` : ''}
                    </div>
                    ${this.renderSchedulingNotes(item.scheduling_notes)}
                </div>
            `;
        });

        container.innerHTML = scheduleHtml;
    }

    renderSchedulingNotes(notes) {
        if (!notes || notes.length === 0) return '';
        
        return `
            <div class="scheduling-notes">
                ${notes.map(note => `<div class="note">${note}</div>`).join('')}
            </div>
        `;
    }

    displayRecommendations(result) {
        const container = document.getElementById('recommendationsList');
        if (!container) return;

        const recommendations = result.insights?.recommended_adjustments || [];
        
        if (recommendations.length === 0) {
            container.innerHTML = '<p>No specific recommendations at this time.</p>';
            return;
        }

        container.innerHTML = `
            <ul class="recommendations-list">
                ${recommendations.map(rec => `<li>${rec}</li>`).join('')}
            </ul>
        `;
    }

    formatTime(isoString) {
        try {
            return new Date(isoString).toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit',
                hour12: false
            });
        } catch (error) {
            console.warn('Error formatting time:', isoString);
            return 'Invalid time';
        }
    }

    clearAll() {
        // Clear form inputs
        const inputs = ['userText', 'tasksInput', 'timeSlots'];
        inputs.forEach(id => {
            const element = document.getElementById(id);
            if (element) element.value = '';
        });

        // Reset stress level
        const stressSlider = document.getElementById('stressLevel');
        if (stressSlider) {
            stressSlider.value = 5;
            this.stressLevel = 5;
            this.updateStressDisplay();
        }

        // Reset mood to focused
        document.querySelectorAll('.mood-option').forEach(opt => opt.classList.remove('active'));
        const focusedOption = document.querySelector('.mood-option[data-mood="focused"]');
        if (focusedOption) {
            focusedOption.classList.add('active');
            this.selectedMood = 'focused';
        }

        // Hide results
        const results = document.getElementById('results');
        if (results) results.classList.remove('show');

        this.showMessage('Form cleared successfully', 'info');
    }
}

// Global functions (for onclick handlers)
let stressCoachApp;

function analyzeAndSchedule() {
    if (stressCoachApp) {
        stressCoachApp.analyzeAndSchedule();
    }
}

function clearAll() {
    if (stressCoachApp) {
        stressCoachApp.clearAll();
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    stressCoachApp = new StressCoachApp();
});

// Add some additional CSS styles dynamically
const additionalStyles = `
    .stress-summary {
        line-height: 1.6;
    }
    
    .action-tags {
        margin-top: 10px;
    }
    
    .action-tag {
        display: inline-block;
        background: rgba(102, 126, 234, 0.1);
        color: #667eea;
        padding: 4px 12px;
        margin: 2px 4px;
        border-radius: 15px;
        font-size: 0.9em;
        font-weight: 500;
        text-transform: capitalize;
    }
    
    .scheduling-notes {
        margin-top: 15px;
        padding-top: 10px;
        border-top: 1px solid #eee;
    }
    
    .scheduling-notes .note {
        background: #fff3cd;
        padding: 8px 12px;
        border-radius: 5px;
        margin: 5px 0;
        font-size: 0.9em;
        border-left: 3px solid #ffc107;
    }
    
    .recommendations-list {
        list-style: none;
        padding: 0;
    }
    
    .recommendations-list li {
        background: rgba(255, 255, 255, 0.7);
        padding: 12px;
        margin: 8px 0;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
        position: relative;
    }
    
    .recommendations-list li:before {
        content: "💡";
        margin-right: 10px;
    }
    
    .no-schedule {
        text-align: center;
        color: #666;
        font-style: italic;
        padding: 20px;
    }
`;

const styleSheet = document.createElement('style');
styleSheet.textContent = additionalStyles;
document.head.appendChild(styleSheet);