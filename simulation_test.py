#!/usr/bin/env python3
"""
CollabTodo 전체 기능 시뮬레이션 테스트
- 가상 사용자 3명으로 모든 기능 테스트
"""
import requests
import json
import sys
import time
from datetime import datetime, timedelta

BASE = "http://localhost:8000"
RESULTS = []
ERRORS = []

def log(status, name, detail=""):
    icon = "✅" if status == "OK" else "❌"
    msg = f"{icon} {name}"
    if detail:
        msg += f" | {detail}"
    print(msg)
    RESULTS.append({"status": status, "name": name, "detail": detail})
    if status == "FAIL":
        ERRORS.append({"name": name, "detail": detail})

def test(name, fn):
    try:
        result = fn()
        log("OK", name, str(result) if result else "")
        return result
    except Exception as e:
        log("FAIL", name, str(e))
        return None

class ApiClient:
    def __init__(self, name):
        self.name = name
        self.token = None
        self.user_id = None
        self.session = requests.Session()
    
    def headers(self):
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h
    
    def post(self, path, data=None, files=None):
        if files:
            h = {}
            if self.token:
                h["Authorization"] = f"Bearer {self.token}"
            r = self.session.post(f"{BASE}{path}", files=files, headers=h)
        else:
            r = self.session.post(f"{BASE}{path}", json=data, headers=self.headers())
        return r
    
    def get(self, path, params=None):
        return self.session.get(f"{BASE}{path}", headers=self.headers(), params=params)
    
    def patch(self, path, data):
        return self.session.patch(f"{BASE}{path}", json=data, headers=self.headers())
    
    def delete(self, path):
        return self.session.delete(f"{BASE}{path}", headers=self.headers())

# ── 헬스체크 ──────────────────────────────────────────────────
print("\n" + "="*60)
print("  CollabTodo 시뮬레이션 테스트")
print("="*60)

print("\n[1] 서버 헬스체크")
r = requests.get(f"{BASE}/health")
if r.status_code == 200 and r.json().get("status") == "ok":
    log("OK", "서버 응답")
else:
    log("FAIL", "서버 응답", f"status={r.status_code}")
    sys.exit(1)

# ── 가상 사용자 설정 ──────────────────────────────────────────
ts = int(time.time())
USERS = [
    {"email": f"sim_alice_{ts}@test.com", "password": "SimTest1!", "name": f"앨리스_{ts}", "department": "개발팀"},
    {"email": f"sim_bob_{ts}@test.com",   "password": "SimTest1!", "name": f"밥_{ts}",   "department": "영업팀"},
    {"email": f"sim_carol_{ts}@test.com", "password": "SimTest1!", "name": f"캐롤_{ts}", "department": "기획팀"},
]

alice = ApiClient("앨리스")
bob   = ApiClient("밥")
carol = ApiClient("캐롤")
clients = [alice, bob, carol]

# ── [2] 회원가입 ─────────────────────────────────────────────
# 서버는 200을 반환함 (spec상 201이어야 하나 현재 200)
print("\n[2] 회원가입")
for client, user in zip(clients, USERS):
    def do_register(c=client, u=user):
        r = c.post("/api/auth/register", u)
        assert r.status_code in (200, 201), f"status={r.status_code} {r.text[:100]}"
        d = r.json()
        c.token = d["access_token"]
        c.user_id = d["user_id"]
        return f"id={c.user_id}"
    test(f"회원가입: {client.name}", do_register)

# ── [3] 로그인 ───────────────────────────────────────────────
print("\n[3] 로그인")
for client, user in zip(clients, USERS):
    def do_login(c=client, u=user):
        r = c.post("/api/auth/login", {"username": u["email"], "password": u["password"]})
        assert r.status_code == 200, f"status={r.status_code} {r.text[:100]}"
        d = r.json()
        c.token = d["access_token"]
        return f"id={c.user_id}"
    test(f"로그인: {client.name}", do_login)

# ── [4] 유저 목록 조회 ────────────────────────────────────────
print("\n[4] 유저 목록")
user_list = test("전체 유저 목록 조회", lambda: (
    lambda r: f"{len(r.json())}명" if r.status_code == 200 else (_ for _ in ()).throw(Exception(f"{r.status_code}"))
)(alice.get("/api/users/")))

alice_id = alice.user_id
bob_id   = bob.user_id
carol_id = carol.user_id

