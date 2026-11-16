import datetime
import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator


def fetch_github_trending():
  """抓取 GitHub Trending 日榜数据"""
  url = "https://github.com/trending"
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
    print(f"抓取 GitHub Trending 失败: {e}")
    return []

  soup = BeautifulSoup(response.text, "html.parser")
  repo_list = []

  # 解析 GitHub Trending 页面的项目列表结构
  # GitHub 页面结构可能会微调，通过 article.Box-row 寻找每个项目卡片
  articles = soup.select("article.Box-row")

  for article in articles:
    try:
      # 获取项目名称
      title_elem = article.select_one("h2.h3 a")
      if not title_elem:
        continue
      repo_relative_url = title_elem["href"].strip()
      repo_name = repo_relative_url.lstrip("/")
      repo_url = f"https://github.com{repo_relative_url}"

      # 获取项目描述
      desc_elem = article.select_one("p")
      description = (
          desc_elem.get_text(strip=True) if desc_elem else "暂无描述"
      )

      # 获取编程语言
      lang_elem = article.select_one(
          "span[itemprop='programmingLanguage']"
      )
      language = lang_elem.get_text(strip=True) if lang_elem else "多语言 / 其它"

      # 获取获得的总 Star 数与今天新增 Star 数
      star_elems = article.select("a.Link--muted")
      total_stars = (
          star_elems[0].get_text(strip=True) if len(star_elems) > 0 else "未知"
      )
      today_stars_elem = article.select_one("span.d-inline-block.float-sm-right")
      today_stars = (
          today_stars_elem.get_text(strip=True)
          if today_stars_elem
          else "今日新增未知"
      )

      repo_list.append({
          "title": repo_name,
          "url": repo_url,
          "description": (
              f"【开发语言】{language} | 【Star数】{total_stars} |"
              f" 【今日新增】{today_stars}<br><br>{description}"
          ),
      })
    except Exception as e:
      print(f"解析单个项目时出错: {e}")
      continue

  return repo_list


def generate_rss(repo_list):
  """将抓取到的项目列表生成标准的 RSS XML 文件"""
  fg = FeedGenerator()
  fg.title("GitHub Trending Daily RSS")
  fg.link(href="https://github.com/trending", rel="alternate")
  fg.description(
      "Automatically generated GitHub Trending daily open source projects"
  )
  fg.language("en")

  # 设置 RSS 的最后更新时间
  fg.lastBuildDate(datetime.datetime.now(datetime.timezone.utc))

  for repo in repo_list:
    fe = fg.add_entry()
    fe.title(repo["title"])
    fe.link(href=repo["url"])
    fe.description(repo["description"])
    # 以当前时间作为该条目的发布时间
    fe.pubDate(datetime.datetime.now(datetime.timezone.utc))

  # 保存为 rss.xml
  fg.rss_file("rss.xml", pretty=True)
  print(f"成功生成 RSS 文件，共收录 {len(repo_list)} 个热门项目。")


if __name__ == "__main__":
  repos = fetch_github_trending()
  if repos:
    generate_rss(repos)
  else:
    print("未获取到任何项目，跳过生成。")