import feedparser
import requests
import os
import json
from datetime import datetime

# 确保导入 pipelines/ai_daily/sources.py 中的 FEEDS
from pipelines.ai_daily.sources import FEEDS

def fetch(limit=10):
    """抓取 RSS 数据源中的文章"""
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
    """调用 AI 模型处理文章"""
    api_key = os.getenv("GROQ_API_KEY")

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",  # 使用的 AI 模型
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3
            }
        )

        # 检查响应状态
        if response.status_code != 200:
            print(f"Error: API request failed with status code {response.status_code}")
            print("Response:", response.text)
            return None

        result = response.json()

        # 输出调试信息：查看原始返回内容
        print("AI Raw Response: ", result)

        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        else:
            print("No valid choices found in response.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error during API request: {e}")
        return None


def main():
    # 读取 prompt.txt 文件
    with open("pipelines/ai_daily/prompt.txt", "r", encoding="utf-8") as f:
        template = f.read()

    # 抓取文章
    articles = fetch(limit=10)[:30]

    if not articles:
        print("No articles fetched.")
        return

    # 拼接文章内容
    text = "\n\n".join([
        f"[{i}] {a['title']}\n{a['summary']}"
        for i, a in enumerate(articles)
    ])

    prompt = template.replace("{content}", text)

    # 调用 AI 处理
    result_text = call_ai(prompt)

    if not result_text:
        print("AI failed")
        return

    # 清理格式：去除可能干扰的部分
    clean_text = result_text.strip()
    if clean_text.startswith("```json"):
        clean_text = clean_text[7:].strip()  # 去掉 JSON 标记
    if clean_text.endswith("```"):
        clean_text = clean_text[:-3].strip()  # 去掉 JSON 结尾标记

    # 尝试解析 JSON
    try:
        data = json.loads(clean_text)
    except json.JSONDecodeError as e:
        print(f"JSON parse failed: {e}")
        print("Response was:", result_text)  # 输出 AI 返回的内容
        return

    # 补充链接信息
    for item in data:
        idx = item.get("index", 0)
        if idx < len(articles):
            item["link"] = articles[idx]["link"]

    today = datetime.now().strftime("%Y-%m-%d")
    os.makedirs("daily", exist_ok=True)

    # 生成 Markdown 文件
    md_file = f"daily/{today}_ai_daily.md"
    with open(md_file, "w") as f:
        f.write(f"# 🧠 AI快讯（{today}）\n\n")
        for i, item in enumerate(data, 1):
            f.write(f"## {i}️⃣ {item['title']}\n")
            f.write(f"👉 {item['summary']}\n")
            f.write(f"📊 评分: {item['score']} | 分类: {item['category']}\n")
            f.write(f"🔗 {item['link']}\n\n")

    # 生成 JSON 文件
    json_file = f"daily/{today}_ai_daily.json"
    with open(json_file, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("Generated:", md_file, json_file)


if __name__ == "__main__":
    main()
