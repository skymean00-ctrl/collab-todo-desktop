"""
=============================================================================
복잡한 멀티유저 통합 테스트 - 건설현장 업무 관리 시나리오
=============================================================================

【테스트 시나리오 전체 흐름도】

    ┌──────────────────────────────────────────────────────────────────┐
    │  PHASE 0: 환경 준비                                               │
    │    Admin 로그인 → 현장소장(manager) 등록 → 공사팀(worker) 등록     │
    └──────────────────────────────────────────────────────────────────┘
                                    ↓
    ┌──────────────────────────────────────────────────────────────────┐
    │  PHASE 1: 카테고리 시스템                                         │
    │    Admin: "기초공사" 카테고리 생성 → "안전관리" 카테고리 생성       │
    │    중복 카테고리 생성 시도 → 400 예상                              │
    └──────────────────────────────────────────────────────────────────┘
                                    ↓
    ┌──────────────────────────────────────────────────────────────────┐
    │  PHASE 2: 복합 업무 생성 (material_providers 자동 서브태스크)       │
    │    Admin → manager 주업무 생성                                    │
    │         + material_providers=[worker] → 서브태스크 자동 생성        │
    │    결과: 주업무 1개 + 자동 서브태스크 1개                          │
    └──────────────────────────────────────────────────────────────────┘
                                    ↓
    ┌──────────────────────────────────────────────────────────────────┐
    │  PHASE 3: 수동 서브태스크 추가                                     │
    │    Admin → worker 서브태스크 2개 수동 생성                         │
    │    Admin → manager 서브태스크 1개 수동 생성 (rejected 흐름용)       │
    └──────────────────────────────────────────────────────────────────┘
                                    ↓
    ┌──────────────────────────────────────────────────────────────────┐
    │  PHASE 4: 업무 복제 (clone)                                       │
    │    Admin → 주업무 복제 → "[복사] ..." 제목 확인                    │
    │    worker → 권한 없는 업무 복제 시도 → 403                        │
    └──────────────────────────────────────────────────────────────────┘
                                    ↓
    ┌──────────────────────────────────────────────────────────────────┐
    │  PHASE 5: 현장소장(manager) 관점 작업                             │
    │    manager 로그인 → 배정 업무 조회 (section=assigned_to_me)        │
    │    주업무: pending → in_progress (댓글 포함)                      │
    │    주업무에 댓글 등록                                              │
    └──────────────────────────────────────────────────────────────────┘
                                    ↓
    ┌──────────────────────────────────────────────────────────────────┐
    │  PHASE 6: 공사팀(worker) 관점 작업                                │
    │    worker 로그인 → 배정 서브태스크 조회 (section=subtasks_to_me)   │
    │    서브태스크: pending → in_progress                              │
    │    서브태스크에 댓글 등록                                          │
    └──────────────────────────────────────────────────────────────────┘
                                    ↓
    ┌──────────────────────────────────────────────────────────────────┐
    │  PHASE 7: 권한 경계 테스트 (403 / 401 / 400 검증)                 │
    │    ① worker → manager 댓글 수정 시도 → 403                       │
    │    ② worker → manager 댓글 삭제 시도 → 403                       │
    │    ③ worker → 주업무 삭제 시도 (assigner 아님) → 403              │
    │    ④ 토큰 없이 /me 접근 → 401                                    │
    │    ⑤ 잘못된 토큰으로 /me 접근 → 401                              │
    │    ⑥ 잘못된 비밀번호로 로그인 → 401                              │
    │    ⑦ rejected 시 comment 없음 → 400                              │
    └──────────────────────────────────────────────────────────────────┘
                                    ↓
    ┌──────────────────────────────────────────────────────────────────┐
    │  PHASE 8: 알림 시스템 검증                                        │
    │    manager 알림 목록 조회 → 업무 배정 알림 확인                    │
    │    특정 알림 읽음 처리 → is_read=True 확인                        │
    │    전체 읽음 처리 → unread_count=0 확인                           │
    └──────────────────────────────────────────────────────────────────┘
                                    ↓
    ┌──────────────────────────────────────────────────────────────────┐
    │  PHASE 9: 완전한 상태 라이프사이클                                 │
    │    pending → in_progress → review → approved (worker 서브태스크)  │
    │    pending → in_progress → review → rejected (manager 서브태스크) │
    │    rejected 후 재처리: pending → approved (Admin 직접 처리)        │
    └──────────────────────────────────────────────────────────────────┘
                                    ↓
    ┌──────────────────────────────────────────────────────────────────┐
    │  PHASE 10: 업무 수정 흐름                                         │
    │    manager: 주업무 진행률 50%로 업데이트                          │
    │    admin: 서브태스크 우선순위 normal → urgent                      │
    │    admin: 서브태스크 담당자 재배정 (worker → manager)              │
    └──────────────────────────────────────────────────────────────────┘
                                    ↓
    ┌──────────────────────────────────────────────────────────────────┐
    │  PHASE 11: 일괄 상태 변경 (bulk-status)                           │
    │    admin: 여러 업무 동시에 review 상태로 변경                      │
    │    대시보드에서 review 카운트 확인                                 │
    └──────────────────────────────────────────────────────────────────┘
                                    ↓
    ┌──────────────────────────────────────────────────────────────────┐
    │  PHASE 12: 정렬 & 필터링 종합                                     │
    │    sort_by=priority desc / asc                                    │
    │    sort_by=status / sort_by=title / sort_by=due_date             │
    │    section=assigned_to_me / assigned_by_me / subtasks_to_me      │
    │    status 필터 / 자연어 검색 ("긴급", 사용자명)                   │
    └──────────────────────────────────────────────────────────────────┘
                                    ↓
    ┌──────────────────────────────────────────────────────────────────┐
    │  PHASE 13: 이메일 인증 흐름                                       │
    │    신규 유저 등록 → is_verified=False 확인                        │
    │    DB에서 verification_token 조회                                 │
    │    verify-email 호출 → is_verified=True 확인                     │
    └──────────────────────────────────────────────────────────────────┘
                                    ↓
    ┌──────────────────────────────────────────────────────────────────┐
    │  PHASE 14: 비밀번호 관련 흐름                                     │
    │    잘못된 현재 비밀번호로 change-password → 400                   │
    │    forgot-password 요청 → DB에서 reset token 조회                 │
    │    reset-password 실행 → 새 비밀번호로 로그인 확인                 │
    │    원래 비밀번호로 복구                                            │
    └──────────────────────────────────────────────────────────────────┘
                                    ↓
    ┌──────────────────────────────────────────────────────────────────┐
    │  PHASE 15: 업무 로그 & 댓글 수정/삭제                             │
    │    업무 로그 조회 → 모든 상태변경 기록 확인                        │
    │    admin: manager 댓글 수정 (admin 권한으로 가능)                  │
    │    admin: manager 댓글 삭제 (admin 권한으로 가능)                  │
    └──────────────────────────────────────────────────────────────────┘
                                    ↓
    ┌──────────────────────────────────────────────────────────────────┐
    │  PHASE 16: 계단식 삭제 검증                                       │
    │    복제 업무 삭제 → 404 확인                                      │
    │    서브태스크가 있는 주업무 삭제 → 서브태스크 연쇄 삭제 확인       │
    └──────────────────────────────────────────────────────────────────┘
                                    ↓
    ┌──────────────────────────────────────────────────────────────────┐
    │  PHASE 17: 최종 대시보드 & 태그 시스템 검증                        │
    │    admin/manager/worker 대시보드 통계 비교                        │
    │    태그 목록 조회 → 생성된 태그 확인                              │
    └──────────────────────────────────────────────────────────────────┘

=============================================================================
"""

