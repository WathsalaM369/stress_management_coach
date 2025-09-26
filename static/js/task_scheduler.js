// Enhanced Stress Management Coach - JavaScript Module
// Fixed time allocation and improved AI agent integration

class StressCoachApp {
    constructor() {
        this.selectedMood = 'focused';
        this.stressLevel = 5;
        this.aiAgent = new AITaskSchedulerAgent();
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
            .map((line, index) => {
                const parts = line.split('|').map(p => p.trim());
                
                if (parts.length >= 1) {
                    const task = {
                        id: `task_${Date.now()}_${index}`,
                        title: parts[0] || `Task ${index + 1}`,
                        description: `Task: ${parts[0]}`,
                        estimated_duration: parseInt(parts[1]) || 60,
                        priority: (parts[2] || 'medium').toLowerCase(),
                        category: 'work',
                        is_flexible: true
                    };
                    
                    if (parts[3] && parts[3].trim()) {
                        task.deadline = parts[3].trim();
                    }
                    
                    return task;
                } else {
                    return {
                        id: `task_${Date.now()}_${index}`,
                        title: line.trim(),
                        description: '',
                        priority: 'medium',
                        category: 'work',
                        estimated_duration: 60,
                        deadline: null,
                        is_flexible: true
                    };
                }
            });
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
                    
                    const startTime = `${today}T${start}:00`;
                    const endTime = `${today}T${end}:00`;
                    
                    // Calculate actual duration
                    const duration = this.calculateSlotDuration(startTime, endTime);
                    
                    return {
                        start_time: startTime,
                        end_time: endTime,
                        duration_minutes: duration,
                        is_available: true,
                        label: label,
                        description: label
                    };
                } catch (error) {
                    console.warn(`Invalid time slot format: ${slot}`);
                    return null;
                }
            })
            .filter(slot => slot !== null);
    }

    calculateSlotDuration(startTime, endTime) {
        try {
            const start = new Date(startTime);
            const end = new Date(endTime);
            return Math.max(0, Math.round((end - start) / (1000 * 60)));
        } catch (error) {
            return 60; // Default fallback
        }
    }

    validateInputs(tasks, timeSlots) {
        if (!tasks.length) {
            this.showMessage('Please enter at least one task. Format: Task Title | Duration(min) | Priority | Deadline');
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
            // Use local AI agent for demonstration if API fails
            let result;
            try {
                // Try API first
                const requestData = {
                    user_text: userText,
                    stress_data: { stress_level: this.stressLevel },
                    mood: this.selectedMood,
                    tasks: tasks,
                    available_blocks: timeSlots
                };

                const response = await fetch('/api/schedule', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(requestData),
                    timeout: 10000
                });

                if (response.ok) {
                    result = await response.json();
                } else {
                    throw new Error('API unavailable');
                }
            } catch (apiError) {
                // Fallback to local AI processing
                console.log('Using local AI agent fallback');
                result = this.aiAgent.processScheduleLocally(tasks, timeSlots, this.stressLevel, this.selectedMood);
            }

            this.displayResults(result);
            this.showMessage('AI schedule generated successfully!', 'success');

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

        this.updateSummaryStats(result);
        this.displayStressAnalysis(result);
        this.displaySchedule(result);
        this.displayRecommendations(result);
    }

    updateSummaryStats(result) {
        const totalTasksEl = document.getElementById('totalTasks');
        const scheduledTasksEl = document.getElementById('scheduledTasks');
        const totalHoursEl = document.getElementById('totalHours');
        const avgConfidenceEl = document.getElementById('avgConfidence');

        if (totalTasksEl) {
            totalTasksEl.textContent = result.task_analysis?.total_tasks || 0;
        }
        
        if (scheduledTasksEl) {
            const scheduledCount = result.optimized_schedule?.filter(item => 
                item.allocated_duration > 0).length || 0;
            scheduledTasksEl.textContent = scheduledCount;
        }
        
        if (totalHoursEl) {
            const totalHours = result.insights?.scheduling_summary?.total_work_hours || 0;
            totalHoursEl.textContent = totalHours + 'h';
        }
        
        if (avgConfidenceEl) {
            const avgConf = result.insights?.scheduling_summary?.average_scheduling_confidence || 0;
            avgConfidenceEl.textContent = Math.round(avgConf * 100) + '%';
        }
    }

    displayStressAnalysis(result) {
        const container = document.getElementById('stressResults');
        if (!container) return;

        const stressLevel = result.stress_analysis?.level || 'N/A';
        const stressImpact = result.stress_analysis?.impact || 'No impact analysis available';
        const stressActions = result.stress_analysis?.recommended_actions || [];

        container.innerHTML = `
            <div class="stress-summary">
                <p><strong>AI Stress Analysis:</strong> Level ${stressLevel}/10</p>
                <p><strong>Impact Assessment:</strong> ${stressImpact}</p>
                <p><strong>Mood Optimization:</strong> ${result.insights?.mood_optimization || 'Schedule optimized for current mood'}</p>
                <p><strong>AI Method:</strong> ${result.ai_metadata?.analysis_method || 'AI-Enhanced Analysis'}</p>
                ${stressActions.length > 0 ? `
                    <div class="stress-actions">
                        <strong>AI Recommendations:</strong>
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
        
        const scheduledItems = result.optimized_schedule.filter(item => 
            item.completion_status !== 'not_scheduled');
        const unscheduledItems = result.optimized_schedule.filter(item => 
            item.completion_status === 'not_scheduled');

        // Display scheduled items
        scheduledItems.forEach((item, index) => {
            scheduleHtml += this.renderScheduleItem(item, index);
        });

        // Display unscheduled items
        if (unscheduledItems.length > 0) {
            scheduleHtml += `
                <div class="unscheduled-section">
                    <h4 style="color: #dc3545; margin: 20px 0 10px 0;">
                        ⚠️ Tasks That Need More Time (${unscheduledItems.length})
                    </h4>
            `;
            
            unscheduledItems.forEach((item, index) => {
                scheduleHtml += this.renderScheduleItem(item, index, true);
            });
            
            scheduleHtml += '</div>';
        }

        container.innerHTML = scheduleHtml;
    }

    renderScheduleItem(item, index, isUnscheduled = false) {
        const task = item.task || {};
        const timeBlock = item.time_block;
        
        let timeDisplay = 'Not Scheduled';
        let statusClass = 'schedule-item';
        let actualDuration = item.allocated_duration || 0;
        
        if (!isUnscheduled && timeBlock) {
            const startTime = this.formatTime(timeBlock.start_time);
            const endTime = this.formatTime(timeBlock.end_time);
            timeDisplay = `${startTime} - ${endTime}`;
            
            // FIXED: Use actual time block duration, not just allocated_duration
            const slotDuration = timeBlock.duration_minutes || this.calculateSlotDuration(timeBlock.start_time, timeBlock.end_time);
            actualDuration = Math.min(actualDuration, slotDuration);
        }
        
        // Status-specific styling
        if (item.completion_status === 'partial') {
            statusClass += ' partial-task';
        } else if (item.completion_status === 'scaled') {
            statusClass += ' scaled-task';
        } else if (item.completion_status === 'not_scheduled') {
            statusClass += ' unscheduled-task';
        }
        
        // Status badges
        let statusBadge = '';
        switch(item.completion_status) {
            case 'partial':
                statusBadge = '<span class="status-badge partial">SPLIT TASK</span>';
                break;
            case 'scaled':
                statusBadge = '<span class="status-badge scaled">CONDENSED</span>';
                break;
            case 'not_scheduled':
                statusBadge = '<span class="status-badge unscheduled">NOT SCHEDULED</span>';
                break;
            default:
                statusBadge = '<span class="status-badge complete">SCHEDULED</span>';
        }
        
        const urgency = item.deadline_urgency || 0;
        let urgencyBadge = '';
        if (urgency > 0.8) {
            urgencyBadge = '<span class="urgency-badge high">URGENT</span>';
        } else if (urgency > 0.5) {
            urgencyBadge = '<span class="urgency-badge medium">MEDIUM</span>';
        } else if (urgency > 0.2) {
            urgencyBadge = '<span class="urgency-badge low">LOW PRIORITY</span>';
        }

        return `
            <div class="${statusClass}">
                <div class="time">${timeDisplay}</div>
                <h4>${task.title || 'Unnamed Task'}</h4>
                ${task.description ? `<div class="description">${task.description}</div>` : ''}
                
                <div class="task-badges">
                    ${statusBadge}
                    ${urgencyBadge}
                </div>
                
                <div class="meta">
                    <span>Time Allocated: ${actualDuration} mins</span>
                    <span>Priority: ${(task.priority || 'medium').toUpperCase()}</span>
                    ${task.estimated_duration ? `<span>Requested: ${task.estimated_duration} mins</span>` : ''}
                    ${task.deadline ? `<span>Due: ${new Date(task.deadline).toLocaleDateString()}</span>` : ''}
                    <span>AI Confidence: ${Math.round((item.scheduling_confidence || 0) * 100)}%</span>
                </div>
                
                ${this.renderSchedulingNotes(item.notes || item.scheduling_notes)}
            </div>
        `;
    }

    renderSchedulingNotes(notes) {
        if (!notes || notes.length === 0) return '';
        
        return `
            <div class="scheduling-notes">
                <strong>AI Analysis:</strong>
                ${notes.map(note => `<div class="note">• ${note}</div>`).join('')}
            </div>
        `;
    }

    displayRecommendations(result) {
        const container = document.getElementById('recommendationsList');
        if (!container) return;

        const recommendations = result.insights?.recommendations || [];
        
        if (recommendations.length === 0) {
            container.innerHTML = '<p>No specific AI recommendations at this time.</p>';
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
        const inputs = ['userText', 'tasksInput', 'timeSlots'];
        inputs.forEach(id => {
            const element = document.getElementById(id);
            if (element) element.value = '';
        });

        const stressSlider = document.getElementById('stressLevel');
        if (stressSlider) {
            stressSlider.value = 5;
            this.stressLevel = 5;
            this.updateStressDisplay();
        }

        document.querySelectorAll('.mood-option').forEach(opt => opt.classList.remove('active'));
        const focusedOption = document.querySelector('.mood-option[data-mood="focused"]');
        if (focusedOption) {
            focusedOption.classList.add('active');
            this.selectedMood = 'focused';
        }

        const results = document.getElementById('results');
        if (results) results.classList.remove('show');

        this.showMessage('Form cleared successfully', 'info');
    }
}

