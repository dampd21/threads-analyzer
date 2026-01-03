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
        """
        Threads 프로필에서 기간 내 모든 게시물 수집
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-web-security'
                ]
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                locale="ko-KR",
                viewport={"width": 1920, "height": 1080}
            )
            
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                window.chrome = { runtime: {} };
            """)
            
            page = await context.new_page()
            
            try:
                print(f"[*] {self.base_url} 접속 중...")
                print(f"[*] 수집 기간: {self.start_date.date()} ~ {self.end_date.date()}")
                print(f"[*] 상위 고정글 {self.skip_pinned}개 제외")
                
                await page.goto(self.base_url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(5000)
                
                # 페이지 로드 확인
                page_content = await page.content()
                if "Log in" in page_content or "로그인" in page_content:
                    print("[!] 로그인 필요할 수 있음")
                
                # ========== 1단계: 고정글 식별 ==========
                pinned_links = set()
                initial_posts = self._parse_all_posts_from_html(await page.content())
                
                print(f"[*] 초기 로드: {len(initial_posts)}개 게시물")
                
                for i, post in enumerate(initial_posts):
                    if i < self.skip_pinned and post.get("link"):
                        pinned_links.add(post["link"])
                        print(f"[PINNED] #{i+1}: {post['text'][:40]}...")
                
                print(f"[*] 고정글 {len(pinned_links)}개 식별 완료\n")
                
                # ========== 2단계: 스크롤하면서 수집 ==========
                posts_data = []
                collected_links = set()
                consecutive_old = 0
                max_consecutive_old = 20
                scroll_count = 0
                max_scrolls = 500
                no_new_count = 0
                max_no_new = 20
                last_post_count = 0
                
                while scroll_count < max_scrolls:
                    scroll_count += 1
                    
                    # 현재 페이지의 모든 게시물 파싱
                    all_posts = self._parse_all_posts_from_html(await page.content())
                    current_post_count = len(all_posts)
                    
                    # 새로 로드된 게시물 처리
                    new_found = 0
                    for post in all_posts:
                        link = post.get("link", "")
                        if not link or link in collected_links or link in pinned_links:
                            continue
                        
                        collected_links.add(link)
                        if not post.get("text"):
                            continue
                        
                        new_found += 1
                        post_date = self._parse_date(post.get("datetime", ""))
                        
                        if post_date is None:
                            posts_data.append(post)
                            consecutive_old = 0
                            print(f"[+] ({len(posts_data)}): (날짜없음) {post['text'][:35]}...")
                            continue
                        
                        # 종료일보다 미래 → 스킵
                        if post_date > self.end_date:
                            consecutive_old = 0
                            continue
                        
                        # 시작일보다 과거 → 카운트
                        if post_date < self.start_date:
                            consecutive_old += 1
                            if consecutive_old >= max_consecutive_old:
                                print(f"\n[*] 시작일 이전 {max_consecutive_old}개 연속, 종료")
                                break
                            continue
                        
                        # 기간 내 → 수집
                        posts_data.append(post)
                        consecutive_old = 0
                        print(f"[+] ({len(posts_data)}): {post_date.date()} {post['text'][:35]}...")
                    
                    if consecutive_old >= max_consecutive_old:
                        break
                    
                    # 새 게시물 로드 여부 확인 (게시물 수 기준)
                    if current_post_count == last_post_count:
                        no_new_count += 1
                        if no_new_count >= max_no_new:
                            print(f"\n[*] 새 게시물 로드 안됨 {max_no_new}회, 종료")
                            break
                    else:
                        no_new_count = 0
                        last_post_count = current_post_count
                    
                    # ========== 핵심: 스크롤 ==========
                    await self._scroll_down(page)
                    
                    if scroll_count % 10 == 0:
                        print(f"[*] 스크롤 #{scroll_count} (수집: {len(posts_data)}, 로드: {current_post_count})")
                
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
    
    async def _scroll_down(self, page):
        """
        페이지 끝까지 스크롤해서 새 게시물 로드
        """
        # 방법 1: 키보드로 스크롤 (End 키)
        await page.keyboard.press("End")
        await page.wait_for_timeout(1000)
        
        # 방법 2: 마우스 휠 시뮬레이션
        await page.mouse.wheel(0, 3000)
        await page.wait_for_timeout(1000)
        
        # 방법 3: JavaScript로 스크롤
        await page.evaluate("""
            window.scrollTo({
                top: document.body.scrollHeight,
                behavior: 'smooth'
            });
        """)
        await page.wait_for_timeout(2000)
        
        # 방법 4: 추가로 더 스크롤
        for _ in range(3):
            await page.evaluate("window.scrollBy(0, 1000)")
            await page.wait_for_timeout(500)
        
        # 로드 대기
        await page.wait_for_timeout(random.randint(1500, 2500))
    
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
        
        stats = {"likes": 0, "replies": 0, "reposts": 0}
        
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
        if not datetime_str:
            return None
        try:
            return date_parser.parse(datetime_str).replace(tzinfo=None)
        except:
            return None