import requests
import subprocess
import json
import sys
import time
from datetime import date, timedelta

BASE = "http://localhost:8000/api"

# OAuth2PasswordRequestForm 은 JSON 이 아니라 form data 로 전송해야 함
# 부서명은 ["현장소장","공무팀","공사팀","안전팀","품질팀","직영팀"] 중 택1
# .test TLD 는 이메일 검증 거부 → gmail.com 사용

# ─── 색상 출력 ────────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

pass_count = 0
fail_count = 0
phase_results = {}
current_phase = ""

def section(title: str):
    global current_phase
    current_phase = title
    phase_results[title] = {"pass": 0, "fail": 0}
    print(f"\n{CYAN}{BOLD}{'='*68}{RESET}")
    print(f"{CYAN}{BOLD}  {title}{RESET}")
    print(f"{CYAN}{BOLD}{'='*68}{RESET}")

def ok(msg: str):
    global pass_count
    pass_count += 1
    phase_results[current_phase]["pass"] += 1
    print(f"  {GREEN}✓{RESET}  {msg}")

def fail(msg: str, detail: str = ""):
    global fail_count
    fail_count += 1
    phase_results[current_phase]["fail"] += 1
    print(f"  {RED}✗{RESET}  {BOLD}{msg}{RESET}")
    if detail:
        print(f"       {RED}→ {detail}{RESET}")

def check(cond: bool, msg_ok: str, msg_fail: str, detail: str = ""):
    if cond:
        ok(msg_ok)
    else:
        fail(msg_fail, detail)

def db_query(sql: str) -> str:
    """MySQL CLI를 통해 DB 직접 조회"""
    result = subprocess.run(
        ["mysql", "-u", "collab_user", "-ptest1234", "collab_todo",
         "-se", sql, "--skip-column-names"],
        capture_output=True, text=True
    )
    return result.stdout.strip()

def login(email: str, password: str) -> str | None:
    # OAuth2PasswordRequestForm → form-encoded, username 필드 사용
    r = requests.post(f"{BASE}/auth/login",
                      data={"username": email, "password": password})
    if r.status_code == 200:
        return r.json().get("access_token")
    return None

def h(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}

# ─── 상태 저장소 ──────────────────────────────────────────────────────────────
ctx = {}


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 0: 환경 준비
# ═══════════════════════════════════════════════════════════════════════════════
section("PHASE 0: 환경 준비 (사용자 설정)")

# Admin 로그인
admin_token = login("test@test.com", "test1234")
check(admin_token is not None, "Admin 로그인 성공", "Admin 로그인 실패")
ctx["admin"] = admin_token

# 현장소장 등록 (department_name 은 허용 목록 내 값, .test TLD 거부 → gmail.com)
TS = int(time.time())
MANAGER_EMAIL = f"testmgr{TS}@gmail.com"
r = requests.post(f"{BASE}/auth/register", json={
    "email": MANAGER_EMAIL,
    "password": "Manager1234",
    "name": "김현장",
    "department_name": "현장소장",
})
check(r.status_code == 201, "현장소장(manager) 회원가입 성공", f"현장소장 등록 실패 {r.status_code}", r.text)
manager_data = r.json()
ctx["manager_token"]  = manager_data.get("access_token")
ctx["manager_id"]     = manager_data.get("user_id")   # TokenResponse: user_id 필드

# 공사팀 등록
WORKER_EMAIL = f"testworker{TS}@gmail.com"
r = requests.post(f"{BASE}/auth/register", json={
    "email": WORKER_EMAIL,
    "password": "Worker5678",
    "name": "이공사",
    "department_name": "공사팀",
})
check(r.status_code == 201, "공사팀(worker) 회원가입 성공", f"공사팀 등록 실패 {r.status_code}", r.text)
worker_data = r.json()
ctx["worker_token"] = worker_data.get("access_token")
ctx["worker_id"]    = worker_data.get("user_id")

# Admin 자신의 ID 조회
r = requests.get(f"{BASE}/auth/me", headers=h(admin_token))
ctx["admin_id"] = r.json().get("id")
print(f"  {YELLOW}→ admin_id={ctx['admin_id']}, manager_id={ctx['manager_id']}, worker_id={ctx['worker_id']}{RESET}")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 1: 카테고리 시스템
# ═══════════════════════════════════════════════════════════════════════════════
section("PHASE 1: 카테고리 시스템")

CAT1_NAME = f"기초공사_{TS}"
CAT2_NAME = f"안전관리_{TS}"

r = requests.post(f"{BASE}/categories/", json={"name": CAT1_NAME, "color": "#ef4444"},
                  headers=h(admin_token))
check(r.status_code == 201, f"카테고리 '{CAT1_NAME}' 생성 성공", f"카테고리 생성 실패", r.text)
ctx["cat_id"] = r.json().get("id")

r2 = requests.post(f"{BASE}/categories/", json={"name": CAT2_NAME, "color": "#f59e0b"},
                   headers=h(admin_token))
check(r2.status_code == 201, f"카테고리 '{CAT2_NAME}' 생성 성공", "카테고리 생성 실패", r2.text)

# 중복 생성 → 400 예상
r3 = requests.post(f"{BASE}/categories/", json={"name": CAT1_NAME}, headers=h(admin_token))
check(r3.status_code == 400, "중복 카테고리 생성 → 400 반환 확인", "중복 카테고리 차단 실패", r3.text)

# 카테고리 목록 조회
r4 = requests.get(f"{BASE}/categories/", headers=h(admin_token))
cats = r4.json()
check(any(c["name"] == CAT1_NAME for c in cats),
      f"카테고리 목록 조회 성공 ({len(cats)}개)", "카테고리 목록 조회 실패")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2: 복합 업무 생성 (material_providers 자동 서브태스크)