// Local AI Agent for fallback processing
// Key fixes for the scheduling algorithm

// Fix 1: In the JavaScript frontend - improve local AI agent scheduling
class AITaskSchedulerAgent {
    processScheduleLocally(tasks, timeSlots, stressLevel, mood) {
        // Analyze tasks with AI-like processing
        const analyzedTasks = tasks.map(task => ({
            ...task,
            analysis: {
                deadline_urgency: this.calculateDeadlineUrgency(task),
                importance_score: this.getImportanceScore(task.priority),
                complexity_score: this.assessComplexity(task.title),
                task_type: this.classifyTaskType(task.title),
                ai_confidence: 0.85,
                stress_compatibility: this.calculateStressCompatibility(task, stressLevel),
                final_priority: this.calculateFinalPriority(task, stressLevel)
            }
        }));

        // Sort by priority
        analyzedTasks.sort((a, b) => b.analysis.final_priority - a.analysis.final_priority);

        // FIXED: Create comprehensive schedule that handles ALL tasks
        const schedule = this.createOptimizedScheduleFixed(analyzedTasks, timeSlots, stressLevel, mood);

        return {
            optimized_schedule: schedule,
            stress_analysis: {
                level: stressLevel,
                impact: this.getStressImpact(stressLevel),
                recommended_actions: this.getStressActions(stressLevel)
            },
            task_analysis: {
                total_tasks: tasks.length,
                scheduled_tasks: schedule.filter(item => item.allocated_duration > 0).length
            },
            insights: {
                scheduling_summary: {
                    total_work_hours: schedule.reduce((total, item) => total + (item.allocated_duration || 0), 0) / 60,
                    average_scheduling_confidence: 0.85
                },
                mood_optimization: `Schedule optimized for ${mood} mood state`,
                recommendations: this.generateRecommendations(schedule, stressLevel)
            },
            ai_metadata: {
                ai_enabled: true,
                analysis_method: "Local AI Agent - Fixed",
                generated_at: new Date().toISOString()
            }
        };
    }

