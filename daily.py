import feedparser
from datetime import datetime
import os

feeds = [
    "https://thegradient.pub/feed/",
    "https://www.technologyreview.com/feed/tag/artificial-intelligence/",
    "https://openai.com/blog/rss.xml"
]

news = []

for url in feeds:
    feed = feedparser.parse(url)
    for entry in feed.entries[:2]:  # 每个源取2条，避免太多
        news.append(f"- {entry.title} ({entry.link})")

today = datetime.now().strftime("%Y-%m-%d")

content = f"# AI日报 {today}\n\n" + "\n".join(news)

# 👇 创建目录
os.makedirs("daily", exist_ok=True)

# 👇 用日期做文件名
filename = f"daily/{today}.md"

with open(filename, "w") as f:
    f.write(content)

print(f"Generated {filename}")
