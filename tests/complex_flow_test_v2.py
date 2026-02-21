import requests, subprocess, sys, time
from datetime import date, timedelta

BASE = "http://localhost:8000/api"
G="[92m";R="[91m";Y="[93m";C="[96m";B="[1m";X="[0m"
pc=0;fc=0;pr={};cp=""

def section(t):
    global cp
    cp=t; pr[t]={"p":0,"f":0}
    print(f"\n{C}{B}{'='*68}{X}\n{C}{B}  {t}{X}\n{C}{B}{'='*68}{X}")

def ok(m):
    global pc; pc+=1; pr[cp]["p"]+=1; print(f"  {G}✓{X}  {m}")

def fail(m,d=""):
    global fc; fc+=1; pr[cp]["f"]+=1; print(f"  {R}✗{X}  {B}{m}{X}")
    if d: print(f"       {R}→ {d}{X}")

def check(c,ok_m,fail_m,d=""):
    ok(ok_m) if c else fail(fail_m,d)

def dbq(sql):
    r=subprocess.run(["mysql","-u","collab_user","-ptest1234","collab_todo","-se",sql,"--skip-column-names"],capture_output=True,text=True)
    return r.stdout.strip()

def login(e,p):
    r=requests.post(f"{BASE}/auth/login",data={"username":e,"password":p})
    return r.json().get("access_token") if r.status_code==200 else None

def h(t): return {"Authorization":f"Bearer {t}"}
def st(tok,tid,status,comment=None):
    p={"status":status}
    if comment: p["comment"]=comment
    return requests.post(f"{BASE}/tasks/{tid}/status",headers=h(tok),json=p)

ctx={}
TS=int(time.time())
TODAY=date.today()
DUE14=(TODAY+timedelta(days=14)).isoformat()
DUE7=(TODAY+timedelta(days=7)).isoformat()
DUE3=(TODAY+timedelta(days=3)).isoformat()

# ═══ PHASE 0: 6개 부서 사용자 등록 ═══════════════════════════════════
section("PHASE 0: 6개 부서 사용자 등록")
admin_token=login("test@test.com","test1234")
check(admin_token is not None,"Admin 로그인 성공","Admin 로그인 실패")
ctx["admin"]=admin_token
ctx["admin_id"]=requests.get(f"{BASE}/auth/me",headers=h(admin_token)).json().get("id")

USERS=[
    ("김현장","현장소장",f"mgr{TS}@gmail.com","Mgr12345","mgr"),
    ("이공사","공사팀",  f"con{TS}@gmail.com","Con12345","con"),
    ("박공무","공무팀",  f"adm{TS}@gmail.com","Adm12345","adm"),
    ("최품질","품질팀",  f"qlt{TS}@gmail.com","Qlt12345","qlt"),
    ("안전맨","안전팀",  f"saf{TS}@gmail.com","Saf12345","saf"),
]
EMAILS={key: email for _,_,email,_,key in USERS}
for name,dept,email,pw,key in USERS:
    r=requests.post(f"{BASE}/auth/register",json={"email":email,"password":pw,"name":name,"department_name":dept})
    check(r.status_code==201,f"{name}({dept}) 회원가입 성공",f"{name} 등록 실패 {r.status_code}",r.text)
    d=r.json()
    ctx[f"{key}_token"]=d.get("access_token")
    ctx[f"{key}_id"]=d.get("user_id")
print(f"  {Y}→ IDs: admin={ctx['admin_id']} mgr={ctx['mgr_id']} con={ctx['con_id']} adm={ctx['adm_id']} qlt={ctx['qlt_id']} saf={ctx['saf_id']}{X}")

# ═══ PHASE 1: 카테고리 3개 ════════════════════════════════════════════
section("PHASE 1: 카테고리 시스템 (3개)")
for cname,color in [(f"시공관리_{TS}","#ef4444"),(f"품질안전_{TS}","#f59e0b"),(f"행정공무_{TS}","#3b82f6")]:
    r=requests.post(f"{BASE}/categories/",json={"name":cname,"color":color},headers=h(admin_token))
    check(r.status_code==201,f"카테고리 '{cname}' 생성",f"카테고리 생성 실패",r.text)
    if "시공" in cname: ctx["cat_A"]=r.json().get("id")
    elif "품질" in cname: ctx["cat_B"]=r.json().get("id")
    else: ctx["cat_C"]=r.json().get("id")
r=requests.post(f"{BASE}/categories/",json={"name":f"시공관리_{TS}"},headers=h(admin_token))
check(r.status_code==400,"중복 카테고리 → 400 확인","중복 카테고리 차단 실패",r.text)
cats=requests.get(f"{BASE}/categories/",headers=h(admin_token)).json()
check(len(cats)>=3,f"카테고리 목록 조회 ({len(cats)}개)","카테고리 목록 조회 실패")