    createOptimizedScheduleFixed(tasks, timeSlots, stressLevel, mood) {
        if (!tasks.length || !timeSlots.length) {
            return tasks.map(task => ({
                task,
                time_block: null,
                allocated_duration: 0,
                completion_status: 'not_scheduled',
                scheduling_confidence: 0.0,
                deadline_urgency: task.analysis?.deadline_urgency || 0,
                notes: ['No time slots available']
            }));
        }

        const schedule = [];
        const remainingTasks = [...tasks];
        const availableSlots = timeSlots.map(slot => ({
            ...slot,
            remaining_time: slot.duration_minutes,
            used: false
        }));

        // Calculate totals
        const totalTaskTime = tasks.reduce((sum, task) => sum + task.estimated_duration, 0);
        const totalAvailableTime = timeSlots.reduce((sum, slot) => sum + slot.duration_minutes, 0);

        console.log(`Scheduling ${tasks.length} tasks (${totalTaskTime}min) into ${timeSlots.length} slots (${totalAvailableTime}min)`);

        // Strategy 1: Try to fit tasks perfectly first
        remainingTasks.forEach(task => {
            const taskDuration = task.estimated_duration;
            
            // Find best fitting slot
            let bestSlot = null;
            let bestSlotIndex = -1;
            let bestFit = Infinity;

            availableSlots.forEach((slot, index) => {
                if (!slot.used && slot.remaining_time >= taskDuration) {
                    const fit = slot.remaining_time - taskDuration; // Prefer tight fits
                    if (fit < bestFit) {
                        bestFit = fit;
                        bestSlot = slot;
                        bestSlotIndex = index;
                    }
                }
            });

            if (bestSlot) {
                schedule.push({
                    task,
                    time_block: bestSlot,
                    allocated_duration: taskDuration,
                    completion_status: 'complete',
                    scheduling_confidence: 0.9,
                    deadline_urgency: task.analysis?.deadline_urgency || 0,
                    notes: [`Perfect fit in ${bestSlot.duration_minutes}-minute slot`]
                });
                
                // Mark slot as used or update remaining time
                if (bestSlot.remaining_time === taskDuration) {
                    availableSlots[bestSlotIndex].used = true;
                } else {
                    availableSlots[bestSlotIndex].remaining_time -= taskDuration;
                }
                
                // Remove task from remaining
                const taskIndex = remainingTasks.indexOf(task);
                remainingTasks.splice(taskIndex, 1);
            }
        });

        // Strategy 2: For remaining tasks, use partial scheduling or time scaling
        remainingTasks.forEach(task => {
            const taskDuration = task.estimated_duration;
            
            // Find any available slot with some time
            let bestSlot = null;
            let bestSlotIndex = -1;
            let maxAvailableTime = 0;

            availableSlots.forEach((slot, index) => {
                if (!slot.used && slot.remaining_time > maxAvailableTime && slot.remaining_time >= 15) { // Minimum 15 minutes
                    maxAvailableTime = slot.remaining_time;
                    bestSlot = slot;
                    bestSlotIndex = index;
                }
            });

            if (bestSlot && maxAvailableTime > 0) {
                const allocatedTime = Math.min(taskDuration, maxAvailableTime);
                const isPartial = allocatedTime < taskDuration;
                const isScaled = totalTaskTime > totalAvailableTime;

                schedule.push({
                    task: {
                        ...task,
                        title: isPartial ? `${task.title} (Partial)` : task.title
                    },
                    time_block: bestSlot,
                    allocated_duration: allocatedTime,
                    completion_status: isPartial ? 'partial' : (isScaled ? 'scaled' : 'complete'),
                    scheduling_confidence: isPartial ? 0.6 : 0.8,
                    deadline_urgency: task.analysis?.deadline_urgency || 0,
                    notes: [
                        isPartial ? 
                            `Partial scheduling: ${allocatedTime} of ${taskDuration} minutes` :
                            `Scheduled in available ${allocatedTime}-minute slot`
                    ]
                });

                // Update slot
                availableSlots[bestSlotIndex].remaining_time -= allocatedTime;
                if (availableSlots[bestSlotIndex].remaining_time < 15) {
                    availableSlots[bestSlotIndex].used = true;
                }
            } else {
                // No slots available - mark as unscheduled
                schedule.push({
                    task,
                    time_block: null,
                    allocated_duration: 0,
                    completion_status: 'not_scheduled',
                    scheduling_confidence: 0.0,
                    deadline_urgency: task.analysis?.deadline_urgency || 0,
                    notes: ['No available time slots remaining - consider adding more time blocks']
                });
            }
        });

        // Strategy 3: If we still have unscheduled high-priority tasks, try to squeeze them in
        const unscheduledHighPriority = schedule.filter(item => 
            item.completion_status === 'not_scheduled' && 
            (item.task.priority === 'high' || item.deadline_urgency > 0.8)
        );

        if (unscheduledHighPriority.length > 0) {
            console.log(`Attempting to reschedule ${unscheduledHighPriority.length} high-priority tasks`);
            
            unscheduledHighPriority.forEach(item => {
                // Find any slot with even minimal time
                const smallestSlot = availableSlots.find(slot => !slot.used && slot.remaining_time >= 10);
                
                if (smallestSlot) {
                    const allocatedTime = Math.min(item.task.estimated_duration, smallestSlot.remaining_time);
                    
                    // Update the schedule item
                    item.time_block = smallestSlot;
                    item.allocated_duration = allocatedTime;
                    item.completion_status = allocatedTime < item.task.estimated_duration ? 'partial' : 'scaled';
                    item.scheduling_confidence = 0.5;
                    item.notes = [`Emergency scheduling: ${allocatedTime} minutes for high-priority task`];
                    
                    // Update slot
                    smallestSlot.remaining_time -= allocatedTime;
                    if (smallestSlot.remaining_time < 10) {
                        smallestSlot.used = true;
                    }
                }
            });
        }

        console.log(`Final schedule: ${schedule.filter(s => s.allocated_duration > 0).length}/${tasks.length} tasks scheduled`);
        return schedule;
    }

