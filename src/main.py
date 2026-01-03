# src/main.py
import asyncio
import pandas as pd
from datetime import datetime
import os
import sys

# 상위 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import THREADS_USERNAME, START_DATE, END_DATE, MAX_POSTS, OUTPUT_DIR
from scraper import ThreadsScraper
from analyzer import GuidelineAnalyzer, generate_summary


async def main():
    print("=" * 60)
    print("Threads 게시물 가이드라인 분석기")
    print("=" * 60)
    print(f"사용자: @{THREADS_USERNAME}")
    print(f"기간: {START_DATE} ~ {END_DATE}")
    print(f"최대 수집: {MAX_POSTS}개")
    print("=" * 60)
    
    # 1. 크롤링
    scraper = ThreadsScraper(
        username=THREADS_USERNAME,
        start_date=START_DATE,
        end_date=END_DATE
    )
    posts = await scraper.scrape_posts(max_posts=MAX_POSTS)
    
    if not posts:
        print("[!] 수집된 게시물이 없습니다.")
        # 빈 결과 파일 생성
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(os.path.join(OUTPUT_DIR, "summary.txt"), "w", encoding="utf-8") as f:
            f.write("수집된 게시물이 없습니다.\n")
        return
    
    # 2. 분석
    print(f"\n[*] {len(posts)}개 게시물 분석 중...")
    analyzer = GuidelineAnalyzer()
    results = analyzer.analyze_all_posts(posts)
    
    # 3. 결과 출력
    print("\n" + "=" * 60)
    print("분석 결과 요약")
    print("=" * 60)
    
    summary = generate_summary(results)
    print(f"총 게시물: {summary['total_posts']}개")
    print(f"🔴 높은 위험: {summary['high_risk_count']}개")
    print(f"🟡 중간 위험: {summary['medium_risk_count']}개")
    print(f"🟢 낮은 위험: {summary['low_risk_count']}개")
    print(f"✅ 안전: {summary['safe_count']}개")
    print(f"반복/중복: {summary['duplicate_count']}개")
    print(f"평균 위험 점수: {summary['average_risk_score']}/100")
    
    # 4. CSV 저장
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    df_data = []
    for r in results:
        df_data.append({
            "사용자명": r["username"],
            "날짜시간": r["datetime"],
            "게시물내용": r["text"],
            "링크": r["link"],
            "좋아요": r["likes"],
            "답글": r["replies"],
            "리포스트": r["reposts"],
            "위험점수": r["risk_score"],
            "위험등급": r["risk_level"],
            "스팸키워드": ", ".join(r["spam_detected"]),
            "과장표현": ", ".join(r["exaggeration_detected"]),
            "브로커표현": ", ".join(r["broker_detected"]),
            "유도표현": ", ".join(r["cta_detected"]),
            "중복여부": "예" if r.get("is_duplicate", False) else "아니오",
            "권고사항": " | ".join(r["recommendations"])
        })
    
    df = pd.DataFrame(df_data)
    
    # 파일명 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"threads_{THREADS_USERNAME}_{START_DATE}_{END_DATE}_{timestamp}"
    
    # UTF-8 CSV (범용)
    csv_path = os.path.join(OUTPUT_DIR, f"{filename}.csv")
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"\n✅ CSV 저장: {csv_path}")
    
    # 요약 파일 저장 (GitHub Actions Summary용)
    summary_path = os.path.join(OUTPUT_DIR, "summary.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"### 분석 결과\n")
        f.write(f"- 총 게시물: **{summary['total_posts']}개**\n")
        f.write(f"- 🔴 높은 위험: **{summary['high_risk_count']}개**\n")
        f.write(f"- 🟡 중간 위험: **{summary['medium_risk_count']}개**\n")
        f.write(f"- 🟢 낮은 위험: **{summary['low_risk_count']}개**\n")
        f.write(f"- ✅ 안전: **{summary['safe_count']}개**\n")
        f.write(f"- 반복/중복: **{summary['duplicate_count']}개**\n")
        f.write(f"- 평균 위험 점수: **{summary['average_risk_score']}/100**\n")
        
        # 위험한 게시물 상위 5개
        high_risk_posts = sorted(results, key=lambda x: x["risk_score"], reverse=True)[:5]
        if high_risk_posts and high_risk_posts[0]["risk_score"] > 0:
            f.write(f"\n### ⚠️ 주의 필요 게시물 (상위 5개)\n")
            for i, post in enumerate(high_risk_posts, 1):
                if post["risk_score"] > 0:
                    text_preview = post["text"][:50] + "..." if len(post["text"]) > 50 else post["text"]
                    f.write(f"{i}. **{post['risk_level']}** (점수: {post['risk_score']}) - {text_preview}\n")
    
    print(f"✅ 요약 저장: {summary_path}")
    print("\n분석 완료!")


if __name__ == "__main__":
    asyncio.run(main())