# ═══ PHASE 2: Task A — Admin→현장소장, material_providers=[공사팀, 공무팀] ═══
section("PHASE 2: Task A — material_providers 2명 동시 자동 서브태스크")
r=requests.post(f"{BASE}/tasks/",headers=h(admin_token),json={
    "title":"1공구 전체 시공 현황 종합 점검","content":"전 부서 협력 점검.",
    "assignee_id":ctx["mgr_id"],"category_id":ctx["cat_A"],"priority":"high",
    "due_date":DUE14,"tag_names":["시공","점검","긴급"],
    "material_providers":[
        {"assignee_id":ctx["con_id"],"title":"공사팀 시공계획서 제출","due_date":DUE7},
        {"assignee_id":ctx["adm_id"],"title":"공무팀 행정서류 준비","due_date":DUE7},
    ],
})
check(r.status_code==201,"Task A 생성 성공 (material_providers 2명)",f"Task A 생성 실패 {r.status_code}",r.text)
ta=r.json(); ctx["task_a"]=ta["id"]
check(ta.get("subtask_count",0)>=2,f"자동 서브태스크 2개 확인 (count={ta.get('subtask_count')})",f"자동 서브태스크 실패 (count={ta.get('subtask_count')})")
tags_a=[t["name"] for t in ta.get("tags",[])]
check("시공" in tags_a and "긴급" in tags_a,f"Task A 태그 확인 {tags_a}","태그 연결 실패")

subs_con=requests.get(f"{BASE}/tasks/",headers=h(ctx["con_token"]),params={"section":"subtasks_to_me"}).json().get("items",[])
subs_adm=requests.get(f"{BASE}/tasks/",headers=h(ctx["adm_token"]),params={"section":"subtasks_to_me"}).json().get("items",[])
ctx["auto_a1"]=subs_con[0]["id"] if subs_con else None
ctx["auto_a2"]=subs_adm[0]["id"] if subs_adm else None
check(ctx["auto_a1"] is not None,f"Auto-A1(공사팀) id={ctx['auto_a1']} 조회","Auto-A1 조회 실패")
check(ctx["auto_a2"] is not None,f"Auto-A2(공무팀) id={ctx['auto_a2']} 조회","Auto-A2 조회 실패")
print(f"  {Y}→ task_a={ctx['task_a']} auto_a1={ctx['auto_a1']} auto_a2={ctx['auto_a2']}{X}")

# ═══ PHASE 3: Task A 수동 서브태스크 (품질팀·안전팀) ═════════════════
section("PHASE 3: Task A 수동 서브태스크 — 품질팀·안전팀")
r=requests.post(f"{BASE}/tasks/",headers=h(admin_token),json={
    "title":"품질팀 검수 결과서 제출","assignee_id":ctx["qlt_id"],
    "priority":"urgent","due_date":DUE3,"parent_task_id":ctx["task_a"],"is_subtask":True,"tag_names":["품질","긴급"]})
check(r.status_code==201,"Manual-A3(품질팀) 생성 성공",f"생성 실패 {r.status_code}",r.text)
ctx["man_a3"]=r.json()["id"]

r=requests.post(f"{BASE}/tasks/",headers=h(admin_token),json={
    "title":"안전팀 현장 안전 점검표 제출","assignee_id":ctx["saf_id"],
    "priority":"high","due_date":DUE7,"parent_task_id":ctx["task_a"],"is_subtask":True})
check(r.status_code==201,"Manual-A4(안전팀) 생성 성공",f"생성 실패 {r.status_code}",r.text)
ctx["man_a4"]=r.json()["id"]
print(f"  {Y}→ man_a3(품질)={ctx['man_a3']} man_a4(안전)={ctx['man_a4']}{X}")

# ═══ PHASE 4: Task B (현장소장→공사팀) + Sub-B1(공무팀) ══════════════
section("PHASE 4: Task B — 현장소장→공사팀 + Sub-B1→공무팀")
r=requests.post(f"{BASE}/tasks/",headers=h(ctx["mgr_token"]),json={
    "title":"2공구 콘크리트 타설 일정 수립","assignee_id":ctx["con_id"],
    "category_id":ctx["cat_A"],"priority":"normal","due_date":DUE14,"tag_names":["콘크리트","2공구"]})
check(r.status_code==201,"Task B(현장소장→공사팀) 생성 성공",f"Task B 생성 실패 {r.status_code}",r.text)
ctx["task_b"]=r.json()["id"]

r=requests.post(f"{BASE}/tasks/",headers=h(ctx["mgr_token"]),json={
    "title":"공무팀 타설 행정 지원","assignee_id":ctx["adm_id"],
    "priority":"normal","parent_task_id":ctx["task_b"],"is_subtask":True})
check(r.status_code==201,"Sub-B1(공무팀) 생성 성공",f"생성 실패 {r.status_code}",r.text)
ctx["sub_b1"]=r.json()["id"]
print(f"  {Y}→ task_b={ctx['task_b']} sub_b1={ctx['sub_b1']}{X}")

# ═══ PHASE 5: Task C (공무팀→품질팀) + material_providers=[안전팀] + Task D ═══
section("PHASE 5: Task C — 공무팀→품질팀 (material_providers=[안전팀]) + Task D")
r=requests.post(f"{BASE}/tasks/",headers=h(ctx["adm_token"]),json={
    "title":"품질 인증 서류 최종 검토","assignee_id":ctx["qlt_id"],
    "category_id":ctx["cat_B"],"priority":"high","due_date":DUE14,"tag_names":["품질인증","서류"],
    "material_providers":[{"assignee_id":ctx["saf_id"],"title":"안전팀 검토 의견서","due_date":DUE7}]})
check(r.status_code==201,"Task C(공무팀→품질팀) + material_providers=[안전팀] 성공",f"Task C 실패 {r.status_code}",r.text)
tc=r.json(); ctx["task_c"]=tc["id"]
check(tc.get("subtask_count",0)>=1,f"Auto-C1(안전팀) 자동 서브태스크 확인 (count={tc.get('subtask_count')})","Auto-C1 생성 실패")

