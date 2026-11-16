import datetime
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator


def fetch_trending_by_since(since_period):
  """根据时间跨度（daily/weekly/monthly）抓取 GitHub Trending 全语言榜单"""
  url = f"https://github.com/trending?since={since_period}"
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      ),
      "Accept-Language": "en-US,en;q=0.9",
  }

  try:
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
  except Exception as e:
    print(f"抓取 {since_period} 榜单失败: {e}")
    return []

  soup = BeautifulSoup(response.text, "html.parser")
  articles = soup.select("article.Box-row")
  repo_list = []

  for article in articles:
    try:
      title_elem = article.select_one("h2.h3 a")
      if not title_elem:
        continue
      repo_relative_url = title_elem["href"].strip()
      repo_name = repo_relative_url.lstrip("/")
      repo_url = f"https://github.com{repo_relative_url}"

      desc_elem = article.select_one("p")
      description = (
          desc_elem.get_text(strip=True) if desc_elem else "暂无描述"
      )

      lang_elem = article.select_one(
          "span[itemprop='programmingLanguage']"
      )
      lang = lang_elem.get_text(strip=True) if lang_elem else "多语言 / 其它"

      star_elems = article.select("a.Link--muted")
      total_stars = (
          star_elems[0].get_text(strip=True) if len(star_elems) > 0 else "未知"
      )

      today_stars_elem = article.select_one("span.d-inline-block.float-sm-right")
      today_stars = (
          today_stars_elem.get_text(strip=True)
          if today_stars_elem
          else "新增未知"
      )

      repo_list.append({
          "title": f"{repo_name} ({lang})",
          "url": repo_url,
          "description": (
              f"<b>开发语言</b>: {lang} | <b>Star数</b>: {total_stars} |"
              f" <b>周期涨幅</b>: {today_stars}<br><br>{description}"
          ),
      })
    except Exception as e:
      continue

  return repo_list


def generate_single_rss(filename, title, period_name):
  """生成指定周期的独立 RSS 文件"""
  print(f"正在生成 {period_name} 榜单...")
  repos = fetch_trending_by_since(period_name)

  fg = FeedGenerator()
  fg.title(title)
  fg.link(href=f"https://github.com/trending?since={period_name}", rel="alternate")
  fg.description(
      f"GitHub Trending {period_name.capitalize()} Open Source Projects"
  )
  fg.language("en")
  fg.lastBuildDate(datetime.datetime.now(datetime.timezone.utc))

  for repo in repos:
    fe = fg.add_entry()
    fe.title(repo["title"])
    fe.link(href=repo["url"])
    fe.description(repo["description"])
    fe.pubDate(datetime.datetime.now(datetime.timezone.utc))

  fg.rss_file(filename, pretty=True)
  print(f"成功生成: {filename}，共收录 {len(repos)} 个项目。")


if __name__ == "__main__":
  # 分别生成三个独立 RSS 文件
  generate_single_rss(
      "daily.xml", "GitHub Trending - Daily (日榜)", "daily"
  )
  generate_single_rss(
      "weekly.xml", "GitHub Trending - Weekly (周榜)", "weekly"
  )
  generate_single_rss(
      "monthly.xml", "GitHub Trending - Monthly (月榜)", "monthly"
  )
