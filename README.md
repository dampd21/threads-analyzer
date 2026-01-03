# Threads 가이드라인 분석기

Threads 게시물을 수집하고 Meta 커뮤니티 가이드라인 위반 가능성을 분석합니다.

## 🚀 GitHub Actions에서 실행

1. 이 저장소를 Fork 합니다
2. **Actions** 탭으로 이동
3. **Threads 게시물 가이드라인 분석** 워크플로우 선택
4. **Run workflow** 클릭
5. 입력값 설정:
   - `username`: 분석할 Threads 아이디 (@ 제외)
   - `start_date`: 시작일 (YYYY-MM-DD)
   - `end_date`: 종료일 (YYYY-MM-DD)
   - `max_posts`: 최대 수집 게시물 수

## 📊 출력 결과

- CSV 파일: 모든 게시물 + 분석 결과
- 위험 등급: 🔴 높음 / 🟡 중간 / 🟢 낮음 / ✅ 안전
- 탐지 항목: 스팸 키워드, 과장 표현, 대행/브로커 표현, CTA 패턴
- 중복 게시물 탐지

## ⚠️ 위험 키워드 예시

| 카테고리 | 키워드 |
|----------|--------|
| 스팸성 | 기억해, 가자, 무조건, 보장, DM 주세요 |
| 과장 | 업종만 괜찮으면, 누구나 가능, 쉽게 |
| 대행/브로커 | 스팩업, 대행, 인증 가자 |
| CTA | 링크 클릭, 문의주세요, 카톡 |

## 🔧 로컬 실행

```bash
# 설치
pip install -r requirements.txt
playwright install chromium

# 환경변수 설정
export THREADS_USERNAME="just_followtax"
export START_DATE="2024-11-01"
export END_DATE="2024-12-31"
export MAX_POSTS="30"



---

## 사용 방법

### GitHub Actions에서 실행

1. **저장소 생성** 후 위 파일들 업로드
2. **Actions** 탭 → **Threads 게시물 가이드라인 분석** 선택
3. **Run workflow** 클릭 후 입력:

| 입력 | 예시 |
|------|------|
| username | `just_followtax` |
| start_date | `2024-11-01` |
| end_date | `2024-12-31` |
| max_posts | `50` |

4. 실행 완료 후 **Artifacts**에서 CSV 다운로드

---

## CSV 출력 예시

| 사용자명 | 날짜시간 | 게시물내용 | 위험점수 | 위험등급 | 스팸키워드 | 중복여부 |
|----------|----------|-----------|----------|----------|-----------|----------|
| just_followtax | 2024-11-15T10:30:00Z | 기업 설립한지 얼마... | 75 | 🔴 높음 | 기억해, 가자 | 예 |
| just_followtax | 2024-12-01T14:20:00Z | 세금이던 직원에게... | 0 | ✅ 안전 | | 아니오 |
# 실행
python src/main.py
