import feedparser
import requests
import os
from datetime import datetime
from pipelines.ai_daily.sources import FEEDS

def fetch(limit=1):
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


def summarize(text, template):
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
        return "⚠️ AI总结失败\n\n" + str(result)


def main():
    # 读 prompt
    with open("pipelines/ai_daily/prompt.txt", "r", encoding="utf-8") as f:
        template = f.read()

    # 抓数据
    articles = fetch(limit=1)

    # 拼内容
    text = "\n\n".join([f"{a['title']}\n{a['summary']}" for a in articles])

    # AI总结
    summary = summarize(text, template)

    # 写文件
    today = datetime.now().strftime("%Y-%m-%d")
    os.makedirs("daily", exist_ok=True)
    filename = f"daily/{today}.md"

    content = f"# AI日报 {today}\n\n{summary}\n\n"
    for a in articles[:3]:
        content += f"\n🔗 {a['link']}\n"

    with open(filename, "w") as f:
        f.write(content)

    print("Generated:", filename)


if __name__ == "__main__":
    main()