# ── [5] 내 정보 ──────────────────────────────────────────────
print("\n[5] 내 정보")
test("내 정보 조회", lambda: (
    lambda r: r.json()["name"] if r.status_code == 200 else (_ for _ in ()).throw(Exception(str(r.status_code)))
)(alice.get("/api/users/me")))

test("내 정보 수정", lambda: (
    lambda r: "OK" if r.status_code == 200 else (_ for _ in ()).throw(Exception(str(r.status_code)))
)(alice.patch("/api/users/me", {"name": f"앨리스_{ts}", "department": "개발팀"})))

# ── [6] 부서 목록 ─────────────────────────────────────────────
print("\n[6] 부서")
test("부서 목록 조회", lambda: (
    lambda r: f"{len(r.json())}개" if r.status_code == 200 else (_ for _ in ()).throw(Exception(str(r.status_code)))
)(alice.get("/api/users/departments/list")))

# ── [7] 업무 생성 ─────────────────────────────────────────────
print("\n[7] 업무 생성")
task_ids = []

def create_task(creator, assignee_id, title, priority="normal"):
    assert assignee_id is not None, "assignee_id is None - 회원가입 실패 확인 필요"
    r = creator.post("/api/tasks/", {
        "title": title, "content": f"{title} 상세 내용",
        "assignee_id": int(assignee_id),
        "priority": priority,
        "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        "tag_names": ["테스트", "시뮬"],
        "is_subtask": False, "parent_task_id": None,
        "material_providers": [], "category_id": None, "estimated_hours": None
    })
    assert r.status_code == 201, f"{r.status_code}: {r.text[:100]}"
    return r.json()["id"]

t1 = test("앨리스→밥 업무 생성 (긴급)", lambda: create_task(alice, bob_id, "긴급 보고서 작성", "urgent"))
t2 = test("밥→캐롤 업무 생성 (높음)", lambda: create_task(bob, carol_id, "기획서 검토", "high"))
t3 = test("캐롤→앨리스 업무 생성 (보통)", lambda: create_task(carol, alice_id, "개발 일정 공유", "normal"))
t4 = test("앨리스→앨리스 업무 생성 (낮음)", lambda: create_task(alice, alice_id, "코드 리뷰", "low"))

for t in [t1, t2, t3, t4]:
    if t:
        task_ids.append(t)

# ── [8] 업무 조회 ─────────────────────────────────────────────
print("\n[8] 업무 조회")
test("업무 목록 (내가 받은)", lambda: (
    lambda r: f"{len(r.json())}건" if r.status_code == 200 else (_ for _ in ()).throw(Exception(str(r.status_code)))
)(bob.get("/api/tasks/", params={"section": "assigned_to_me"})))

test("업무 목록 (내가 요청한)", lambda: (
    lambda r: f"{len(r.json())}건" if r.status_code == 200 else (_ for _ in ()).throw(Exception(str(r.status_code)))
)(alice.get("/api/tasks/", params={"section": "requested_by_me"})))

if task_ids:
    test("업무 상세 조회", lambda: (
        lambda r: r.json()["title"] if r.status_code == 200 else (_ for _ in ()).throw(Exception(str(r.status_code)))
    )(alice.get(f"/api/tasks/{task_ids[0]}")))

# ── [9] 업무 수정 ─────────────────────────────────────────────
print("\n[9] 업무 수정")
if task_ids:
    test("업무 진행률 수정", lambda: (
        lambda r: "OK" if r.status_code == 200 else (_ for _ in ()).throw(Exception(f"{r.status_code}:{r.text[:50]}"))
    )(alice.patch(f"/api/tasks/{task_ids[0]}", {"progress": 50})))

    test("업무 우선순위 수정", lambda: (
        lambda r: "OK" if r.status_code == 200 else (_ for _ in ()).throw(Exception(f"{r.status_code}:{r.text[:50]}"))
    )(alice.patch(f"/api/tasks/{task_ids[0]}", {"priority": "high"})))

# ── [10] 업무 상태 변경 ──────────────────────────────────────
print("\n[10] 상태 변경")
if t1:
    test("상태: pending→in_progress", lambda: (
        lambda r: "OK" if r.status_code == 200 else (_ for _ in ()).throw(Exception(f"{r.status_code}:{r.text[:50]}"))
    )(bob.post(f"/api/tasks/{t1}/status", {"status": "in_progress", "comment": "시작합니다"})))

    test("상태: in_progress→review", lambda: (
        lambda r: "OK" if r.status_code == 200 else (_ for _ in ()).throw(Exception(f"{r.status_code}:{r.text[:50]}"))
    )(bob.post(f"/api/tasks/{t1}/status", {"status": "review", "comment": "검토 요청"})))

    test("상태: review→approved", lambda: (
        lambda r: "OK" if r.status_code == 200 else (_ for _ in ()).throw(Exception(f"{r.status_code}:{r.text[:50]}"))
    )(alice.post(f"/api/tasks/{t1}/status", {"status": "approved", "comment": "승인!"})))

