const skills = window.skillsData || [];
const CATEGORY_OPTIONS = ["文档", "开发", "嵌入式", "工作流", "插件", "图像", "自动化", "研究"];
const AUDIENCE_OPTIONS = ["开发", "设计", "工作流"];
const CATEGORY_LABELS = {
  zh: {
    文档: "文档",
    开发: "开发",
    嵌入式: "嵌入式",
    工作流: "工作流",
    插件: "插件",
    图像: "图像",
    自动化: "自动化",
    研究: "研究",
  },
  en: {
    文档: "Documents",
    开发: "Development",
    嵌入式: "Embedded",
    工作流: "Workflow",
    插件: "Plugins",
    图像: "Images",
    自动化: "Automation",
    研究: "Research",
  },
};
const AUDIENCE_LABELS = {
  zh: {
    开发: "开发",
    设计: "设计",
    工作流: "工作流",
  },
  en: {
    开发: "Developers",
    设计: "Designers",
    工作流: "Workflow users",
  },
};

const searchInput = document.getElementById("searchInput");
const categoryFilter = document.getElementById("categoryFilter");
const audienceFilter = document.getElementById("audienceFilter");
const cardGrid = document.getElementById("cardGrid");
const resultCount = document.getElementById("resultCount");
const sourceTagsPanel = document.getElementById("sourceTagsPanel");
const sourceTags = document.getElementById("sourceTags");
const languageButtons = [...document.querySelectorAll(".language-button")];

const SOURCE_TAG_THRESHOLD = 15;
const PINNED_SOURCE_TAGS = ["anthropics", "zuoliangyu"];
const TRANSLATIONS = {
  zh: {
    pageTitle: "SkillScope - AI Skills 发现与筛选",
    brandSubtitle: "AI Skills 发现与筛选目录",
    heroTitle: "发现值得使用的 AI Skills",
    heroCopy: "汇集来自 GitHub 的优质 AI Skills，以卡片方式呈现核心能力、使用场景与来源，帮助你快速判断、比较并找到值得深入了解的工具。",
    filterKicker: "筛选",
    filterTitle: "缩小范围",
    searchLabel: "搜索 Skill",
    searchPlaceholder: "名称、场景或标签",
    categoryLabel: "类别",
    audienceLabel: "适用人群",
    allCategories: "全部类别",
    allAudiences: "全部人群",
    sourceTagsTitle: "高频来源",
    allSources: "全部来源",
    cardsKicker: "全部 Skills",
    cardsTitle: "浏览卡片列表",
    resultCount: (count) => `${count} 个 Skills`,
    emptyState: "没有找到匹配结果，试试其他关键词或筛选条件。",
    dataEmpty: "数据加载失败，请刷新页面后重试。如果问题仍然存在，请联系维护者。",
    audienceMeta: "适用人群",
    sourceMeta: "来源",
    missingSource: "待补充",
    githubLink: "查看 GitHub",
    feedbackKicker: "反馈",
    feedbackTitle: "想推荐新的 Skill？",
    feedbackCopy: "如果你发现值得收录的 AI Skill，可以通过 GitHub Discussions 留下项目链接和简要说明。",
    feedbackLink: "前往反馈",
  },
  en: {
    pageTitle: "SkillScope - Discover and Filter AI Skills",
    brandSubtitle: "AI Skills discovery directory",
    heroTitle: "Discover useful AI Skills",
    heroCopy: "A curated directory of AI Skills from GitHub, presented as compact cards so you can quickly compare capabilities, use cases, and sources.",
    filterKicker: "Filters",
    filterTitle: "Narrow results",
    searchLabel: "Search Skill",
    searchPlaceholder: "Name, use case, or tag",
    categoryLabel: "Category",
    audienceLabel: "Audience",
    allCategories: "All categories",
    allAudiences: "All audiences",
    sourceTagsTitle: "Frequent sources",
    allSources: "All sources",
    cardsKicker: "All Skills",
    cardsTitle: "Browse cards",
    resultCount: (count) => `${count} Skills`,
    emptyState: "No matching results. Try another keyword or filter.",
    dataEmpty: "Failed to load skill data. Please refresh the page. If the issue persists, contact the maintainer.",
    audienceMeta: "Audience",
    sourceMeta: "Source",
    missingSource: "To be added",
    githubLink: "View GitHub",
    feedbackKicker: "Feedback",
    feedbackTitle: "Want to suggest a Skill?",
    feedbackCopy: "If you find an AI Skill worth adding, leave its project link and a short note in GitHub Discussions.",
    feedbackLink: "Send feedback",
  },
};
let activeSource = "all";
let currentLanguage = "zh";

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function t(key, ...args) {
  const value = TRANSLATIONS[currentLanguage][key] || TRANSLATIONS.zh[key] || key;
  return typeof value === "function" ? value(...args) : value;
}