    // Keep other existing methods...
    calculateDeadlineUrgency(task) {
        if (!task.deadline) return 0.2;
        
        try {
            const deadline = new Date(task.deadline);
            const now = new Date();
            const hoursUntil = (deadline - now) / (1000 * 60 * 60);
            
            if (hoursUntil <= 6) return 1.0;
            if (hoursUntil <= 24) return 0.9;
            if (hoursUntil <= 48) return 0.7;
            if (hoursUntil <= 168) return 0.5;
            return 0.3;
        } catch {
            return 0.2;
        }
    }

    getImportanceScore(priority) {
        const priorityMap = { high: 1.0, medium: 0.6, low: 0.3 };
        return priorityMap[priority] || 0.6;
    }

    assessComplexity(title) {
        const complexWords = ['analysis', 'research', 'development', 'complex', 'detailed'];
        const simpleWords = ['update', 'check', 'review', 'simple', 'quick'];
        
        let score = 0.5;
        if (complexWords.some(word => title.toLowerCase().includes(word))) score += 0.2;
        if (simpleWords.some(word => title.toLowerCase().includes(word))) score -= 0.2;
        
        return Math.max(0.1, Math.min(1.0, score));
    }

    classifyTaskType(title) {
        const titleLower = title.toLowerCase();
        if (['code', 'develop', 'analysis'].some(word => titleLower.includes(word))) return 'deep_work';
        if (['design', 'create', 'brainstorm'].some(word => titleLower.includes(word))) return 'creative';
        if (['email', 'meeting', 'plan'].some(word => titleLower.includes(word))) return 'administrative';
        return 'routine';
    }

