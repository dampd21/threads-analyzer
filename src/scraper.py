# src/scraper.py
import asyncio
from datetime import datetime
from dateutil import parser as date_parser
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

class ThreadsScraper:
    def __init__(self, username: str, start_date: str, end_date: str):
        self.username = username.replace("@", "")
        self.base_url = f"https://www.threads.net/@{self.username}"
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        self.posts = []
    
    async def scrape_posts(self) -> list:
        """
        Threads 프로필에서 기간 내 모든 게시물 수집
        시작일 이전 게시물이 나올 때까지 계속 스크롤
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="ko-KR",
                viewport={"width": 1280, "height": 800}
            )
            page = await context.new_page()
            
            try:
                print(f"[*] {self.base_url} 접속 중...")
                print(f"[*] 수집 기간: {self.start_date.date()} ~ {self.end_date.date()}")
                print(f"[*] 기간 내 모든 게시물을 수집합니다...")
                
                await page.goto(self.base_url, wait_until="networkidle", timeout=60000)
                await page.wait_for_timeout(5000)
                
                posts_data = []
                collected_links = set()
                last_height = 0
                no_change_count = 0
                reached_start_date = False
                
                while not reached_start_date:
                    # 페이지 HTML 가져오기
                    html_content = await page.content()
                    new_posts = self._parse_posts_from_html(html_content, collected_links)
                    
                    for post in new_posts:
                        post_date_str = post.get("datetime", "")
                        
                        # 날짜 파싱
                        post_date = self._parse_date(post_date_str)
                        
                        if post_date is None:
                            # 날짜 없으면 일단 수집
                            posts_data.append(post)
                            collected_links.add(post["link"])
                            print(f"[+] 수집: (날짜 없음) | {post['text'][:30]}...")
                            continue
                        
                        # 종료일보다 이후 → 스킵 (계속 스크롤)
                        if post_date > self.end_date:
                            continue
                        
                        # 시작일보다 이전 → 수집 중단
                        if post_date < self.start_date:
                            print(f"[*] 시작일({self.start_date.date()}) 이전 게시물 도달")
                            print(f"    → {post_date.date()} | {post['text'][:30]}...")
                            reached_start_date = True
                            break
                        
                        # 기간 내 → 수집
                        posts_data.append(post)
                        collected_links.add(post["link"])
                        print(f"[+] 수집 ({len(posts_data)}개): {post_date.date()} | {post['text'][:30]}...")
                    
                    if reached_start_date:
                        break
                    
                    # 스크롤
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(2000)
                    
                    # 스크롤 변화 감지
                    new_height = await page.evaluate("document.body.scrollHeight")
                    if new_height == last_height:
                        no_change_count += 1
                        if no_change_count >= 5:
                            print("[*] 더 이상 스크롤되지 않음, 수집 종료")
                            break
                    else:
                        no_change_count = 0
                    last_height = new_height
                
                self.posts = posts_data
                print(f"\n[완료] 총 {len(self.posts)}개 게시물 수집됨")
                
            except Exception as e:
                print(f"[에러] 크롤링 실패: {e}")
                import traceback
                traceback.print_exc()
            finally:
                await browser.close()
        
        return self.posts
    
    def _parse_posts_from_html(self, html: str, existing_links: set) -> list:
        """
        HTML에서 게시물 파싱
        """
        soup = BeautifulSoup(html, 'html.parser')
        posts = []
        
        containers = soup.select('[data-pressable-container="true"]')
        
        for container in containers:
            try:
                post = self._extract_post_from_element(container)
                if post and post.get("link") and post["link"] not in existing_links and post.get("text"):
                    posts.append(post)
            except:
                continue
        
        return posts
    
    def _extract_post_from_element(self, element) -> dict:
        """
        HTML 요소에서 게시물 정보 추출
        """
        # 본문 텍스트 추출
        text_container = element.select_one('div.x1a6qonq')
        text_parts = []
        if text_container:
            for span in text_container.select('span > span'):
                text = span.get_text(strip=True)
                if text:
                    text_parts.append(text)
        text_content = "\n".join(text_parts)
        
        # 날짜/시간 추출 (time 태그의 datetime 속성)
        time_el = element.select_one('time[datetime]')
        post_time = time_el.get('datetime') if time_el else ""
        
        # 게시물 링크 추출
        link_el = element.select_one('a[href*="/post/"]')
        post_link = ""
        if link_el:
            href = link_el.get('href', '')
            post_link = f"https://www.threads.net{href}" if href.startswith('/') else href
        
        # 사용자명 추출
        username_el = element.select_one('a[href^="/@"] span span')
        username = username_el.get_text(strip=True) if username_el else ""
        
        # 좋아요/답글/리포스트 수 추출
        stats = {"likes": 0, "replies": 0, "reposts": 0}
        stat_spans = element.select('div.x6s0dn4.x17zd0t2 span.x1o0tod')
        for i, span in enumerate(stat_spans[:3]):
            val = span.get_text(strip=True)
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
    
    def _parse_date(self, datetime_str: str):
        """
        datetime 문자열을 파싱하여 datetime 객체 반환
        실패 시 None 반환
        """
        if not datetime_str:
            return None
        try:
            return date_parser.parse(datetime_str).replace(tzinfo=None)
        except:
            return None