function localizedField(value) {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return value[currentLanguage] || value.zh || value.en || "";
  }

  return value || "";
}

function applyTranslations() {
  document.documentElement.lang = currentLanguage === "zh" ? "zh-CN" : "en";

  document.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = t(element.dataset.i18n);
  });

  document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
    element.placeholder = t(element.dataset.i18nPlaceholder);
  });

  languageButtons.forEach((button) => {
    button.classList.toggle("is-active", button.dataset.lang === currentLanguage);
  });

  updateSelectOptionLabels();
}

function formatCategory(value) {
  return CATEGORY_LABELS[currentLanguage][value] || value;
}

function formatAudience(value) {
  return AUDIENCE_LABELS[currentLanguage][value] || value;
}

function updateSelectOptionLabels() {
  [...categoryFilter.options].forEach((option) => {
    if (option.value !== "all") {
      option.textContent = formatCategory(option.value);
    }
  });

  [...audienceFilter.options].forEach((option) => {
    if (option.value !== "all") {
      option.textContent = formatAudience(option.value);
    }
  });
}

function syncCardHeights() {
  const cards = [...cardGrid.querySelectorAll(".card")];

  // Phase 1: Reset heights and collect layout measurements (reads)
  cards.forEach((card) => {
    card.style.height = "auto";
  });

  if (!cards.length) {
    return;
  }

  const rows = new Map();
  cards.forEach((card) => {
    const rowTop = Math.round(card.offsetTop);
    rows.set(rowTop, [...(rows.get(rowTop) || []), card]);
  });

  // Phase 2: Compute row heights (reads after reset)
  const rowHeights = new Map();
  rows.forEach((rowCards, rowTop) => {
    rowHeights.set(rowTop, Math.max(...rowCards.map((card) => card.offsetHeight)));
  });

  // Phase 3: Apply heights (writes)
  rows.forEach((rowCards, rowTop) => {
    const rowHeight = rowHeights.get(rowTop);
    rowCards.forEach((card) => {
      card.style.height = `${rowHeight}px`;
    });
  });
}

let resizePending = false;
function onResize() {
  if (resizePending) {
    return;
  }
  resizePending = true;
  requestAnimationFrame(() => {
    syncCardHeights();
    resizePending = false;
  });
}

function fillSelect(select, values) {
  values.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    select.appendChild(option);
  });
}

function getSourceOwner(source) {
  if (!source) {
    return "";
  }

  return String(source).replace(/^gitee:/, "").split("/")[0].trim();
}

function getFrequentSources() {
  const counts = new Map();

  skills.forEach((skill) => {
    const owner = getSourceOwner(skill.source);
    if (!owner) {
      return;
    }

    counts.set(owner, (counts.get(owner) || 0) + 1);
  });

  return [...counts.entries()]
    .filter(([owner, count]) => count > SOURCE_TAG_THRESHOLD || PINNED_SOURCE_TAGS.includes(owner))
    .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]));
}

function createSourceTag(label, count, value) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = `source-tag${activeSource === value ? " is-active" : ""}`;
  button.dataset.source = value;
  button.textContent = count ? `${label} ${count}` : label;
  return button;
}

function renderSourceTags() {
  const frequentSources = getFrequentSources();

  if (!frequentSources.length) {
    sourceTagsPanel.hidden = true;
    return;
  }

  sourceTagsPanel.hidden = false;
  sourceTags.innerHTML = "";
  sourceTags.appendChild(createSourceTag(t("allSources"), 0, "all"));

  frequentSources.forEach(([owner, count]) => {
    sourceTags.appendChild(createSourceTag(owner, count, owner));
  });
}

function createTag(tag) {
  const span = document.createElement("span");
  span.className = "tag";
  span.textContent = tag;
  return span;
}

function getLogoFallback(name) {
  return (name || "?").trim().charAt(0).toUpperCase();
}

function isSafeUrl(url) {
  return typeof url === "string" && /^https:\/\//i.test(url);
}

