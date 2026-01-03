#!/usr/bin/env python3
# run_local.py
# 로컬에서 쉽게 실행하기 위한 스크립트

import asyncio
import sys
import os

# src 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    print("=" * 60)
    print("Threads 가이드라인 분석기 (로컬 실행)")
    print("=" * 60)
    
    # 입력 받기
    print("\n[1] 사용자 정보 입력")
    username = input("Threads 아이디 (@ 제외, 기본값: just_followtax): ").strip()
    if not username:
        username = "just_followtax"
    
    print("\n[2] 분석 기간 설정")
    start_date = input("시작일 (YYYY-MM-DD, 기본값: 2024-01-01): ").strip()
    if not start_date:
        start_date = "2024-01-01"
    
    end_date = input("종료일 (YYYY-MM-DD, 기본값: 2024-12-31): ").strip()
    if not end_date:
        end_date = "2024-12-31"
    
    max_posts = input("최대 수집 게시물 수 (기본값: 30): ").strip()
    if not max_posts:
        max_posts = "30"
    
    print("\n[3] 수집 방식 선택")
    print("    1: 자동 크롤링 (Playwright)")
    print("    2: JSON 파일에서 로드")
    print("    3: HTML 파일에서 파싱")
    print("    4: 테스트 데이터로 실행")
    
    method = input("\n선택 (1/2/3/4, 기본값: 1): ").strip()
    if not method:
        method = "1"
    
    # 환경변수 설정
    os.environ["THREADS_USERNAME"] = username
    os.environ["START_DATE"] = start_date
    os.environ["END_DATE"] = end_date
    os.environ["MAX_POSTS"] = max_posts
    
    if method == "1":
        # 자동 크롤링
        from main import main as run_main
        asyncio.run(run_main())
    
    elif method == "2":
        # JSON 파일 로드
        filepath = input("JSON 파일 경로: ").strip()
        run_with_json(filepath)
    
    elif method == "3":
        # HTML 파일 파싱
        filepath = input("HTML 파일 경로: ").strip()
        run_with_html(filepath)
    
    else:
        # 테스트 데이터
        run_with_test_data()


def run_with_json(filepath: str):
    """JSON 파일에서 게시물 로드하여 분석"""
    from manual_input import ManualInputHandler
    from analyzer import GuidelineAnalyzer, generate_summary
    from config import OUTPUT_DIR
    import pandas as pd
    from datetime import datetime
    
    handler = ManualInputHandler()
    posts = handler.load_from_json(filepath)
    
    print(f"\n[*] {len(posts)}개 게시물 로드됨")
    
    analyzer = GuidelineAnalyzer()
    results = analyzer.analyze_all_posts(posts)
    
    # 결과 출력 및 저장
    save_results(results, OUTPUT_DIR)


def run_with_html(filepath: str):
    """HTML 파일에서 파싱하여 분석"""
    from html_parser import ThreadsHTMLParser
    from analyzer import GuidelineAnalyzer, generate_summary
    from config import OUTPUT_DIR
    
    parser = ThreadsHTMLParser()
    posts = parser.parse_from_file(filepath)
    
    print(f"\n[*] {len(posts)}개 게시물 파싱됨")
    
    analyzer = GuidelineAnalyzer()
    results = analyzer.analyze_all_posts(posts)
    
    save_results(results, OUTPUT_DIR)


