# src/scraper.py
import asyncio
from datetime import datetime
from dateutil import parser as date_parser
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re

class ThreadsScraper:
    def __init__(self, username: str, start_date: str, end_date: str):
        self.username = username.replace("@", "")
        self.base_url = f"https://www.threads.net/@{self.username}"
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        self.posts = []
    
    async def scrape_posts(self, max_posts: int = 50) -> list:
        """
        Threads 프로필에서 게시물 수집 (기간 필터 적용)
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="ko-KR"
            )
            page = await context.new_page()
            
            try:
                print(f"[*] {self.base_url} 접속 중...")
                print(f"[*] 기간: {self.start_date.date()} ~ {self.end_date.date()}")
                
                await page.goto(self.base_url, wait_until="networkidle")
                await page.wait_for_timeout(3000)
                
                posts_data = []
                collected_links = set()
                last_height = 0
                scroll_count = 0
                max_scrolls = 30
                no_new_posts_count = 0
                
                while len(posts_data) < max_posts and scroll_count < max_scrolls:
                    # 페이지 HTML 가져오기
                    html_content = await page.content()
                    new_posts = self._parse_posts_from_html(html_content, collected_links)
                    
                    for post in new_posts:
                        # 기간 필터링
                        if self._is_within_date_range(post["datetime"]):
                            posts_data.append(post)
                            collected_links.add(post["link"])
                            print(f"[+] 게시물 {len(posts_data)}개 수집됨 | {post['datetime'][:10]}")
                        
                        # 기간보다 오래된 게시물이면 스크롤 중단
                        if self._is_before_start_date(post["datetime"]):
                            print(f"[*] 시작일 이전 게시물 도달, 수집 종료")
                            scroll_count = max_scrolls  # 루프 종료
                            break
                    
                    if len(new_posts) == 0:
                        no_new_posts_count += 1
                        if no_new_posts_count >= 3:
                            print("[*] 더 이상 새 게시물 없음, 종료")
                            break
                    else:
                        no_new_posts_count = 0
                    
                    # 스크롤
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(2000)
                    
                    new_height = await page.evaluate("document.body.scrollHeight")
                    if new_height == last_height:
                        scroll_count += 1
                    last_height = new_height
                    scroll_count += 1
                
                self.posts = posts_data[:max_posts]
                print(f"[완료] 총 {len(self.posts)}개 게시물 수집 (기간 내)")
                
            except Exception as e:
                print(f"[에러] 크롤링 실패: {e}")
            finally:
                await browser.close()
        
        return self.posts
    
    def _parse_posts_from_html(self, html: str, existing_links: set) -> list:
        """
        HTML에서 게시물 파싱
        """
        soup = BeautifulSoup(html, 'html.parser')
        posts = []
        
        # 게시물 컨테이너 찾기
        containers = soup.select('[data-pressable-container="true"]')
        
        for container in containers:
            try:
                post = self._extract_post_from_element(container)
                if post and post["link"] not in existing_links and post["text"]:
                    posts.append(post)
            except Exception as e:
                continue
        
        return posts
    
    def _extract_post_from_element(self, element) -> dict:
        """
        BeautifulSoup element에서 게시물 정보 추출
        """
        # 본문 텍스트 추출
        text_container = element.select_one('div.x1a6qonq')
        text_parts = []
        if text_container:
            for span in text_container.select('span > span'):
                if span.string:
                    text_parts.append(span.string.strip())
                elif span.get_text():
                    text_parts.append(span.get_text().strip())
        text_content = "\n".join(text_parts)
        
        # 시간 추출
        time_el = element.select_one('time[datetime]')
        post_time = time_el.get('datetime') if time_el else ""
        
        # 링크 추출
        link_el = element.select_one('a[href*="/post/"]')
        post_link = ""
        if link_el:
            href = link_el.get('href', '')
            post_link = f"https://www.threads.net{href}" if href.startswith('/') else href
        
        # 사용자명 추출
        username_el = element.select_one('a[href^="/@"] span span')
        username = username_el.get_text() if username_el else ""
        
        # 좋아요/답글/리포스트 수 추출
        stats = {"likes": 0, "replies": 0, "reposts": 0}
        stat_spans = element.select('div.x6s0dn4.x17zd0t2 span.x1o0tod')
        for i, span in enumerate(stat_spans[:3]):
            val = span.get_text().strip()
            if val.isdigit():
                if i == 0:
                    stats["likes"] = int(val)
                elif i == 1:
                    stats["replies"] = int(val)
                elif i == 2:
                    stats["reposts"] = int(val)
        
        if text_content.strip():
            return {
                "username": username,
                "text": text_content.strip(),
                "datetime": post_time,
                "link": post_link,
                "likes": stats["likes"],
                "replies": stats["replies"],
                "reposts": stats["reposts"],
                "scraped_at": datetime.now().isoformat()
            }
        
        return None
    
    def _is_within_date_range(self, datetime_str: str) -> bool:
        """
        게시물이 지정 기간 내인지 확인
        """
        if not datetime_str:
            return False
        try:
            post_date = date_parser.parse(datetime_str).replace(tzinfo=None)
            return self.start_date <= post_date <= self.end_date
        except:
            return False
    
    def _is_before_start_date(self, datetime_str: str) -> bool:
        """
        게시물이 시작일보다 이전인지 확인
        """
        if not datetime_str:
            return False
        try:
            post_date = date_parser.parse(datetime_str).replace(tzinfo=None)
            return post_date < self.start_date
        except:
            return False