function createCard(skill) {
  const article = document.createElement("article");
  article.className = "card";

  const skillName = escapeHtml(localizedField(skill.name));
  const skillDescription = escapeHtml(localizedField(skill.description));
  const tags = Array.isArray(skill.tags) ? skill.tags.map(createTag) : [];
  const logoSrc = isSafeUrl(skill.logo_url) ? escapeHtml(skill.logo_url) : "";
  const logo = logoSrc
    ? `<img src="${logoSrc}" alt="${skillName} logo" loading="lazy">`
    : `<span>${getLogoFallback(skillName)}</span>`;

  article.innerHTML = `
    <div class="card-top">
      <div class="card-logo">${logo}</div>
      <div class="card-headline">
        <h3>${skillName}</h3>
        <p class="card-desc">${skillDescription}</p>
      </div>
      <span class="badge">${escapeHtml(formatCategory(skill.category))}</span>
    </div>
    <div class="meta-list">
      <p><strong>${t("audienceMeta")}</strong><span>${escapeHtml(formatAudience(skill.audience))}</span></p>
      <p><strong>${t("sourceMeta")}</strong><span>${escapeHtml(skill.source || t("missingSource"))}</span></p>
    </div>
  `;

  const footer = document.createElement("div");
  footer.className = "card-footer";

  const tagList = document.createElement("div");
  tagList.className = "tag-list";
  tags.forEach((tag) => tagList.appendChild(tag));

  const link = document.createElement("a");
  link.className = "card-link";
  link.href = skill.github_url;
  link.target = "_blank";
  link.rel = "noreferrer";
  link.textContent = t("githubLink");

  footer.appendChild(tagList);
  footer.appendChild(link);
  article.appendChild(footer);

  return article;
}

function filterSkills() {
  const query = searchInput.value.trim().toLowerCase();
  const category = categoryFilter.value;
  const audience = audienceFilter.value;

  return skills.filter((skill) => {
    const skillName = localizedField(skill.name);
    const skillDescription = localizedField(skill.description);
    const searchable = [
      skillName,
      skillDescription,
      skill.audience,
      skill.category,
      skill.source,
      ...(skill.tags || [])
    ]
      .join(" ")
      .toLowerCase();

    const matchesQuery = !query || searchable.includes(query);
    const matchesCategory = category === "all" || skill.category === category;
    const matchesAudience = audience === "all" || skill.audience === audience;
    const matchesSource = activeSource === "all" || getSourceOwner(skill.source) === activeSource;

    return matchesQuery && matchesCategory && matchesAudience && matchesSource;
  });
}

function renderCards() {
  cardGrid.innerHTML = "";

  if (!skills.length) {
    const emptyState = document.createElement("div");
    emptyState.className = "empty-state";
    emptyState.classList.add("is-data-error");
    emptyState.textContent = t("dataEmpty");
    cardGrid.appendChild(emptyState);
    resultCount.textContent = t("resultCount", 0);
    return;
  }

  const filtered = filterSkills();
  resultCount.textContent = t("resultCount", filtered.length);

  if (!filtered.length) {
    const emptyState = document.createElement("div");
    emptyState.className = "empty-state";
    emptyState.textContent = t("emptyState");
    cardGrid.appendChild(emptyState);
    return;
  }

  filtered.sort((left, right) => {
    if (left.category === right.category) {
      return localizedField(left.name).localeCompare(localizedField(right.name));
    }

    return left.category.localeCompare(right.category);
  });

  filtered.forEach((skill) => {
    cardGrid.appendChild(createCard(skill));
  });

  syncCardHeights();
}

fillSelect(categoryFilter, CATEGORY_OPTIONS);
fillSelect(audienceFilter, AUDIENCE_OPTIONS);
applyTranslations();
renderSourceTags();

searchInput.addEventListener("input", renderCards);
categoryFilter.addEventListener("change", renderCards);
audienceFilter.addEventListener("change", renderCards);
sourceTags.addEventListener("click", (event) => {
  const button = event.target.closest(".source-tag");
  if (!button) {
    return;
  }

  activeSource = button.dataset.source || "all";
  renderSourceTags();
  renderCards();
});
languageButtons.forEach((button) => {
  button.addEventListener("click", () => {
    currentLanguage = button.dataset.lang || "zh";
    applyTranslations();
    renderSourceTags();
    renderCards();
  });
});
window.addEventListener("resize", onResize);

renderCards();
