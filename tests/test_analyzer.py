# tests/test_analyzer.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from analyzer import GuidelineAnalyzer, generate_summary

def test_basic_analysis():
    """
    기본 분석 테스트
    """
    analyzer = GuidelineAnalyzer()
    
    # 위험한 게시물
    risky_post = {
        "text": "기업 설립한지 얼마 안되고\n업종만 괜찮으면\n법인 스팩업 기억해\n\n- 여성기업인증과 소부장인증 가자 -",
        "datetime": "2024-11-15T10:30:00.000Z",
        "link": "https://threads.net/@test/post/1"
    }
    
    result = analyzer.analyze_post(risky_post)
    
    print("=== 위험 게시물 분석 ===")
    print(f"위험 점수: {result['risk_score']}")
    print(f"위험 등급: {result['risk_level']}")
    print(f"스팸 키워드: {result['spam_detected']}")
    print(f"과장 표현: {result['exaggeration_detected']}")
    print(f"브로커 표현: {result['broker_detected']}")
    print(f"권고사항: {result['recommendations']}")
    
    assert result['risk_score'] > 0, "위험 점수가 0보다 커야 함"
    assert "기억해" in result['spam_detected'], "기억해가 탐지되어야 함"
    assert "가자" in result['spam_detected'], "가자가 탐지되어야 함"
    print("✅ 위험 게시물 테스트 통과\n")
    
    # 안전한 게시물
    safe_post = {
        "text": "오늘 점심 뭐 먹지? 날씨가 좋네요.",
        "datetime": "2024-11-16T12:00:00.000Z",
        "link": "https://threads.net/@test/post/2"
    }
    
    result = analyzer.analyze_post(safe_post)
    
    print("=== 안전 게시물 분석 ===")
    print(f"위험 점수: {result['risk_score']}")
    print(f"위험 등급: {result['risk_level']}")
    
    assert result['risk_score'] == 0, "안전 게시물은 점수가 0이어야 함"
    assert "안전" in result['risk_level'], "안전 등급이어야 함"
    print("✅ 안전 게시물 테스트 통과\n")


def test_duplicate_detection():
    """
    중복 게시물 탐지 테스트
    """
    analyzer = GuidelineAnalyzer()
    
    posts = [
        {
            "text": "이것은 테스트 게시물입니다. 반복됩니다.",
            "datetime": "2024-11-15T10:00:00.000Z",
            "link": "https://threads.net/@test/post/1"
        },
        {
            "text": "이것은 테스트 게시물입니다. 반복됩니다.",
            "datetime": "2024-12-15T10:00:00.000Z",
            "link": "https://threads.net/@test/post/2"
        },
        {
            "text": "완전히 다른 게시물입니다.",
            "datetime": "2024-12-20T10:00:00.000Z",
            "link": "https://threads.net/@test/post/3"
        }
    ]
    
    results = analyzer.analyze_all_posts(posts)
    
    print("=== 중복 탐지 테스트 ===")
    for i, r in enumerate(results):
        print(f"게시물 {i+1}: 중복={r['is_duplicate']}, 점수={r['risk_score']}")
    
    # 첫 번째와 두 번째는 중복으로 탐지되어야 함
    assert results[0]['is_duplicate'] == True or results[1]['is_duplicate'] == True
    # 세 번째는 중복이 아니어야 함
    assert results[2]['is_duplicate'] == False
    print("✅ 중복 탐지 테스트 통과\n")


def test_summary_generation():
    """
    요약 생성 테스트
    """
    results = [
        {"risk_score": 80, "risk_level": "🔴 높음", "is_duplicate": True},
        {"risk_score": 45, "risk_level": "🟡 중간", "is_duplicate": False},
        {"risk_score": 15, "risk_level": "🟢 낮음", "is_duplicate": False},
        {"risk_score": 0, "risk_level": "✅ 안전", "is_duplicate": False},
    ]
    
    summary = generate_summary(results)
    
    print("=== 요약 생성 테스트 ===")
    print(f"총 게시물: {summary['total_posts']}")
    print(f"높은 위험: {summary['high_risk_count']}")
    print(f"중간 위험: {summary['medium_risk_count']}")
    print(f"평균 점수: {summary['average_risk_score']}")
    
    assert summary['total_posts'] == 4
    assert summary['high_risk_count'] == 1
    assert summary['medium_risk_count'] == 1
    assert summary['duplicate_count'] == 1
    print("✅ 요약 생성 테스트 통과\n")


if __name__ == "__main__":
    print("=" * 50)
    print("Threads 분석기 테스트")
    print("=" * 50 + "\n")
    
    test_basic_analysis()
    test_duplicate_detection()
    test_summary_generation()
    
    print("=" * 50)
    print("모든 테스트 통과! ✅")
    print("=" * 50)