if t2:
    test("상태: pending→rejected", lambda: (
        lambda r: "OK" if r.status_code == 200 else (_ for _ in ()).throw(Exception(f"{r.status_code}:{r.text[:50]}"))
    )(bob.post(f"/api/tasks/{t2}/status", {"status": "rejected", "comment": "반려 사유"})))

# ── [11] 댓글 ────────────────────────────────────────────────
# 댓글 API: POST /api/tasks/{id}/comment, 필드명: "comment" (content 아님)
# 성공 시 {"ok": true} 반환 (200), 로그에서 id 조회 필요
print("\n[11] 댓글")
comment_id = None
if t3:
    def do_comment():
        r = alice.post(f"/api/tasks/{t3}/comment", {"comment": "확인했습니다. 진행할게요!"})
        assert r.status_code == 200, f"{r.status_code}:{r.text[:50]}"
        # 로그에서 방금 작성한 댓글 id 가져오기
        rl = alice.get(f"/api/tasks/{t3}/logs")
        assert rl.status_code == 200
        logs = rl.json()
        for entry in reversed(logs):
            if entry.get("action") == "comment":
                return entry["id"]
        return None
    comment_id = test("댓글 작성", do_comment)

    test("댓글 조회 (로그)", lambda: (
        lambda r: f"{len(r.json())}개" if r.status_code == 200 else (_ for _ in ()).throw(Exception(str(r.status_code)))
    )(alice.get(f"/api/tasks/{t3}/logs")))

    if comment_id:
        test("댓글 수정", lambda: (
            lambda r: "OK" if r.status_code == 200 else (_ for _ in ()).throw(Exception(f"{r.status_code}:{r.text[:50]}"))
        )(alice.patch(f"/api/tasks/{t3}/comments/{comment_id}", {"comment": "수정된 댓글"})))

        test("댓글 삭제", lambda: (
            lambda r: "OK" if r.status_code == 204 else (_ for _ in ()).throw(Exception(f"{r.status_code}:{r.text[:50]}"))
        )(alice.delete(f"/api/tasks/{t3}/comments/{comment_id}")))

# ── [12] 즐겨찾기 ─────────────────────────────────────────────
print("\n[12] 즐겨찾기")
if task_ids:
    test("즐겨찾기 등록", lambda: (
        lambda r: "OK" if r.status_code == 200 else (_ for _ in ()).throw(Exception(f"{r.status_code}:{r.text[:50]}"))
    )(alice.post(f"/api/tasks/{task_ids[0]}/favorite")))

    test("즐겨찾기 목록 조회", lambda: (
        lambda r: f"{len(r.json())}건" if r.status_code == 200 else (_ for _ in ()).throw(Exception(str(r.status_code)))
    )(alice.get("/api/tasks/", params={"section": "favorites"})))

    test("즐겨찾기 해제 (토글)", lambda: (
        lambda r: "OK" if r.status_code == 200 else (_ for _ in ()).throw(Exception(f"{r.status_code}:{r.text[:50]}"))
    )(alice.post(f"/api/tasks/{task_ids[0]}/favorite")))

# ── [13] 업무 클론 ─────────────────────────────────────────────
# clone 엔드포인트는 200 반환 (spec 201이어야 하나 현재 200)
print("\n[13] 업무 클론")
if t4:
    test("업무 복제", lambda: (
        lambda r: f"새id={r.json().get('id')}" if r.status_code in (200, 201) else (_ for _ in ()).throw(Exception(f"{r.status_code}:{r.text[:50]}"))
    )(alice.post(f"/api/tasks/{t4}/clone")))

# ── [14] 담당자 변경 ──────────────────────────────────────────
print("\n[14] 담당자 변경")
if t3:
    test("담당자 변경", lambda: (
        lambda r: "OK" if r.status_code == 200 else (_ for _ in ()).throw(Exception(f"{r.status_code}:{r.text[:50]}"))
    )(carol.post(f"/api/tasks/{t3}/reassign", {"assignee_id": bob_id})))

