import os
import json
import requests
from datetime import datetime
from ai_daily.fetch import fetch_articles
from ai_daily.sources import FEEDS

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
                "model": "llama-3.1-8b-instant",  # 使用的 AI 模型，可以根据需要替换
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3
            }
        )

        # 检查 API 响应状态
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


def process_articles(articles):
    """处理抓取到的文章并调用 AI"""
    # 将文章内容拼接成适合 AI 处理的格式
    text = "\n\n".join([f"[{i}] {a['title']}\n{a['summary']}" for i, a in enumerate(articles)])

    # 从 prompt.txt 中读取模板
    with open("ai_daily/prompt.txt", "r", encoding="utf-8") as f:
        prompt = f.read().replace("{content}", text)

    # 调用 AI 处理
    result_text = call_ai(prompt)

    if not result_text:
        print("AI failed to process the articles.")
        return None

    # 清理 AI 返回的内容，去掉多余的格式
    clean_text = result_text.strip()
    if clean_text.startswith("```json"):
        clean_text = clean_text[7:].strip()  # 去掉 JSON 标记
    if clean_text.endswith("```"):
        clean_text = clean_text[:-3].strip()  # 去掉 JSON 结尾标记

    # 尝试解析 JSON 数据
    try:
        data = json.loads(clean_text)
    except json.JSONDecodeError as e:
        print(f"JSON parse failed: {e}")
        print("Response was:", result_text)  # 输出 AI 返回的内容
        return None

    return data


def save_files(data, today):
    """生成 .md 和 .json 文件并保存"""
    os.makedirs("daily", exist_ok=True)

    # 生成 .md 文件
    md_file = f"daily/{today}_ai_daily.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(f"# 🧠 AI快讯 - {today}\n\n")
        for i, item in enumerate(data, 1):
            f.write(f"## {i}️⃣ {item['title']}\n")
            f.write(f"👉 {item['summary']}\n")
            f.write(f"📊 评分: {item['score']} | 分类: {item['category']}\n")
            f.write(f"🔗 {item['link']}\n\n")

    # 生成 .json 文件
    json_file = f"daily/{today}_ai_daily.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Generated files: {md_file}, {json_file}")


def main():
    # 获取当前日期
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"Running AI daily pipeline for {today}...")

    # 步骤 1: 获取文章
    articles = fetch_articles(limit=30)

    if not articles:
        print("No articles fetched.")
        return

    # 步骤 2: 处理文章，生成 AI 输出
    processed_data = process_articles(articles)

    if not processed_data:
        print("Failed to process articles with AI.")
        return

    # 步骤 3: 保存文件
    save_files(processed_data, today)


if __name__ == "__main__":
    main()
