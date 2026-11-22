(() => {
  'use strict';
  const CATEGORIES = ['All', 'AI', 'Tech', 'Startups', 'Funding', 'Cybersecurity', 'Gadgets', 'Software', 'Science'];
  const STORAGE_KEY = 'techdailynews-bookmarks-v1';
  const state = { articles: [], category: 'All', q: '', period: 'all', sort: 'new', savedOnly: false, limit: 12, country: 'WORLD' };
  const $ = id => document.getElementById(id);
  let saved = new Set();
  try { saved = new Set(JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')); } catch (_) {}
  const node = (tag, className, value) => {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (value !== undefined) el.textContent = String(value);
    return el;
  };
  const readableDate = value => {
    const d = new Date(value);
    return Number.isNaN(d.getTime()) ? 'Recently' : d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };
  const relativeTime = value => {
    const n = new Date(value).getTime();
    if (!Number.isFinite(n)) return 'Recently';
    const hours = Math.max(0, Math.floor((Date.now() - n) / 3600000));
    if (hours < 1) return 'Just now';
    if (hours < 24) return hours + 'h ago';
    return Math.floor(hours / 24) + 'd ago';
  };
  const safeUrl = value => {
    try { const u = new URL(value); return ['http:', 'https:'].includes(u.protocol) ? u.href : null; } catch (_) { return null; }
  };
  const storyLink = (article, label, className) => {
    const a = node('a', className || '', label);
    a.href = safeUrl(article.url) || '#latest';
    a.rel = 'noopener noreferrer';
    a.target = '_blank';
    return a;
  };
  const isSaved = article => saved.has(article.id);
  const persist = () => {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(Array.from(saved))); } catch (_) {}
    $('saved-number').textContent = String(saved.size);
  };
  function initTabs() {
    const fragment = document.createDocumentFragment();
    CATEGORIES.forEach(cat => {
      const button = node('button', cat === state.category ? 'active' : '', cat === 'All' ? 'All stories' : cat === 'Funding' ? 'Funding & VC' : cat);
      button.type = 'button';
      button.setAttribute('aria-pressed', String(cat === state.category));
      button.addEventListener('click', () => {
        state.category = cat;
        state.limit = 12;
        initTabs();
        render();
      });
      fragment.appendChild(button);
    });
    $('tabs').replaceChildren(fragment);
  }
  const filtered = () => {
    const q = state.q.trim().toLowerCase();
    const now = Date.now();
    const days = state.period === '24h' ? 1 : state.period === '7d' ? 7 : 0;
    return state.articles.filter(a => {
      if (state.country !== 'WORLD' && !(Array.isArray(a.countries) && a.countries.includes(state.country))) return false;
      if (state.category !== 'All' && a.category !== state.category) return false;
      if (state.savedOnly && !isSaved(a)) return false;
      if (days && (now - new Date(a.publishedAt).getTime()) > days * 86400000) return false;
      if (q && ![a.title, a.summary, a.category, a.source].join(' ').toLowerCase().includes(q)) return false;
      return true;
    }).sort((a, b) => state.sort === 'old'
      ? new Date(a.publishedAt) - new Date(b.publishedAt)
      : new Date(b.publishedAt) - new Date(a.publishedAt));
  };
  function makeCard(article) {
    const card = node('article', 'story');
    const art = node('div', 'story-art');
    const imageUrl = safeUrl(article.image);
    if (imageUrl && imageUrl.startsWith('https:')) {
      art.classList.add('has-image');
      const img = node('img');
      img.src = imageUrl;
      img.alt = '';
      img.loading = 'lazy';
      img.referrerPolicy = 'no-referrer';
      img.addEventListener('error', () => { img.remove(); art.classList.remove('has-image'); });
      art.appendChild(img);
    }
    art.appendChild(node('span', 'art-category', article.category || 'Tech'));
    art.appendChild(node('span', 'art-title', (article.category || 'TECH').toUpperCase()));
    card.appendChild(art);
    const body = node('div', 'story-body');
    body.appendChild(node('div', 'story-meta', (article.source || 'Publisher') + ' · ' + relativeTime(article.publishedAt)));
    const heading = node('h3', 'story-title');
    heading.appendChild(storyLink(article, article.title || 'Open original reporting'));
    body.appendChild(heading);
    body.appendChild(node('p', 'story-description', article.summary || 'Read the full story from the original publisher.'));
    const bottom = node('div', 'story-bottom');
    bottom.appendChild(storyLink(article, 'READ SOURCE ↗'));
    const btn = node('button', isSaved(article) ? 'active' : '', isSaved(article) ? '★' : '☆');
    btn.type = 'button';
    btn.title = 'Save or unsave this article';
    btn.setAttribute('aria-label', (isSaved(article) ? 'Remove saved' : 'Save') + ' article');
    btn.addEventListener('click', () => {
      if (isSaved(article)) saved.delete(article.id); else saved.add(article.id);
      persist();
      render();
    });
    bottom.appendChild(btn);
    body.appendChild(bottom);
    card.appendChild(body);
    return card;
  }
  function render() {
    const list = filtered();
    $('result-count').textContent = list.length + ' STORIES';
    $('stat-articles').textContent = String(list.length);
    $('stat-sources').textContent = String(new Set(list.map(a => a.source)).size);
    fillFeature(list);
    const fragment = document.createDocumentFragment();
    if (list.length === 0) fragment.appendChild(node('div', 'empty', state.articles.length === 0
      ? 'No articles yet. News will appear after the first successful GitHub Actions refresh.'
      : state.country !== 'WORLD' ? 'No verified '+(document.querySelector('[data-edition-name]')?.textContent || state.country)+' technology headlines match these filters. Select Worldwide to browse global stories.' : 'No stories match the selected filters. Try another category or search.'));
    list.slice(0, state.limit).forEach(a => fragment.appendChild(makeCard(a)));
    $('news-grid').replaceChildren(fragment);
    $('load-more').hidden = list.length <= state.limit;
    $('saved-filter').classList.toggle('active', state.savedOnly);
    $('saved-filter').setAttribute('aria-pressed', String(state.savedOnly));
    persist();
  }
  function fillFeature(list) {
    const a = list[0];
    if (!a) {
      $('lead-category').textContent = state.country === 'WORLD' ? 'GLOBAL TECHNOLOGY' : state.country + ' TECHNOLOGY';
      $('lead-title').textContent = 'No verified country headlines available';
      $('lead-description').textContent = 'Select Worldwide or another country to browse original publisher reporting.';
      $('lead-source').textContent = 'TECHDAILY NEWS';
      $('lead-time').textContent = '';
      $('lead-link').href = '#latest';$('lead-link').textContent = 'BROWSE NEWS ↗';
      $('radar-list').replaceChildren(node('p','muted','No recent reporting for this selection.'));
      return;
    }
    $('lead-category').textContent = (a.category || 'Tech').toUpperCase();
    $('lead-title').textContent = a.title;
    $('lead-description').textContent = a.summary || 'Explore the original story from the publisher.';
    $('lead-source').textContent = (a.source || 'Publisher').toUpperCase();
    $('lead-time').textContent = relativeTime(a.publishedAt);
    $('lead-link').href = safeUrl(a.url) || '#latest';
    $('lead-link').target = '_blank';
    $('lead-link').rel = 'noopener noreferrer';
    $('lead-link').textContent = 'READ STORY ↗';
    const fragment = document.createDocumentFragment();
    list.slice(1, 5).forEach(article => {
      const link = storyLink(article, '', 'radar-item');
      link.appendChild(node('small', '', (article.category || 'Tech').toUpperCase()));
      link.appendChild(node('b', '', article.title));
      link.appendChild(node('span', '', (article.source || 'Publisher') + ' · ' + relativeTime(article.publishedAt)));
      fragment.appendChild(link);
    });
    $('radar-list').replaceChildren(fragment);
  }
  async function loadNews() {
    try {
      const response = await fetch('/data/news.json', { cache: 'no-store' });
      if (!response.ok) throw new Error('News feed returned HTTP ' + response.status);
      const data = await response.json();
      if (!data || !Array.isArray(data.articles)) throw new Error('Invalid news format');
      state.articles = data.articles.filter(a => a && a.title && safeUrl(a.url));
      state.articles.sort((a, b) => new Date(b.publishedAt) - new Date(a.publishedAt));
      $('stat-articles').textContent = state.articles.length;
      $('stat-sources').textContent = new Set(state.articles.map(a => a.source)).size;
      const live = data.status === 'live';
      $('status-label').textContent = live ? 'AUTOMATED NEWS LIVE' : 'AWAITING FIRST REFRESH';
      $('status-time').textContent = data.generatedAt ? 'Updated ' + readableDate(data.generatedAt) : 'Scheduled RSS collection';
      $('edition').textContent = live ? 'UPDATED ' + readableDate(data.generatedAt).toUpperCase() : 'FIRST EDITION PENDING';
      $('radar-date').textContent = readableDate(new Date().toISOString()).toUpperCase();
      if (!state.articles.length) $('radar-list').replaceChildren(node('p', 'muted', 'New articles will appear after the first scheduled news collection.'));
    } catch (error) {
      $('status-label').textContent = 'NEWS FEED UNAVAILABLE';
      $('status-time').textContent = 'Please try refreshing the page';
      $('radar-list').replaceChildren(node('p', 'muted', 'Could not load the latest feed.'));
      console.warn('TechDaily data could not be loaded:', error);
    }
    render();
  }
  function bind() {
    document.addEventListener('countryeditionchange', event => {
      const next = event.detail?.country || 'WORLD';
      state.country = next;
      state.limit = 12;
      render();
    });
    $('year').textContent = String(new Date().getFullYear());
    $('top-date').textContent = readableDate(new Date().toISOString()).toUpperCase();
    $('search').addEventListener('input', e => { state.q = e.target.value; state.limit = 12; render(); });
    $('sort').addEventListener('change', e => { state.sort = e.target.value; render(); });
    $('period').addEventListener('change', e => { state.period = e.target.value; state.limit = 12; render(); });
    $('saved-filter').addEventListener('click', () => { state.savedOnly = !state.savedOnly; state.limit = 12; render(); });
    $('load-more').addEventListener('click', () => { state.limit += 12; render(); });
    document.querySelectorAll('[data-jump]').forEach(link => link.addEventListener('click', () => {
      state.category = link.getAttribute('data-jump');
      state.savedOnly = false;
      state.limit = 12;
      initTabs();
      render();
    }));
    initTabs();
    persist();
  }
  bind();
  loadNews();
})();