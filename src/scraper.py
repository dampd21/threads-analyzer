# src/scraper.py - 수정 버전

import asyncio
import json
import os
from datetime import datetime
from dateutil import parser as date_parser
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

COOKIES_FILE = "threads_cookies.json"

class ThreadsScraper:
    def __init__(self, username: str, start_date: str, end_date: str, skip_pinned: int = 10):
        self.username = username.replace("@", "")
        self.base_url = f"https://www.threads.net/@{self.username}"
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        self.skip_pinned = skip_pinned
        self.posts = []
    
    async def login_and_save_cookies(self):
        """
        브라우저를 열어 수동 로그인 후 쿠키 저장
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,  # 브라우저 보이게
                args=['--no-sandbox']
            )
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800}
            )
            page = await context.new_page()
            
            print("=" * 50)
            print("Threads 로그인이 필요합니다")
            print("=" * 50)
            print("\n1. 브라우저에서 Threads에 로그인하세요")
            print("2. 로그인 완료 후 이 터미널에서 Enter를 누르세요\n")
            
            # Threads 로그인 페이지로 이동
            await page.goto("https://www.threads.net/login", wait_until="networkidle")
            
            # 사용자가 로그인할 때까지 대기
            input(">>> 로그인 완료 후 Enter를 누르세요...")
            
            # 쿠키 저장
            cookies = await context.cookies()
            with open(COOKIES_FILE, 'w') as f:
                json.dump(cookies, f, indent=2)
            
            print(f"\n✅ 쿠키 저장 완료: {COOKIES_FILE}")
            print(f"   저장된 쿠키: {len(cookies)}개")
            
            await browser.close()
    
    async def scrape_posts(self) -> list:
        """
        쿠키를 사용하여 로그인 상태로 크롤링
        """
        # 쿠키 파일 확인
        if not os.path.exists(COOKIES_FILE):
            print("[!] 쿠키 파일이 없습니다. 먼저 로그인이 필요합니다.")
            await self.login_and_save_cookies()
        
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
            
            # 저장된 쿠키 로드
            try:
                with open(COOKIES_FILE, 'r') as f:
                    cookies = json.load(f)
                await context.add_cookies(cookies)
                print(f"[*] 쿠키 로드 완료: {len(cookies)}개")
            except Exception as e:
                print(f"[!] 쿠키 로드 실패: {e}")
                print("[!] 다시 로그인합니다...")
                await browser.close()
                await self.login_and_save_cookies()
                return await self.scrape_posts()  # 재시도
            
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            """)
            
            page = await context.new_page()
            
            try:
                print(f"[*] {self.base_url} 접속 중...")
                await page.goto(self.base_url, wait_until="networkidle", timeout=60000)
                await page.wait_for_timeout(3000)
                
                # 로그인 상태 확인
                is_logged_in = await self._check_login_status(page)
                if not is_logged_in:
                    print("[!] 로그인 세션 만료. 다시 로그인합니다...")
                    await browser.close()
                    os.remove(COOKIES_FILE)
                    await self.login_and_save_cookies()
                    return await self.scrape_posts()
                
                print("[✓] 로그인 상태 확인됨")
                
                # 이하 기존 크롤링 로직...
                await page.click("body")
                await page.wait_for_timeout(1000)
                
                # 고정글 식별
                pinned_links = set()
                initial_posts = self._parse_all_posts_from_html(await page.content())
                print(f"[*] 초기 로드: {len(initial_posts)}개")
                
                for i, post in enumerate(initial_posts):
                    if i < self.skip_pinned and post.get("link"):
                        pinned_links.add(post["link"])
                        print(f"[PINNED] #{i+1}: {post['text'][:40]}...")
                
                print(f"[*] 고정글 {len(pinned_links)}개 식별 완료\n")
                
                # 스크롤하며 수집
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
                    
                    await page.wait_for_timeout(1500)
                    
                    all_posts = self._parse_all_posts_from_html(await page.content())
                    current_count = len(all_posts)
                    
                    if current_count > last_post_count:
                        print(f"[*] 새 게시물 로드: {last_post_count} → {current_count}")
                        stuck_count = 0
                        last_post_count = current_count
                    else:
                        stuck_count += 1
                        if stuck_count >= max_stuck:
                            print(f"\n[*] {max_stuck}회 연속 새 게시물 없음, 종료")
                            break
                    
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
    
    async def _check_login_status(self, page) -> bool:
        """
        로그인 상태 확인
        """
        try:
            # 로그인 버튼이 있으면 미로그인
            login_button = await page.query_selector('text="Log in"')
            if login_button:
                return False
            
            # 프로필 요소가 있으면 로그인됨
            content = await page.content()
            if 'data-pressable-container="true"' in content:
                return True
            
            return False
        except:
            return False
    
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


# 쿠키 로그인 전용 함수
async def login_only():
    """쿠키 저장만 수행"""
    scraper = ThreadsScraper("dummy", "2024-01-01", "2024-12-31")
    await scraper.login_and_save_cookies()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "login":
        asyncio.run(login_only())
    else:
        print("Usage: python scraper.py login")
