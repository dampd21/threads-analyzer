# src/html_parser.py
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional

class ThreadsHTMLParser:
    """
    Threads HTML을 직접 파싱하는 클래스
    (브라우저 개발자 도구에서 복사한 HTML 처리)
    """
    
    def parse_single_post(self, html: str) -> Optional[Dict]:
        """
        단일 게시물 HTML 파싱
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        try:
            # 게시물 컨테이너 찾기
            container = soup.select_one('[data-pressable-container="true"]')
            if not container:
                container = soup  # 전체가 컨테이너인 경우
            
            return self._extract_post_data(container)
        except Exception as e:
            print(f"[파싱 에러] {e}")
            return None
    
    def parse_multiple_posts(self, html: str) -> List[Dict]:
        """
        여러 게시물이 포함된 HTML 파싱
        """
        soup = BeautifulSoup(html, 'html.parser')
        posts = []
        
        containers = soup.select('[data-pressable-container="true"]')
        
        for container in containers:
            try:
                post = self._extract_post_data(container)
                if post and post.get('text'):
                    posts.append(post)
            except Exception as e:
                continue
        
        return posts
    
    def _extract_post_data(self, container) -> Optional[Dict]:
        """
        컨테이너에서 게시물 데이터 추출
        """
        # 1. 본문 텍스트 추출
        text_parts = []
        text_container = container.select_one('div.x1a6qonq')
        
        if text_container:
            # 각 span > span 에서 텍스트 추출
            for span in text_container.select('span > span'):
                text = span.get_text(strip=True)
                if text:
                    text_parts.append(text)
        
        text_content = '\n'.join(text_parts)
        
        # 2. 날짜/시간 추출
        time_el = container.select_one('time[datetime]')
        datetime_str = time_el.get('datetime', '') if time_el else ''
        
        # 3. 게시물 링크 추출
        link_el = container.select_one('a[href*="/post/"]')
        post_link = ''
        if link_el:
            href = link_el.get('href', '')
            if href.startswith('/'):
                post_link = f"https://www.threads.net{href}"
            else:
                post_link = href
        
        # 4. 사용자명 추출
        username = ''
        username_el = container.select_one('a[href^="/@"] span span')
        if username_el:
            username = username_el.get_text(strip=True)
        
        # 5. 좋아요/답글/리포스트 수 추출
        stats = {"likes": 0, "replies": 0, "reposts": 0}
        stat_spans = container.select('div.x6s0dn4.x17zd0t2 span.x1o0tod')
        
        for i, span in enumerate(stat_spans[:3]):
            val = span.get_text(strip=True)
            if val.isdigit():
                if i == 0:
                    stats["likes"] = int(val)
                elif i == 1:
                    stats["replies"] = int(val)
                elif i == 2:
                    stats["reposts"] = int(val)
        
        if text_content:
            return {
                "username": username,
                "text": text_content,
                "datetime": datetime_str,
                "link": post_link,
                "likes": stats["likes"],
                "replies": stats["replies"],
                "reposts": stats["reposts"],
                "scraped_at": datetime.now().isoformat()
            }
        
        return None
    
    def parse_from_file(self, filepath: str) -> List[Dict]:
        """
        HTML 파일에서 게시물 파싱
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            html = f.read()
        
        return self.parse_multiple_posts(html)


# 테스트용 함수
def test_parse():
    """
    제공된 HTML 예시로 테스트
    """
    # 예시 1
    html1 = """
    <div class="x78zum5 xdt5ytf"><div class="x9f619 x1n2onr6 x1ja2u2z">
    <!-- 첫 번째 HTML 예시 내용 -->
    </div></div>
    """
    
    parser = ThreadsHTMLParser()
    
    # 단일 파싱 테스트
    result = parser.parse_single_post(html1)
    if result:
        print("=== 파싱 결과 ===")
        print(f"사용자: {result['username']}")
        print(f"날짜: {result['datetime']}")
        print(f"내용: {result['text'][:100]}...")
        print(f"좋아요: {result['likes']}")
        print(f"링크: {result['link']}")


if __name__ == "__main__":
    test_parse()
