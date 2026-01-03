# src/utils.py
import re
from datetime import datetime
from typing import List, Dict

def clean_text(text: str) -> str:
    """
    텍스트 정리 (불필요한 공백, 줄바꿈 정리)
    """
    if not text:
        return ""
    # 연속 공백 제거
    text = re.sub(r'\s+', ' ', text)
    # 앞뒤 공백 제거
    text = text.strip()
    return text

def extract_hashtags(text: str) -> List[str]:
    """
    텍스트에서 해시태그 추출
    """
    pattern = r'#(\w+)'
    return re.findall(pattern, text)

def extract_mentions(text: str) -> List[str]:
    """
    텍스트에서 멘션(@사용자) 추출
    """
    pattern = r'@(\w+)'
    return re.findall(pattern, text)

def extract_urls(text: str) -> List[str]:
    """
    텍스트에서 URL 추출
    """
    pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    return re.findall(pattern, text)

def format_datetime(datetime_str: str) -> str:
    """
    ISO 형식 날짜를 읽기 쉬운 형식으로 변환
    """
    if not datetime_str:
        return ""
    try:
        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return datetime_str

def calculate_text_stats(text: str) -> Dict:
    """
    텍스트 통계 계산
    """
    return {
        "char_count": len(text),
        "word_count": len(text.split()),
        "line_count": len(text.split('\n')),
        "hashtag_count": len(extract_hashtags(text)),
        "mention_count": len(extract_mentions(text)),
        "url_count": len(extract_urls(text))
    }

def is_short_url(url: str) -> bool:
    """
    단축 URL 여부 확인 (스팸 위험 요소)
    """
    short_domains = [
        'bit.ly', 'tinyurl.com', 'goo.gl', 't.co', 
        'ow.ly', 'is.gd', 'buff.ly', 'adf.ly',
        'bl.ink', 'lnkd.in', 'shorte.st'
    ]
    url_lower = url.lower()
    return any(domain in url_lower for domain in short_domains)
