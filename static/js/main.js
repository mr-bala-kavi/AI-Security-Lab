/**
 * AI Security Lab - Main JavaScript
 * Handles global functionality: dark mode, security levels, toasts, etc.
 */

// ============================================
// Dark Mode Toggle
// ============================================

function initDarkMode() {
    const toggle = document.getElementById('dark-mode-toggle');
    const html = document.documentElement;

    // Check for saved preference or system preference
    const savedTheme = localStorage.getItem('theme');
    const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (savedTheme === 'dark' || (!savedTheme && systemDark)) {
        html.classList.add('dark');
    }

    if (toggle) {
        toggle.addEventListener('click', () => {
            html.classList.toggle('dark');
            localStorage.setItem('theme', html.classList.contains('dark') ? 'dark' : 'light');
        });
    }
}

// ============================================
// Security Level Selector
// ============================================

function initSecurityLevelSelector() {
    const selector = document.getElementById('security-level-selector');

    if (selector) {
        selector.addEventListener('change', async (e) => {
            const level = e.target.value;

            try {
                const response = await fetch('/api/security-level', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ level })
                });

                const data = await response.json();

                if (data.success) {
                    showToast(`Security level set to ${level}`, 'success');
                    updateSecurityLevelUI(level);
                    // Reload page to apply new level
                    setTimeout(() => window.location.reload(), 500);
                } else {
                    showToast(data.error || 'Failed to change security level', 'error');
                }
            } catch (error) {
                showToast('Error changing security level', 'error');
                console.error(error);
            }
        });
    }
}

function updateSecurityLevelUI(level) {
    const selector = document.getElementById('security-level-selector');
    if (!selector) return;

    // Remove existing color classes
    selector.classList.remove(
        'bg-green-100', 'border-green-500', 'text-green-700',
        'bg-yellow-100', 'border-yellow-500', 'text-yellow-700',
        'bg-red-100', 'border-red-500', 'text-red-700',
        'dark:bg-green-900', 'dark:text-green-300',
        'dark:bg-yellow-900', 'dark:text-yellow-300',
        'dark:bg-red-900', 'dark:text-red-300'
    );

    // Add new color classes based on level
    const colors = {
        'LOW': ['bg-green-100', 'border-green-500', 'text-green-700', 'dark:bg-green-900', 'dark:text-green-300'],
        'MEDIUM': ['bg-yellow-100', 'border-yellow-500', 'text-yellow-700', 'dark:bg-yellow-900', 'dark:text-yellow-300'],
        'HIGH': ['bg-red-100', 'border-red-500', 'text-red-700', 'dark:bg-red-900', 'dark:text-red-300']
    };

    colors[level].forEach(cls => selector.classList.add(cls));
}

// ============================================
// Reset Button
// ============================================

function initResetButton() {
    const resetBtn = document.getElementById('reset-button');

    if (resetBtn) {
        resetBtn.addEventListener('click', async () => {
            if (!confirm('Are you sure you want to reset all progress? This cannot be undone.')) {
                return;
            }

            try {
                const response = await fetch('/api/reset', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ type: 'all' })
                });

                const data = await response.json();

                if (data.success) {
                    showToast('Progress reset successfully', 'success');
                    setTimeout(() => window.location.reload(), 500);
                } else {
                    showToast(data.error || 'Failed to reset', 'error');
                }
            } catch (error) {
                showToast('Error resetting progress', 'error');
                console.error(error);
            }
        });
    }
}

// ============================================
// Progress Bar Updates
// ============================================

async function updateProgress() {
    try {
        const response = await fetch('/api/progress');
        const data = await response.json();

        const progressBar = document.getElementById('progress-bar');
        const progressText = document.getElementById('progress-text');

        if (progressBar && data.summary) {
            progressBar.style.width = `${data.summary.percentage}%`;
        }

        if (progressText && data.summary) {
            progressText.textContent = `${data.summary.completed} of ${data.summary.total} modules completed`;
        }
    } catch (error) {
        console.error('Error fetching progress:', error);
    }
}

// ============================================
// Toast Notifications
// ============================================

function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast px-4 py-3 rounded-lg shadow-lg flex items-center space-x-3 max-w-sm
                       ${type === 'success' ? 'bg-green-500 text-white' :
                         type === 'error' ? 'bg-red-500 text-white' :
                         type === 'warning' ? 'bg-yellow-500 text-white' :
                         'bg-blue-500 text-white'}`;

    // Icon based on type
    const icons = {
        success: `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                  </svg>`,
        error: `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>`,
        warning: `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                  </svg>`,
        info: `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                 <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
               </svg>`
    };

    toast.innerHTML = `
        ${icons[type] || icons.info}
        <span>${message}</span>
    `;

    container.appendChild(toast);

    // Remove after duration
    setTimeout(() => {
        toast.classList.add('toast-exit');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ============================================
// Loading Overlay
// ============================================

function showLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.remove('hidden');
        overlay.classList.add('flex');
    }
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.add('hidden');
        overlay.classList.remove('flex');
    }
}

// ============================================
// Hint System
// ============================================

async function showHint(moduleName, hintNumber = 1) {
    try {
        const response = await fetch(`/api/hints/${moduleName}?hint=${hintNumber}`);
        const data = await response.json();

        if (data.success) {
            const hintContainer = document.getElementById('hint-container');
            if (hintContainer) {
                hintContainer.innerHTML = `
                    <div class="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                        <h4 class="font-medium text-yellow-800 dark:text-yellow-200 mb-2">Hint ${data.hint_number}</h4>
                        <p class="text-yellow-700 dark:text-yellow-300">${data.hint_text}</p>
                        ${data.has_more ? `
                            <button onclick="showHint('${moduleName}', ${hintNumber + 1})"
                                    class="mt-3 text-sm text-yellow-600 dark:text-yellow-400 hover:underline">
                                Show next hint
                            </button>
                        ` : ''}
                    </div>
                `;
                hintContainer.classList.remove('hidden');
            }
            showToast(`Hint ${hintNumber} revealed`, 'info');
        } else {
            showToast(data.error || 'Failed to get hint', 'error');
        }
    } catch (error) {
        showToast('Error fetching hint', 'error');
        console.error(error);
    }
}

// ============================================
// Chat Interface Helpers
// ============================================

function addChatMessage(container, role, content, isExploit = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message flex ${role === 'user' ? 'justify-end' : 'justify-start'} mb-4`;

    const bubbleClass = role === 'user'
        ? 'bg-blue-500 text-white rounded-br-none'
        : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white rounded-bl-none';

    const exploitBorder = isExploit ? 'border-2 border-red-500' : '';

    messageDiv.innerHTML = `
        <div class="max-w-[80%] ${bubbleClass} ${exploitBorder} rounded-2xl px-4 py-2">
            <p class="text-sm whitespace-pre-wrap">${escapeHtml(content)}</p>
        </div>
    `;

    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================
// Utility Functions
// ============================================

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard', 'success');
    }).catch(() => {
        showToast('Failed to copy', 'error');
    });
}

function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

function formatDuration(ms) {
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
}

// ============================================
// Initialize on DOM Ready
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    initDarkMode();
    initSecurityLevelSelector();
    initResetButton();
    updateProgress();

    // Initialize syntax highlighting
    if (typeof hljs !== 'undefined') {
        hljs.highlightAll();
    }
});

// Export functions for use in module-specific scripts
window.AISecurityLab = {
    showToast,
    showLoading,
    hideLoading,
    showHint,
    addChatMessage,
    copyToClipboard,
    formatBytes,
    formatDuration,
    escapeHtml
};
