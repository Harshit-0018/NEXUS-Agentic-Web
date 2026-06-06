/**
 * NEXUS — Main UI Logic
 * Handles button interactions, form handling, and utility functions.
 */

// ─── Set task text from preset buttons ──────────────────────────────────────
function setTask(text) {
  const textarea = document.getElementById('task-input');
  if (textarea) {
    textarea.value = text;
    textarea.focus();
    // Scroll to demo section smoothly
    document.getElementById('demo').scrollIntoView({ behavior: 'smooth' });
  }
}

// ─── Run agent ───────────────────────────────────────────────────────────────
function runAgent() {
  const textarea = document.getElementById('task-input');
  const task = textarea?.value?.trim();

  if (!task) {
    textarea?.classList.add('shake');
    textarea?.focus();
    setTimeout(() => textarea?.classList.remove('shake'), 600);
    return;
  }

  const maxSteps = parseInt(document.getElementById('max-steps')?.value || '20');
  const runBtn = document.getElementById('run-btn');
  const stopBtn = document.getElementById('stop-btn');
  const runBtnText = document.getElementById('run-btn-text');

  if (runBtn) runBtn.disabled = true;
  if (stopBtn) stopBtn.style.display = 'block';
  if (runBtnText) runBtnText.textContent = '⟳ Agent Running...';

  AgentSimulator.run(task, maxSteps).then(() => {
    if (runBtn) runBtn.disabled = false;
    if (stopBtn) stopBtn.style.display = 'none';
    if (runBtnText) runBtnText.textContent = '⬡ Launch Agent';
  });
}

// ─── Stop agent ──────────────────────────────────────────────────────────────
function stopAgent() {
  AgentSimulator.stop();
  const runBtn = document.getElementById('run-btn');
  const stopBtn = document.getElementById('stop-btn');
  const runBtnText = document.getElementById('run-btn-text');

  if (runBtn) runBtn.disabled = false;
  if (stopBtn) stopBtn.style.display = 'none';
  if (runBtnText) runBtnText.textContent = '⬡ Launch Agent';
}

// ─── Copy result ──────────────────────────────────────────────────────────────
function copyResult() {
  const body = document.getElementById('result-body');
  if (!body) return;
  const text = body.innerText;
  navigator.clipboard.writeText(text).then(() => {
    const btn = document.querySelector('.copy-btn');
    if (btn) {
      const orig = btn.textContent;
      btn.textContent = '✓ Copied!';
      btn.style.color = 'var(--accent-green)';
      btn.style.borderColor = 'var(--accent-green)';
      setTimeout(() => {
        btn.textContent = orig;
        btn.style.color = '';
        btn.style.borderColor = '';
      }, 2000);
    }
  });
}

// ─── Copy code blocks ─────────────────────────────────────────────────────────
function copyCode(btn, codeId) {
  const code = document.getElementById(codeId);
  if (!code) return;
  navigator.clipboard.writeText(code.innerText).then(() => {
    const orig = btn.textContent;
    btn.textContent = '✓ Copied!';
    setTimeout(() => { btn.textContent = orig; }, 2000);
  });
}

// ─── Scroll to demo ───────────────────────────────────────────────────────────
function scrollToDemo() {
  document.getElementById('demo')?.scrollIntoView({ behavior: 'smooth' });
}

// ─── Add shake animation ──────────────────────────────────────────────────────
const shakeStyle = document.createElement('style');
shakeStyle.textContent = `
  @keyframes shake {
    0%, 100% { transform: translateX(0); }
    20% { transform: translateX(-6px); }
    40% { transform: translateX(6px); }
    60% { transform: translateX(-4px); }
    80% { transform: translateX(4px); }
  }
  .shake { animation: shake 0.5s ease; border-color: #f87171 !important; }

  /* Typing effect for textarea placeholder */
  .task-textarea:focus { border-color: rgba(0,255,178,0.3) !important; outline: none; }

  /* Button ripple */
  .btn-ripple {
    position: absolute; top: 50%; left: 50%;
    width: 0; height: 0;
    border-radius: 50%;
    background: rgba(255,255,255,0.2);
    transform: translate(-50%, -50%);
    transition: width 0.4s, height 0.4s, opacity 0.4s;
    pointer-events: none;
  }
  .run-btn:active .btn-ripple {
    width: 300px; height: 300px; opacity: 0;
  }
`;
document.head.appendChild(shakeStyle);

// ─── Keyboard shortcut: Ctrl/Cmd + Enter to run ──────────────────────────────
document.addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    const demo = document.getElementById('demo');
    const rect = demo?.getBoundingClientRect();
    if (rect && rect.top < window.innerHeight && rect.bottom > 0) {
      runAgent();
    }
  }
});

// ─── Smooth scroll for nav links ─────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('a[href^="#"]').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const target = document.querySelector(link.getAttribute('href'));
      if (target) target.scrollIntoView({ behavior: 'smooth' });
    });
  });

  // Auto-fill textarea hint
  const textarea = document.getElementById('task-input');
  if (textarea && !textarea.value) {
    // Subtle typewriter effect for default value
    const examples = [
      'Find the top 5 AI startups funded in 2024...',
      'Compare iPhone 16 Pro prices across Amazon and Flipkart...',
      'Search for flights from Delhi to New York next month...',
    ];
    let idx = 0;
    // Just set a hint, not a value
  }
});

console.log('%c NEXUS Agent Platform ', 'background: #00FFB2; color: #060810; font-weight: bold; font-size: 16px; padding: 8px 16px;');
console.log('%c Microsoft Hackathon 2025 — Agentic Web Theme', 'color: #7A8BA0; font-size: 12px;');