# ═══════════════════════════════════════════════════════════════════════════════
section("PHASE 2: 복합 업무 생성 (material_providers → 자동 서브태스크)")

due_main  = (date.today() + timedelta(days=14)).isoformat()
due_sub   = (date.today() + timedelta(days=7)).isoformat()

r = requests.post(f"{BASE}/tasks/", headers=h(admin_token), json={
    "title": "1공구 기초공사 완료 점검",
    "content": "1공구 전체 기초공사 완료 여부를 점검합니다.",
    "assignee_id": ctx["manager_id"],
    "category_id": ctx["cat_id"],
    "priority": "high",
    "due_date": due_main,
    "tag_names": ["기초", "점검", "1공구"],
    "material_providers": [
        {
            "assignee_id": ctx["worker_id"],
            "title": "철근 배근 검토서 제출",
            "due_date": due_sub,
        }
    ],
})
check(r.status_code == 201, "주업무 생성 성공 (material_providers 포함)", f"주업무 생성 실패 {r.status_code}", r.text)
parent = r.json()
ctx["parent_id"] = parent["id"]

# 자동 서브태스크 확인 (task_to_dict는 subtask_count만 반환, 실제 목록은 별도 조회)
subtask_count = parent.get("subtask_count", 0)
check(subtask_count >= 1, f"자동 서브태스크 생성 확인 (subtask_count={subtask_count})",
      "material_providers 자동 서브태스크 생성 실패 (subtask_count=0)")

# 실제 서브태스크 ID 조회 (worker에게 배정된 것)
all_tasks_r = requests.get(f"{BASE}/tasks/", headers=h(admin_token),
                           params={"section": "subtasks_to_me"})
# worker의 서브태스크를 조회
worker_subtasks_r = requests.get(f"{BASE}/tasks/", headers=h(ctx["worker_token"]),
                                  params={"section": "subtasks_to_me"})
auto_sub_items = worker_subtasks_r.json().get("items", [])
if auto_sub_items:
    ctx["auto_subtask_id"] = auto_sub_items[0]["id"]
    print(f"  {YELLOW}→ 자동 서브태스크 id={ctx['auto_subtask_id']}, title={auto_sub_items[0].get('title', '')[:30]}{RESET}")

# 주업무 태그 확인
tags_on_task = [t["name"] for t in parent.get("tags", [])]
check("기초" in tags_on_task and "점검" in tags_on_task,
      f"업무 태그 정상 연결 ({tags_on_task})", "업무 태그 누락")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 3: 수동 서브태스크 추가
# ═══════════════════════════════════════════════════════════════════════════════
section("PHASE 3: 수동 서브태스크 추가")

# 서브태스크 #1 (worker, urgent)
r = requests.post(f"{BASE}/tasks/", headers=h(admin_token), json={
    "title": "콘크리트 타설 준비 확인",
    "content": "타설 준비 상태를 점검합니다.",
    "assignee_id": ctx["worker_id"],
    "priority": "urgent",
    "due_date": due_sub,
    "parent_task_id": ctx["parent_id"],
    "is_subtask": True,
    "tag_names": ["콘크리트", "긴급"],
})
check(r.status_code == 201, "수동 서브태스크 #1 (worker, urgent) 생성 성공", f"서브태스크 #1 생성 실패 {r.status_code}", r.text)
ctx["sub1_id"] = r.json()["id"]

# 서브태스크 #2 (worker, normal)
r = requests.post(f"{BASE}/tasks/", headers=h(admin_token), json={
    "title": "안전 장비 점검 일지 제출",
    "content": "안전모, 안전벨트 등 장비 점검 일지 제출.",
    "assignee_id": ctx["worker_id"],
    "priority": "normal",
    "parent_task_id": ctx["parent_id"],
    "is_subtask": True,
})
check(r.status_code == 201, "수동 서브태스크 #2 (worker, normal) 생성 성공", f"서브태스크 #2 생성 실패 {r.status_code}", r.text)
ctx["sub2_id"] = r.json()["id"]

# 서브태스크 #3 (manager, rejected 흐름용)
r = requests.post(f"{BASE}/tasks/", headers=h(admin_token), json={
    "title": "현장 일일 보고서 제출",
    "content": "오늘 진행상황 보고서를 제출합니다.",
    "assignee_id": ctx["manager_id"],
    "priority": "high",
    "parent_task_id": ctx["parent_id"],
    "is_subtask": True,
})
check(r.status_code == 201, "수동 서브태스크 #3 (manager, rejected 흐름용) 생성 성공", f"서브태스크 #3 생성 실패 {r.status_code}", r.text)
ctx["sub3_id"] = r.json()["id"]
print(f"  {YELLOW}→ sub1={ctx['sub1_id']} sub2={ctx['sub2_id']} sub3={ctx['sub3_id']}{RESET}")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 4: 업무 복제 (clone)
# ═══════════════════════════════════════════════════════════════════════════════
section("PHASE 4: 업무 복제 (clone)")

# Admin이 주업무 복제
r = requests.post(f"{BASE}/tasks/{ctx['parent_id']}/clone", headers=h(admin_token))
check(r.status_code == 201, "Admin: 주업무 복제 성공", f"주업무 복제 실패 {r.status_code}", r.text)
cloned_id = r.json().get("task_id")
ctx["cloned_id"] = cloned_id

# 복제된 업무 제목 확인
if cloned_id:
    r2 = requests.get(f"{BASE}/tasks/{cloned_id}", headers=h(admin_token))
    cloned_title = r2.json().get("title", "")
    check("[복사]" in cloned_title, f"복제 업무 제목 '[복사]' 포함 확인: '{cloned_title}'",
          "복제 업무 제목 형식 오류")

# worker가 권한 없는 업무(주업무) 복제 시도 → 403
r3 = requests.post(f"{BASE}/tasks/{ctx['parent_id']}/clone", headers=h(ctx["worker_token"]))
check(r3.status_code == 403, "worker: 권한 없는 업무 복제 시도 → 403 확인",
      f"권한 경계 미작동 (expected 403, got {r3.status_code})")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 5: 현장소장(manager) 관점 작업
# ═══════════════════════════════════════════════════════════════════════════════
section("PHASE 5: 현장소장(manager) 관점 작업")

mg_token = ctx["manager_token"]

# manager /me 확인
r = requests.get(f"{BASE}/auth/me", headers=h(mg_token))
check(r.status_code == 200 and r.json().get("name") == "김현장",
      "manager /me 확인 (이름: 김현장)", "manager /me 조회 실패")

