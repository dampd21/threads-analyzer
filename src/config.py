# src/config.py
import os
from datetime import datetime

# 환경변수에서 설정 읽기 (GitHub Actions에서 주입)
THREADS_USERNAME = os.getenv("THREADS_USERNAME", "just_followtax")
START_DATE = os.getenv("START_DATE", "2024-01-01")
END_DATE = os.getenv("END_DATE", "2024-12-31")
MAX_POSTS = int(os.getenv("MAX_POSTS", "50"))

# 위험 키워드/패턴 정의
RISK_PATTERNS = {
    "spam_keywords": [
        "기억해", "가자", "무조건", "보장", "100%", 
        "바로 가능", "쉽게", "DM 주세요", "댓글 달면",
        "선착순", "한정", "급구", "지금 바로"
    ],
    "exaggeration_keywords": [
        "업종만 괜찮으면", "조건만 맞으면", "누구나 가능",
        "무료로", "공짜", "대박", "확실", "무조건 된다"
    ],
    "broker_keywords": [
        "대행", "스팩업", "대신 해드림", "인증 가자",
        "자격증 취득", "빠르게 처리", "알선", "중개"
    ],
    "cta_patterns": [
        "링크 클릭", "프로필 링크", "연락주세요",
        "문의주세요", "상담", "카톡", "톡방"
    ]
}

# 중복 판단 기준
DUPLICATE_THRESHOLD = 0.8

# 출력 설정
OUTPUT_DIR = "output"
