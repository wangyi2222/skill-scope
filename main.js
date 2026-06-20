const skills = window.skillsData || [];
const CATEGORY_OPTIONS = ["文档", "开发", "嵌入式", "工作流", "插件", "图像", "自动化", "研究"];
const AUDIENCE_OPTIONS = ["开发", "设计", "工作流"];

const searchInput = document.getElementById("searchInput");
const categoryFilter = document.getElementById("categoryFilter");
const audienceFilter = document.getElementById("audienceFilter");
const cardGrid = document.getElementById("cardGrid");
const resultCount = document.getElementById("resultCount");

function syncCardHeights() {
  const cards = [...cardGrid.querySelectorAll(".card")];

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

  rows.forEach((rowCards) => {
    const rowHeight = Math.max(...rowCards.map((card) => card.offsetHeight));
    rowCards.forEach((card) => {
      card.style.height = `${rowHeight}px`;
    });
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

function createTag(tag) {
  const span = document.createElement("span");
  span.className = "tag";
  span.textContent = tag;
  return span;
}

function getLogoFallback(name) {
  return (name || "?").trim().charAt(0).toUpperCase();
}

function createCard(skill) {
  const article = document.createElement("article");
  article.className = "card";

  const tags = Array.isArray(skill.tags) ? skill.tags.map(createTag) : [];
  const logo = skill.logo_url
    ? `<img src="${skill.logo_url}" alt="${skill.name} logo" loading="lazy">`
    : `<span>${getLogoFallback(skill.name)}</span>`;

  article.innerHTML = `
    <div class="card-top">
      <div class="card-logo">${logo}</div>
      <div class="card-headline">
        <h3>${skill.name}</h3>
        <p class="card-desc">${skill.description}</p>
      </div>
      <span class="badge">${skill.category}</span>
    </div>
    <div class="meta-list">
      <p><strong>适用人群</strong><span>${skill.audience}</span></p>
      <p><strong>来源</strong><span>${skill.source || "待补充"}</span></p>
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
  link.textContent = "查看 GitHub";

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
    const searchable = [
      skill.name,
      skill.description,
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

    return matchesQuery && matchesCategory && matchesAudience;
  });
}

function renderCards() {
  const filtered = filterSkills();
  cardGrid.innerHTML = "";
  resultCount.textContent = `${filtered.length} 个 Skills`;

  if (!filtered.length) {
    const emptyState = document.createElement("div");
    emptyState.className = "empty-state";
    emptyState.textContent = "没有找到匹配结果，试试其他关键词或筛选条件。";
    cardGrid.appendChild(emptyState);
    return;
  }

  filtered.sort((left, right) => {
    if (left.category === right.category) {
      return left.name.localeCompare(right.name);
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

searchInput.addEventListener("input", renderCards);
categoryFilter.addEventListener("change", renderCards);
audienceFilter.addEventListener("change", renderCards);
window.addEventListener("resize", syncCardHeights);

renderCards();
