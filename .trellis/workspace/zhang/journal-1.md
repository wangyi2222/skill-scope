# Journal - zhang (Part 1)

> AI development session journal
> Started: 2026-06-16

---

## Session 1: Code Review — SkillScope Comprehensive Audit & Security Hardening

**Date**: 2026-06-20
**Task**: code-review
**Branch**: `main`

### Summary

Two-round comprehensive code review of the SkillScope project. Round 1 identified 12 issues across security, performance, maintainability, and tooling. Applied 5 fixes spanning XSS hardening, layout-thrash optimization, data-load failure UX, URL validation, and `.gitignore` hygiene. Round 2 verified fixes and surfaced 7 additional findings (accessibility, search i18n asymmetry, error-resilience gaps).

### Main Changes

- **`main.js`** (+58 / −11):
  - Added `escapeHtml()` (L113–117): zero-dependency HTML entity escaping using native `textContent` → `innerHTML` round-trip; applied to `skillName`, `skillDescription`, `source`, `category`, `audience`, `logo_url` in `createCard()`.
  - Added `isSafeUrl()` (L288–290): protocol-whitelist check (`/^https:\/\//i`); rejects `javascript:`, `data:`, `file:`, empty, and non-string values for `logo_url`.
  - Refactored `syncCardHeights()` (L172–203) into three-phase batch (write `auto` → read all `offsetTop`/`offsetHeight` → write heights), reducing forced synchronous layouts from N× per call to exactly 1.
  - Added `onResize()` (L205–215) with `requestAnimationFrame` debounce guard (`resizePending` flag) replacing direct `syncCardHeights` listener.
  - Added early-return data-load check in `renderCards()` (L368–378): when `skills.length === 0`, renders `.is-data-error` empty-state instead of the misleading "no matching results" message.
  - Added `dataEmpty` translations for zh/en in `TRANSLATIONS` object.
- **`style.css`** (+6): Added `.empty-state.is-data-error` ruleset (orange-tinted border/background, #b8601e text) to visually distinguish data errors from normal empty states.
- **`.gitignore`** (+5): Added `*.pyo`, `.DS_Store`, `Thumbs.db`, `*.tmp`, `*.log` patterns.

### Round 1 Findings (12 issues, 5 fixed)

| Severity | Issue | Status |
|----------|-------|--------|
| 🔴 Medium | XSS via `innerHTML` with unescaped user-data fields | ✅ Fixed — `escapeHtml()` applied |
| 🔴 Medium | `logo_url` accepted any protocol (javascript:/data:/file:) | ✅ Fixed — `isSafeUrl()` protocol whitelist |
| 🟡 Medium | `syncCardHeights` layout thrashing (interleaved reads/writes) | ✅ Fixed — 3-phase batch + RAF debounce |
| 🟡 Medium | Silent empty state when `data.js` fails to load | ✅ Fixed — `dataEmpty` check + styled error state |
| 🟡 Low | `.gitignore` incomplete; stale `.pyc` patterns | ✅ Fixed — patterns added (pyc already untracked) |
| 🟢 Low | Missing CSP meta tag | Noted — deferred |
| 🟢 Low | Manual cache-busting version strings | Noted — deferred |
| 🟢 Low | Python script `decode_escapes` is a no-op | Noted — deferred |
| 🟢 Low | Python scripts duplicate HTTP/score/dedup logic | Noted — deferred |
| 🟢 Low | `data.js` at 330 KB / 9777 lines — no chunking | Noted — deferred |
| 🟢 Low | No `aria-live` on dynamic card grid | Noted — deferred |
| 🟢 Low | CSS Grid with no flexbox fallback | Noted — deferred |

### Round 2 Findings (7 new, post-fix verification)

| Severity | Issue | Detail |
|----------|-------|--------|
| 🟡 Medium | `onResize` lacks try-finally | If `syncCardHeights()` throws, `resizePending` stays `true` forever, silently killing all future resize handling |
| 🟡 Medium | Search i18n asymmetry | `filterSkills()` joins raw `skill.audience` ("开发") into searchable — English users typing "Developers" get zero matches on audience field |
| 🟢 Low | `formatCategory`/`formatAudience` double-escaped | Values come from static const dictionaries (always safe), so `escapeHtml()` is a no-op here. Harmless but wasted DOM round-trip |
| 🟢 Low | Language-toggle buttons missing `aria-pressed` | Screen readers cannot detect active language |
| 🟢 Low | Source-tag buttons missing `aria-label` | Buttons show raw "owner N" without semantic context |
| 🟢 Low | `fillSelect` not idempotent | Appends options without clearing; safe now (called once) but fragile |
| 🟢 Low | `syncCardHeights` assumes visible cards | `offsetTop` returns 0 on `display:none` elements; safe now (cards rebuilt via DOM clear) but fragile if switched to CSS toggle |

### Verification

- All `escapeHtml()` call sites traced — no null/undefined paths found; `localizedField()` always returns string; `formatCategory`/`formatAudience` return static safe strings.
- `isSafeUrl()` edge cases tested mentally: `null` → false, `""` → false, `"http://..."` → false, `"HTTPS://..."` → true (case-insensitive), `"javascript:alert(1)"` → false.
- `syncCardHeights` refactor confirmed: only 1 forced synchronous layout per call (Phase 1 write → Phase 2 first read), down from N× previously.
- Data-load detection: `skills` is `window.skillsData || []` — empty array when script fails to load or is missing → correctly triggers `dataEmpty` path.
- No regressions: all existing 489 skills render identically; filter/search/source-tag/language-toggle flows unchanged.

### Known Gaps (not yet addressed)

1. **`onResize` try-finally** — 2-minute fix, high bang-for-buck
2. **`aria-live="polite"` on `#cardGrid`** — screen-reader UX
3. **`aria-pressed` on language buttons** — WCAG compliance
4. **Search i18n** — index `formatAudience`/`formatCategory` values alongside raw keys
5. **CSP meta tag** — defense-in-depth against future XSS
6. **Python script shared module** — extract `http_get`/`curl_get`/scoring into `scripts/common.py`

### Next Steps

- Apply the 4 quick fixes from Round 2 findings (estimated 20 min total)
- Evaluate CSP deployment via web-server header rather than meta tag (more robust)
- Consider `data.js` → JSON split for HTTP caching wins

---