subs_saf=requests.get(f"{BASE}/tasks/",headers=h(ctx["saf_token"]),params={"section":"subtasks_to_me"}).json().get("items",[])
ctx["auto_c1"]=subs_saf[0]["id"] if subs_saf else None
check(ctx["auto_c1"] is not None,f"Auto-C1(안전팀) id={ctx['auto_c1']} 조회","Auto-C1 조회 실패")

r=requests.post(f"{BASE}/tasks/",headers=h(admin_token),json={
    "title":"안전관리 종합보고서 제출","assignee_id":ctx["saf_id"],
    "priority":"urgent","due_date":DUE3,"tag_names":["안전","보고서"]})
check(r.status_code==201,"Task D(Admin→안전팀, rejected재처리용) 생성 성공",f"Task D 실패 {r.status_code}",r.text)
ctx["task_d"]=r.json()["id"]
print(f"  {Y}→ task_c={ctx['task_c']} auto_c1={ctx['auto_c1']} task_d={ctx['task_d']}{X}")

# ═══ PHASE 6: 업무 복제 (3가지) ══════════════════════════════════════
section("PHASE 6: 업무 복제 (clone) — 성공 2, 실패 1")
r=requests.post(f"{BASE}/tasks/{ctx['task_a']}/clone",headers=h(admin_token))
check(r.status_code==201,"Admin: Task A 복제 성공",f"복제 실패 {r.status_code}",r.text)
ctx["clone_a"]=r.json().get("task_id")
if ctx["clone_a"]:
    title=requests.get(f"{BASE}/tasks/{ctx['clone_a']}",headers=h(admin_token)).json().get("title","")
    check("[복사]" in title,f"복제 제목 '[복사]' 포함: '{title}'","복제 제목 형식 오류")

r=requests.post(f"{BASE}/tasks/{ctx['task_c']}/clone",headers=h(ctx["qlt_token"]))
check(r.status_code==201,"품질팀: 본인 배정 Task C 복제 성공",f"복제 실패 {r.status_code}",r.text)
ctx["clone_c"]=r.json().get("task_id")

r=requests.post(f"{BASE}/tasks/{ctx['task_b']}/clone",headers=h(ctx["adm_token"]))
check(r.status_code==403,"공무팀: 무관 업무(Task B) 복제 시도 → 403",f"권한 미작동 got {r.status_code}")

# ═══ PHASE 7: 각 사용자별 업무 뷰 검증 ══════════════════════════════
section("PHASE 7: 사용자별 업무 뷰 검증 (section 필터)")
items=requests.get(f"{BASE}/tasks/",headers=h(ctx["mgr_token"]),params={"section":"assigned_to_me"}).json().get("items",[])
check(any(t["id"]==ctx["task_a"] for t in items),f"현장소장 assigned_to_me → Task A 포함 ({len(items)}개)","현장소장 배정 업무 조회 실패")

items=requests.get(f"{BASE}/tasks/",headers=h(ctx["mgr_token"]),params={"section":"assigned_by_me"}).json().get("items",[])
check(any(t["id"]==ctx["task_b"] for t in items),f"현장소장 assigned_by_me → Task B 포함 ({len(items)}개)","현장소장 지시 업무 조회 실패")

items=requests.get(f"{BASE}/tasks/",headers=h(ctx["con_token"]),params={"section":"assigned_to_me"}).json().get("items",[])
check(any(t["id"]==ctx["task_b"] for t in items),f"공사팀 assigned_to_me → Task B 포함 ({len(items)}개)","공사팀 배정 업무 조회 실패")

items=requests.get(f"{BASE}/tasks/",headers=h(ctx["con_token"]),params={"section":"subtasks_to_me"}).json().get("items",[])
check(any(t["id"]==ctx["auto_a1"] for t in items),f"공사팀 subtasks_to_me → Auto-A1 포함 ({len(items)}개)","공사팀 서브태스크 조회 실패")

items_main=requests.get(f"{BASE}/tasks/",headers=h(ctx["adm_token"]),params={"section":"assigned_by_me"}).json().get("items",[])
items_sub=requests.get(f"{BASE}/tasks/",headers=h(ctx["adm_token"]),params={"section":"subtasks_to_me"}).json().get("items",[])
check(any(t["id"]==ctx["task_c"] for t in items_main),f"공무팀 assigned_by_me → Task C 포함","공무팀 지시 업무 조회 실패")
check(len(items_sub)>=2,f"공무팀 subtasks_to_me → {len(items_sub)}개 (Auto-A2, Sub-B1)","공무팀 서브태스크 조회 실패")

items_saf_sub=requests.get(f"{BASE}/tasks/",headers=h(ctx["saf_token"]),params={"section":"subtasks_to_me"}).json().get("items",[])
items_saf_main=requests.get(f"{BASE}/tasks/",headers=h(ctx["saf_token"]),params={"section":"assigned_to_me"}).json().get("items",[])
check(len(items_saf_sub)>=2,f"안전팀 subtasks_to_me → {len(items_saf_sub)}개","안전팀 서브태스크 조회 실패")
check(any(t["id"]==ctx["task_d"] for t in items_saf_main),f"안전팀 assigned_to_me → Task D 포함","안전팀 Task D 조회 실패")