    calculateStressCompatibility(task, stressLevel) {
        const complexity = this.assessComplexity(task.title);
        return Math.max(0.1, 1.0 - (complexity * stressLevel / 10 * 0.7));
    }

    calculateFinalPriority(task, stressLevel) {
        const urgency = this.calculateDeadlineUrgency(task);
        const importance = this.getImportanceScore(task.priority);
        const compatibility = this.calculateStressCompatibility(task, stressLevel);
        
        return urgency * 0.5 + importance * 0.3 + compatibility * 0.2;
    }

    getStressImpact(level) {
        if (level >= 8) return "High stress significantly limits task capacity";
        if (level >= 5) return "Moderate stress affects task selection";
        return "Low stress allows for optimal productivity";
    }

    getStressActions(level) {
        if (level >= 7) return ["simplify_tasks", "add_breaks", "postpone_non_urgent"];
        if (level >= 4) return ["balance_tasks", "moderate_breaks"];
        return ["challenge_optimal", "minimal_breaks"];
    }

    generateRecommendations(schedule, stressLevel) {
        const recommendations = [];
        const unscheduled = schedule.filter(item => item.completion_status === 'not_scheduled').length;
        const partial = schedule.filter(item => item.completion_status === 'partial').length;
        const scheduled = schedule.filter(item => item.allocated_duration > 0).length;
        
        if (scheduled === schedule.length) {
            recommendations.push("All tasks successfully scheduled!");
        } else {
            if (unscheduled > 0) {
                recommendations.push(`${unscheduled} tasks need additional time slots - consider extending your schedule`);
            }
            if (partial > 0) {
                recommendations.push(`${partial} tasks are partially scheduled - plan follow-up sessions`);
            }
        }
        
        if (stressLevel >= 7) {
            recommendations.push("High stress detected - take breaks between tasks");
        }
        
        return recommendations;
    }
}
// Global functions
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

// Initialize when DOM loads
document.addEventListener('DOMContentLoaded', function() {
    stressCoachApp = new StressCoachApp();
});