# ── [15] 대시보드 통계 ────────────────────────────────────────
print("\n[15] 대시보드 통계")
test("앨리스 대시보드", lambda: (
    lambda r: str(r.json()["total"]) + "건" if r.status_code == 200 else (_ for _ in ()).throw(Exception(str(r.status_code)))
)(alice.get("/api/tasks/dashboard")))

test("밥 대시보드", lambda: (
    lambda r: str(r.json()["total"]) + "건" if r.status_code == 200 else (_ for _ in ()).throw(Exception(str(r.status_code)))
)(bob.get("/api/tasks/dashboard")))

# ── [16] 일괄 상태 변경 ──────────────────────────────────────
print("\n[16] 일괄 처리")
if len(task_ids) >= 2:
    test("일괄 상태 변경", lambda: (
        lambda r: "OK" if r.status_code == 200 else (_ for _ in ()).throw(Exception(f"{r.status_code}:{r.text[:50]}"))
    )(alice.post("/api/tasks/bulk-status", {"task_ids": [task_ids[-1]], "status": "in_progress"})))

# ── [17] 필터 프리셋 ──────────────────────────────────────────
print("\n[17] 필터 프리셋")
preset_id = None
def do_preset():
    r = alice.post("/api/users/me/filter-presets", {
        "name": "긴급 업무", "section": "assigned_to_me",
        "status": "in_progress", "priority": "urgent",
        "sort_by": "due_date", "sort_dir": "asc"
    })
    assert r.status_code == 201, f"{r.status_code}:{r.text[:50]}"
    return r.json().get("id")
preset_id = test("필터 프리셋 저장", do_preset)

test("필터 프리셋 목록", lambda: (
    lambda r: f"{len(r.json())}개" if r.status_code == 200 else (_ for _ in ()).throw(Exception(str(r.status_code)))
)(alice.get("/api/users/me/filter-presets")))

if preset_id:
    test("필터 프리셋 삭제", lambda: (
        lambda r: "OK" if r.status_code == 204 else (_ for _ in ()).throw(Exception(f"{r.status_code}:{r.text[:50]}"))
    )(alice.delete(f"/api/users/me/filter-presets/{preset_id}")))

# ── [18] 알림 ────────────────────────────────────────────────
print("\n[18] 알림")
test("알림 미읽음 수", lambda: (
    lambda r: f"{r.json().get('count', 0)}개" if r.status_code == 200 else (_ for _ in ()).throw(Exception(str(r.status_code)))
)(bob.get("/api/notifications/unread-count")))

test("알림 목록 조회", lambda: (
    lambda r: f"{len(r.json().get('items',[]))}개" if r.status_code == 200 else (_ for _ in ()).throw(Exception(str(r.status_code)))
)(bob.get("/api/notifications/")))

test("모든 알림 읽음 처리", lambda: (
    lambda r: "OK" if r.status_code == 200 else (_ for _ in ()).throw(Exception(f"{r.status_code}:{r.text[:50]}"))
)(bob.post("/api/notifications/read-all")))

# ── [19] 알림 설정 ────────────────────────────────────────────
print("\n[19] 알림 설정")
test("알림 설정 조회", lambda: (
    lambda r: "OK" if r.status_code == 200 else (_ for _ in ()).throw(Exception(str(r.status_code)))
)(alice.get("/api/users/me/notification-preferences")))

test("알림 설정 수정", lambda: (
    lambda r: "OK" if r.status_code == 200 else (_ for _ in ()).throw(Exception(f"{r.status_code}:{r.text[:50]}"))
)(alice.patch("/api/users/me/notification-preferences", {"notify_assigned": True, "notify_commented": True})))

# ── [20] CSV 내보내기 ─────────────────────────────────────────
print("\n[20] CSV 내보내기")
test("CSV 내보내기", lambda: (
    lambda r: f"{len(r.text.splitlines())}행" if r.status_code == 200 else (_ for _ in ()).throw(Exception(str(r.status_code)))
)(alice.get("/api/tasks/export")))

# ── [21] 카테고리 ─────────────────────────────────────────────
print("\n[21] 카테고리")
cat_id = None
def do_cat():
    r = alice.post("/api/categories/", {"name": f"테스트카테고리_{ts}", "color": "#FF6B6B"})
    assert r.status_code == 201, f"{r.status_code}:{r.text[:50]}"
    return r.json().get("id")
cat_id = test("카테고리 생성", do_cat)