# ═══ PHASE 8: 6개 부서 댓글 등록 ════════════════════════════════════
section("PHASE 8: 6개 부서 댓글 등록")
COMMENT_CFG=[
    (ctx["mgr_token"],ctx["task_a"], ctx["mgr_id"],"현장소장","task_a","현장 전체 점검 시작합니다."),
    (ctx["con_token"],ctx["auto_a1"],ctx["con_id"],"공사팀",  "auto_a1","시공계획서 작성 중입니다."),
    (ctx["adm_token"],ctx["auto_a2"],ctx["adm_id"],"공무팀",  "auto_a2","행정서류 준비 중입니다."),
    (ctx["qlt_token"],ctx["man_a3"], ctx["qlt_id"],"품질팀",  "man_a3","품질 검수 착수합니다."),
    (ctx["saf_token"],ctx["man_a4"], ctx["saf_id"],"안전팀",  "man_a4","안전 점검 완료 예정."),
    (ctx["adm_token"],ctx["task_c"], ctx["adm_id"],"공무팀",  "task_c","품질 인증 서류 검토 시작."),
]
for tok,tid,uid,label,key,msg in COMMENT_CFG:
    r=requests.post(f"{BASE}/tasks/{tid}/comment",headers=h(tok),json={"comment":msg})
    check(r.status_code in (200,201),f"{label}: 댓글 등록 성공",f"{label} 댓글 실패 {r.status_code}",r.text)
    logs=requests.get(f"{BASE}/tasks/{tid}/logs",headers=h(admin_token)).json()
    clogs=[l for l in logs if l["action"]=="comment" and l.get("user",{}).get("id")==uid]
    if clogs: ctx[f"comment_{key}"]=clogs[-1]["id"]

# ═══ PHASE 9: 교차 부서 권한 경계 (11가지) ═══════════════════════════
section("PHASE 9: 교차 부서 권한 경계 (11가지 403/401/400)")
r=requests.patch(f"{BASE}/tasks/{ctx['task_c']}",headers=h(ctx["con_token"]),json={"title":"해킹시도"})
check(r.status_code==403,"① 공사팀→Task C(공무팀→품질팀) PATCH → 403",f"권한 미작동 {r.status_code}")

r=requests.post(f"{BASE}/tasks/{ctx['man_a3']}/status",headers=h(ctx["adm_token"]),json={"status":"in_progress"})
check(r.status_code==403,"② 공무팀→품질팀 서브(Man-A3) 상태변경 → 403",f"권한 미작동 {r.status_code}")

r=requests.delete(f"{BASE}/tasks/{ctx['man_a4']}",headers=h(ctx["qlt_token"]))
check(r.status_code==403,"③ 품질팀→안전팀 서브(Man-A4) DELETE → 403",f"권한 미작동 {r.status_code}")

if ctx.get("comment_auto_a1"):
    r=requests.patch(f"{BASE}/tasks/{ctx['auto_a1']}/comments/{ctx['comment_auto_a1']}",headers=h(ctx["saf_token"]),json={"comment":"타인댓글"})
    check(r.status_code==403,"④ 안전팀→공사팀 댓글 수정 시도 → 403",f"권한 미작동 {r.status_code}")

r=requests.delete(f"{BASE}/tasks/{ctx['task_a']}",headers=h(ctx["con_token"]))
check(r.status_code==403,"⑤ 공사팀→Task A(Admin→현장소장) DELETE → 403",f"권한 미작동 {r.status_code}")

r=requests.post(f"{BASE}/tasks/{ctx['task_d']}/status",headers=h(ctx["qlt_token"]),json={"status":"in_progress"})
check(r.status_code==403,"⑥ 품질팀→Task D(Admin→안전팀) 상태변경 → 403",f"권한 미작동 {r.status_code}")

if ctx.get("comment_task_a"):
    r=requests.patch(f"{BASE}/tasks/{ctx['task_a']}/comments/{ctx['comment_task_a']}",headers=h(ctx["adm_token"]),json={"comment":"타인댓글수정"})
    check(r.status_code==403,"⑦ 공무팀→현장소장 댓글 수정 → 403",f"권한 미작동 {r.status_code}")

r=requests.get(f"{BASE}/auth/me")
check(r.status_code in (401,403),f"⑧ 토큰 없이 /me → {r.status_code}","인증 미작동")

r=requests.get(f"{BASE}/auth/me",headers={"Authorization":"Bearer INVALID.XYZ"})
check(r.status_code in (401,403),f"⑨ 잘못된 토큰 → {r.status_code}","토큰 검증 미작동")

r=requests.post(f"{BASE}/auth/login",data={"username":"test@test.com","password":"WRONG"})
check(r.status_code==401,"⑩ 잘못된 비밀번호 → 401","비밀번호 검증 미작동")

r=requests.post(f"{BASE}/tasks/{ctx['task_d']}/status",headers=h(admin_token),json={"status":"rejected"})
check(r.status_code==400,"⑪ rejected comment 없음 → 400","rejected 검증 미작동")

# ═══ PHASE 10: 알림 팬아웃 — 6명 독립 검증 ══════════════════════════
section("PHASE 10: 알림 팬아웃 — 5명 독립 검증")
for label,key in [("현장소장","mgr"),("공사팀","con"),("공무팀","adm"),("품질팀","qlt"),("안전팀","saf")]:
    tok=ctx[f"{key}_token"]
    notifs=requests.get(f"{BASE}/notifications/",headers=h(tok)).json()
    cnt=requests.get(f"{BASE}/notifications/unread-count",headers=h(tok)).json().get("count",0)
    check(len(notifs)>0,f"{label}: 알림 {len(notifs)}개 수신 확인",f"{label} 알림 없음")
    check(cnt>0,f"{label}: unread={cnt} 확인",f"{label} unread=0 (알림 미도달)")

