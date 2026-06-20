import json
import re
from pathlib import Path


DATA_FILE = Path("data.js")

CATEGORY_CONTEXT = {
    "文档": "document workflows",
    "开发": "development workflows",
    "嵌入式": "embedded development workflows",
    "工作流": "AI agent workflows",
    "插件": "plugin and integration workflows",
    "图像": "image and visual creation workflows",
    "自动化": "automation workflows",
    "研究": "research workflows",
}

KEYWORD_PHRASES = [
    ("Claude Code", "Claude Code"),
    ("Codex CLI", "Codex CLI"),
    ("Claude Desktop", "Claude Desktop"),
    ("Gemini CLI", "Gemini CLI"),
    ("Visual Studio Code", "Visual Studio Code"),
    ("STM32", "STM32"),
    ("GD32", "GD32"),
    ("MSPM0", "MSPM0"),
    ("SolidWorks", "SolidWorks"),
    ("Simulink", "Simulink"),
    ("MATLAB", "MATLAB"),
    ("Multisim", "Multisim"),
    ("SPICE", "SPICE"),
    ("ngspice", "ngspice"),
    ("LaTeX", "LaTeX"),
    ("Excel", "Excel"),
    ("CSV", "CSV"),
    ("TSV", "TSV"),
    ("PDF", "PDF"),
    ("Word", "Word"),
    ("PowerPoint", "PowerPoint"),
    ("MCP", "MCP"),
    ("API", "API"),
    ("OAuth", "OAuth"),
    ("React", "React"),
    ("Tailwind", "Tailwind"),
    ("Cloudflare", "Cloudflare"),
    ("Workers", "Cloudflare Workers"),
    ("n8n", "n8n"),
    ("Kubernetes", "Kubernetes"),
    ("Docker", "Docker"),
    ("GitHub", "GitHub"),
    ("Git", "Git"),
    ("p5.js", "p5.js"),
    ("Slack", "Slack"),
    ("BLE", "BLE"),
    ("RTT", "RTT"),
    ("OCR", "OCR"),
]

ACTION_PHRASES = [
    ("创建", "creating"),
    ("读取", "reading"),
    ("编辑", "editing"),
    ("整理", "organizing"),
    ("生成", "generating"),
    ("分析", "analyzing"),
    ("管理", "managing"),
    ("配置", "configuring"),
    ("调用", "calling"),
    ("集成", "integrating"),
    ("构建", "building"),
    ("优化", "optimizing"),
    ("部署", "deploying"),
    ("测试", "testing"),
    ("调试", "debugging"),
    ("仿真", "simulating"),
    ("自动化", "automating"),
    ("批改", "reviewing"),
    ("转换", "converting"),
    ("抓取", "collecting"),
    ("推送", "delivering notifications"),
    ("规划", "planning"),
    ("撰写", "writing"),
    ("检查", "checking"),
]


def load_items() -> list[dict]:
    raw = DATA_FILE.read_text(encoding="utf-8-sig")
    match = re.search(r"window\.skillsData\s*=\s*(\[[\s\S]*\]);?\s*$", raw)
    if not match:
        raise RuntimeError("Unable to parse data.js")
    return json.loads(match.group(1))


def write_items(items: list[dict]) -> None:
    payload = "window.skillsData = " + json.dumps(items, ensure_ascii=False, indent=2) + ";\n"
    DATA_FILE.write_text(payload, encoding="utf-8")


def source_slug(item: dict) -> str:
    source = str(item.get("source") or item.get("github_url") or "")
    parts = [part for part in re.split(r"[/#?]+", source) if part]
    return parts[-1] if parts else "skill"


def readable_name(value: str, item: dict) -> str:
    if value and not re.search(r"[\u4e00-\u9fff]", value):
        return value
    slug = source_slug(item)
    return slug.replace("_", "-")


def extract_terms(text: str, item: dict) -> list[str]:
    terms: list[str] = []
    for keyword, label in KEYWORD_PHRASES:
        if keyword.lower() in text.lower() and label not in terms:
            terms.append(label)
    for tag in item.get("tags") or []:
        tag_text = str(tag).strip()
        if tag_text and not re.search(r"[\u4e00-\u9fff]", tag_text) and tag_text not in terms:
            terms.append(tag_text)
    return terms[:4]


def extract_actions(text: str) -> list[str]:
    actions: list[str] = []
    for keyword, phrase in ACTION_PHRASES:
        if keyword in text and phrase not in actions:
            actions.append(phrase)
    return actions[:3]


def english_description(item: dict) -> str:
    description = item.get("description")
    zh = description.get("zh", "") if isinstance(description, dict) else str(description or "")
    name_value = item.get("name")
    zh_name = name_value.get("zh", "") if isinstance(name_value, dict) else str(name_value or "")
    name = readable_name(zh_name, item)
    category = CATEGORY_CONTEXT.get(str(item.get("category") or ""), "AI agent workflows")
    terms = extract_terms(f"{zh} {name}", item)
    actions = extract_actions(zh)

    if terms and actions:
        return f"Helps with {', '.join(actions)} {', '.join(terms)} for {category}."
    if terms:
        return f"Helps users work with {', '.join(terms)} in {category}."
    if actions:
        return f"Helps with {', '.join(actions)} tasks in {category}."
    return f"Helps users handle {name} related tasks in {category}."


def main() -> None:
    items = load_items()
    filled_names = 0
    filled_descriptions = 0

    for item in items:
        name = item.get("name")
        if isinstance(name, dict) and not str(name.get("en") or "").strip():
            name["en"] = readable_name(str(name.get("zh") or ""), item)
            filled_names += 1

        description = item.get("description")
        if isinstance(description, dict) and not str(description.get("en") or "").strip():
            description["en"] = english_description(item)
            filled_descriptions += 1

    write_items(items)
    print(f"filled_names={filled_names}")
    print(f"filled_descriptions={filled_descriptions}")


if __name__ == "__main__":
    main()
