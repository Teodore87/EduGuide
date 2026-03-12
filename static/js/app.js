/**
 * EduGuide Main Application Logic
 * Handles persona selection, image upload, chat scaffolding, and XP rewards.
 */

document.addEventListener('DOMContentLoaded', () => {
    const config = window.EduGuideConfig;

    // --- UI Elements ---
    const studentForm = document.getElementById('student-entry-form');
    const inputZone = document.getElementById('input-zone');
    const chatZone = document.getElementById('chat-zone');
    const chatMessages = document.getElementById('chat-messages');
    const answerForm = document.getElementById('answer-form');
    const answerInput = document.getElementById('student-answer');
    const submitBtn = document.getElementById('btn-submit-answer');
    const hintBtn = document.getElementById('btn-get-hint');
    const imageInput = document.getElementById('image-upload');
    const manualTextInput = document.getElementById('manual-text');
    const submitTextBtn = document.getElementById('btn-submit-text');
    const loadingSpinner = document.getElementById('upload-loading');

    // --- State ---
    let state = {
        studentId: config.currentStudentId,
        currentQuestionId: null,
        hintCount: 0,
        attempts: 0
    };

    // ============================================================
    // STUDENT LIST (Landing Page)
    // ============================================================

    const loadStudentList = async () => {
        const listSection = document.getElementById('existing-students-section');
        const listContainer = document.getElementById('student-list');
        const template = document.getElementById('tmpl-student-item');

        if (!listSection || !listContainer) return;

        try {
            const response = await fetch(config.endpoints.listStudents);
            const students = await response.json();

            if (students.length > 0) {
                listSection.classList.remove('hidden');
                listContainer.innerHTML = '';

                students.forEach(student => {
                    const clone = template.content.cloneNode(true);
                    const btn = clone.querySelector('.student-item-btn');

                    btn.dataset.id = student.id;
                    clone.querySelector('.student-item-icon').textContent = getPersonaEmoji(student.persona);
                    clone.querySelector('.student-item-name').textContent = student.name;
                    clone.querySelector('.student-item-meta').textContent = `Nivå ${calculateLevel(student.total_xp)} • ${student.total_xp} XP`;

                    btn.addEventListener('click', () => selectExistingStudent(student.id));
                    listContainer.appendChild(clone);
                });
            }
        } catch (err) {
            console.error("Error loading student list:", err);
        }
    };

    const selectExistingStudent = async (studentId) => {
        try {
            const response = await fetch(config.endpoints.selectStudent, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ student_id: studentId })
            });

            const result = await response.json();
            if (result.success) {
                window.location.href = '/study';
            }
        } catch (err) {
            console.error("Error selecting student:", err);
        }
    };

    const getPersonaEmoji = (persona) => {
        const emojis = {
            'explorer': '🔭',
            'gamer': '🎮',
            'coach': '📣',
            'zen': '🧘‍♂️'
        };
        return emojis[persona] || '👤';
    };

    const calculateLevel = (xp) => {
        return Math.floor(xp / 100) + 1;
    };

    // Auto-load student list if on landing page
    if (document.body.classList.contains('page-index')) {
        loadStudentList();
    }

    // ============================================================
    // INITIALIZATION & PERSONA SELECTION
    // ============================================================

    if (studentForm) {
        studentForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = document.getElementById('student-name').value;
            const persona = document.querySelector('input[name="persona"]:checked').value;

            try {
                const response = await fetch(config.endpoints.createStudent, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, persona })
                });

                const result = await response.json();
                if (result.success) {
                    window.location.href = '/study';
                }
            } catch (err) {
                console.error("Error creating student:", err);
            }
        });
    }

    // ============================================================
    // HOMEWORK INPUT (Image / Text)
    // ============================================================

    const startStudySession = (data) => {
        state.currentQuestionId = data.question_id;
        state.hintCount = 0;
        state.attempts = 0;

        // Switch views
        inputZone.classList.add('hidden');
        chatZone.classList.remove('hidden');

        // Clear chat and set subject
        chatMessages.innerHTML = '';
        document.getElementById('chat-subject').textContent = data.subject || 'LÄXA';

        // Add original question to chat
        addMessage('student', data.text);

        // Trigger reformulation
        getReformulations();
    };

    // Handle Image Upload
    if (imageInput) {
        imageInput.addEventListener('change', async () => {
            if (!imageInput.files[0]) return;

            loadingSpinner.classList.remove('hidden');
            const formData = new FormData();
            formData.append('image', imageInput.files[0]);

            try {
                const response = await fetch(config.endpoints.uploadImage, {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();

                loadingSpinner.classList.add('hidden');
                if (result.success) {
                    startStudySession(result);
                } else {
                    alert(result.error || "Kunde inte läsa bilden.");
                }
            } catch (err) {
                loadingSpinner.classList.add('hidden');
                console.error("Upload error:", err);
            }
        });
    }

    // Handle Manual Text
    if (submitTextBtn) {
        submitTextBtn.addEventListener('click', async () => {
            const text = manualTextInput.value.trim();
            if (!text) return;

            try {
                const response = await fetch(config.endpoints.submitText, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text })
                });
                const result = await response.json();
                if (result.success) {
                    startStudySession(result);
                }
            } catch (err) {
                console.error("Text submit error:", err);
            }
        });
    }

    // ============================================================
    // SCAFFOLDING LOGIC
    // ============================================================

    const getReformulations = async () => {
        addMessage('bot', "Jag läsar din fråga... Här är tre sätt att se på den. Vilken hjälper dig mest?");

        try {
            const response = await fetch(config.endpoints.reformulate, { method: 'POST' });
            const result = await response.json();

            if (result.success) {
                renderReformulationCards(result);
            }
        } catch (err) {
            console.error("Reformulation error:", err);
        }
    };

    const renderReformulationCards = (data) => {
        const template = document.getElementById('tmpl-reformulations');
        const clone = template.content.cloneNode(true);

        clone.querySelector('.simple .rcard-text').textContent = data.simple;
        clone.querySelector('.context .rcard-text').textContent = data.context;
        clone.querySelector('.steps .rcard-text').textContent = data.steps;

        chatMessages.appendChild(clone);
        scrollToBottom();

        // Enable answer inputs
        answerInput.disabled = false;
        submitBtn.disabled = false;
        hintBtn.disabled = false;
    };

    // ============================================================
    // ANSWER SUBMISSION & FEEDBACK
    // ============================================================

    if (answerForm) {
        answerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const answer = answerInput.value.trim();
            if (!answer) return;

            addMessage('student', answer);
            answerInput.value = '';

            try {
                const response = await fetch(config.endpoints.submitAnswer, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ answer })
                });
                const result = await response.json();

                addMessage('bot', result.feedback);

                if (result.is_correct) {
                    handleSuccess(result);
                } else if (result.suggest_break) {
                    document.getElementById('break-overlay').classList.remove('hidden');
                }
            } catch (err) {
                console.error("Submit error:", err);
            }
        });
    }

    hintBtn?.addEventListener('click', async () => {
        try {
            addMessage('bot', "Ett ögonblick, jag plockar fram en ledtråd...");
            const response = await fetch(config.endpoints.hint, { method: 'POST' });
            const result = await response.json();
            if (result.success) {
                addMessage('bot', result.hint);
            }
        } catch (err) {
            console.error("Hint error:", err);
        }
    });

    const handleSuccess = (result) => {
        // Update XP in header
        const xpElement = document.getElementById('header-xp');
        if (xpElement) xpElement.textContent = `${result.total_xp} XP`;

        // Show celebration
        addMessage('bot', `🎉 +${result.xp_earned} XP! ${result.xp_message}`);
        // Test-funktion
        confetti({
            particleCount: 100,
            spread: 70,
            origin: { y: 0.6 }
        });

        // Update progress bar if sidebar exists
        const progressFill = document.getElementById('xp-progress');
        if (progressFill && result.level) {
            progressFill.style.width = `${result.level.progress}%`;
            document.getElementById('level-badge').textContent = `Nivå ${result.level.level}`;
            document.getElementById('level-title').textContent = result.level.title;
        }

        // Disable further input for this question
        answerInput.disabled = true;
        submitBtn.disabled = true;
        hintBtn.disabled = true;
    };

    // ============================================================
    // UI HELPERS
    // ============================================================

    const addMessage = (sender, text) => {
        const template = document.getElementById('tmpl-message');
        const clone = template.content.cloneNode(true);

        const wrapper = clone.querySelector('.message-wrapper');
        wrapper.classList.add(sender === 'student' ? 'justify-end' : 'justify-start');

        const message = clone.querySelector('.message');
        message.classList.add(sender === 'student' ? 'student-msg' : 'bot-msg');

        clone.querySelector('.message-text').textContent = text;

        // TTS linkage
        const ttsBtn = clone.querySelector('.btn-tts');
        ttsBtn.onclick = () => window.EduGuideTTS?.speak(text);

        chatMessages.appendChild(clone);
        scrollToBottom();
    };

    const scrollToBottom = () => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    // Accessibility Controls
    document.getElementById('toggle-contrast')?.addEventListener('click', () => {
        const theme = document.documentElement.getAttribute('data-theme');
        document.documentElement.setAttribute('data-theme', theme === 'dark' ? 'light' : 'dark');
    });

    let fontSize = 18;
    document.getElementById('font-increase')?.addEventListener('click', () => {
        fontSize += 2;
        document.body.style.fontSize = `${fontSize}px`;
    });
    document.getElementById('font-decrease')?.addEventListener('click', () => {
        if (fontSize > 12) {
            fontSize -= 2;
            document.body.style.fontSize = `${fontSize}px`;
        }
    });
});