requests.post(f"{BASE}/notifications/read-all",headers=h(ctx["mgr_token"]))
cnt=requests.get(f"{BASE}/notifications/unread-count",headers=h(ctx["mgr_token"])).json().get("count",-1)
check(cnt==0,f"현장소장 전체 읽음 후 unread=0 ({cnt})","전체 읽음 미작동")

notifs_con=requests.get(f"{BASE}/notifications/",headers=h(ctx["con_token"])).json()
if notifs_con:
    nid=notifs_con[0]["id"]
    r=requests.post(f"{BASE}/notifications/{nid}/read",headers=h(ctx["con_token"]))
    check(r.status_code==200,f"공사팀 알림 {nid} 개별 읽음 성공",f"알림 읽음 실패 {r.status_code}")

# ═══ PHASE 11: 10개 업무 전체 상태 라이프사이클 ═══════════════════════
section("PHASE 11: 전체 상태 라이프사이클 (10개 업무 동시 진행)")

# 경로A: pending→in_progress→review→approved (7개 업무)
flows_ok=[
    (ctx["mgr_token"],ctx["task_a"],"현장소장→Task A"),
    (ctx["con_token"],ctx["auto_a1"],"공사팀→Auto-A1"),
    (ctx["adm_token"],ctx["auto_a2"],"공무팀→Auto-A2"),
    (ctx["saf_token"],ctx["man_a4"],"안전팀→Man-A4"),
    (ctx["con_token"],ctx["task_b"],"공사팀→Task B"),
    (ctx["adm_token"],ctx["sub_b1"],"공무팀→Sub-B1"),
    (ctx["saf_token"],ctx["auto_c1"],"안전팀→Auto-C1"),
]
for tok,tid,label in flows_ok:
    r1=st(tok,tid,"in_progress","작업 시작합니다.")
    check(r1.status_code==200,f"{label}: pending→in_progress",f"실패 {r1.status_code}")
    r2=st(tok,tid,"review","검토 요청합니다.")
    check(r2.status_code==200,f"{label}: in_progress→review",f"실패 {r2.status_code}")
    r3=st(admin_token,tid,"approved","승인 완료.")
    check(r3.status_code==200,f"{label}: review→approved(admin)",f"실패 {r3.status_code}")

# 경로B: rejected 재처리 — Man-A3(품질팀)
for status,tok,msg,label in [
    ("in_progress",ctx["qlt_token"],None,"품질팀→Man-A3: pending→in_progress"),
    ("review",ctx["qlt_token"],"1차 검토 완료","품질팀→Man-A3: in_progress→review"),
    ("rejected",admin_token,"수정 후 재제출 요청","Admin→Man-A3: review→rejected"),
    ("in_progress",ctx["qlt_token"],"수정 후 재진행","품질팀→Man-A3: rejected→in_progress"),
    ("approved",admin_token,"재검토 후 최종 승인","Admin→Man-A3: in_progress→approved"),
]:
    r=st(ctx["qlt_token"] if "qlt" in tok else admin_token, ctx["man_a3"],status,msg)
    check(r.status_code==200,label,f"실패 {r.status_code}")

# 경로C: Task C rejected 재처리 (공무팀→품질팀)
for status,tok,msg,label in [
    ("in_progress",ctx["qlt_token"],None,"품질팀→Task C: pending→in_progress"),
    ("review",ctx["qlt_token"],"검토 완료","품질팀→Task C: in_progress→review"),
    ("rejected",ctx["adm_token"],"내용 보완 필요","공무팀→Task C: review→rejected(assigner)"),
    ("in_progress",ctx["qlt_token"],"보완 후 재진행","품질팀→Task C: rejected→in_progress"),
    ("approved",ctx["adm_token"],"최종 승인","공무팀→Task C: in_progress→approved"),
]:
    r=st(tok,ctx["task_c"],status,msg)
    check(r.status_code==200,label,f"실패 {r.status_code}")

# 경로D: Task D double-rejected (Admin→안전팀)
for status,tok,msg,label in [
    ("in_progress",ctx["saf_token"],None,"안전팀→Task D: pending→in_progress"),
    ("rejected",admin_token,"보고서 형식 오류","Admin→Task D: in_progress→rejected(1차)"),
    ("in_progress",ctx["saf_token"],"형식 수정 후 재진행","안전팀→Task D: rejected→in_progress"),
    ("review",ctx["saf_token"],"최종본 제출","안전팀→Task D: in_progress→review"),
    ("approved",admin_token,"최종 승인","Admin→Task D: review→approved"),
]:
    r=st(tok,ctx["task_d"],status,msg)
    check(r.status_code==200,label,f"실패 {r.status_code}")

logs_d=requests.get(f"{BASE}/tasks/{ctx['task_d']}/logs",headers=h(admin_token)).json()
sc_logs=[l for l in logs_d if l["action"]=="status_changed"]
check(len(sc_logs)>=4,f"Task D 상태변경 로그 {len(sc_logs)}개 확인 (최소 4)","상태변경 로그 부족")

