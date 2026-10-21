'use strict';

// The guide remains readable without JavaScript; this adds optional interactions.
const root = document.documentElement;
const themeButton = document.querySelector('.theme-toggle');
const systemTheme = matchMedia('(prefers-color-scheme: dark)');
let themePreference = null;
try { themePreference = localStorage.getItem('apple-apps-lab-theme'); } catch (_) { /* Storage may be unavailable. */ }
function setTheme(theme) {
  root.dataset.theme = theme;
  themeButton.setAttribute('aria-pressed', String(theme === 'dark'));
  themeButton.setAttribute('aria-label', theme === 'dark' ? 'Увімкнути світлу тему' : 'Увімкнути темну тему');
  document.querySelector('meta[name="theme-color"]').content = theme === 'dark' ? '#111810' : '#f7f9f2';
}
setTheme(themePreference === 'light' || themePreference === 'dark' ? themePreference : systemTheme.matches ? 'dark' : 'light');
themeButton.addEventListener('click', () => {
  themePreference = root.dataset.theme === 'dark' ? 'light' : 'dark';
  setTheme(themePreference);
  try { localStorage.setItem('apple-apps-lab-theme', themePreference); } catch (_) { /* Theme still works for this session. */ }
});
systemTheme.addEventListener('change', event => { if (!themePreference) setTheme(event.matches ? 'dark' : 'light'); });

const menuButton = document.querySelector('.menu-toggle');
const sidebar = document.querySelector('.sidebar');
const scrim = document.querySelector('.scrim');
const mobileLayout = matchMedia('(max-width: 1100px)');
function setMenu(open, returnFocus = false) {
  document.body.classList.toggle('nav-open', open);
  menuButton.setAttribute('aria-expanded', String(open));
  menuButton.setAttribute('aria-label', open ? 'Закрити навігацію' : 'Відкрити навігацію');
  scrim.hidden = !open;
  sidebar.inert = mobileLayout.matches && !open;
  if (open) sidebar.querySelector('a').focus();
  if (returnFocus) menuButton.focus();
}
menuButton.addEventListener('click', () => setMenu(!document.body.classList.contains('nav-open')));
scrim.addEventListener('click', () => setMenu(false, true));
mobileLayout.addEventListener('change', () => setMenu(false));
setMenu(false);
sidebar.querySelectorAll('a').forEach(link => link.addEventListener('click', () => setMenu(false)));
document.addEventListener('keydown', event => {
  if (!document.body.classList.contains('nav-open')) return;
  if (event.key === 'Escape') { setMenu(false, true); return; }
  if (event.key === 'Tab') {
    const links = [...sidebar.querySelectorAll('a')];
    const first = links[0], last = links[links.length - 1];
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  }
});

const navLinks = [...document.querySelectorAll('.nav-link')];
function updateNavigation() {
  const sections = [...document.querySelectorAll('.content-section')];
  let current = sections[0].id;
  for (const section of sections) if (section.getBoundingClientRect().top <= 155) current = section.id;
  navLinks.forEach(link => {
    const active = link.hash === '#' + current;
    link.classList.toggle('active', active);
    if (active) link.setAttribute('aria-current', 'location'); else link.removeAttribute('aria-current');
  });
}
let scrollQueued = false;
window.addEventListener('scroll', () => {
  if (!scrollQueued) requestAnimationFrame(() => { updateNavigation(); scrollQueued = false; });
  scrollQueued = true;
}, { passive: true });
updateNavigation();

const comparisonRows = [...document.querySelectorAll('#compare tbody tr')];
const filterButtons = [...document.querySelectorAll('[data-filter]')];
filterButtons.forEach(button => button.addEventListener('click', () => {
  const filter = button.dataset.filter;
  comparisonRows.forEach((row, index) => { row.hidden = filter === 'free' ? index > 4 : filter === 'native' ? index < 3 : false; });
  filterButtons.forEach(item => { const active = item === button; item.classList.toggle('selected', active); item.setAttribute('aria-pressed', String(active)); });
  const count = comparisonRows.filter(row => !row.hidden).length;
  document.querySelector('.result-count').textContent = `${count} ${count === 7 || count === 5 ? 'варіантів' : 'варіанти'}`;
}));

let snackbarTimer;
function notify(message) {
  const snackbar = document.querySelector('.snackbar');
  snackbar.textContent = message;
  snackbar.hidden = false;
  clearTimeout(snackbarTimer);
  snackbarTimer = setTimeout(() => { snackbar.hidden = true; }, 4500);
}
document.querySelectorAll('[data-copy]').forEach(button => button.addEventListener('click', async () => {
  const code = document.getElementById(button.dataset.copy);
  let copied = false;
  try {
    if (navigator.clipboard && window.isSecureContext) { await navigator.clipboard.writeText(code.textContent); copied = true; }
  } catch (_) { /* Try a fallback for local-file previews or denied clipboard permission. */ }
  if (!copied) {
    const helper = document.createElement('textarea');
    helper.value = code.textContent;
    helper.setAttribute('readonly', '');
    helper.style.cssText = 'position:fixed;top:0;left:-9999px;font-size:16px';
    document.body.append(helper); helper.select();
    try { copied = document.execCommand('copy'); } catch (_) { /* Show a manual selection below. */ }
    helper.remove(); button.focus();
  }
  if (copied) notify('Скопійовано. Вставте текст у Claude Code або Terminal.');
  else {
    const range = document.createRange(); range.selectNodeContents(code);
    const selection = window.getSelection(); selection.removeAllRanges(); selection.addRange(range);
    notify('Текст виділено. Скопіюйте його вручну через меню або ⌘C.');
  }
}));

const checks = [...document.querySelectorAll('.checklist input')];
checks.forEach(check => check.addEventListener('change', () => {
  document.getElementById('check-count').textContent = `${checks.filter(item => item.checked).length} / ${checks.length}`;
}));