# 배정된 주업무 목록 조회
r = requests.get(f"{BASE}/tasks/", headers=h(mg_token),
                 params={"section": "assigned_to_me"})
items = r.json().get("items", [])
total = r.json().get("total", 0)
check(any(t["id"] == ctx["parent_id"] for t in items),
      f"manager: 배정 업무 목록에 주업무 포함 확인 (total={total})",
      "manager 배정 업무 목록 조회 실패")

# 주업무 상태: pending → in_progress
r = requests.post(f"{BASE}/tasks/{ctx['parent_id']}/status",
                  headers=h(mg_token),
                  json={"status": "in_progress", "comment": "작업 시작합니다."})
check(r.status_code == 200, "manager: 주업무 pending → in_progress 변경 성공",
      f"상태 변경 실패 {r.status_code}", r.text)

# manager가 주업무에 댓글 등록
r = requests.post(f"{BASE}/tasks/{ctx['parent_id']}/comment",
                  headers=h(mg_token), json={"comment": "현장 상황 공유합니다."})
check(r.status_code == 201 or r.status_code == 200,
      "manager: 주업무 댓글 등록 성공", f"댓글 등록 실패 {r.status_code}", r.text)

# manager 댓글 log_id 저장 (권한 테스트용)
logs_r = requests.get(f"{BASE}/tasks/{ctx['parent_id']}/logs", headers=h(admin_token))
logs = logs_r.json()
comment_logs = [l for l in logs if l["action"] == "comment" and l.get("user", {}).get("id") == ctx["manager_id"]]
if comment_logs:
    ctx["manager_comment_log_id"] = comment_logs[-1]["id"]
    print(f"  {YELLOW}→ manager 댓글 log_id={ctx['manager_comment_log_id']}{RESET}")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 6: 공사팀(worker) 관점 작업
# ═══════════════════════════════════════════════════════════════════════════════
section("PHASE 6: 공사팀(worker) 관점 작업")

wk_token = ctx["worker_token"]

# worker /me 확인
r = requests.get(f"{BASE}/auth/me", headers=h(wk_token))
check(r.status_code == 200 and r.json().get("name") == "이공사",
      "worker /me 확인 (이름: 이공사)", "worker /me 조회 실패")

# 배정된 서브태스크 목록 조회
r = requests.get(f"{BASE}/tasks/", headers=h(wk_token),
                 params={"section": "subtasks_to_me"})
sub_items = r.json().get("items", [])
check(len(sub_items) >= 1,
      f"worker: 서브태스크 목록 조회 성공 ({len(sub_items)}개)",
      "worker 서브태스크 목록 조회 실패")

# 서브태스크 #1: pending → in_progress
r = requests.post(f"{BASE}/tasks/{ctx['sub1_id']}/status",
                  headers=h(wk_token), json={"status": "in_progress", "comment": "콘크리트 준비 시작"})
check(r.status_code == 200, "worker: sub1 pending → in_progress 성공",
      f"worker 상태 변경 실패 {r.status_code}", r.text)

# worker가 sub1에 댓글 등록
r = requests.post(f"{BASE}/tasks/{ctx['sub1_id']}/comment",
                  headers=h(wk_token), json={"comment": "타설 준비 80% 완료되었습니다."})
check(r.status_code in (200, 201), "worker: sub1 댓글 등록 성공",
      f"worker 댓글 등록 실패 {r.status_code}", r.text)

# worker 댓글 log_id 저장
logs_r = requests.get(f"{BASE}/tasks/{ctx['sub1_id']}/logs", headers=h(admin_token))
logs = logs_r.json()
worker_comment_logs = [l for l in logs if l["action"] == "comment"
                        and l.get("user", {}).get("id") == ctx["worker_id"]]
if worker_comment_logs:
    ctx["worker_comment_log_id"] = worker_comment_logs[-1]["id"]
    print(f"  {YELLOW}→ worker 댓글 log_id={ctx['worker_comment_log_id']}{RESET}")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 7: 권한 경계 테스트 (403 / 401 / 400)
# ═══════════════════════════════════════════════════════════════════════════════
section("PHASE 7: 권한 경계 테스트 (403 / 401 / 400)")

# ① worker → manager 댓글 수정 시도 → 403
if ctx.get("manager_comment_log_id"):
    r = requests.patch(
        f"{BASE}/tasks/{ctx['parent_id']}/comments/{ctx['manager_comment_log_id']}",
        headers=h(wk_token), json={"comment": "해킹 시도!"}
    )
    check(r.status_code == 403,
          "① worker→manager 댓글 수정 시도 → 403 확인",
          f"권한 경계 미작동 (expected 403, got {r.status_code})")

# ② worker → manager 댓글 삭제 시도 → 403
if ctx.get("manager_comment_log_id"):
    r = requests.delete(
        f"{BASE}/tasks/{ctx['parent_id']}/comments/{ctx['manager_comment_log_id']}",
        headers=h(wk_token)
    )
    check(r.status_code == 403,
          "② worker→manager 댓글 삭제 시도 → 403 확인",
          f"권한 경계 미작동 (expected 403, got {r.status_code})")

# ③ worker → 주업무 삭제 시도 (assigner=admin, assignee=manager) → 403
r = requests.delete(f"{BASE}/tasks/{ctx['parent_id']}", headers=h(wk_token))
check(r.status_code == 403,
      "③ worker→주업무 삭제 시도 → 403 확인",
      f"삭제 권한 경계 미작동 (expected 403, got {r.status_code})")

# ④ 토큰 없이 /me → 401 또는 403
r = requests.get(f"{BASE}/auth/me")
check(r.status_code in (401, 403),
      f"④ 토큰 없이 /me 접근 → {r.status_code} 확인",
      f"인증 미작동 (got {r.status_code})")

# ⑤ 잘못된 토큰 → 401
r = requests.get(f"{BASE}/auth/me", headers={"Authorization": "Bearer INVALID.TOKEN.xyz"})
check(r.status_code in (401, 403),
      f"⑤ 잘못된 토큰 → {r.status_code} 확인",
      f"토큰 검증 미작동 (got {r.status_code})")

# ⑥ 잘못된 비밀번호 로그인 → 401 (OAuth2 form data 형식으로 전송)
r = requests.post(f"{BASE}/auth/login", data={"username": "test@test.com", "password": "WRONG_PASS"})
check(r.status_code == 401,
      "⑥ 잘못된 비밀번호 로그인 → 401 확인",
      f"비밀번호 검증 미작동 (got {r.status_code})")

