# src/config.py
import os

# 환경변수에서 설정 읽기
THREADS_USERNAME = os.getenv("THREADS_USERNAME", "just_followtax")
START_DATE = os.getenv("START_DATE", "2025-01-01")
END_DATE = os.getenv("END_DATE", "2026-12-31")
SKIP_PINNED = int(os.getenv("SKIP_PINNED", "10"))  # 상위 고정글 제외 개수

# 출력 설정
OUTPUT_DIR = "output"
