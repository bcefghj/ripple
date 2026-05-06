/* ============================================================================
 * Version B · Agent OS 渲染 + 交互（默认暗色，可切换浅色）
 * ========================================================================== */
(function () {
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => root.querySelectorAll(sel);
  const D = window.FG;

  function initTheme() {
    const html = document.documentElement;
    const saved = localStorage.getItem('fg-theme-b');
    if (saved === 'light') html.setAttribute('data-theme', 'light');
    // B 版默认暗色（不读 prefers-color-scheme）
    const btn = $('#themeToggle');
    if (!btn) return;
    const setIcon = () => btn.textContent = html.getAttribute('data-theme') === 'light' ? '☾' : '☀';
    setIcon();
    btn.addEventListener('click', () => {
      const isLight = html.getAttribute('data-theme') === 'light';
      if (isLight) { html.removeAttribute('data-theme'); localStorage.setItem('fg-theme-b', 'dark'); }
      else { html.setAttribute('data-theme', 'light'); localStorage.setItem('fg-theme-b', 'light'); }
      setIcon();
      // 重载 demo（颜色相关）
      remountDemos();
    });
  }

  function initReveal() {
    const els = $$('.reveal');
    const io = new IntersectionObserver(entries => {
      entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('visible'); io.unobserve(e.target); } });
    }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });
    els.forEach(el => io.observe(el));
  }

  function renderHeroStats() {
    const root = $('#heroStats');
    if (!root) return;
    root.innerHTML = D.heroStats.map(s => `
      <div class="stat reveal">
        <div class="v">${s.v}</div>
        <div class="k">${s.k}</div>
        <div class="n">${s.note}</div>
      </div>`).join('');
  }
  function renderProblem() {
    const root = $('#problemGrid');
    if (!root) return;
    root.innerHTML = D.problemStats.map(s => `
      <div class="stat-card reveal">
        <div class="num">${s.num}<span>${s.unit}</span></div>
        <div class="label">${s.label}</div>
        <div class="src">// ${s.src}</div>
      </div>`).join('');
  }
  function renderSolution() {
    const root = $('#solutionGrid');
    if (!root) return;
    root.innerHTML = D.solutions.map(s => `
      <div class="sol-card reveal">
        <div class="meta"><span class="num">${s.code}</span><span class="tag">${s.tag}</span></div>
        <h3>${s.title}</h3>
        <p>${s.desc}</p>
        <ul>${s.bullets.map(b => `<li>${b}</li>`).join('')}</ul>
      </div>`).join('');
  }
  function renderPriority() {
    const root = $('#priorityGrid');
    if (!root) return;
    root.innerHTML = D.priorityLevels.map(p => `
      <div class="class-card reveal" style="border-left-color:${p.color}">
        <div class="lvl" style="color:${p.color}">${p.lvl} · ${p.name}</div>
        <h4>${p.desc}</h4>
        <p>${p.rule}</p>
        <div class="ex">"${p.example}"</div>
      </div>`).join('');
  }
  function renderEngine() {
    const root = $('#engineWrap');
    if (!root) return;
    const layers = D.architecture.layers.map(l => `
      <div class="layer-row">
        <div class="layer-name">${l.name}</div>
        <div class="nodes">${l.nodes.map(n => `<div class="node">${n}</div>`).join('')}</div>
      </div>`).join('');
    const insps = D.architecture.inspirations.map(i => `
      <div class="insp-row">
        <span class="from">${i.from}</span>
        <span class="arrow">→</span>
        <span class="to">${i.to}</span>
        <span class="detail">${i.detail}</span>
      </div>`).join('');
    root.innerHTML = `
      <div class="reveal">${layers}</div>
      <div class="inspirations reveal">
        <div class="insp-h">// inspirations · 借鉴源</div>
        <div class="insp-grid">${insps}</div>
      </div>`;
  }
  function renderGates() {
    const root = $('#gateGrid');
    if (!root) return;
    root.innerHTML = D.securityGates.map(g => `
      <div class="gate-card reveal">
        <div class="gid">${g.id}</div>
        <h4>${g.name}</h4>
        <div class="en">// ${g.en}</div>
        <p>${g.desc}</p>
      </div>`).join('');
  }
  function renderPrivacy() {
    const root = $('#privacyGrid');
    if (!root) return;
    root.innerHTML = D.privacy.map(p => `
      <div class="priv-card reveal">
        <div class="priv-icon">${p.icon}</div>
        <h4>${p.title}</h4>
        <p>${p.desc}</p>
      </div>`).join('');
  }
  function renderStatus() {
    const root = $('#statusGrid');
    if (!root) return;
    root.innerHTML = ['built', 'lab', 'planned'].map(k => {
      const g = D.statusGroups[k];
      return `
      <div class="status-col ${k} reveal">
        <span class="badge">${g.title.split(' · ')[0]}</span>
        <h3>${g.title.split(' · ')[1] || g.title}</h3>
        <p class="sub">${g.subtitle}</p>
        <ul>${g.items.map(it => `<li>${it}</li>`).join('')}</ul>
      </div>`;
    }).join('');
  }
  function renderTracks() {
    const root = $('#tracksGrid');
    if (!root) return;
    const tracks = [
      { order: 'TRACK_01 · 第一志愿', title: '飞书 AI 产品创新 · 课题二', desc: '基于 IM 的办公协同智能助手 · 串联 IM / 文档 / 演示稿等办公套件' },
      { order: 'TRACK_02 · 第二志愿', title: '飞书 OpenClaw · 课题二', desc: '企业级长程协作 Memory 系统 · FlowMemory 三层正是为此设计' },
      { order: 'TRACK_03 · 第三志愿', title: 'AI 大模型安全 · 课题一', desc: 'Agent + 客户端环境安全防护 · 8 层安全栈 + Promptfoo 红队覆盖' },
    ];
    root.innerHTML = tracks.map(t => `
      <div class="track-card reveal">
        <div class="order">${t.order}</div>
        <h4>${t.title}</h4>
        <p>${t.desc}</p>
      </div>`).join('');
  }
  function renderApis() {
    const root = $('#apiCloud');
    if (!root) return;
    root.innerHTML = D.feishuApis.map(a => `
      <span class="api-pill ${a.status}"><span class="dot"></span>${a.name} <span style="opacity:.55">${a.scope}</span></span>`).join('');
  }
  function renderTeam() {
    const root = $('#teamGrid');
    if (!root) return;
    root.innerHTML = D.team.map(t => `
      <div class="team-card reveal">
        <div class="order">${t.order} / TEAM</div>
        <div class="name-line">
          <h3>${t.name}</h3>
          <span class="en-name">${t.enName}</span>
        </div>
        <div class="role">${t.roleZh}</div>
        <div class="edu">${t.eduPrimary}</div>
        <div class="edu"><strong>${t.eduHighlight}</strong></div>
        <div class="bio">${t.bio}</div>
        <div class="quote">"${t.quote}"</div>
        <div class="h-sub">// experiences</div>
        ${t.experiences.map(e => `<div class="exp-row"><span class="org">${e.org}</span><span><strong style="color:var(--fg)">${e.role}</strong> · ${e.detail}</span></div>`).join('')}
        <div class="h-sub">// achievements</div>
        <div class="achievement-list">${t.achievements.map(a => `<span class="ach-pill">${a}</span>`).join('')}</div>
        <div class="h-sub">// contributions to FlowGuard</div>
        <p style="font-size:.85rem;color:var(--fg2);line-height:1.7">${t.contributions.join(' · ')}</p>
        <div class="links">${t.links.map(l => `<a href="${l.href}" ${l.external?'target="_blank" rel="noopener"':''}>${l.label}${l.external?' ↗':''}</a>`).join('')}</div>
      </div>`).join('');
    const nar = $('#teamNarrative');
    if (nar) nar.textContent = '"' + D.teamNarrative + '"';
  }
  function renderResources() {
    const root = $('#resGrid');
    if (!root) return;
    root.innerHTML = D.resources.map(r => `
      <a class="res-card reveal" href="${r.href}" ${r.kind==='ext'||r.kind==='live'||r.kind==='code'?'target="_blank" rel="noopener"':''}>
        <div class="icon">${r.icon}</div>
        <h4>${r.title}</h4>
        <div class="note">${r.note}</div>
      </a>`).join('');
  }
  function renderFAQ() {
    const root = $('#faqList');
    if (!root) return;
    root.innerHTML = D.faq.map(f => `
      <details class="faq-item reveal">
        <summary>${f.q}</summary>
        <div class="ans">${f.a}</div>
      </details>`).join('');
  }

  function currentDemoTheme() {
    return document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
  }
  function mountDemos() {
    const t = currentDemoTheme();
    if ($('#chatSimRoot') && D.ChatSim) {
      $('#chatSimRoot').innerHTML = '';
      D.ChatSim.mount($('#chatSimRoot'), { theme: t });
    }
    if ($('#classifierRoot') && D.Classifier) {
      $('#classifierRoot').innerHTML = '';
      D.Classifier.mount($('#classifierRoot'), { theme: t });
    }
    if ($('#mcpRoot') && D.MCPPlayground) {
      $('#mcpRoot').innerHTML = '';
      D.MCPPlayground.mount($('#mcpRoot'), { theme: t });
    }
    const gal = $('#shotGallery');
    if (gal && D.Screens) {
      const shots = ['p0', 'recovery', 'welcome', 'dashboard', 'weekly', 'cursor'];
      const labels = { p0: 'P0 加急卡片', recovery: 'Recovery Card', welcome: '欢迎卡片 · 自动建工作台', dashboard: 'Dashboard 概览', weekly: '周报卡片', cursor: 'Cursor 调用 MCP' };
      gal.innerHTML = '';
      shots.forEach(name => {
        const wrap = document.createElement('div');
        wrap.style.cssText = 'display:flex;flex-direction:column;gap:8px;align-items:center';
        wrap.appendChild(D.Screens.render(name, t));
        const cap = document.createElement('div');
        cap.style.cssText = 'font-size:.78rem;color:var(--fg3);font-family:var(--font-mono);text-align:center';
        cap.textContent = '// ' + labels[name];
        wrap.appendChild(cap);
        gal.appendChild(wrap);
      });
    }
  }
  function remountDemos() {
    // Strip styles to re-inject with new theme
    ['fg-chatsim-style', 'fg-classifier-style', 'fg-mcp-style', 'fg-screens-style'].forEach(id => {
      const e = document.getElementById(id);
      if (e) e.remove();
    });
    mountDemos();
  }

  function init() {
    initTheme();
    renderHeroStats();
    renderProblem();
    renderSolution();
    renderPriority();
    renderEngine();
    renderGates();
    renderPrivacy();
    renderStatus();
    renderTracks();
    renderApis();
    renderTeam();
    renderResources();
    renderFAQ();
    mountDemos();
    initReveal();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