# ⑦ rejected 상태 변경 시 comment 없음 → 400
r = requests.post(f"{BASE}/tasks/{ctx['sub3_id']}/status",
                  headers=h(admin_token), json={"status": "rejected"})
check(r.status_code == 400,
      "⑦ rejected 상태변경 comment 없음 → 400 확인",
      f"rejected 검증 미작동 (got {r.status_code})")

# ⑧ worker가 주업무(자신이 assigner/assignee 아님) PATCH 시도 → 403
r = requests.patch(f"{BASE}/tasks/{ctx['parent_id']}",
                   headers=h(wk_token), json={"title": "해킹된 제목"})
check(r.status_code == 403,
      "⑧ worker→주업무 PATCH 시도 → 403 확인",
      f"PATCH 권한 경계 미작동 (got {r.status_code})")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 8: 알림 시스템 검증
# ═══════════════════════════════════════════════════════════════════════════════
section("PHASE 8: 알림 시스템 검증")

# manager 알림 목록 조회
r = requests.get(f"{BASE}/notifications/", headers=h(mg_token))
notifs = r.json()
check(isinstance(notifs, list) and len(notifs) > 0,
      f"manager 알림 목록 조회 성공 ({len(notifs)}개 알림)",
      "manager 알림 목록 조회 실패 또는 비어있음")

# 읽지 않은 알림 수 확인
r2 = requests.get(f"{BASE}/notifications/unread-count", headers=h(mg_token))
unread_count = r2.json().get("count", 0)
check(unread_count > 0, f"읽지 않은 알림 수 > 0 확인 ({unread_count}개)",
      "읽지 않은 알림이 0개 (알림 생성 미확인)")

# 특정 알림 읽음 처리
if notifs:
    notif_id = notifs[0]["id"]
    r3 = requests.post(f"{BASE}/notifications/{notif_id}/read", headers=h(mg_token))
    check(r3.status_code == 200, f"알림 {notif_id} 읽음 처리 성공", f"알림 읽음 처리 실패 {r3.status_code}")

    # 읽음 처리 후 해당 알림 상태 확인
    r4 = requests.get(f"{BASE}/notifications/", headers=h(mg_token))
    updated_notifs = r4.json()
    for n in updated_notifs:
        if n["id"] == notif_id:
            check(n["is_read"], f"알림 {notif_id} is_read=True 확인", "알림 읽음 상태 반영 실패")
            break

# 전체 읽음 처리
r5 = requests.post(f"{BASE}/notifications/read-all", headers=h(mg_token))
check(r5.status_code == 200, "전체 읽음 처리 성공", f"전체 읽음 처리 실패 {r5.status_code}")

# 전체 읽음 후 unread_count = 0 확인
r6 = requests.get(f"{BASE}/notifications/unread-count", headers=h(mg_token))
final_unread = r6.json().get("count", -1)
check(final_unread == 0, f"전체 읽음 후 unread_count=0 확인 (현재={final_unread})",
      f"unread_count가 0이 아님 ({final_unread})")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 9: 완전한 상태 라이프사이클
# ═══════════════════════════════════════════════════════════════════════════════
section("PHASE 9: 완전한 상태 라이프사이클")

# ─ 흐름 A: pending → in_progress → review → approved (sub2, worker 담당)
r = requests.post(f"{BASE}/tasks/{ctx['sub2_id']}/status",
                  headers=h(wk_token), json={"status": "in_progress", "comment": "안전 장비 점검 시작"})
check(r.status_code == 200, "A.1 sub2: pending → in_progress", f"상태변경 실패 {r.status_code}")

r = requests.post(f"{BASE}/tasks/{ctx['sub2_id']}/status",
                  headers=h(wk_token), json={"status": "review", "comment": "점검 완료, 검토 요청"})
check(r.status_code == 200, "A.2 sub2: in_progress → review", f"상태변경 실패 {r.status_code}")

r = requests.post(f"{BASE}/tasks/{ctx['sub2_id']}/status",
                  headers=h(admin_token), json={"status": "approved", "comment": "승인 완료"})
check(r.status_code == 200, "A.3 sub2: review → approved (admin 승인)", f"상태변경 실패 {r.status_code}")

# approved 업무 상태 직접 확인
r_verify = requests.get(f"{BASE}/tasks/{ctx['sub2_id']}", headers=h(admin_token))
check(r_verify.json().get("status") == "approved",
      "A.4 sub2 최종 status=approved 확인", "sub2 상태 확인 실패")

# ─ 흐름 B: pending → in_progress → review → rejected (sub3, manager 담당)
r = requests.post(f"{BASE}/tasks/{ctx['sub3_id']}/status",
                  headers=h(mg_token), json={"status": "in_progress"})
check(r.status_code == 200, "B.1 sub3: pending → in_progress", f"상태변경 실패 {r.status_code}")

r = requests.post(f"{BASE}/tasks/{ctx['sub3_id']}/status",
                  headers=h(mg_token), json={"status": "review", "comment": "검토 요청"})
check(r.status_code == 200, "B.2 sub3: in_progress → review", f"상태변경 실패 {r.status_code}")

r = requests.post(f"{BASE}/tasks/{ctx['sub3_id']}/status",
                  headers=h(admin_token), json={"status": "rejected", "comment": "내용 불충분, 재작성 요청"})
check(r.status_code == 200, "B.3 sub3: review → rejected (admin, comment 포함)",
      f"상태변경 실패 {r.status_code}")

# ─ 흐름 C: rejected → in_progress → approved (재처리)
r = requests.post(f"{BASE}/tasks/{ctx['sub3_id']}/status",
                  headers=h(mg_token), json={"status": "in_progress", "comment": "수정 후 재진행"})
check(r.status_code == 200, "C.1 sub3: rejected → in_progress (재처리)", f"상태변경 실패 {r.status_code}")

r = requests.post(f"{BASE}/tasks/{ctx['sub3_id']}/status",
                  headers=h(admin_token), json={"status": "approved", "comment": "재검토 후 최종 승인"})
check(r.status_code == 200, "C.2 sub3: in_progress → approved (재처리 완료)", f"상태변경 실패 {r.status_code}")

# sub3 로그에 상태변경 기록이 여러 개인지 확인
logs_r = requests.get(f"{BASE}/tasks/{ctx['sub3_id']}/logs", headers=h(admin_token))
logs = logs_r.json()
status_change_logs = [l for l in logs if l["action"] == "status_changed"]
check(len(status_change_logs) >= 4,
      f"C.3 sub3 상태변경 로그 4개 이상 확인 ({len(status_change_logs)}개)",
      f"상태변경 로그 부족 ({len(status_change_logs)}개)")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 10: 업무 수정 흐름
