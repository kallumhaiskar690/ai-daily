import feedparser
import requests
import os
import json
from datetime import datetime
from pipelines.ai_daily.sources import FEEDS

def fetch(limit=10):
    articles = []
    for url in FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:limit]:
            articles.append({
                "title": entry.title,
                "link": entry.link,
                "summary": entry.summary if "summary" in entry else ""
            })
    return articles


def summarize_and_select(text, template):
    api_key = os.getenv("GROQ_API_KEY")

    prompt = template.replace("{content}", text)

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3
        }
    )

    result = response.json()

    if "choices" in result:
        return result["choices"][0]["message"]["content"]
    else:
        return None


def main():
    # 读 prompt
    with open("pipelines/ai_daily/prompt.txt", "r", encoding="utf-8") as f:
        template = f.read()

    # 抓 30 条
    articles = fetch(limit=10)[:30]

    # 拼内容
    text = "\n\n".join([
        f"{i+1}. {a['title']}\n{a['summary']}"
        for i, a in enumerate(articles)
    ])

    # AI筛选 + 结构化输出
    result_text = summarize_and_select(text, template)

    today = datetime.now().strftime("%Y-%m-%d")
    os.makedirs("daily", exist_ok=True)

    # 👉 Markdown
    md_file = f"daily/{today}.md"
    with open(md_file, "w") as f:
        f.write(f"# 🧠 AI快讯（{today}）\n\n")
        f.write(result_text)

    # 👉 JSON（简单解析版）
    json_file = f"daily/{today}.json"

    data = []
    if result_text:
        lines = result_text.split("\n")
        current = {}

        for line in lines:
            if line.startswith("##"):
                if current:
                    data.append(current)
                current = {"title": line.replace("#", "").strip()}
            elif line.startswith("👉"):
                current["summary"] = line.replace("👉", "").strip()

        if current:
            data.append(current)

    # 补充链接（简单匹配）
    for i, item in enumerate(data):
        if i < len(articles):
            item["link"] = articles[i]["link"]

    with open(json_file, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("Generated:", md_file, json_file)


if __name__ == "__main__":
    main()
