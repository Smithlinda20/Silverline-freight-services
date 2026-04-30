/* ============================================================
   SILVERLINE FREIGHT — site.js
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {

  // ── Navbar scroll shadow ──────────────────────────────────
  const header = document.getElementById('siteHeader');
  if (header) {
    window.addEventListener('scroll', () => {
      header.classList.toggle('scrolled', window.scrollY > 40);
    }, { passive: true });
  }

  // ── Mobile nav toggle ─────────────────────────────────────
  const toggle = document.getElementById('navToggle');
  const nav    = document.getElementById('mainNav');
  if (toggle && nav) {
    toggle.addEventListener('click', () => {
      nav.classList.toggle('open');
      const open = nav.classList.contains('open');
      toggle.setAttribute('aria-expanded', open);
      toggle.querySelectorAll('span').forEach((s, i) => {
        if (open) {
          if (i === 0) { s.style.transform = 'rotate(45deg) translate(5px,5px)'; }
          if (i === 1) { s.style.opacity = '0'; }
          if (i === 2) { s.style.transform = 'rotate(-45deg) translate(5px,-5px)'; }
        } else {
          s.style.transform = '';
          s.style.opacity = '';
        }
      });
    });
    // Close on outside click
    document.addEventListener('click', (e) => {
      if (!header.contains(e.target)) {
        nav.classList.remove('open');
        toggle.querySelectorAll('span').forEach(s => { s.style.transform = ''; s.style.opacity = ''; });
      }
    });
  }

  // ── Reveal on scroll (IntersectionObserver) ───────────────
  const revealEls = document.querySelectorAll('.reveal');
  if (revealEls.length) {
    const revealObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          revealObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    revealEls.forEach(el => revealObserver.observe(el));
  }

  // ── Counter animation (stat-bar) ─────────────────────────
  const counters = document.querySelectorAll('.stat-bar-val[data-count]');
  if (counters.length) {
    const counterObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        const el     = entry.target;
        const target = parseInt(el.dataset.count, 10);
        const step   = Math.ceil(target / 60);
        let   current = 0;
        const timer = setInterval(() => {
          current = Math.min(current + step, target);
          el.textContent = current.toLocaleString();
          if (current >= target) clearInterval(timer);
        }, 20);
        counterObserver.unobserve(el);
      });
    }, { threshold: 0.5 });
    counters.forEach(c => counterObserver.observe(c));
  }

  // ── Progress bar animation trigger ───────────────────────
  const progressFills = document.querySelectorAll('.progress-fill');
  progressFills.forEach(fill => {
    const targetWidth = fill.style.width;
    fill.style.width = '0%';
    setTimeout(() => { fill.style.width = targetWidth; }, 300);
  });

  // ── Smooth scroll for anchor links ───────────────────────
  document.querySelectorAll('a[href^="#"]').forEach(link => {
    link.addEventListener('click', (e) => {
      const id = link.getAttribute('href').slice(1);
      const target = document.getElementById(id);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        // Close mobile nav if open
        if (nav) { nav.classList.remove('open'); }
      }
    });
  });

  // ── Active nav highlighting ───────────────────────────────
  const sections = document.querySelectorAll('section[id]');
  if (sections.length) {
    const navObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const id = entry.target.id;
          document.querySelectorAll('nav a').forEach(a => {
            a.classList.toggle('active', a.getAttribute('href').includes(`#${id}`));
          });
        }
      });
    }, { threshold: 0.3 });
    sections.forEach(s => navObserver.observe(s));
  }

  // ── Dashboard: progress slider live value ─────────────────
  document.querySelectorAll('.progress-slider').forEach(slider => {
    const targetId = slider.dataset.target;
    const valueEl  = document.getElementById(targetId);
    if (valueEl) {
      slider.addEventListener('input', () => {
        valueEl.textContent = slider.value + '%';
      });
    }
  });

  // ── Dashboard: auto-expand hold textarea on focus ─────────
  document.querySelectorAll('.hold-form textarea').forEach(ta => {
    ta.addEventListener('focus', () => {
      if (ta.style.minHeight === '' || parseInt(ta.style.minHeight) < 160) {
        ta.style.minHeight = '160px';
      }
    });
  });

  // ── Dashboard: confirm delete ─────────────────────────────
  document.querySelectorAll('form[data-confirm]').forEach(form => {
    form.addEventListener('submit', (e) => {
      if (!confirm(form.dataset.confirm)) e.preventDefault();
    });
  });

});