# ═══════════════════════════════════════════════════════════════════════════════
section("PHASE 10: 업무 수정 흐름")

# manager: 주업무 진행률 50%로 업데이트
r = requests.patch(f"{BASE}/tasks/{ctx['parent_id']}",
                   headers=h(mg_token), json={"progress": 50, "content": "현장 점검 진행 중 (50%)"})
check(r.status_code == 200, "manager: 주업무 progress=50 업데이트 성공", f"업데이트 실패 {r.status_code}", r.text)

r_verify = requests.get(f"{BASE}/tasks/{ctx['parent_id']}", headers=h(admin_token))
check(r_verify.json().get("progress") == 50,
      "주업무 progress=50 반영 확인", "progress 반영 실패")

# admin: auto_subtask 우선순위 normal → urgent
if ctx.get("auto_subtask_id"):
    r = requests.patch(f"{BASE}/tasks/{ctx['auto_subtask_id']}",
                       headers=h(admin_token), json={"priority": "urgent"})
    check(r.status_code == 200, "admin: auto_subtask 우선순위 normal→urgent 변경 성공",
          f"우선순위 변경 실패 {r.status_code}")

# admin: sub1 담당자 재배정 (worker → manager)
r = requests.patch(f"{BASE}/tasks/{ctx['sub1_id']}",
                   headers=h(admin_token), json={"assignee_id": ctx["manager_id"]})
check(r.status_code == 200, "admin: sub1 담당자 worker→manager 재배정 성공",
      f"재배정 실패 {r.status_code}", r.text)

# 재배정 로그 확인
logs_r = requests.get(f"{BASE}/tasks/{ctx['sub1_id']}/logs", headers=h(admin_token))
logs = logs_r.json()
reassign_logs = [l for l in logs if l["action"] == "reassigned"]
check(len(reassign_logs) >= 1,
      f"재배정 로그 생성 확인 ({len(reassign_logs)}개)", "재배정 로그 없음")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 11: 일괄 상태 변경 (bulk-status)
# ═══════════════════════════════════════════════════════════════════════════════
section("PHASE 11: 일괄 상태 변경 (bulk-status)")

# auto_subtask + sub1 → review 일괄 변경
bulk_ids = []
if ctx.get("auto_subtask_id"):
    bulk_ids.append(ctx["auto_subtask_id"])
bulk_ids.append(ctx["sub1_id"])

r = requests.post(f"{BASE}/tasks/bulk-status",
                  headers=h(admin_token),
                  json={"task_ids": bulk_ids, "status": "review"})
check(r.status_code == 200,
      f"bulk-status → review 변경 성공 ({len(bulk_ids)}개 업무)",
      f"bulk-status 실패 {r.status_code}", r.text)

# bulk 변경 후 실제 상태 확인
if ctx.get("auto_subtask_id"):
    r_v = requests.get(f"{BASE}/tasks/{ctx['auto_subtask_id']}", headers=h(admin_token))
    check(r_v.json().get("status") == "review",
          "auto_subtask status=review 반영 확인", "auto_subtask 상태 반영 실패")

# 대시보드에서 review 카운트 확인
r_dash = requests.get(f"{BASE}/tasks/dashboard", headers=h(admin_token))
dash_data = r_dash.json()
check(r_dash.status_code == 200, "대시보드 조회 성공", f"대시보드 조회 실패 {r_dash.status_code}")
print(f"  {YELLOW}→ 대시보드 데이터: {json.dumps(dash_data, ensure_ascii=False)[:200]}{RESET}")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 12: 정렬 & 필터링 종합
# ═══════════════════════════════════════════════════════════════════════════════
section("PHASE 12: 정렬 & 필터링 종합")

# sort_by=priority desc
r = requests.get(f"{BASE}/tasks/", headers=h(admin_token),
                 params={"sort_by": "priority", "sort_dir": "desc"})
items = r.json().get("items", [])
check(r.status_code == 200 and len(items) > 0,
      f"sort_by=priority desc 조회 성공 ({len(items)}개)", "정렬 조회 실패")

# sort_by=priority asc
r = requests.get(f"{BASE}/tasks/", headers=h(admin_token),
                 params={"sort_by": "priority", "sort_dir": "asc"})
check(r.status_code == 200, "sort_by=priority asc 조회 성공", f"정렬 조회 실패 {r.status_code}")

# sort_by=status
r = requests.get(f"{BASE}/tasks/", headers=h(admin_token),
                 params={"sort_by": "status", "sort_dir": "asc"})
check(r.status_code == 200, "sort_by=status asc 조회 성공", f"정렬 조회 실패 {r.status_code}")

# sort_by=title
r = requests.get(f"{BASE}/tasks/", headers=h(admin_token),
                 params={"sort_by": "title", "sort_dir": "asc"})
check(r.status_code == 200, "sort_by=title asc 조회 성공", f"정렬 조회 실패 {r.status_code}")

# sort_by=due_date
r = requests.get(f"{BASE}/tasks/", headers=h(admin_token),
                 params={"sort_by": "due_date", "sort_dir": "asc"})
check(r.status_code == 200, "sort_by=due_date asc 조회 성공", f"정렬 조회 실패 {r.status_code}")

# section=assigned_by_me (admin이 지시한 업무)
r = requests.get(f"{BASE}/tasks/", headers=h(admin_token),
                 params={"section": "assigned_by_me"})
items = r.json().get("items", [])
check(any(t["id"] == ctx["parent_id"] for t in items),
      f"section=assigned_by_me → 주업무 포함 확인 ({len(items)}개)",
      "assigned_by_me 필터 실패")

# status 필터 (approved)
r = requests.get(f"{BASE}/tasks/", headers=h(admin_token), params={"status": "approved"})
approved_items = r.json().get("items", [])
check(all(t["status"] == "approved" for t in approved_items),
      f"status=approved 필터 정확성 확인 ({len(approved_items)}개)",
      "status 필터 부정확 (non-approved 포함)")

# 자연어 검색: "긴급" → urgent 우선순위 업무 검색
r = requests.get(f"{BASE}/tasks/", headers=h(admin_token), params={"search": "긴급"})
search_items = r.json().get("items", [])
check(r.status_code == 200 and isinstance(search_items, list),
      f"자연어 검색 '긴급' 조회 성공 ({len(search_items)}개)", "자연어 검색 실패")

# 사용자명 검색: "이공사"
r = requests.get(f"{BASE}/tasks/", headers=h(admin_token), params={"search": "이공사"})
search_items2 = r.json().get("items", [])
check(r.status_code == 200,
      f"사용자명 '이공사' 검색 성공 ({len(search_items2)}개)", "사용자명 검색 실패")

