"""Generate the static guide from its Markdown report; no external dependencies."""
from pathlib import Path
import html
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'report_ipad_apps_pwa_2026-10-21.md'
DOCS = ROOT / 'docs'

def inline(text):
    protected = []
    def stash(value):
        protected.append(value)
        return f'\x00{len(protected)-1}\x00'
    text = re.sub(r'`([^`]+)`', lambda m: stash('<code>' + html.escape(m[1]) + '</code>'), text)
    text = re.sub(r'\[([^\]]+)\]\((https://[^\s)]+)\)', lambda m: stash(f'<a href="{html.escape(m[2], quote=True)}" target="_blank" rel="noopener noreferrer">{html.escape(m[1])}<span aria-hidden="true"> ↗</span></a>'), text)
    text = html.escape(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\[(\d+)\]', r'<a class="citation" href="#source-\1">[\1]</a>', text)
    return re.sub(r'\x00(\d+)\x00', lambda m: protected[int(m[1])], text)

def icon(name):
    return f'<svg class="icon" aria-hidden="true"><use href="#i-{name}"/></svg>'

def markdown(text, sid):
    lines = text.strip().splitlines()
    out, i, block = [], 0, 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1; continue
        if line.startswith('```'):
            language, code = line[3:], []
            i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                code.append(lines[i]); i += 1
            block += 1
            cid = f'{sid}-code-{block}'
            label = 'ГОТОВИЙ ПРОМПТ ДЛЯ CLAUDE CODE' if language == 'text' else 'TERMINAL · MACOS'
            out.append(f'<div class="code-card"><div class="code-toolbar"><span>{label}</span><button class="copy-button" data-copy="{cid}">{icon("copy")}<span>Копіювати</span></button></div><pre tabindex="0"><code id="{cid}">{html.escape(chr(10).join(code))}</code></pre></div>')
            i += 1; continue
        if line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')]); i += 1
            headers = ''.join(f'<th scope="col">{inline(c)}</th>' for c in rows[0])
            body = []
            for row in rows[2:]:
                body.append('<tr>' + ''.join(f'<th scope="row">{inline(c)}</th>' if n == 0 else f'<td>{inline(c)}</td>' for n, c in enumerate(row)) + '</tr>')
            toolbar = '<div class="comparison-toolbar"><div class="segmented" role="group" aria-label="Фільтр способів розробки"><button data-filter="all" aria-pressed="true" class="selected">Усі варіанти</button><button data-filter="free" aria-pressed="false">Без внеску Apple</button><button data-filter="native" aria-pressed="false">Нативні</button></div><span class="result-count" role="status">7 варіантів</span></div>' if sid == 'compare' else ''
            out.append(toolbar + f'<div class="table-card"><div class="table-scroll" role="region" aria-label="Таблиця: {html.escape(rows[0][0])}" tabindex="0"><table><thead><tr>{headers}</tr></thead><tbody>{"".join(body)}</tbody></table></div></div>')
            continue
        if line.startswith('### '):
            out.append(f'<h3>{inline(line[4:])}</h3>'); i += 1; continue
        if re.match(r'^\d+\. ', line):
            items = []
            while i < len(lines) and re.match(r'^\d+\. ', lines[i]):
                item = re.sub(r'^\d+\. ', '', lines[i])
                attr = f' id="source-{len(items)+1}"' if sid == 'sources' else ''
                items.append(f'<li{attr}>{inline(item)}</li>'); i += 1
            cls = 'source-list' if sid == 'sources' else 'step-list'
            out.append(f'<ol class="{cls}">{"".join(items)}</ol>'); continue
        paragraph = [line]; i += 1
        while i < len(lines) and lines[i].strip() and not lines[i].startswith(('```', '|', '### ')) and not re.match(r'^\d+\. ', lines[i]):
            paragraph.append(lines[i]); i += 1
        out.append('<p>' + inline(' '.join(paragraph)) + '</p>')
    return '\n'.join(out)

sections = [
 ('overview', 'З чого почати', 'book', 'Зрозуміти головне.', 'Що варто знати перед першою програмою.'),
 ('compare', 'Порівняти варіанти', 'compare', 'Одна ідея. Кілька шляхів.', 'Вартість, підписування та способи запуску.'),
 ('pwa', 'Як працює PWA', 'device', 'Від коду — до іконки.', 'Знайомство з прогресивним вебзастосунком.'),
 ('limits', 'Можливості й межі', 'shield', 'Можливості без ілюзій.', 'Що працює у вебі та що потрібно передбачити.'),
 ('architecture', 'Архітектура', 'grid', 'Зберіть свій набір.', 'Проста архітектура для особистого інструмента.'),
 ('native', 'Якщо потрібен SwiftUI', 'code', 'Коли варто обрати SwiftUI.', 'Нативні можливості та підготовка Xcode.'),
 ('practice', 'Перша PWA', 'check', 'Час створити щось своє.', 'Готове завдання для Claude Code та критерії приймання.'),
 ('sources', 'Офіційні джерела', 'link', 'Більше першоджерел.', 'Apple, WebKit, W3C та розробники інструментів.'),
]
source = SOURCE.read_text(encoding='utf-8')
parts = re.split(r'^## \d+\. .+$', source, flags=re.M)[1:]
assert len(parts) == len(sections), 'Update section mapping when the report structure changes.'
articles = []
for n, (info, content) in enumerate(zip(sections, parts), 1):
    sid, label, glyph, title, subtitle = info
    rendered = markdown(content, sid)
    if sid == 'overview':
        intro, rest = rendered.split('<h3>', 1)
        rendered = intro + '<details class="report-details"><summary>Що уточнено у вихідному матеріалі<span aria-hidden="true">+</span></summary><div class="details-content"><h3>' + rest + '</div></details>'
    if sid == 'pwa':
        journey = '<div class="journey">' + ''.join(f'<article><span class="step-number">0{j}</span>{icon(g)}<h3>{t}</h3><p>{d}</p><span class="chip">{c}</span></article>' for j, g, t, d, c in [(1, 'code', 'Створюєте на Mac', 'Claude Code допомагає з інтерфейсом і логікою.', 'MacBook Air'), (2, 'link', 'Розміщуєте у вебі', 'Статична збірка за захищеною HTTPS-адресою.', 'GitHub Pages'), (3, 'device', 'Запускаєте на iPad', 'Safari → «Поділитися» → «На початковий екран».', 'Ваша іконка')]) + '</div>'
        rendered = journey + rendered
    if sid == 'practice':
        rendered = rendered.replace('<ol class="step-list">', '<div class="checklist-toolbar"><span>Ваш робочий чекліст</span><span class="chip" id="check-count" role="status">0 / 7</span></div><p class="checklist-note">Позначки діють до перезавантаження сторінки.</p><ol class="checklist">')
        rendered = re.sub(r'<li>(.*?)</li>', r'<li><label><input type="checkbox"><span>\1</span></label></li>', rendered)
    articles.append(f'<section id="{sid}" class="content-section section-anchor" aria-labelledby="{sid}-title"><div class="section-heading"><div><span class="eyebrow">{n:02} / {label.upper()}</span><h2 id="{sid}-title">{title}</h2></div><p>{subtitle}</p></div><div class="report-content">{rendered}</div></section>')
nav = ''.join(f'<a class="nav-link" href="#{sid}">{icon(g)}<span>{label}</span><small>{n:02}</small></a>' for n, (sid, label, g, _, _) in enumerate(sections, 1))
icons = {
 'grid':'<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/>',
 'arrow':'<path d="M5 12h14m-6-6 6 6-6 6"/>',
 'book':'<path d="M12 6c-3-3-7-3-10-2v15c4-1 7 0 10 2 3-2 6-3 10-2V4c-3-1-7-1-10 2Zm0 0v15"/>',
 'compare':'<rect x="3" y="4" width="7" height="16" rx="2"/><rect x="14" y="4" width="7" height="16" rx="2"/><path d="M5 9h3m8 5h3"/>',
 'device':'<rect x="4" y="2" width="16" height="20" rx="3"/><path d="M10 18h4"/>',
 'shield':'<path d="m12 2 8 4v6c0 5-8 10-8 10S4 17 4 12V6l8-4Z"/><path d="m8 12 3 3 5-6"/>',
 'code':'<path d="m8 6-6 6 6 6m8-12 6 6-6 6M14 3l-4 18"/>',
 'link':'<path d="m10 7 3-3a5 5 0 0 1 7 7l-3 3m-3 3-3 3a5 5 0 0 1-7-7l3-3m1 6 8-8"/>',
 'copy':'<rect x="8" y="8" width="13" height="13" rx="2"/><path d="M16 4V3H3v13h1"/>',
 'download':'<path d="M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5"/>',
 'sun':'<circle cx="12" cy="12" r="4"/><path d="M12 1v2m0 18v2M1 12h2m18 0h2M4 4l2 2m12 12 2 2M4 20l2-2M18 6l2-2"/>',
 'menu':'<path d="M4 6h16M4 12h16M4 18h16"/>',
 'check':'<path d="m5 12 4 4L19 6"/>',
 'close':'<path d="m6 6 12 12M6 18 18 6"/>',
}
symbols = ''.join(f'<symbol id="i-{name}" viewBox="0 0 24 24">{path}</symbol>' for name, path in icons.items())
page = '''<!doctype html>
<html lang="uk"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#f7fbff">
<meta name="description" content="Практичний посібник: власні застосунки для iPad через Claude Code, PWA, SwiftUI та GitHub Pages. Порівняння, інструкції й офіційні джерела.">
<title>Власні застосунки для iPad · Apple Apps Lab</title>
<link rel="icon" href="icon.svg" type="image/svg+xml"><link rel="stylesheet" href="styles.css"><script src="app.js" defer></script>
</head><body>
<a class="skip-link" href="#main">Перейти до вмісту</a>
<svg class="icon-library" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><defs>SYMBOLS</defs></svg>
<button class="scrim" aria-label="Закрити навігацію" tabindex="-1" hidden></button>
<aside class="sidebar" id="navigation">
<a class="brand" href="#start" aria-label="Apple Apps Lab — на початок"><span class="brand-mark">GRID</span><span>apple apps<span class="brand-sub">lab / особисті інструменти</span></span></a>
<div class="nav-heading">ПРАКТИЧНИЙ ПОСІБНИК</div><nav aria-label="Розділи посібника">NAV</nav>
<div class="sidebar-note"><span class="small-label">ВАШ НАСТУПНИЙ КРОК</span><p>Від ідеї на Mac —<br>до іконки на iPad.</p><a href="#practice">Створити першу PWA ARROW</a></div>
<a class="repo-link" href="https://github.com/StsZu/apple-apps-lab" target="_blank" rel="noopener noreferrer">Проєкт на GitHub <span aria-hidden="true">↗</span></a></aside>
<div class="page"><header class="topbar"><div class="topbar-left"><button class="icon-button menu-toggle" aria-label="Відкрити навігацію" aria-expanded="false" aria-controls="navigation">MENU</button><span class="breadcrumb">База знань <span>/</span> <strong>Розробка для iPad</strong></span></div><div class="topbar-actions"><span class="date-label">Перевірено 21.10.2026</span><button class="icon-button theme-toggle" aria-label="Увімкнути темну тему" aria-pressed="false" title="Змінити тему">SUN</button></div></header>
<main id="main"><section id="start" class="hero section-anchor" aria-labelledby="hero-title"><div class="hero-copy"><span class="eyebrow"><span class="status-dot"></span> MACBOOK + CLAUDE CODE → IPAD</span><h1 id="hero-title">Ваші ідеї.<br>Ваші <em>застосунки.</em></h1><p class="hero-description">Створюйте власні інструменти для iPad. Дізнайтеся, коли достатньо PWA, коли потрібен SwiftUI та за що насправді платить розробник.</p><div class="hero-actions"><a class="button filled" href="#compare">Обрати свій шлях ARROW</a><a class="button text-button" href="report.md" download>DOWNLOAD Звіт .md</a></div><p class="hero-footnote">Практичний матеріал · офіційні джерела · українською</p></div>
<div class="hero-art" role="img" aria-label="Ілюстрація вебзастосунку зі списком завдань на iPad"><span class="art-orbit orbit-one"></span><span class="art-orbit orbit-two"></span><div class="floating-label label-top"><span class="status-dot"></span> Ваша ідея — вже на екрані</div><div class="tablet"><div class="tablet-camera"></div><div class="tablet-screen"><div class="demo-top"><span class="demo-logo">GRID</span><span>Мій простір<small>Маленькі кроки. Власний темп.</small></span><span class="demo-avatar">С</span></div><div class="demo-greeting">Почнімо з ідеї<span>Що створимо сьогодні?</span></div><div class="demo-task"><span class="demo-tick checked">✓</span><span>Навчальний тренажер<small>Польська мова · щоденна практика</small></span></div><div class="demo-task"><span class="demo-tick checked">✓</span><span>Особистий довідник<small>Усе потрібне під рукою</small></span></div><div class="demo-task"><span class="demo-tick"></span><span>Мій наступний застосунок<small>Від ідеї до першої версії</small></span></div><div class="demo-bottom"><span>Локальні дані</span><span>Ваш iPad ↗</span></div></div></div><div class="floating-label label-bottom">CHECK PWA · без підпису Apple</div></div></section>
<div class="facts" aria-label="Ключові орієнтири"><div class="fact"><span class="fact-number">$0<span> / Apple</span></span><p>для використання власної PWA</p></div><div class="fact"><span class="fact-number">7 <span>днів</span></span><p>строк профілю Personal Team</p></div><div class="fact"><span class="fact-number">1 <span>кодова база</span></span><p>для адаптації під різні пристрої</p></div></div>
ARTICLES
<footer><a class="footer-brand" href="#start">apple apps lab<span>Власні інструменти. Власний досвід.</span></a><span>Навчальний проєкт · 2026</span><a href="#start">На початок ↑</a></footer></main></div><div class="snackbar" role="status" aria-live="polite" hidden></div>
</body></html>'''
for key, value in {'SYMBOLS': symbols, 'NAV': nav, 'ARTICLES': '\n'.join(articles), 'GRID': icon('grid'), 'ARROW': icon('arrow'), 'MENU': icon('menu'), 'SUN': icon('sun'), 'DOWNLOAD': icon('download'), 'CHECK': icon('check')}.items():
    page = page.replace(key, value)
DOCS.mkdir(exist_ok=True)
(DOCS / 'index.html').write_text(page, encoding='utf-8')
shutil.copyfile(SOURCE, DOCS / 'report.md')
(DOCS / 'icon.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="19" fill="#b8dfff"/><g fill="#225575"><rect x="14" y="14" width="15" height="15" rx="5"/><rect x="35" y="14" width="15" height="15" rx="5"/><rect x="14" y="35" width="15" height="15" rx="5"/><rect x="35" y="35" width="15" height="15" rx="5"/></g></svg>\n', encoding='utf-8')
print('Built docs/index.html, docs/report.md and docs/icon.svg')
