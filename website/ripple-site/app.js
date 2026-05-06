/* ============================================================================
 * Ripple · 产品展示网站 · 交互与动效
 * 功能：主题切换 / IntersectionObserver reveal /
 *        Hero 打字机 / CountUp / 预览窗口状态循环 / 导航滚动激活
 * ========================================================================== */
(function () {
  'use strict';

  /* ---------- 工具 ---------- */
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
  const raf = requestAnimationFrame;

  /* ====================================================
   * 1. 主题切换
   * ================================================== */
  function initTheme() {
    const html = document.documentElement;
    const btn  = $('#themeToggle');
    if (!btn) return;

    // 读取偏好
    const saved = localStorage.getItem('ripple-theme');
    if (saved === 'light') {
      html.setAttribute('data-theme', 'light');
    } else if (!saved) {
      // 默认跟随系统，但保持暗色为主
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      if (!prefersDark) html.setAttribute('data-theme', 'light');
    }

    const syncIcon = () => {
      const isLight = html.getAttribute('data-theme') === 'light';
      btn.textContent = isLight ? '☾' : '☀';
    };
    syncIcon();

    btn.addEventListener('click', () => {
      const isLight = html.getAttribute('data-theme') === 'light';
      if (isLight) {
        html.removeAttribute('data-theme');
        localStorage.setItem('ripple-theme', 'dark');
      } else {
        html.setAttribute('data-theme', 'light');
        localStorage.setItem('ripple-theme', 'light');
      }
      syncIcon();
    });
  }

  /* ====================================================
   * 2. IntersectionObserver 滚动 reveal
   * ================================================== */
  function initReveal() {
    const els = $$('.reveal');
    if (!els.length) return;

    const io = new IntersectionObserver(
      entries => {
        entries.forEach(e => {
          if (e.isIntersecting) {
            // 读取 CSS 变量 --delay，叠加阶梯延迟
            const delay = parseFloat(
              getComputedStyle(e.target).getPropertyValue('--delay') || '0'
            );
            setTimeout(() => {
              e.target.classList.add('visible');
            }, isNaN(delay) ? 0 : delay);
            io.unobserve(e.target);
          }
        });
      },
      { threshold: 0.07, rootMargin: '0px 0px -36px 0px' }
    );

    els.forEach(el => io.observe(el));
  }

  /* ====================================================
   * 3. CountUp 数字动画（进入视口时触发）
   * ================================================== */
  function countUp(el, target, duration = 1200) {
    const start = performance.now();
    const startVal = 0;

    function step(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.round(startVal + (target - startVal) * eased);
      if (progress < 1) raf(step);
    }
    raf(step);
  }

  function initCountUp() {
    // Hero stats (data-count attribute)
    const heroStats = $$('[data-count]');
    heroStats.forEach(el => {
      const target = parseInt(el.dataset.count, 10);
      const io = new IntersectionObserver(entries => {
        entries.forEach(e => {
          if (e.isIntersecting) {
            countUp(el, target);
            io.unobserve(el);
          }
        });
      }, { threshold: 0.3 });
      io.observe(el);
    });

    // Problem section .ps-n (data-count)
    const problemNums = $$('.ps-n[data-count]');
    problemNums.forEach(el => {
      const target = parseInt(el.dataset.count, 10);
      const io = new IntersectionObserver(entries => {
        entries.forEach(e => {
          if (e.isIntersecting) {
            countUp(el, target, 1400);
            io.unobserve(el);
          }
        });
      }, { threshold: 0.3 });
      io.observe(el);
    });
  }

  /* ====================================================
   * 4. Hero 打字机效果（Demo CTA 区块）
   * ================================================== */
  const TYPEWRITER_TEXTS = [
    '分析"大学生穿搭"赛道，找出今年最有潜力的细分方向',
    '帮我评估这个选题的爆款潜力，给出 CES 评分和专家意见',
    '写一篇面向大学生的护肤科普文案，同步生成微信四端策略',
    '分析@美妆博主的内容风格，帮我蒸馏出可复用的写作套路',
    '探索"户外运动"赛道，找出适合大学生 KOC 的切入角度',
  ];

  let twIndex = 0;
  let twCharIndex = 0;
  let twIsDeleting = false;
  let twTimer = null;

  function initTypewriter() {
    const el = $('#twText');
    if (!el) return;

    function type() {
      const current = TYPEWRITER_TEXTS[twIndex];

      if (!twIsDeleting) {
        // Typing
        twCharIndex++;
        el.textContent = current.slice(0, twCharIndex);

        if (twCharIndex === current.length) {
          // Pause at end
          twTimer = setTimeout(() => {
            twIsDeleting = true;
            type();
          }, 2800);
          return;
        }
        twTimer = setTimeout(type, 45 + Math.random() * 25);
      } else {
        // Deleting
        twCharIndex--;
        el.textContent = current.slice(0, twCharIndex);

        if (twCharIndex === 0) {
          twIsDeleting = false;
          twIndex = (twIndex + 1) % TYPEWRITER_TEXTS.length;
          twTimer = setTimeout(type, 400);
          return;
        }
        twTimer = setTimeout(type, 20);
      }
    }

    // Start after short delay
    setTimeout(type, 1200);
  }

  /* ====================================================
   * 5. 预览窗口状态循环（status + typing label）
   * ================================================== */
  const PREVIEW_STATES = [
    { status: '多引擎检索中...', typing: '正在构建知识图谱...' },
    { status: '图谱构建完成 ✓', typing: '正在启动 AI 圆桌...' },
    { status: 'AI 圆桌进行中...', typing: '正在生成爆款评分...' },
    { status: 'CES 评分完成 ✓', typing: '正在生成微信四端策略...' },
    { status: '策略生成完成 ✓', typing: '正在汇总分析报告...' },
    { status: '分析完成 🎉', typing: '准备好了，一键追问 →' },
  ];

  function initPreviewCycle() {
    const statusEl   = $('#previewStatus');
    const typingEl   = $('#typingLabel');
    if (!statusEl || !typingEl) return;

    let idx = 0;
    setInterval(() => {
      idx = (idx + 1) % PREVIEW_STATES.length;
      const state = PREVIEW_STATES[idx];

      // Fade out → update → fade in
      statusEl.style.opacity = '0';
      typingEl.style.opacity  = '0';
      setTimeout(() => {
        statusEl.textContent = state.status;
        typingEl.textContent  = state.typing;
        statusEl.style.opacity = '1';
        typingEl.style.opacity  = '1';
      }, 300);
    }, 2600);

    // Add transition style
    if (statusEl) statusEl.style.transition = 'opacity .3s';
    if (typingEl) typingEl.style.transition  = 'opacity .3s';
  }

  /* ====================================================
   * 6. 导航激活（滚动时高亮当前 section）
   * ================================================== */
  function initNavActive() {
    const sections = $$('section[id]');
    const navLinks = $$('nav .links a[href^="#"]');
    if (!sections.length || !navLinks.length) return;

    const io = new IntersectionObserver(
      entries => {
        entries.forEach(e => {
          if (e.isIntersecting) {
            navLinks.forEach(a => {
              a.classList.remove('nav-active');
              if (a.getAttribute('href') === '#' + e.target.id) {
                a.classList.add('nav-active');
              }
            });
          }
        });
      },
      { rootMargin: '-40% 0px -55% 0px', threshold: 0 }
    );

    sections.forEach(s => io.observe(s));

    // Add nav-active style dynamically
    const style = document.createElement('style');
    style.textContent = 'nav .links a.nav-active { color: var(--fg) !important; background: var(--bg2); }';
    document.head.appendChild(style);
  }

  /* ====================================================
   * 7. 平滑滚动 polyfill（拦截 #anchor 点击）
   * ================================================== */
  function initSmoothScroll() {
    $$('a[href^="#"]').forEach(a => {
      a.addEventListener('click', e => {
        const id = a.getAttribute('href').slice(1);
        if (!id) return;
        const target = document.getElementById(id);
        if (!target) return;
        e.preventDefault();
        const navH = 62;
        const top  = target.getBoundingClientRect().top + window.scrollY - navH;
        window.scrollTo({ top, behavior: 'smooth' });
      });
    });
  }

  /* ====================================================
   * 8. 知识图谱 SVG 节点微动画（hover 后 pulse）
   * ================================================== */
  function initGraphAnimation() {
    const nodes = $$('.preview-graph-svg .g-node');
    nodes.forEach((node, i) => {
      // Stagger subtle scale animation
      node.style.animation = `nodeFloat ${3 + i * 0.4}s ease-in-out ${i * 0.3}s infinite alternate`;
    });

    // Add keyframe if not already
    if (!document.getElementById('graphKeyframes')) {
      const style = document.createElement('style');
      style.id = 'graphKeyframes';
      style.textContent = `
        @keyframes nodeFloat {
          from { transform: scale(1); opacity: .85; }
          to   { transform: scale(1.08); opacity: 1; }
        }
        .preview-graph-svg .center-node {
          animation: centerNodePulse 2.4s ease-in-out infinite !important;
        }
        @keyframes centerNodePulse {
          0%, 100% { filter: drop-shadow(0 0 6px rgba(139,92,246,.6)); }
          50% { filter: drop-shadow(0 0 14px rgba(139,92,246,.9)); }
        }
      `;
      document.head.appendChild(style);
    }
  }

  /* ====================================================
   * 8b. 浮动徽章 appear → float 动画切换
   * ================================================== */
  function initFloatingBadges() {
    const b1 = $('.badge-1');
    const b2 = $('.badge-2');
    if (b1) {
      // After appear animation finishes (0.9s delay + 1.2s duration = 2.1s), switch to float
      setTimeout(() => { b1.classList.add('animate-float'); }, 2100);
    }
    if (b2) {
      setTimeout(() => { b2.classList.add('animate-float'); }, 2600);
    }
  }

  /* ====================================================
   * 9. Hero 统计数字（∞ 节点特殊处理）
   * ================================================== */
  function initHeroStatInfinity() {
    // The ∞ stat doesn't use data-count, keep as-is but add a gentle pulse
    const infEl = $('[data-suffix="+"]');
    if (infEl) {
      // Animate between realistic numbers
      const vals = ['120+', '340+', '200+', '∞'];
      let vi = 0;
      setInterval(() => {
        vi = (vi + 1) % vals.length;
        infEl.style.opacity = '0';
        setTimeout(() => {
          infEl.textContent = vals[vi];
          infEl.style.opacity = '1';
        }, 300);
      }, 2200);
      infEl.style.transition = 'opacity .3s';
    }
  }

  /* ====================================================
   * 10. 步骤连接线入场动画
   * ================================================== */
  function initStepConnectors() {
    const connectors = $$('.step-connector');
    connectors.forEach((conn, i) => {
      // Already handled by reveal class + CSS opacity
      // Add a slight delay for the arrow appearance
      conn.style.transitionDelay = `${(i + 1) * 120}ms`;
    });
  }

  /* ====================================================
   * 11. Feature 卡片悬停增强（动态渐变描边颜色）
   * ================================================== */
  function initFeatureHover() {
    $$('.feat-card').forEach(card => {
      card.addEventListener('mouseenter', () => {
        card.style.setProperty('--hover-glow', '1');
      });
      card.addEventListener('mouseleave', () => {
        card.style.setProperty('--hover-glow', '0');
      });
    });
  }

  /* ====================================================
   * 12. 导航栏滚动后加深背景
   * ================================================== */
  function initNavScroll() {
    const nav = $('nav.topbar');
    if (!nav) return;

    let lastY = 0;
    window.addEventListener('scroll', () => {
      const y = window.scrollY;
      if (y > 20) {
        nav.style.boxShadow = '0 1px 20px rgba(0,0,0,.4)';
      } else {
        nav.style.boxShadow = 'none';
      }
      lastY = y;
    }, { passive: true });
  }

  /* ====================================================
   * 13. Demo 报告按钮 tooltip
   * ================================================== */
  function initReportBtn() {
    const btn = $('#downloadBtn');
    if (!btn) return;
    btn.addEventListener('click', e => {
      e.preventDefault();
      // 已在 HTML 中 disabled，但增加视觉反馈
      btn.style.transform = 'scale(.98)';
      setTimeout(() => { btn.style.transform = ''; }, 200);
    });
  }

  /* ====================================================
   * 14. 预览窗口中的打字加载消息轮换
   * ================================================== */
  function initPreviewMessages() {
    // Keep typing indicator text cycling even after graph loads visually
    const labels = [
      '正在生成微信四端策略...',
      '正在撰写 30 天行动路径...',
      '正在整理可引用来源...',
      '正在生成爆款预测曲线...',
      '正在计算共识度...',
    ];
    const labelEl = $('#typingLabel');
    if (!labelEl) return;

    let li = 0;
    setInterval(() => {
      li = (li + 1) % labels.length;
      labelEl.style.opacity = '0';
      setTimeout(() => {
        labelEl.textContent = labels[li];
        labelEl.style.opacity = '1';
      }, 250);
    }, 3000);
    labelEl.style.transition = 'opacity .25s';
  }

  /* ====================================================
   * Init all
   * ================================================== */
  function init() {
    initTheme();
    initReveal();
    initCountUp();
    initTypewriter();
    initPreviewCycle();
    initNavActive();
    initSmoothScroll();
    initGraphAnimation();
    initFloatingBadges();
    initHeroStatInfinity();
    initStepConnectors();
    initFeatureHover();
    initNavScroll();
    initReportBtn();
    initPreviewMessages();

    // Hero copy 入场动画（不走 reveal，直接 CSS 触发）
    const heroTag  = $('.hero-tag');
    const heroH1   = $('.hero-copy h1');
    const heroSub  = $('.hero-sub');
    const ctaRow   = $('.cta-row');
    const heroStat = $('.hero-stats');

    [heroTag, heroH1, heroSub, ctaRow, heroStat].forEach((el, i) => {
      if (!el) return;
      el.style.cssText += `
        opacity: 0;
        transform: translateY(20px);
        transition: opacity .7s cubic-bezier(.16,1,.3,1) ${i * 100 + 100}ms,
                    transform .7s cubic-bezier(.16,1,.3,1) ${i * 100 + 100}ms;
      `;
    });

    // Trigger after paint
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        [heroTag, heroH1, heroSub, ctaRow, heroStat].forEach(el => {
          if (!el) return;
          el.style.opacity = '1';
          el.style.transform = 'translateY(0)';
        });
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