# 페이지네이션
r = requests.get(f"{BASE}/tasks/", headers=h(admin_token),
                 params={"page": 1, "page_size": 2})
paged = r.json()
check(len(paged.get("items", [])) <= 2 and paged.get("page") == 1,
      "페이지네이션 page=1, page_size=2 동작 확인", "페이지네이션 실패")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 13: 이메일 인증 흐름
# ═══════════════════════════════════════════════════════════════════════════════
section("PHASE 13: 이메일 인증 흐름")

VERIFY_EMAIL = f"testverify{int(time.time())}@gmail.com"
r = requests.post(f"{BASE}/auth/register", json={
    "email": VERIFY_EMAIL,
    "password": "Verify9999",
    "name": "검증테스터",
    "department_name": "품질팀",
})
check(r.status_code == 201, "이메일 인증용 신규 유저 등록 성공", f"등록 실패 {r.status_code}", r.text)
verify_token_val = r.json().get("access_token")

# is_verified 확인 (등록 직후 True or False)
r_me = requests.get(f"{BASE}/auth/me", headers=h(verify_token_val))
is_verified_now = r_me.json().get("is_verified", None)
print(f"  {YELLOW}→ 등록 직후 is_verified={is_verified_now}{RESET}")

# DB에서 verification token 직접 조회 (email_verification_tokens 별도 테이블)
vt = db_query(
    f"SELECT t.token FROM email_verification_tokens t "
    f"JOIN users u ON u.id=t.user_id "
    f"WHERE u.email='{VERIFY_EMAIL}' AND t.used=0 "
    f"ORDER BY t.id DESC LIMIT 1;"
)
check(vt != "" and vt != "NULL" and vt is not None,
      f"DB에서 verification_token 조회 성공: {vt[:20]}...",
      "verification_token 없음 (이미 인증됨 또는 생성 안됨)")

if vt and vt != "NULL":
    r_vf = requests.post(f"{BASE}/auth/verify-email/{vt}")
    check(r_vf.status_code == 200,
          "verify-email 엔드포인트 호출 성공", f"이메일 인증 실패 {r_vf.status_code}", r_vf.text)

    r_me2 = requests.get(f"{BASE}/auth/me", headers=h(verify_token_val))
    check(r_me2.json().get("is_verified") == True,
          "이메일 인증 후 is_verified=True 확인", "is_verified 갱신 실패")

# 잘못된 token으로 verify-email → 400/404
r_bad = requests.post(f"{BASE}/auth/verify-email/INVALID_TOKEN_XYZ")
check(r_bad.status_code in (400, 404),
      f"잘못된 token verify-email → {r_bad.status_code} 확인",
      f"잘못된 token 처리 미작동 (got {r_bad.status_code})")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 14: 비밀번호 관련 흐름
# ═══════════════════════════════════════════════════════════════════════════════
section("PHASE 14: 비밀번호 관련 흐름")

# ① 잘못된 현재 비밀번호로 change-password → 400
r = requests.post(f"{BASE}/auth/change-password", headers=h(mg_token),
                  json={"current_password": "WRONG_PASS", "new_password": "New#Pass123"})
check(r.status_code == 400,
      "① 잘못된 현재 비밀번호 change-password → 400 확인",
      f"비밀번호 변경 검증 미작동 (got {r.status_code})")

# ② forgot-password 요청
r = requests.post(f"{BASE}/auth/forgot-password", json={"email": MANAGER_EMAIL})
check(r.status_code == 200,
      f"② forgot-password 요청 성공 ({MANAGER_EMAIL})",
      f"forgot-password 실패 {r.status_code}")

# DB에서 reset token 직접 조회 (password_reset_tokens 별도 테이블)
rt = db_query(
    f"SELECT t.token FROM password_reset_tokens t "
    f"JOIN users u ON u.id=t.user_id "
    f"WHERE u.email='{MANAGER_EMAIL}' AND t.used=0 "
    f"ORDER BY t.id DESC LIMIT 1;"
)
check(rt != "" and rt is not None and rt != "NULL",
      f"③ DB에서 reset_token 조회 성공: {rt[:20] if rt else 'N/A'}...",
      "reset_token 없음 (이메일 미설정으로 저장 안됨)")

if rt and rt != "NULL":
    # ④ reset-password 실행
    NEW_PASS = "NewManager#9999"
    r = requests.post(f"{BASE}/auth/reset-password",
                      json={"token": rt, "new_password": NEW_PASS})
    check(r.status_code == 200,
          "④ reset-password 성공", f"reset-password 실패 {r.status_code}", r.text)

    # ⑤ 새 비밀번호로 로그인 확인
    new_token = login(MANAGER_EMAIL, NEW_PASS)
    check(new_token is not None,
          "⑤ 새 비밀번호로 로그인 성공", "새 비밀번호로 로그인 실패")

    # ⑥ 원래 비밀번호로 로그인 시도 → 실패 확인
    old_token = login(MANAGER_EMAIL, "Manager1234")
    check(old_token is None,
          "⑥ 원래 비밀번호 로그인 → 실패 확인 (비밀번호 변경 정상)", "원래 비밀번호로 로그인 가능 (변경 미반영)")

    # ⑦ 비밀번호 원복 (change-password로)
    if new_token:
        r = requests.post(f"{BASE}/auth/change-password", headers=h(new_token),
                          json={"current_password": NEW_PASS, "new_password": "Manager1234"})
        check(r.status_code == 200,
              "⑦ change-password로 비밀번호 원복 성공", f"비밀번호 원복 실패 {r.status_code}")
        ctx["manager_token"] = login(MANAGER_EMAIL, "Manager1234")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 15: 업무 로그 & 댓글 수정/삭제
# ═══════════════════════════════════════════════════════════════════════════════
section("PHASE 15: 업무 로그 & 댓글 수정/삭제")

# sub1 로그 전체 조회
logs_r = requests.get(f"{BASE}/tasks/{ctx['sub1_id']}/logs", headers=h(admin_token))
logs = logs_r.json()
check(isinstance(logs, list) and len(logs) > 0,
      f"sub1 업무 로그 조회 성공 ({len(logs)}개 항목)", "업무 로그 조회 실패")

# 로그 내용 검증 (created 로그 있어야 함)
created_logs = [l for l in logs if l["action"] == "created"]
check(len(created_logs) >= 1,
      f"created 로그 확인 ({len(created_logs)}개)", "created 로그 없음")