# ═══ PHASE 12: 업무 수정 흐름 ════════════════════════════════════════
section("PHASE 12: 업무 수정 흐름 (progress/priority/reassign/tag)")
r=requests.patch(f"{BASE}/tasks/{ctx['task_a']}",headers=h(ctx["mgr_token"]),json={"progress":70})
check(r.status_code==200,"현장소장: Task A progress=70 업데이트",f"실패 {r.status_code}")
pval=requests.get(f"{BASE}/tasks/{ctx['task_a']}",headers=h(admin_token)).json().get("progress")
check(pval==70,f"Task A progress=70 반영 ({pval})","progress 반영 실패")

r=requests.patch(f"{BASE}/tasks/{ctx['auto_a1']}",headers=h(admin_token),json={"priority":"urgent"})
check(r.status_code==200,"Admin: Auto-A1 우선순위→urgent",f"실패 {r.status_code}")

r=requests.patch(f"{BASE}/tasks/{ctx['sub_b1']}",headers=h(ctx["mgr_token"]),json={"assignee_id":ctx["qlt_id"]})
check(r.status_code==200,"현장소장: Sub-B1 담당자 공무팀→품질팀 재배정",f"실패 {r.status_code}")
rl=requests.get(f"{BASE}/tasks/{ctx['sub_b1']}/logs",headers=h(admin_token)).json()
check(any(l["action"]=="reassigned" for l in rl),"Sub-B1 재배정 로그 확인","재배정 로그 없음")

r=requests.patch(f"{BASE}/tasks/{ctx['task_d']}",headers=h(admin_token),json={"tag_names":["안전","최종","승인완료"]})
check(r.status_code==200,"Admin: Task D 태그 업데이트",f"실패 {r.status_code}")

# ═══ PHASE 13: bulk-status ════════════════════════════════════════════
section("PHASE 13: 일괄 상태 변경 (bulk-status)")
clone_ids=[i for i in [ctx.get("clone_a"),ctx.get("clone_c")] if i]
if clone_ids:
    r=requests.post(f"{BASE}/tasks/bulk-status",headers=h(admin_token),json={"task_ids":clone_ids,"status":"review"})
    check(r.status_code==200,f"clone {len(clone_ids)}개 bulk→review 성공",f"bulk-status 실패 {r.status_code}",r.text)
    for cid in clone_ids:
        sv=requests.get(f"{BASE}/tasks/{cid}",headers=h(admin_token)).json().get("status")
        check(sv=="review",f"clone id={cid} status=review 반영","status 반영 실패")
    r=requests.post(f"{BASE}/tasks/bulk-status",headers=h(admin_token),json={"task_ids":clone_ids,"status":"approved"})
    check(r.status_code==200,"clone bulk→approved 성공",f"실패 {r.status_code}")

# ═══ PHASE 14: 정렬 & 필터링 (14가지) ════════════════════════════════
section("PHASE 14: 정렬 & 필터링 종합 (14가지)")
for sb,sd in [("priority","desc"),("priority","asc"),("status","asc"),("status","desc"),("title","asc"),("due_date","asc"),("created_at","desc")]:
    r=requests.get(f"{BASE}/tasks/",headers=h(admin_token),params={"sort_by":sb,"sort_dir":sd})
    items=r.json().get("items",[])
    check(r.status_code==200 and len(items)>0,f"sort_by={sb} {sd} ({len(items)}개)",f"정렬 실패 {r.status_code}")

for sv,uk,label in [("assigned_to_me","mgr","현장소장"),("assigned_by_me","adm","공무팀"),("subtasks_to_me","qlt","품질팀")]:
    r=requests.get(f"{BASE}/tasks/",headers=h(ctx[f"{uk}_token"]),params={"section":sv})
    check(r.status_code==200,f"section={sv}({label}) total={r.json().get('total',0)}","section 필터 실패")

approved_items=requests.get(f"{BASE}/tasks/",headers=h(admin_token),params={"status":"approved"}).json().get("items",[])
check(all(t["status"]=="approved" for t in approved_items),f"status=approved 필터 정확성 ({len(approved_items)}개)","status 필터 부정확")

r=requests.get(f"{BASE}/tasks/",headers=h(admin_token),params={"assignee_id":ctx["con_id"]})
check(r.status_code==200,f"assignee_id 필터(공사팀) total={r.json().get('total',0)}","assignee_id 필터 실패")

for name in ["이공사","박공무","최품질","안전맨"]:
    r=requests.get(f"{BASE}/tasks/",headers=h(admin_token),params={"search":name})
    check(r.status_code==200,f"사용자명 '{name}' 검색 ({r.json().get('total',0)}개)",f"'{name}' 검색 실패")

r=requests.get(f"{BASE}/tasks/",headers=h(admin_token),params={"search":"긴급"})
check(r.status_code==200,f"자연어 '긴급' 검색 ({r.json().get('total',0)}개)","자연어 검색 실패")

paged=requests.get(f"{BASE}/tasks/",headers=h(admin_token),params={"page":1,"page_size":3}).json()
check(len(paged.get("items",[]))<=3,"페이지네이션 page_size=3 확인","페이지네이션 실패")

from datetime import datetime
r=requests.get(f"{BASE}/tasks/",headers=h(admin_token),params={"due_date_from":str(TODAY),"due_date_to":(TODAY+timedelta(days=30)).isoformat()})
check(r.status_code==200,f"due_date 범위 필터 ({r.json().get('total',0)}개)","due_date 범위 필터 실패")

