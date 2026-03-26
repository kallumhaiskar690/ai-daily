import feedparser
from datetime import datetime
import os
import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

feeds = [
    "https://thegradient.pub/feed/",
    "https://www.technologyreview.com/feed/tag/artificial-intelligence/",
    "https://openai.com/blog/rss.xml"
]

articles = []

for url in feeds:
    feed = feedparser.parse(url)
    for entry in feed.entries[:2]:
        articles.append({
            "title": entry.title,
            "link": entry.link,
            "summary": entry.summary if "summary" in entry else ""
        })

articles = articles[:5]

text = "\n\n".join([f"{a['title']}\n{a['summary']}" for a in articles])

prompt = f"""
请从以下AI新闻中提炼最重要的3条，并用中文总结：
要求：
1. 每条一句话
2. 通俗易懂
3. 不要废话

内容：
{text}
"""

response = requests.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "model": "llama3-70b-8192",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }
)

result = response.json()
print(result)
summary = result["choices"][0]["message"]["content"]

today = datetime.now().strftime("%Y-%m-%d")

content = f"# AI日报 {today}\n\n{summary}\n\n"

for a in articles[:3]:
    content += f"\n🔗 {a['link']}\n"

os.makedirs("daily", exist_ok=True)

filename = f"daily/{today}.md"

with open(filename, "w") as f:
    f.write(content)

print("Done:", filename)
