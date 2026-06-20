# Quality Guidelines

> Code quality standards for frontend development.

---

## Overview

This project is a static site (HTML/CSS/JS, no framework). All data lives in `data.js`, rendered client-side. The main attack surface is XSS via dynamic HTML construction; the main performance concern is layout thrashing from JS-driven card height synchronization.

---

## Forbidden Patterns

### F1: `innerHTML` with unescaped data

**Never** interpolate data values into `innerHTML` template literals without HTML entity escaping. Even if the data source is "trusted" (maintainer-edited `data.js`), any future automated import pipeline creates an injection path.

```js
// ❌ WRONG
article.innerHTML = `<h3>${skillName}</h3>`;

// ✅ CORRECT
const escaped = escapeHtml(skillName);
article.innerHTML = `<h3>${escaped}</h3>`;
```

Use `escapeHtml()` defined in `main.js` — a zero-dependency approach using browser-native `textContent` → `innerHTML` round-trip:

```js
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
```

### F2: Unvalidated external URLs in `<img src>`

**Never** pass raw data values into `src` attributes without protocol validation. `logo_url` values can contain `javascript:`, `data:`, or `file:` URIs.

```js
// ❌ WRONG
`<img src="${skill.logo_url}">`

// ✅ CORRECT
const safe = isSafeUrl(skill.logo_url) ? escapeHtml(skill.logo_url) : "";
function isSafeUrl(url) { return typeof url === "string" && /^https:\/\//i.test(url); }
```

### F3: Interleaved DOM reads and writes across collections

**Never** alternate `style.* =` writes with `offsetTop`/`offsetHeight` reads across a card list — each read forces a synchronous layout reflow.

```js
// ❌ WRONG (N forced reflows)
cards.forEach(card => {
  card.style.height = "auto";
  const top = card.offsetTop;  // forces reflow for EACH card
  // ...
});

// ✅ CORRECT (exactly 1 forced reflow)
cards.forEach(card => card.style.height = "auto");           // Phase 1: all writes
const rows = collectRows(cards, card => card.offsetTop);     // Phase 2: all reads
applyHeights(rows);                                           // Phase 3: all writes
```

### F4: Silent empty state when data fails to load

**Never** show "no matching results" when the underlying data array is empty. Distinguish between "data loaded but nothing matched the filter" and "data script failed to load entirely".

```js
// ✅ CORRECT — check skills.length BEFORE filterSkills()
if (!skills.length) {
  showErrorState("Data failed to load");   // .is-data-error styled
  return;
}
const filtered = filterSkills();
if (!filtered.length) {
  showEmptyState("No matching results");   // regular empty state
}
```

---

## Required Patterns

### R1: Use `textContent` for dynamic text, not `innerHTML`

When building DOM via `document.createElement()` (tags, footer, etc.), always set `.textContent` — not `.innerHTML` — for user-provided strings:

```js
// ✅ CORRECT — createTag already safe
function createTag(tag) {
  const span = document.createElement("span");
  span.textContent = tag;    // safe, no HTML parsing
  return span;
}
```

### R2: `requestAnimationFrame` for resize-triggered DOM measurement

Resize events can fire at 60+ Hz. Gate `syncCardHeights` behind a single-flight RAF guard:

```js
let resizePending = false;
function onResize() {
  if (resizePending) return;
  resizePending = true;
  requestAnimationFrame(() => {
    try { syncCardHeights(); } finally { resizePending = false; }
  });
}
```

Note: `try-finally` is critical — if `syncCardHeights` throws, the guard must still reset.

### R3: `rel="noreferrer"` on all external links

All `<a>` elements pointing to GitHub (or any external domain) must include `rel="noreferrer"` and `target="_blank"`.

---

## Testing Requirements

This project has no automated test suite. Manual verification checklist for any change:

- [ ] All 489 skills render without console errors
- [ ] Search by name, tag, category, audience, and source works correctly
- [ ] Language toggle (zh ↔ en) updates all UI text and card content
- [ ] Empty state shows correctly when no skills match
- [ ] Data-failure state shows correctly (delete `data.js` script tag to test)
- [ ] All external links open with `rel="noreferrer"`
- [ ] Layout is correct at 1920px, 980px, and 375px viewport widths

---

## Code Review Checklist

When reviewing changes to `main.js`, `style.css`, or `index.html`:

- [ ] Any new `innerHTML` usage? → Must be `escapeHtml()`-wrapped or from a static trusted source
- [ ] Any new `<img>` or `<a href>` with dynamic values? → Must be protocol-validated
- [ ] Any new DOM measurement (`offsetTop`, `offsetHeight`, `getBoundingClientRect`)? → Check batch read/write separation
- [ ] Any new event listener? → Check for debounce/throttle if it triggers DOM work
- [ ] New text visible to users? → Added to both `zh` and `en` in `TRANSLATIONS`
- [ ] `data.js` field format changed? → `localizedField()` must handle new shape
- [ ] CSS class added? → Check responsive breakpoints (980px, 760px)