# ═══ PHASE 15: 이메일 인증 흐름 ══════════════════════════════════════
section("PHASE 15: 이메일 인증 흐름")
VF_EMAIL=f"vfy{TS}@gmail.com"
r=requests.post(f"{BASE}/auth/register",json={"email":VF_EMAIL,"password":"Vfy12345","name":"검증자","department_name":"품질팀"})
check(r.status_code==201,"이메일 인증용 신규 유저 등록 성공",f"등록 실패 {r.status_code}",r.text)
vf_tok=r.json().get("access_token")
is_ver=requests.get(f"{BASE}/auth/me",headers=h(vf_tok)).json().get("is_verified")
print(f"  {Y}→ 등록 직후 is_verified={is_ver}{X}")
vt=dbq(f"SELECT t.token FROM email_verification_tokens t JOIN users u ON u.id=t.user_id WHERE u.email='{VF_EMAIL}' AND t.used=0 ORDER BY t.id DESC LIMIT 1;")
check(bool(vt) and vt!="NULL",f"DB verification_token 조회: {vt[:15] if vt else 'N/A'}...","verification_token 없음")
if vt and vt!="NULL":
    r=requests.post(f"{BASE}/auth/verify-email/{vt}")
    check(r.status_code==200,"verify-email 호출 성공",f"실패 {r.status_code}",r.text)
    is_ver2=requests.get(f"{BASE}/auth/me",headers=h(vf_tok)).json().get("is_verified")
    check(is_ver2==True,"이메일 인증 후 is_verified=True 확인","is_verified 갱신 실패")
r=requests.post(f"{BASE}/auth/verify-email/INVALID_TOKEN")
check(r.status_code in (400,404),f"잘못된 token → {r.status_code} 확인","잘못된 token 처리 실패")

# ═══ PHASE 16: 비밀번호 관련 흐름 ═══════════════════════════════════
section("PHASE 16: 비밀번호 관련 흐름")
CON_EMAIL=f"con{TS}@gmail.com"
r=requests.post(f"{BASE}/auth/change-password",headers=h(ctx["con_token"]),json={"current_password":"WRONG","new_password":"New12345"})
check(r.status_code==400,"① 잘못된 현재 비밀번호 → 400",f"검증 미작동 {r.status_code}")
r=requests.post(f"{BASE}/auth/forgot-password",json={"email":CON_EMAIL})
check(r.status_code==200,f"② forgot-password 요청 성공 ({CON_EMAIL})",f"실패 {r.status_code}")
rt=dbq(f"SELECT t.token FROM password_reset_tokens t JOIN users u ON u.id=t.user_id WHERE u.email='{CON_EMAIL}' AND t.used=0 ORDER BY t.id DESC LIMIT 1;")
check(bool(rt) and rt!="NULL",f"③ DB reset_token 조회: {rt[:15] if rt else 'N/A'}...","reset_token 없음")
if rt and rt!="NULL":
    NEW_PW="NewCon99999"
    r=requests.post(f"{BASE}/auth/reset-password",json={"token":rt,"new_password":NEW_PW})
    check(r.status_code==200,"④ reset-password 성공",f"실패 {r.status_code}",r.text)
    new_tok=login(CON_EMAIL,NEW_PW)
    check(new_tok is not None,"⑤ 새 비밀번호 로그인 성공","새 비밀번호 로그인 실패")
    old_tok=login(CON_EMAIL,"Con12345")
    check(old_tok is None,"⑥ 기존 비밀번호 로그인 실패 확인","기존 비밀번호 로그인 가능 (변경 미반영)")
    if new_tok:
        r=requests.post(f"{BASE}/auth/change-password",headers=h(new_tok),json={"current_password":NEW_PW,"new_password":"Con12345"})
        check(r.status_code==200,"⑦ 비밀번호 원복 성공",f"원복 실패 {r.status_code}")
        ctx["con_token"]=login(CON_EMAIL,"Con12345")

# ═══ PHASE 17: 업무 로그 & 댓글 수정/삭제 ════════════════════════════
section("PHASE 17: 업무 로그 & 댓글 수정/삭제")
logs_d=requests.get(f"{BASE}/tasks/{ctx['task_d']}/logs",headers=h(admin_token)).json()
check(isinstance(logs_d,list) and len(logs_d)>0,f"Task D 로그 {len(logs_d)}개 조회","로그 조회 실패")
sc=[l for l in logs_d if l["action"]=="status_changed"]
check(len(sc)>=4,f"Task D 상태변경 로그 {len(sc)}개 확인","상태변경 로그 부족")

if ctx.get("comment_auto_a1"):
    r=requests.patch(f"{BASE}/tasks/{ctx['auto_a1']}/comments/{ctx['comment_auto_a1']}",headers=h(ctx["con_token"]),json={"comment":"시공계획서 최종본 첨부합니다."})
    check(r.status_code==200,"공사팀: 자신의 댓글 수정 성공",f"실패 {r.status_code}")

if ctx.get("comment_man_a4"):
    r=requests.patch(f"{BASE}/tasks/{ctx['man_a4']}/comments/{ctx['comment_man_a4']}",headers=h(admin_token),json={"comment":"admin 수정 시도"})
    check(r.status_code==403,"admin: 타인 댓글 수정 시도 → 403 (admin 예외 없음)",f"권한 미작동 {r.status_code}")

