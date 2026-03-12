/**
 * EduGuide Parent Dashboard Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    const loginSection = document.getElementById('parent-login');
    const dashboardSection = document.getElementById('parent-dashboard');
    const loginForm = document.getElementById('parent-login-form');
    const pinInput = document.getElementById('parent-pin');
    const loginError = document.getElementById('login-error');
    const studentContainer = document.getElementById('student-reports');
    const logoutBtn = document.getElementById('btn-parent-logout');

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const pin = pinInput.value;

        try {
            const response = await fetch('/api/parent/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pin })
            });

            if (response.ok) {
                loginSection.classList.add('hidden');
                dashboardSection.classList.remove('hidden');
                loadProgressData();
            } else {
                loginError.classList.remove('hidden');
                pinInput.value = '';
            }
        } catch (err) {
            console.error("Login error:", err);
        }
    });

    logoutBtn.addEventListener('click', () => {
        window.location.reload();
    });

    async function loadProgressData() {
        try {
            const response = await fetch('/api/parent/progress');
            const data = await response.json();
            renderReports(data);
        } catch (err) {
            console.error("Error loading progress:", err);
        }
    }

    function renderReports(students) {
        studentContainer.innerHTML = '';
        const template = document.getElementById('tmpl-student-report');

        students.forEach(student => {
            const clone = template.content.cloneNode(true);

            clone.querySelector('.student-name').textContent = student.name;
            clone.querySelector('.student-level').textContent = student.level.level;
            clone.querySelector('.persona-tag').textContent = student.persona;
            clone.querySelector('.student-xp').textContent = student.total_xp;
            clone.querySelector('.student-accuracy').textContent = `${student.accuracy}%`;
            clone.querySelector('.student-time').textContent = student.total_time_minutes;

            const list = clone.querySelector('.struggle-list');
            if (student.struggle_areas.length > 0) {
                student.struggle_areas.forEach(area => {
                    const li = document.createElement('li');
                    li.innerHTML = `<strong>${area.subject}:</strong> ${area.question}... (${area.hints_used} ledtrådar)`;
                    list.appendChild(li);
                });
            } else {
                clone.querySelector('.no-struggles').classList.remove('hidden');
            }

            // Simple progress bars for subjects
            const bars = clone.querySelector('.subject-bars');
            Object.entries(student.subjects).forEach(([name, count]) => {
                const barWrapper = document.createElement('div');
                barWrapper.className = 'subject-bar-row mb-2';
                barWrapper.innerHTML = `
                    <div class="flex justify-between text-xs mb-1">
                        <span>${name}</span>
                        <span>${count} frågor</span>
                    </div>
                    <div class="progress-bar-bg" style="height: 6px;">
                        <div class="progress-bar-fill" style="width: ${Math.min(100, count * 10)}%"></div>
                    </div>
                `;
                bars.appendChild(barWrapper);
                const canvas = document.createElement('canvas');
                bars.appendChild(canvas);
                new Chart(canvas, {
                    type: 'bar',
                    data: { labels: Object.keys(student.subjects), datasets: [{ data: Object.values(student.subjects) }] },
                    options: { scales: { y: { beginAtZero: true } } }
                });
            });

            studentContainer.appendChild(clone);
        });
    }
});
