// ==UserScript==
// @name         Mobilism → MAM Search Button
// @namespace    https://github.com/tanya
// @version      0.1.0
// @description  Adds a MyAnonamouse (MAM) search button to each topic row on Mobilism forum listing pages.
// @author       GitHub Copilot
// @match        https://forum.mobilism.me/viewforum.php*
// @match        http://forum.mobilism.me/viewforum.php*
// @icon         https://www.myanonamouse.net/favicon.ico
// @grant        GM_addStyle
// @run-at       document-idle
// ==/UserScript==

(function () {
  'use strict';

  const MAM_BASE = 'https://www.myanonamouse.net/tor/browse.php';
  const AUDIBLE_BASE = 'https://www.audible.com/search';

  function buildQueryFromText(text) {
    if (!text) return '';
    // Remove parenthetical or bracketed suffixes like (.M4B) or [Audiobook]
    let clean = text
      .replace(/\s*[\(\[].*?[\)\]]\s*/g, ' ')
      .replace(/\s{2,}/g, ' ')
      .trim();

    // Split into title and author
    const parts = clean.split(/\s+by\s+/i);
    let title = (parts[0] || '').trim();
    let author = (parts[1] || '').trim();

    // Remove leading articles from title
    title = title.replace(/^(The|A|An)\s+/i, '').trim();

    // Keep only safe characters
    title = title.replace(/[^A-Za-z0-9'\- ]+/g, '').trim();
    author = author.replace(/[^A-Za-z0-9'\- ]+/g, '').trim();

    // Use author's last name if present to mirror example
    let authorLast = '';
    if (author) {
      const tokens = author.split(/\s+/);
      authorLast = tokens[tokens.length - 1];
    }

    let query = authorLast ? `${title} ${authorLast}` : title;
    query += ' m4b';
    return query.replace(/\s{2,}/g, ' ').trim();
  }

  function makeButton(label, href) {
    const btn = document.createElement('a');
    btn.textContent = label;
    btn.className = 'mam-search-btn';
    btn.href = href;
    btn.target = '_blank';
    btn.rel = 'noopener noreferrer';
    return btn;
  }

  function makeAudibleButton(label, href) {
    const btn = document.createElement('a');
    btn.textContent = label;
    btn.className = 'audible-search-btn';
    btn.href = href;
    btn.target = '_blank';
    btn.rel = 'noopener noreferrer';
    return btn;
  }

  function buildAudibleQueryFromText(text) {
    if (!text) return '';
    let clean = text
      .replace(/\s*[\(\[].*?[\)\]]\s*/g, ' ')
      .replace(/\s{2,}/g, ' ')
      .trim();

    const parts = clean.split(/\s+by\s+/i);
    let title = (parts[0] || '').trim();
    let author = (parts[1] || '').trim();

    title = title.replace(/^(The|A|An)\s+/i, '').trim();
    title = title.replace(/[^A-Za-z0-9'\- ]+/g, '').trim();
    author = author.replace(/[^A-Za-z0-9'\- ]+/g, '').trim();

    let authorLast = '';
    if (author) {
      const tokens = author.split(/\s+/);
      authorLast = tokens[tokens.length - 1];
    }

    const query = authorLast ? `${title} ${authorLast}` : title;
    return query.replace(/\s{2,}/g, ' ').trim();
  }

  function injectIntoCell(td) {
    if (!td || td.dataset.mamBtnInjected === '1') return;
    const topictitle = td.querySelector('a.topictitle');
    if (!topictitle) return;

    const mamQ = buildQueryFromText(topictitle.textContent || '');
    const audibleQ = buildAudibleQueryFromText(topictitle.textContent || '');
    if (!mamQ) return;

    const mamUrl = `${MAM_BASE}?tor%5Btext%5D=${encodeURIComponent(
      mamQ
    )}&tor%5BsrchIn%5D%5Btitle%5D=true&tor%5BsrchIn%5D%5Bauthor%5D=true&tor%5BsrchIn%5D%5Bnarrator%5D=true&tor%5BsrchIn%5D%5BfileTypes%5D=true&tor%5BsearchType%5D=all&tor%5BsearchIn%5D=torrents&tor%5Bcat%5D%5B%5D=0&tor%5BbrowseFlagsHideVsShow%5D=0&tor%5Bunit%5D=1&tor%5BsortType%5D=dateDesc&tor%5BstartNumber%5D=0`;
    const audibleUrl = `${AUDIBLE_BASE}?keywords=${encodeURIComponent(audibleQ)}`;
    const mamBtn = makeButton('MAM', mamUrl);
    const audibleBtn = makeAudibleButton('Audible', audibleUrl);

    // Insert a small space then the button right after the title link
    const spacer = document.createTextNode(' ');
    const spacer2 = document.createTextNode(' ');
    topictitle.after(spacer, mamBtn, spacer2, audibleBtn);

    td.dataset.mamBtnInjected = '1';
  }

  function processAll() {
    document
      .querySelectorAll('td.expand.footable-first-column')
      .forEach(injectIntoCell);
  }

  // Minimal, legible styling for the button
  GM_addStyle(`
    .mam-search-btn {
      display: inline-block;
      margin-left: 6px;
      padding: 2px 6px;
      font-size: 11px;
      line-height: 1.6;
      border-radius: 3px;
      color: #fff !important;
      background: #4a7bd4;
      text-decoration: none;
      border: 1px solid #3662af;
    }
    .mam-search-btn:hover {
      background: #365fb0;
    }
    .audible-search-btn {
      display: inline-block;
      margin-left: 6px;
      padding: 2px 6px;
      font-size: 11px;
      line-height: 1.6;
      border-radius: 3px;
      color: #fff !important;
      background: #f8991c;
      text-decoration: none;
      border: 1px solid #cf7a15;
    }
    .audible-search-btn:hover {
      background: #e28510;
    }
  `);

  // Initial run
  processAll();

  // Observe dynamically added rows (e.g., pagination or client updates)
  const observer = new MutationObserver((mutations) => {
    for (const m of mutations) {
      if (m.type === 'childList') {
        m.addedNodes.forEach((node) => {
          if (!(node instanceof Element)) return;
          if (node.matches && node.matches('td.expand.footable-first-column')) {
            injectIntoCell(node);
          } else if (node.querySelectorAll) {
            node
              .querySelectorAll('td.expand.footable-first-column')
              .forEach(injectIntoCell);
          }
        });
      } else if (m.type === 'attributes' && m.attributeName === 'class') {
        const el = m.target;
        if (el instanceof Element) {
          if (el.matches('td.expand.footable-first-column')) {
            injectIntoCell(el);
          } else {
            el
              .querySelectorAll?.('td.expand.footable-first-column')
              .forEach(injectIntoCell);
          }
        }
      }
    }
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ['class'],
  });
})();
