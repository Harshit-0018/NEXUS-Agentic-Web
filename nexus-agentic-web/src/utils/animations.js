/**
 * NEXUS — Animations
 * Handles scroll-triggered animations, counter animations,
 * and intersection observer setup.
 */

// ─── Counter Animation ───────────────────────────────────────────────────────
function animateCounter(el, target, duration = 2000) {
  const start = 0;
  const step = (timestamp) => {
    if (!el._startTime) el._startTime = timestamp;
    const progress = Math.min((timestamp - el._startTime) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
    el.textContent = Math.floor(eased * target);
    if (progress < 1) requestAnimationFrame(step);
    else el.textContent = target;
  };
  requestAnimationFrame(step);
}

// ─── Intersection Observer for scroll-triggered effects ──────────────────────
const observerOptions = {
  root: null,
  rootMargin: '0px 0px -60px 0px',
  threshold: 0.15
};

const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const el = entry.target;

      // Counter animation
      if (el.hasAttribute('data-count')) {
        const target = parseInt(el.getAttribute('data-count'));
        animateCounter(el, target);
        observer.unobserve(el);
        return;
      }

      // Reveal animation
      el.classList.add('revealed');
      observer.unobserve(el);
    }
  });
}, observerOptions);

// ─── Initialize on DOM ready ─────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {

  // Observe counters
  document.querySelectorAll('[data-count]').forEach(el => {
    observer.observe(el);
  });

  // Observe sections and cards for reveal
  document.querySelectorAll('.feature-card, .usecase-card, .tech-card, .arch-layer').forEach((el, i) => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = `opacity 0.5s ease ${i * 0.05}s, transform 0.5s ease ${i * 0.05}s`;
    el.classList.add('will-reveal');
    observer.observe(el);
  });

  // Override observer for reveal elements
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

  document.querySelectorAll('.will-reveal').forEach(el => {
    revealObserver.observe(el);
  });

  // Active nav link on scroll
  const navLinks = document.querySelectorAll('.nav-link');
  const sections = document.querySelectorAll('section[id]');

  const navObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        navLinks.forEach(link => link.classList.remove('active'));
        const active = document.querySelector(`.nav-link[href="#${entry.target.id}"]`);
        if (active) active.classList.add('active');
      }
    });
  }, { threshold: 0.4 });

  sections.forEach(s => navObserver.observe(s));

  // Add active nav style
  const style = document.createElement('style');
  style.textContent = `.nav-link.active { color: var(--accent-green) !important; }`;
  document.head.appendChild(style);
});
