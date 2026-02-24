#!/usr/bin/env python3
"""
ColabTodo API 통합 테스트 + Race Condition 디버깅
실행: docker exec collab-todo-api python3 /app/run_tests.py
"""
import urllib.request
import urllib.error
import json
import time
import threading
import sys
import random
import string

BASE = "http://localhost:8000"
PASS_COUNT = 0
FAIL_COUNT = 0
RESULTS = []


def req(method, path, body=None, token=None):
    url = BASE + path
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(r, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, {}
    except Exception as e:
        return 0, {"error": str(e)}


def check(name, condition, detail=""):
    global PASS_COUNT, FAIL_COUNT
    status = "PASS" if condition else "FAIL"
    if condition:
        PASS_COUNT += 1
        print(f"  ✅ {name}")
    else:
        FAIL_COUNT += 1
        print(f"  ❌ {name}" + (f" — {detail}" if detail else ""))
    RESULTS.append((status, name, detail))


def rand_str(n=8):
    return ''.join(random.choices(string.ascii_lowercase, k=n))


# ─── 테스트 사용자 생성 ──────────────────────────────────────────
def make_test_user(suffix=""):
    email = f"test_{rand_str()}_{suffix}@test.com"
    pw = "TestPass1!"
    s, d = req("POST", "/api/auth/register", {
        "email": email, "password": pw, "name": f"테스트유저{suffix}", "department_name": "테스트팀"
    })
    return email, pw, d.get("access_token"), d.get("user_id"), s


# ═══════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("  ColabTodo API 통합 테스트")
print("="*60)


# ─── 1. 기본 연결 ───────────────────────────────────────────────
print("\n[1] 기본 연결 테스트")
s, d = req("GET", "/api/health")
check("Health check (200 or 404 허용)", s in (200, 404))

s, d = req("GET", "/api/users/departments/list")
check("부서 목록 조회 (인증 없이)", s == 200)


# ─── 2. 회원가입 / 로그인 ────────────────────────────────────────
print("\n[2] 인증 테스트")

# 회원가입
email, pw, token, uid, s = make_test_user("auth")
check("회원가입 성공 (200)", s == 200)
check("회원가입 시 access_token 반환", bool(token))

# 중복 이메일 회원가입
s2, d2 = req("POST", "/api/auth/register", {
    "email": email, "password": pw, "name": "중복", "department_name": "팀"
})
check("중복 이메일 거부 (409)", s2 == 409)

# 로그인
s, d = req("POST", "/api/auth/login", {"username": email, "password": pw})
check("로그인 성공 (200)", s == 200)
login_token = d.get("access_token")
check("로그인 시 access_token 반환", bool(login_token))
check("로그인 응답에 user_id 포함", "user_id" in d)
check("로그인 응답에 is_admin 포함", "is_admin" in d)

# 잘못된 비밀번호
s, d = req("POST", "/api/auth/login", {"username": email, "password": "wrongpw"})
check("잘못된 비밀번호 → 401", s == 401)

# 없는 사용자
s, d = req("POST", "/api/auth/login", {"username": "nobody@x.com", "password": "pw"})
check("존재하지 않는 사용자 → 401", s == 401)


# ─── 3. 인증 토큰 검증 ──────────────────────────────────────────
print("\n[3] 토큰 인증 테스트")

# 토큰 없이 보호 API 호출
s, d = req("GET", "/api/notifications/unread-count")
check("토큰 없이 보호 API → 401", s == 401)
check("토큰 없음 에러 메시지 확인", "인증" in d.get("detail", ""))

# 빈 토큰
s, d = req("GET", "/api/notifications/unread-count", token="")
check("빈 토큰 → 401", s == 401)

# 유효한 토큰
s, d = req("GET", "/api/notifications/unread-count", token=login_token)
check("유효한 토큰 → 200", s == 200)
check("unread-count 응답에 count 포함", "count" in d)

# 잘못된 JWT
s, d = req("GET", "/api/notifications/unread-count", token="invalid.jwt.token")
check("잘못된 JWT → 401", s == 401)

# 대시보드
s, d = req("GET", "/api/tasks/dashboard", token=login_token)
check("대시보드 API → 200", s == 200)
check("대시보드 응답에 total 포함", "total" in d)

# filter-presets
s, d = req("GET", "/api/users/me/filter-presets", token=login_token)
check("filter-presets → 200", s == 200)


# ─── 4. Race Condition 시뮬레이션 ────────────────────────────────
print("\n[4] Race Condition 시뮬레이션 (핵심 버그 검증)")
print("   로그인 전에 보낸 토큰 없는 요청이 로그인 후 401을 받아도")
print("   새 토큰에 영향을 주지 않는지 확인\n")

# 새 사용자 생성
email2, pw2, _, uid2, _ = make_test_user("race")

# 시나리오: 로그인 + 동시에 토큰 없는 stale 요청 발생
results_race = []

def stale_request():
    """토큰 없이 보호 API 호출 (stale request 시뮬레이션)"""
    time.sleep(0.05)  # 로그인 직전
    s, d = req("GET", "/api/tasks/dashboard")  # no token
    results_race.append(("stale", s, d))

def login_then_check():
    """로그인 후 즉시 보호 API 호출"""
    time.sleep(0.1)
    s, d = req("POST", "/api/auth/login", {"username": email2, "password": pw2})
    if s == 200:
        tok = d.get("access_token")
        time.sleep(0.05)  # stale 응답이 도착할 시간
        # 이 시점에서 새 토큰으로 API 호출
        s2, d2 = req("GET", "/api/notifications/unread-count", token=tok)
        s3, d3 = req("GET", "/api/tasks/dashboard", token=tok)
        results_race.append(("login", s, tok[:20] if tok else None))
        results_race.append(("notify", s2, d2))
        results_race.append(("dash", s3, d3))
    else:
        results_race.append(("login_fail", s, d))

# 병렬 실행
threads = [
    threading.Thread(target=stale_request),
    threading.Thread(target=stale_request),
    threading.Thread(target=stale_request),
    threading.Thread(target=login_then_check),
]
for t in threads:
    t.start()
for t in threads:
    t.join()

stale_results = [r for r in results_race if r[0] == "stale"]
login_result = next((r for r in results_race if r[0] == "login"), None)
notify_result = next((r for r in results_race if r[0] == "notify"), None)
dash_result = next((r for r in results_race if r[0] == "dash"), None)

check("Stale 요청 3개 모두 401 반환", all(r[1] == 401 for r in stale_results),
      f"stale results: {[r[1] for r in stale_results]}")
check("로그인 성공 (200)", login_result and login_result[1] == 200,
      f"login: {login_result}")
check("로그인 후 알림 API 200 (토큰 유효)", notify_result and notify_result[1] == 200,
      f"notify: {notify_result}")
check("로그인 후 대시보드 API 200 (토큰 유효)", dash_result and dash_result[1] == 200,
      f"dash: {dash_result}")

print(f"\n   Stale 요청 결과: {[r[1] for r in stale_results]}")
print(f"   로그인 결과: {login_result[1] if login_result else 'N/A'}")
print(f"   로그인 후 알림: {notify_result[1] if notify_result else 'N/A'}")
print(f"   로그인 후 대시보드: {dash_result[1] if dash_result else 'N/A'}")


# ─── 5. 사용자 관리 ─────────────────────────────────────────────
print("\n[5] 사용자 관리 테스트")

# 관리자 로그인
s, d = req("POST", "/api/auth/login", {"username": "skymean00", "password": "이윤서"})
admin_token = d.get("access_token") if s == 200 else None
check("관리자 로그인", s == 200, f"status={s}")
check("관리자 is_admin=True", d.get("is_admin") == True if s == 200 else False)

if admin_token:
    # 사용자 목록 (관리자)
    s, d = req("GET", "/api/users/admin/all", token=admin_token)
    check("관리자 전체 사용자 목록 조회", s == 200)
    users = d if isinstance(d, list) else []
    check("사용자 목록에 is_deleted=0만 포함", all(not u.get("is_deleted") for u in users))

    # 일반 사용자 목록 (전체 공개)
    s, d = req("GET", "/api/users/", token=login_token)
    check("일반 사용자 목록 조회 (200)", s == 200)

    # 소프트 삭제 테스트
    email3, pw3, tok3, uid3, s3 = make_test_user("softdel")
    check("소프트 삭제 대상 사용자 생성", s3 == 200)

    if uid3:
        # 삭제 전 로그인 가능 확인
        s, d = req("POST", "/api/auth/login", {"username": email3, "password": pw3})
        check("삭제 전 로그인 가능", s == 200)

        # 소프트 삭제
        s, d = req("DELETE", f"/api/users/admin/{uid3}", token=admin_token)
        check("소프트 삭제 성공 (200)", s == 200, f"resp={d}")

        # 삭제 후 로그인 불가
        s, d = req("POST", "/api/auth/login", {"username": email3, "password": pw3})
        check("삭제 후 로그인 차단", s == 401, f"got status={s}")

        # 삭제 사용자가 목록에서 제외되는지
        s, users_after = req("GET", "/api/users/admin/all", token=admin_token)
        if s == 200:
            deleted_in_list = any(u.get("id") == uid3 for u in (users_after if isinstance(users_after, list) else []))
            check("삭제된 사용자가 목록에서 제외됨", not deleted_in_list)

    # 자기 자신 삭제 불가
    s, d = req("DELETE", f"/api/users/admin/3", token=admin_token)
    check("자기 자신 삭제 불가 (400)", s == 400, f"resp={d}")


# ─── 6. 태스크 CRUD ──────────────────────────────────────────────
print("\n[6] 업무(Task) CRUD 테스트")

# 다른 사용자 생성 (담당자용)
email4, pw4, tok4, uid4, s4 = make_test_user("assignee")
check("담당자 사용자 생성", s4 == 200)

if login_token and uid4:
    # 업무 생성
    s, d = req("POST", "/api/tasks/", {
        "title": "테스트 업무",
        "content": "업무 내용입니다",
        "assignee_id": uid4,
        "priority": "normal",
        "due_date": "2026-12-31"
    }, token=login_token)
    check("업무 생성 (201 or 200)", s in (200, 201), f"status={s}, d={d}")
    task_id = d.get("id") if s in (200, 201) else None

    if task_id:
        # 업무 조회
        s, d = req("GET", f"/api/tasks/{task_id}", token=login_token)
        check("업무 단건 조회", s == 200)
        check("업무 제목 일치", d.get("title") == "테스트 업무")

        # 업무 목록
        s, d = req("GET", "/api/tasks/?section=assigned_by_me&page=1&page_size=20", token=login_token)
        check("내가 요청한 업무 목록 조회", s == 200)

        # 담당자 입장에서 조회
        s, d = req("GET", "/api/tasks/?section=assigned_to_me&page=1&page_size=20", token=tok4)
        check("담당자가 받은 업무 목록 조회", s == 200)

        # 상태 변경
        s, d = req("POST", f"/api/tasks/{task_id}/status",
                   {"status": "in_progress", "comment": "작업 시작"},
                   token=tok4)
        check("담당자가 상태 변경 (in_progress)", s == 200, f"d={d}")

        # 재배정 (담당자도 가능 - 이번에 추가된 기능)
        email5, pw5, tok5, uid5, s5 = make_test_user("newassignee")
        if uid5:
            s, d = req("POST", f"/api/tasks/{task_id}/reassign",
                       {"assignee_id": uid5}, token=tok4)
            check("담당자가 재배정 가능", s == 200, f"d={d}")

        # 업무 대시보드
        s, d = req("GET", "/api/tasks/dashboard", token=login_token)
        check("업무 통계 대시보드", s == 200)


# ─── 7. 알림 ────────────────────────────────────────────────────
print("\n[7] 알림 테스트")

if login_token:
    s, d = req("GET", "/api/notifications/unread-count", token=login_token)
    check("읽지 않은 알림 수 조회", s == 200)
    check("count 필드 존재", "count" in d)

    s, d = req("GET", "/api/notifications/?page=1&page_size=10", token=login_token)
    check("알림 목록 조회", s == 200)

    s, d = req("POST", "/api/notifications/read-all", token=login_token)
    check("전체 읽음 처리", s == 200)


# ─── 8. 필터 프리셋 ─────────────────────────────────────────────
print("\n[8] 필터 프리셋 테스트")

if login_token:
    s, d = req("GET", "/api/users/me/filter-presets", token=login_token)
    check("필터 프리셋 목록 조회", s == 200)

    # 프리셋 저장
    s, d = req("POST", "/api/users/me/filter-presets", {
        "name": "테스트 프리셋",
        "filters": {"status": "in_progress", "priority": "high"}
    }, token=login_token)
    check("필터 프리셋 저장", s in (200, 201), f"d={d}")


# ─── 9. 비밀번호 변경 ───────────────────────────────────────────
print("\n[9] 비밀번호 변경 테스트")

email6, pw6, tok6, uid6, _ = make_test_user("pwchange")
if tok6:
    # 잘못된 현재 비밀번호
    s, d = req("POST", "/api/auth/change-password",
               {"current_password": "wrongpw", "new_password": "NewPass2!"},
               token=tok6)
    check("잘못된 현재 비밀번호 거부 (400)", s == 400, f"d={d}")

    # 올바른 비밀번호 변경
    s, d = req("POST", "/api/auth/change-password",
               {"current_password": pw6, "new_password": "NewPass2!"},
               token=tok6)
    check("비밀번호 변경 성공", s == 200, f"d={d}")

    # 새 비밀번호로 로그인
    s, d = req("POST", "/api/auth/login", {"username": email6, "password": "NewPass2!"})
    check("변경된 비밀번호로 로그인 성공", s == 200, f"d={d}")

    # 이전 비밀번호로 로그인 불가
    s, d = req("POST", "/api/auth/login", {"username": email6, "password": pw6})
    check("이전 비밀번호 로그인 차단", s == 401)


# ─── 10. 버그 리포트 ─────────────────────────────────────────────
print("\n[10] 버그 리포트 테스트")

if login_token:
    s, d = req("POST", "/api/bugs/report", {
        "title": "테스트 버그",
        "description": "버그 내용",
        "severity": "low"
    }, token=login_token)
    check("버그 리포트 제출", s in (200, 201, 404), f"d={d}")

    if s in (200, 201) and admin_token:
        s2, d2 = req("GET", "/api/bugs/", token=admin_token)
        check("관리자 버그 목록 조회", s2 == 200, f"d={d2}")


# ═══════════════════════════════════════════════════════════════
print("\n" + "="*60)
print(f"  결과: {PASS_COUNT}개 통과 / {FAIL_COUNT}개 실패")
print(f"  합계: {PASS_COUNT + FAIL_COUNT}개 테스트")
print("="*60)

if FAIL_COUNT > 0:
    print("\n❌ 실패한 테스트:")
    for status, name, detail in RESULTS:
        if status == "FAIL":
            print(f"   - {name}" + (f": {detail}" if detail else ""))

sys.exit(0 if FAIL_COUNT == 0 else 1)