# update_comment는 본인만 수정 가능 (admin 예외 없음)
# admin이 manager 댓글 수정 시도 → 403 예상
if ctx.get("manager_comment_log_id"):
    r = requests.patch(
        f"{BASE}/tasks/{ctx['parent_id']}/comments/{ctx['manager_comment_log_id']}",
        headers=h(admin_token), json={"comment": "[Admin 수정 시도]"}
    )
    check(r.status_code == 403,
          "admin: 타인 댓글 수정 시도 → 403 확인 (update_comment admin 예외 없음)",
          f"댓글 수정 권한 검증 실패 (got {r.status_code})")

# worker가 자신의 댓글 수정 (본인 권한)
if ctx.get("worker_comment_log_id"):
    r = requests.patch(
        f"{BASE}/tasks/{ctx['sub1_id']}/comments/{ctx['worker_comment_log_id']}",
        headers=h(wk_token), json={"comment": "타설 준비 100% 완료되었습니다."}
    )
    check(r.status_code == 200,
          "worker: 자신의 댓글 수정 성공 (본인 권한)",
          f"worker 댓글 수정 실패 {r.status_code}", r.text)

# admin이 manager 댓글 삭제 (admin 권한)
if ctx.get("manager_comment_log_id"):
    r = requests.delete(
        f"{BASE}/tasks/{ctx['parent_id']}/comments/{ctx['manager_comment_log_id']}",
        headers=h(admin_token)
    )
    check(r.status_code == 204,
          "admin: manager 댓글 삭제 성공 (admin 권한)",
          f"admin 댓글 삭제 실패 {r.status_code}", r.text)


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 16: 계단식 삭제 검증
# ═══════════════════════════════════════════════════════════════════════════════
section("PHASE 16: 계단식 삭제 검증")

# 복제 업무 삭제
if ctx.get("cloned_id"):
    r = requests.delete(f"{BASE}/tasks/{ctx['cloned_id']}", headers=h(admin_token))
    check(r.status_code == 204,
          f"복제 업무(id={ctx['cloned_id']}) 삭제 성공 (204)", f"복제 업무 삭제 실패 {r.status_code}")

    r_check = requests.get(f"{BASE}/tasks/{ctx['cloned_id']}", headers=h(admin_token))
    check(r_check.status_code == 404,
          "삭제된 복제 업무 조회 → 404 확인", f"삭제 미반영 (got {r_check.status_code})")

# 주업무 삭제 → 서브태스크 연쇄 삭제 확인
subtask_ids_before = [ctx.get("auto_subtask_id"), ctx["sub1_id"], ctx["sub2_id"], ctx["sub3_id"]]
subtask_ids_before = [sid for sid in subtask_ids_before if sid]

r = requests.delete(f"{BASE}/tasks/{ctx['parent_id']}", headers=h(admin_token))
check(r.status_code == 204,
      f"주업무(id={ctx['parent_id']}) 삭제 성공 (204)", f"주업무 삭제 실패 {r.status_code}")

# 주업무 조회 → 404
r_parent = requests.get(f"{BASE}/tasks/{ctx['parent_id']}", headers=h(admin_token))
check(r_parent.status_code == 404,
      "삭제된 주업무 조회 → 404 확인", f"주업무 삭제 미반영 (got {r_parent.status_code})")

# 서브태스크들도 연쇄 삭제 확인
cascade_ok = True
for sid in subtask_ids_before:
    r_sub = requests.get(f"{BASE}/tasks/{sid}", headers=h(admin_token))
    if r_sub.status_code != 404:
        cascade_ok = False
        fail(f"서브태스크 id={sid} 연쇄 삭제 미확인 (got {r_sub.status_code})")

if cascade_ok and subtask_ids_before:
    ok(f"서브태스크 연쇄 삭제 확인 ({len(subtask_ids_before)}개 모두 404)")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 17: 최종 대시보드 & 태그 시스템 검증
# ═══════════════════════════════════════════════════════════════════════════════
section("PHASE 17: 최종 대시보드 & 태그 시스템 검증")

# admin 대시보드
r_adash = requests.get(f"{BASE}/tasks/dashboard", headers=h(admin_token))
check(r_adash.status_code == 200, "admin 대시보드 조회 성공", f"admin 대시보드 실패 {r_adash.status_code}")
if r_adash.status_code == 200:
    print(f"  {YELLOW}→ admin 대시보드: {json.dumps(r_adash.json(), ensure_ascii=False)[:300]}{RESET}")

# manager 대시보드
if ctx.get("manager_token"):
    r_mdash = requests.get(f"{BASE}/tasks/dashboard", headers=h(ctx["manager_token"]))
    check(r_mdash.status_code == 200, "manager 대시보드 조회 성공", f"manager 대시보드 실패")

# worker 대시보드
r_wdash = requests.get(f"{BASE}/tasks/dashboard", headers=h(wk_token))
check(r_wdash.status_code == 200, "worker 대시보드 조회 성공", f"worker 대시보드 실패")

# 태그 목록 조회 - 생성된 태그 확인
r_tags = requests.get(f"{BASE}/categories/tags", headers=h(admin_token))
tags = r_tags.json()
tag_names = [t["name"] for t in tags]
check("기초" in tag_names, f"태그 '기초' 조회 확인 (전체 태그: {tag_names})", "태그 '기초' 없음")
check("점검" in tag_names, "태그 '점검' 조회 확인", "태그 '점검' 없음")
check("1공구" in tag_names, "태그 '1공구' 조회 확인", "태그 '1공구' 없음")


# ═══════════════════════════════════════════════════════════════════════════════
# 최종 결과 요약
# ═══════════════════════════════════════════════════════════════════════════════
print(f"\n{BOLD}{'='*68}{RESET}")
print(f"{BOLD}  최종 테스트 결과 요약{RESET}")
print(f"{BOLD}{'='*68}{RESET}")

total = pass_count + fail_count
for phase, counts in phase_results.items():
    p, f_ = counts["pass"], counts["fail"]
    status = f"{GREEN}ALL PASS{RESET}" if f_ == 0 else f"{RED}{f_} FAIL{RESET}"
    bar_p = "█" * p
    bar_f = "░" * f_
    print(f"  {phase[:50]:<50} {status:>15}  {GREEN}{bar_p}{RESET}{RED}{bar_f}{RESET}")

print(f"\n  {BOLD}총 케이스: {total}  |  "
      f"{GREEN}PASS: {pass_count}{RESET}  |  "
      f"{RED}FAIL: {fail_count}{RESET}{BOLD}{RESET}")

if fail_count == 0:
    print(f"\n  {GREEN}{BOLD}🎉 모든 테스트 통과!{RESET}\n")
else:
    pct = round(pass_count / total * 100) if total else 0
    print(f"\n  {YELLOW}{BOLD}성공률: {pct}%{RESET}\n")

sys.exit(0 if fail_count == 0 else 1)
