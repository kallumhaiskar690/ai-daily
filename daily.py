import feedparser
from datetime import datetime

feeds = [
    "https://thegradient.pub/feed/",
    "https://www.technologyreview.com/feed/tag/artificial-intelligence/",
    "https://openai.com/blog/rss.xml"
]

news = []

for url in feeds:
    feed = feedparser.parse(url)
    for entry in feed.entries[:3]:
        news.append(f"- {entry.title} ({entry.link})")

today = datetime.now().strftime("%Y-%m-%d")

content = f"# AI日报 {today}\n\n" + "\n".join(news)

with open("daily.md", "w") as f:
    f.write(content)
