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


def call_ai(prompt):
    api_key = os.getenv("GROQ_API_KEY")

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
        print(result)
        return None


def main():
    # 读 prompt
    with open("pipelines/ai_daily/prompt.txt", "r", encoding="utf-8") as f:
        template = f.read()

    # 抓30条
    articles = fetch(limit=10)[:30]

    # 编号 + 拼内容
    text = "\n\n".join([
        f"[{i}] {a['title']}\n{a['summary']}"
        for i, a in enumerate(articles)
    ])

    prompt = template.replace("{content}", text)

    # AI处理
    result_text = call_ai(prompt)

    if not result_text:
        print("AI failed")
        return

    # 尝试解析JSON
    try:
        data = json.loads(result_text)
    except:
        print("JSON parse failed")
        print(result_text)
        return

    # 补 link
    for item in data:
        idx = item.get("index", 0)
        if idx < len(articles):
            item["link"] = articles[idx]["link"]

    today = datetime.now().strftime("%Y-%m-%d")
    os.makedirs("daily", exist_ok=True)

    # 🧾 Markdown（IM版）
    md_file = f"daily/{today}.md"
    with open(md_file, "w") as f:
        f.write(f"# 🧠 AI快讯（{today}）\n\n")

        for i, item in enumerate(data, 1):
            f.write(f"## {i}️⃣ {item['title']}\n")
            f.write(f"👉 {item['summary']}\n")
            f.write(f"📊 评分: {item['score']} | 分类: {item['category']}\n")
            f.write(f"🔗 {item['link']}\n\n")

    # 🧾 JSON（完整结构）
    json_file = f"daily/{today}.json"
    with open(json_file, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("Generated:", md_file, json_file)


if __name__ == "__main__":
    main()