if ctx.get("comment_task_a"):
    r=requests.delete(f"{BASE}/tasks/{ctx['task_a']}/comments/{ctx['comment_task_a']}",headers=h(admin_token))
    check(r.status_code==204,"admin: 현장소장 댓글 삭제 성공 (admin 삭제 허용)",f"실패 {r.status_code}")

if ctx.get("comment_man_a3"):
    r=requests.delete(f"{BASE}/tasks/{ctx['man_a3']}/comments/{ctx['comment_man_a3']}",headers=h(ctx["qlt_token"]))
    check(r.status_code==204,"품질팀: 자신의 댓글 삭제 성공",f"실패 {r.status_code}")

# ═══ PHASE 18: 6개 사용자 대시보드 비교 ══════════════════════════════
section("PHASE 18: 6개 사용자 대시보드 비교")
dashes={}
for label,tok in [("Admin",admin_token),("현장소장",ctx["mgr_token"]),("공사팀",ctx["con_token"]),("공무팀",ctx["adm_token"]),("품질팀",ctx["qlt_token"]),("안전팀",ctx["saf_token"])]:
    r=requests.get(f"{BASE}/tasks/dashboard",headers=h(tok))
    check(r.status_code==200,f"{label} 대시보드 조회 성공",f"{label} 대시보드 실패")
    dashes[label]=r.json()
    print(f"  {Y}→ {label}: total={r.json().get('total',0)} breakdown={r.json().get('status_breakdown',{})}{X}")
totals={k:v.get("total",0) for k,v in dashes.items()}
check(len(set(totals.values()))>1,f"사용자별 대시보드 total 다양성 확인 {totals}","모든 사용자 동일 total (비정상)")

# ═══ PHASE 19: 태그 시스템 최종 검증 ═════════════════════════════════
section("PHASE 19: 태그 시스템 최종 검증")
tags=requests.get(f"{BASE}/categories/tags",headers=h(admin_token)).json()
tag_names=[t["name"] for t in tags]
print(f"  {Y}→ 전체 태그: {tag_names}{X}")
for expected in ["시공","점검","긴급","품질","안전","콘크리트","보고서"]:
    check(expected in tag_names,f"태그 '{expected}' 존재 확인",f"태그 '{expected}' 없음")

# ═══ PHASE 20: 계단식 삭제 검증 ══════════════════════════════════════
section("PHASE 20: 계단식 삭제 검증")
for cid,label in [(ctx.get("clone_a"),"clone_a"),(ctx.get("clone_c"),"clone_c")]:
    if cid:
        r=requests.delete(f"{BASE}/tasks/{cid}",headers=h(admin_token))
        check(r.status_code==204,f"{label}(id={cid}) 삭제 성공",f"삭제 실패 {r.status_code}")
        check(requests.get(f"{BASE}/tasks/{cid}",headers=h(admin_token)).status_code==404,f"{label} 삭제 후 404","삭제 미반영")

sub_ids_a=[sid for sid in [ctx.get("auto_a1"),ctx.get("auto_a2"),ctx.get("man_a3"),ctx.get("man_a4")] if sid]
r=requests.delete(f"{BASE}/tasks/{ctx['task_a']}",headers=h(admin_token))
check(r.status_code==204,f"Task A(id={ctx['task_a']}) 삭제 성공 (서브태스크 {len(sub_ids_a)}개 연쇄)",f"삭제 실패 {r.status_code}")
check(requests.get(f"{BASE}/tasks/{ctx['task_a']}",headers=h(admin_token)).status_code==404,"Task A 삭제 후 404","삭제 미반영")
ok_cascade=all(requests.get(f"{BASE}/tasks/{sid}",headers=h(admin_token)).status_code==404 for sid in sub_ids_a)
check(ok_cascade,f"Task A 서브태스크 {len(sub_ids_a)}개 연쇄 삭제 확인","연쇄 삭제 실패")

for tid,label in [(ctx["task_b"],"Task B"),(ctx["task_c"],"Task C"),(ctx["task_d"],"Task D")]:
    r=requests.delete(f"{BASE}/tasks/{tid}",headers=h(admin_token))
    check(r.status_code==204,f"{label} 삭제 성공",f"{label} 삭제 실패 {r.status_code}")
    check(requests.get(f"{BASE}/tasks/{tid}",headers=h(admin_token)).status_code==404,f"{label} 삭제 후 404","삭제 미반영")

# ═══ 최종 결과 요약 ══════════════════════════════════════════════════
total=pc+fc
print(f"\n{B}{'='*68}{X}\n{B}  최종 테스트 결과 요약 (v2 — 6개 부서 전원 투입){X}\n{B}{'='*68}{X}")
for phase,counts in pr.items():
    p,f_=counts["p"],counts["f"]
    status=f"{G}ALL PASS{X}" if f_==0 else f"{R}{f_} FAIL{X}"
    print(f"  {phase[:50]:<50} {status:>15}  {G}{'█'*p}{X}{R}{'░'*f_}{X}")
print(f"\n  {B}총 케이스: {total}  |  {G}PASS: {pc}{X}  |  {R}FAIL: {fc}{X}{B}{X}")
if fc==0:
    print(f"\n  {G}{B}🎉 모든 테스트 통과! (v2){X}\n")
else:
    pct=round(pc/total*100) if total else 0
    print(f"\n  {Y}{B}성공률: {pct}%{X}\n")
sys.exit(0 if fc==0 else 1)
