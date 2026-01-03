# src/main.py
import asyncio
import pandas as pd
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import THREADS_USERNAME, START_DATE, END_DATE, SKIP_PINNED, OUTPUT_DIR
from scraper import ThreadsScraper
from analyzer import GuidelineAnalyzer, generate_summary


async def main():
    print("=" * 70)
    print("Threads 게시물 가이드라인 분석기 (Meta 공식 커뮤니티 규정 기반)")
    print("=" * 70)
    print(f"사용자: @{THREADS_USERNAME}")
    print(f"기간: {START_DATE} ~ {END_DATE}")
    print(f"상위 고정글 제외: {SKIP_PINNED}개")
    print("=" * 70)
    
    # 1. 크롤링 (고정글 제외)
    scraper = ThreadsScraper(
        username=THREADS_USERNAME,
        start_date=START_DATE,
        end_date=END_DATE,
        skip_pinned=SKIP_PINNED
    )
    posts = await scraper.scrape_posts()
    
    if not posts:
        print("[!] 수집된 게시물이 없습니다.")
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(os.path.join(OUTPUT_DIR, "summary.txt"), "w", encoding="utf-8") as f:
            f.write("수집된 게시물이 없습니다.\n")
        return
    
    # 2. 분석
    print(f"\n[*] {len(posts)}개 게시물을 Meta 커뮤니티 규정 기준으로 분석 중...")
    analyzer = GuidelineAnalyzer()
    results = analyzer.analyze_all_posts(posts)
    
    # 3. 결과 요약
    summary = generate_summary(results)
    
    print("\n" + "=" * 70)
    print("분석 결과 요약")
    print("=" * 70)
    print(f"총 게시물: {summary['total_posts']}개")
    print(f"🔴 매우 높음 (삭제 가능성): {summary['critical_count']}개")
    print(f"🟠 높음 (경고/제한 가능성): {summary['high_risk_count']}개")
    print(f"🟡 중간 (주의 필요): {summary['medium_risk_count']}개")
    print(f"🟢 낮음: {summary['low_risk_count']}개")
    print(f"✅ 안전: {summary['safe_count']}개")
    print(f"반복/중복: {summary['duplicate_count']}개")
    print(f"평균 위험 점수: {summary['average_risk_score']}/100")
    
    if summary['top_violations']:
        print("\n[주요 위반 유형]")
        for violation, count in summary['top_violations']:
            print(f"  • {violation}: {count}건")
    
    # 4. CSV 저장
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    df_data = []
    for r in results:
        violation_summary = "; ".join([
            f"{v['category']}/{v['subcategory']}" 
            for v in r.get("violations", [])
        ])
        policy_refs = "; ".join(r.get("official_policy_refs", []))
        
        df_data.append({
            "사용자명": r["username"],
            "날짜시간": r["datetime"],
            "게시물내용": r["text"],
            "링크": r["link"],
            "좋아요": r["likes"],
            "답글": r["replies"],
            "위험점수": r["risk_score"],
            "위험등급": r["risk_level"],
            "위반항목": violation_summary,
            "관련정책": policy_refs,
            "중복여부": "예" if r.get("is_duplicate", False) else "아니오",
            "권고사항": " | ".join(r.get("recommendations", []))
        })
    
    df = pd.DataFrame(df_data)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"threads_{THREADS_USERNAME}_{START_DATE}_to_{END_DATE}_{timestamp}"
    
    csv_path = os.path.join(OUTPUT_DIR, f"{filename}.csv")
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"\n✅ CSV 저장: {csv_path}")
    
    # 5. 요약 파일 저장
    summary_path = os.path.join(OUTPUT_DIR, "summary.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"# Threads 게시물 가이드라인 분석 결과\n\n")
        f.write(f"### 요약\n")
        f.write(f"- 총 게시물: **{summary['total_posts']}개**\n")
        f.write(f"- 🔴 매우 높음: **{summary['critical_count']}개**\n")
        f.write(f"- 🟠 높음: **{summary['high_risk_count']}개**\n")
        f.write(f"- 🟡 중간: **{summary['medium_risk_count']}개**\n")
        f.write(f"- 🟢 낮음: **{summary['low_risk_count']}개**\n")
        f.write(f"- ✅ 안전: **{summary['safe_count']}개**\n")
        f.write(f"- 반복/중복: **{summary['duplicate_count']}개**\n")
        f.write(f"- 평균 위험 점수: **{summary['average_risk_score']}/100**\n\n")
        
        if summary['top_violations']:
            f.write(f"### 주요 위반 유형\n")
            for violation, count in summary['top_violations']:
                f.write(f"- {violation}: {count}건\n")
            f.write("\n")
        
        critical_posts = sorted(results, key=lambda x: x["risk_score"], reverse=True)[:10]
        if critical_posts and critical_posts[0]["risk_score"] > 0:
            f.write(f"### ⚠️ 주의 필요 게시물 (상위 10개)\n\n")
            for i, post in enumerate(critical_posts, 1):
                if post["risk_score"] > 0:
                    text_preview = post["text"][:80].replace("\n", " ") + "..."
                    f.write(f"**{i}. {post['risk_level']}** (점수: {post['risk_score']})\n")
                    f.write(f"- 내용: {text_preview}\n")
                    f.write(f"- 날짜: {post['datetime'][:10] if post['datetime'] else 'N/A'}\n")
                    if post.get("recommendations"):
                        f.write(f"- 권고: {post['recommendations'][0][:80]}...\n")
                    f.write("\n")
    
    print(f"✅ 요약 저장: {summary_path}")
    print("\n분석 완료!")


if __name__ == "__main__":
    asyncio.run(main())