def run_with_test_data():
    """테스트 데이터로 분석"""
    from analyzer import GuidelineAnalyzer, generate_summary
    from config import OUTPUT_DIR
    
    posts = [
        {
            "username": "just_followtax",
            "text": "기업 설립한지 얼마 안되고\n업종만 괜찮으면\n법인 스팩업 기억해\n\n- 여성기업인증과 소부장인증 가자 -",
            "datetime": "2024-11-15T10:30:00.000Z",
            "link": "https://threads.net/@just_followtax/post/1",
            "likes": 10,
            "replies": 5,
            "reposts": 2
        },
        {
            "username": "just_followtax",
            "text": "기업 설립한지 얼마 안되고\n업종만 괜찮으면\n법인 스팩업 기억해\n\n- 여성기업인증과 소부장인증 가자 -",
            "datetime": "2024-12-30T14:20:00.000Z",
            "link": "https://threads.net/@just_followtax/post/2",
            "likes": 8,
            "replies": 3,
            "reposts": 1
        },
        {
            "username": "just_followtax",
            "text": "세금이던 직원에게 줘야할 돈이던 빨리 줘야하는이유?\n세금 이자 대략 8퍼\n직원에게 대략 20퍼.\n심지어 비용처리도안됨",
            "datetime": "2025-01-01T12:01:49.000Z",
            "link": "https://threads.net/@just_followtax/post/3",
            "likes": 5,
            "replies": 0,
            "reposts": 1
        },
        {
            "username": "just_followtax",
            "text": "재밌는게 뭔지알아?\n마케팅을 잘하시는 분들 젊은분들일수록 강의 많이들어.\n반면\n아닌 사람들일수록 강의팔이라 욕한다.\n그러나 재밌는건 그 중에 노하우들 흡수가 진짜여.\n돈 낭비 아니다.",
            "datetime": "2025-01-01T05:53:47.000Z",
            "link": "https://threads.net/@just_followtax/post/4",
            "likes": 42,
            "replies": 22,
            "reposts": 1
        }
    ]
    
    print(f"\n[*] 테스트 데이터 {len(posts)}개 사용")
    
    analyzer = GuidelineAnalyzer()
    results = analyzer.analyze_all_posts(posts)
    
    save_results(results, OUTPUT_DIR)


def save_results(results: list, output_dir: str):
    """결과 저장 및 출력"""
    import pandas as pd
    from datetime import datetime
    from analyzer import generate_summary
    import os
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 요약 출력
    summary = generate_summary(results)
    print("\n" + "=" * 60)
    print("분석 결과")
    print("=" * 60)
    print(f"총 게시물: {summary['total_posts']}개")
    print(f"🔴 높은 위험: {summary['high_risk_count']}개")
    print(f"🟡 중간 위험: {summary['medium_risk_count']}개")
    print(f"🟢 낮은 위험: {summary['low_risk_count']}개")
    print(f"✅ 안전: {summary['safe_count']}개")
    print(f"반복/중복: {summary['duplicate_count']}개")
    print(f"평균 위험 점수: {summary['average_risk_score']}/100")
    
    # 상세 결과 출력
    print("\n" + "-" * 60)
    print("상세 분석")
    print("-" * 60)
    
    for i, r in enumerate(results, 1):
        print(f"\n[{i}] {r['risk_level']} (점수: {r['risk_score']})")
        print(f"    날짜: {r['datetime'][:10] if r['datetime'] else '알 수 없음'}")
        text_preview = r['text'][:50] + "..." if len(r['text']) > 50 else r['text']
        print(f"    내용: {text_preview}")
        if r['recommendations']:
            print(f"    권고: {r['recommendations'][0][:50]}...")
    
    # CSV 저장
    df_data = []
    for r in results:
        df_data.append({
            "날짜시간": r.get("datetime", ""),
            "게시물내용": r.get("text", ""),
            "위험점수": r.get("risk_score", 0),
            "위험등급": r.get("risk_level", ""),
            "스팸키워드": ", ".join(r.get("spam_detected", [])),
            "과장표현": ", ".join(r.get("exaggeration_detected", [])),
            "브로커표현": ", ".join(r.get("broker_detected", [])),
            "중복여부": "예" if r.get("is_duplicate") else "아니오",
            "권고사항": " | ".join(r.get("recommendations", []))
        })
    
    df = pd.DataFrame(df_data)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(output_dir, f"analysis_{timestamp}.csv")
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    
    print(f"\n✅ CSV 저장됨: {csv_path}")


if __name__ == "__main__":
    main()
