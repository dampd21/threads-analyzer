# src/scraper.py
import asyncio
from datetime import datetime
from dateutil import parser as date_parser
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import random

class ThreadsScraper:
    def __init__(self, username: str, start_date: str, end_date: str, skip_pinned: int = 10):
        self.username = username.replace("@", "")
        self.base_url = f"https://www.threads.net/@{self.username}"
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        self.skip_pinned = skip_pinned
        self.posts = []
    
    async def scrape_posts(self) -> list:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage'
                ]
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                locale="ko-KR",
                viewport={"width": 1920, "height": 1080}
            )
            
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            """)
            
            page = await context.new_page()
            
            try:
                print(f"[*] {self.base_url} 접속 중...")
                print(f"[*] 수집 기간: {self.start_date.date()} ~ {self.end_date.date()}")
                print(f"[*] 상위 고정글 {self.skip_pinned}개 제외")
                
                await page.goto(self.base_url, wait_until="networkidle", timeout=60000)
                await page.wait_for_timeout(5000)
                
                # 페이지 클릭해서 포커스 (스크롤 작동하게)
                await page.click("body")
                await page.wait_for_timeout(1000)
                
                # ========== 1단계: 고정글 식별 ==========
                pinned_links = set()
                initial_posts = self._parse_all_posts_from_html(await page.content())
                
                print(f"[*] 초기 로드: {len(initial_posts)}개")
                
                for i, post in enumerate(initial_posts):
                    if i < self.skip_pinned and post.get("link"):
                        pinned_links.add(post["link"])
                        print(f"[PINNED] #{i+1}: {post['text'][:40]}...")
                
                print(f"[*] 고정글 {len(pinned_links)}개 식별 완료\n")
                
                # ========== 2단계: Page Down으로 스크롤 ==========
                posts_data = []
                collected_links = set()
                consecutive_old = 0
                max_consecutive_old = 20
                scroll_count = 0
                max_scrolls = 500
                last_post_count = len(initial_posts)
                stuck_count = 0
                max_stuck = 30
                
                while scroll_count < max_scrolls:
                    scroll_count += 1
                    
                    # Page Down 키로 스크롤
                    for _ in range(5):
                        await page.keyboard.press("PageDown")
                        await page.wait_for_timeout(300)
                    
                    # 로드 대기
                    await page.wait_for_timeout(1500)
                    
                    # 현재 게시물 파싱
                    all_posts = self._parse_all_posts_from_html(await page.content())
                    current_count = len(all_posts)
                    
                    # 새 게시물 로드 확인
                    if current_count > last_post_count:
                        print(f"[*] 새 게시물 로드: {last_post_count} → {current_count}")
                        stuck_count = 0
                        last_post_count = current_count
                    else:
                        stuck_count += 1
                        if stuck_count >= max_stuck:
                            print(f"\n[*] {max_stuck}회 연속 새 게시물 없음, 종료")
                            break
                    
                    # 새 게시물 처리
                    for post in all_posts:
                        link = post.get("link", "")
                        if not link or link in collected_links or link in pinned_links:
                            continue
                        
                        collected_links.add(link)
                        if not post.get("text"):
                            continue
                        
                        post_date = self._parse_date(post.get("datetime", ""))
                        
                        if post_date is None:
                            posts_data.append(post)
                            consecutive_old = 0
                            print(f"[+] ({len(posts_data)}): (날짜없음) {post['text'][:35]}...")
                            continue
                        
                        if post_date > self.end_date:
                            consecutive_old = 0
                            continue
                        
                        if post_date < self.start_date:
                            consecutive_old += 1
                            if consecutive_old >= max_consecutive_old:
                                print(f"\n[*] 시작일 이전 {max_consecutive_old}개 연속, 종료")
                                break
                            continue
                        
                        posts_data.append(post)
                        consecutive_old = 0
                        print(f"[+] ({len(posts_data)}): {post_date.date()} {post['text'][:35]}...")
                    
                    if consecutive_old >= max_consecutive_old:
                        break
                    
                    if scroll_count % 20 == 0:
                        print(f"[*] 스크롤 #{scroll_count} (수집: {len(posts_data)}, 로드: {current_count})")
                
                self.posts = posts_data
                print(f"\n{'='*50}")
                print(f"[완료] 수집: {len(self.posts)}개")
                print(f"{'='*50}")
                
            except Exception as e:
                print(f"[에러] {e}")
                import traceback
                traceback.print_exc()
            finally:
                await browser.close()
        
        return self.posts
    
    def _parse_all_posts_from_html(self, html: str) -> list:
        soup = BeautifulSoup(html, 'html.parser')
        posts = []
        containers = soup.select('[data-pressable-container="true"]')
        for container in containers:
            try:
                post = self._extract_post_from_element(container)
                if post and post.get("link"):
                    posts.append(post)
            except:
                continue
        return posts
    
    def _extract_post_from_element(self, element) -> dict:
        text_container = element.select_one('div.x1a6qonq')
        text_parts = []
        if text_container:
            for span in text_container.select('span > span'):
                text = span.get_text(strip=True)
                if text:
                    text_parts.append(text)
        text_content = "\n".join(text_parts)
        
        time_el = element.select_one('time[datetime]')
        post_time = time_el.get('datetime') if time_el else ""
        
        link_el = element.select_one('a[href*="/post/"]')
        post_link = ""
        if link_el:
            href = link_el.get('href', '')
            post_link = f"https://www.threads.net{href}" if href.startswith('/') else href
        
        username_el = element.select_one('a[href^="/@"] span span')
        username = username_el.get_text(strip=True) if username_el else ""
        
        if text_content.strip():
            return {
                "username": username,
                "text": text_content.strip(),
                "datetime": post_time,
                "link": post_link,
                "likes": 0,
                "replies": 0,
                "reposts": 0,
                "scraped_at": datetime.now().isoformat()
            }
        return None
    
    def _parse_date(self, datetime_str: str):
        if not datetime_str:
            return None
        try:
            return date_parser.parse(datetime_str).replace(tzinfo=None)
        except:
            return None