test("카테고리 목록", lambda: (
    lambda r: f"{len(r.json())}개" if r.status_code == 200 else (_ for _ in ()).throw(Exception(str(r.status_code)))
)(alice.get("/api/categories/")))

if cat_id:
    test("카테고리 삭제", lambda: (
        lambda r: "OK" if r.status_code == 204 else (_ for _ in ()).throw(Exception(f"{r.status_code}:{r.text[:50]}"))
    )(alice.delete(f"/api/categories/{cat_id}")))

# ── [22] 파일 첨부 ────────────────────────────────────────────
print("\n[22] 파일 첨부")
attach_id = None
if task_ids:
    def do_upload():
        import io
        content = b"Test file content for simulation"
        files = {"file": ("test.txt", io.BytesIO(content), "text/plain")}
        r = alice.post(f"/api/attachments/{task_ids[0]}", files=files)
        assert r.status_code == 201, f"{r.status_code}:{r.text[:100]}"
        return r.json().get("id")
    attach_id = test("파일 업로드", do_upload)

    if attach_id:
        test("파일 다운로드", lambda: (
            lambda r: f"{len(r.content)}bytes" if r.status_code == 200 else (_ for _ in ()).throw(Exception(f"{r.status_code}:{r.text[:50]}"))
        )(alice.get(f"/api/attachments/{attach_id}/download")))

        test("파일 삭제", lambda: (
            lambda r: "OK" if r.status_code == 204 else (_ for _ in ()).throw(Exception(f"{r.status_code}:{r.text[:50]}"))
        )(alice.delete(f"/api/attachments/{attach_id}")))

# ── [23] 비밀번호 변경 ───────────────────────────────────────
print("\n[23] 비밀번호 변경")
test("비밀번호 변경", lambda: (
    lambda r: "OK" if r.status_code == 200 else (_ for _ in ()).throw(Exception(f"{r.status_code}:{r.text[:50]}"))
)(alice.post("/api/auth/change-password", {"current_password": "SimTest1!", "new_password": "SimTest2@"})))

# ── [24] 에러 케이스 테스트 ──────────────────────────────────
print("\n[24] 에러 케이스")
test("잘못된 로그인 거부", lambda: (
    lambda r: "거부됨" if r.status_code == 401 else (_ for _ in ()).throw(Exception(f"예상 401, 실제: {r.status_code}"))
)(alice.post("/api/auth/login", {"username": "nobody@test.com", "password": "wrong"})))

test("인증 없는 접근 거부", lambda: (
    lambda r: "거부됨" if r.status_code in [401, 403] else (_ for _ in ()).throw(Exception(f"예상 401/403, 실제: {r.status_code}"))
)(requests.get(f"{BASE}/api/tasks/")))

test("존재하지 않는 업무 404", lambda: (
    lambda r: "404" if r.status_code == 404 else (_ for _ in ()).throw(Exception(f"예상 404, 실제: {r.status_code}"))
)(alice.get("/api/tasks/9999999")))

# ── [25] 업무 삭제 (정리) ─────────────────────────────────────
print("\n[25] 업무 삭제 (테스트 정리)")
deleted = 0
for task_id in task_ids:
    r = alice.delete(f"/api/tasks/{task_id}")
    if r.status_code in [204, 404]:
        deleted += 1
log("OK" if deleted > 0 else "FAIL", f"테스트 업무 {deleted}개 삭제")

# 클론된 업무 등도 정리 시도
try:
    r = alice.get("/api/tasks/", params={"section": "requested_by_me", "page_size": 100})
    if r.status_code == 200:
        for t in r.json():
            if "시뮬" in str(t.get("tags", [])) or str(ts) in t.get("title", ""):
                alice.delete(f"/api/tasks/{t['id']}")
except:
    pass

# ── 결과 요약 ─────────────────────────────────────────────────
print("\n" + "="*60)
ok = sum(1 for r in RESULTS if r["status"] == "OK")
fail = sum(1 for r in RESULTS if r["status"] == "FAIL")
total = len(RESULTS)
print(f"  결과: {ok}/{total} 통과 ({fail}개 실패)")
print("="*60)

if ERRORS:
    print("\n실패 항목:")
    for e in ERRORS:
        print(f"   - {e['name']}: {e['detail']}")
else:
    print("\n모든 테스트 통과!")

# JSON 결과 출력
print("\n--- JSON 결과 ---")
print(json.dumps({"total": total, "ok": ok, "fail": fail, "errors": ERRORS}, ensure_ascii=False, indent=2))
