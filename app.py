import os
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import random

# ----------------------------------------------------
# 홈페이지 사이드바, 메인 배경 색상변경
# ----------------------------------------------------
st.markdown("""    
<style>

[data-testid="stAppViewContainer"]{
background-color:#FFFBF1;
}

[data-testid="stSidebar"]{
background-color:#FFF2D0;
}

.stButton>button{
background-color:#E36A6A;
color:white;
border-radius:8px;
}

</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="에겐로그 유튜브", layout="wide")
st.markdown("""
<style>
/* 메인 콘텐츠 영역 폭 제한 */
.block-container {
    max-width: 1100px;
    padding-top: 2rem;
    padding-bottom: 2rem;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# Firestore 연결 (key.json 또는 st.secrets 둘 다 지원)
# ----------------------------------------------------
def get_db():
    if not firebase_admin._apps:
        try:
            svc = st.secrets.get("firebase_service_account", None)
        except Exception:
            svc = None

        if svc:
            cred = credentials.Certificate(dict(svc))
            firebase_admin.initialize_app(cred)
        else:
            if not os.path.exists("key.json"):
                st.error("key.json이 프로젝트 폴더에 없어요. app.py 옆에 key.json을 넣어주세요.")
                st.stop()
            cred = credentials.Certificate("key.json")
            firebase_admin.initialize_app(cred)

    return firestore.client()

db = get_db()

def now_ts():
    return datetime()

def safe_text(x):
    return (x or "").strip()

def render_divider():
    st.markdown("---")

# ----------------------------------------------------
# 로그인 상태 (session_state)
# ----------------------------------------------------
if "login" not in st.session_state:
    st.session_state["login"] = False
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None

def do_logout():
    st.session_state["login"] = False
    st.session_state["user_id"] = None


# ----------------------------------------------------
# 사이드바: 날짜 + 로그인/회원가입 + 메뉴
# ----------------------------------------------------
today = datetime.now().date()
st.sidebar.write(f"📅 오늘 날짜: {today}")
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔐 계정")

# ----------------------------------------------------
# ✅ 로그인 안 된 상태: 로그인/회원가입 탭 제공
# ----------------------------------------------------
if not st.session_state["login"]:
    auth_tab = st.sidebar.radio("선택", ["로그인", "회원가입"], key="auth_tab")

    if auth_tab == "로그인":
        login_id = st.sidebar.text_input("아이디", key="login_id")
        login_pw = st.sidebar.text_input("비밀번호", type="password", key="login_pw")

        if st.sidebar.button("로그인", key="login_btn"):
            uid = safe_text(login_id)
            pw = safe_text(login_pw)

            if not uid or not pw:
                st.sidebar.warning("아이디/비밀번호를 입력해주세요!")
            else:
                # users 컬렉션에서 아이디로 찾기
                q = db.collection("users").where("user_id", "==", uid).limit(1).stream()
                user_doc = None
                for doc in q:
                    user_doc = doc
                    break

                if user_doc is None:
                    st.sidebar.error("아이디가 없어요. 회원가입부터 해주세요!")
                else:
                    data = user_doc.to_dict()
                    if data.get("password") == pw:
                        st.session_state["login"] = True
                        st.session_state["user_id"] = uid
                        st.sidebar.success("로그인 성공!")
                        st.rerun()
                    else:
                        st.sidebar.error("비밀번호가 틀렸어요.")

    # -------- 회원가입 --------
    else:
        join_id = st.sidebar.text_input("아이디(영문/숫자 추천)", key="join_id")
        join_pw = st.sidebar.text_input("비밀번호", type="password", key="join_pw")
        join_pw2 = st.sidebar.text_input("비밀번호 확인", type="password", key="join_pw2")

        if st.sidebar.button("회원가입", key="join_btn"):
            uid = safe_text(join_id)
            pw = safe_text(join_pw)
            pw2 = safe_text(join_pw2)

            if not uid or not pw:
                st.sidebar.warning("아이디/비밀번호를 입력해주세요!")
            elif pw != pw2:
                st.sidebar.error("비밀번호가 서로 달라요.")
            else:
                # 중복 체크
                q = db.collection("users").where("user_id", "==", uid).limit(1).stream()
                exists = False
                for _ in q:
                    exists = True
                    break

                if exists:
                    st.sidebar.error("이미 존재하는 아이디예요.")
                else:
                    db.collection("users").add(
                        {
                            "user_id": uid,
                            "password": pw,  
                            "created_at": now_ts(),
                        }
                    )
                    st.sidebar.success("회원가입 완료! 이제 로그인해주세요 🙂")
                    st.rerun()

# ✅ 로그인 된 상태
else:
    st.sidebar.success(f"로그인됨 ✅ ({st.session_state['user_id']})")
    st.sidebar.button("로그아웃", on_click=do_logout)

st.sidebar.markdown("---")

# 로그인 안 했으면 메인 막기
if not st.session_state["login"]:
    st.title("에겐로그 유튜브 제작 툴")
    st.info("왼쪽 사이드바에서 회원가입 후 로그인하면 사용할 수 있어요.")
    st.stop()

# 로그인 된 경우에만 메뉴 보이게
menu = st.sidebar.radio("📌 메뉴", ["💡 아이디어", "💌 사연함(제보)", "🧠 스크립트", "✅ 업로드 체크"])

# =========================================================
# 1) 아이디어
# =========================================================
if menu == "💡 아이디어":
    st.subheader("영상 아이디어 저장")

    colA, colB, colC = st.columns([2, 1, 2])
    with colA:
        idea_title = st.text_input("제목", key="idea_title")
    with colB:
        idea_category = st.selectbox(
            "카테고리",
            ["인간관계", "연애", "MBTI", "자기계발", "일상", "기타"],
            key="idea_category",
        )
    with colC:
        idea_one = st.text_input("한줄요약", key="idea_one")

    idea_memo = st.text_area("메모(상세)", key="idea_memo", height=120)

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("저장", key="idea_save"):
            t = safe_text(idea_title)
            if not t:
                st.warning("제목은 꼭 입력해주세요!")
            else:
                db.collection("ideas").add(
                    {
                        "title": t,
                        "category": idea_category,
                        "one_line": safe_text(idea_one),
                        "memo": safe_text(idea_memo),
                        "status": "new",
                        "created_at": now_ts(),
                    }
                )
                st.success("아이디어 저장 완료!")
                st.rerun()

    render_divider()

    st.subheader("아이디어 목록")
    filter_col1, filter_col2, filter_col3 = st.columns([1, 1, 2])
    with filter_col1:
        idea_filter_status = st.selectbox("상태", ["전체", "new", "done"], key="idea_filter_status")
    with filter_col2:
        idea_filter_cat = st.selectbox(
            "카테고리",
            ["전체", "인간관계", "연애", "MBTI", "자기계발", "일상", "기타"],
            key="idea_filter_cat",
        )
    with filter_col3:
        idea_search = st.text_input("검색(제목/메모)", key="idea_search")

    docs = db.collection("ideas").order_by("created_at", direction=firestore.Query.DESCENDING).stream()

    shown = 0
    for d in docs:
        data = d.to_dict()
        title = data.get("title", "")
        memo = data.get("memo", "")
        cat = data.get("category", "")
        status = data.get("status", "new")

        if idea_filter_status != "전체" and status != idea_filter_status:
            continue
        if idea_filter_cat != "전체" and cat != idea_filter_cat:
            continue
        if idea_search:
            s = idea_search.strip().lower()
            if s not in (title or "").lower() and s not in (memo or "").lower():
                continue

        shown += 1

        c1, c2, c3, c4 = st.columns([0.6, 2.6, 1.2, 1.2])
        with c1:
            checked = st.checkbox("완료", value=(status == "done"), key=f"idea_done_{d.id}")
            if checked and status != "done":
                db.collection("ideas").document(d.id).update({"status": "done"})
                st.rerun()
            if (not checked) and status == "done":
                db.collection("ideas").document(d.id).update({"status": "new"})
                st.rerun()

        with c2:
            st.markdown(f"**{title}**")
            if data.get("one_line"):
                st.caption(data.get("one_line"))
            if memo:
                st.write(memo)

        with c3:
            st.write(f"#{cat}")
            st.caption(status)

        with c4:
            if st.button("삭제", key=f"idea_del_{d.id}"):
                db.collection("ideas").document(d.id).delete()
                st.rerun()

        st.markdown("---")

    if shown == 0:
        st.info("조건에 맞는 아이디어가 아직 없어요!")

# =========================================================
# 2) 사연함(제보)
# =========================================================
elif menu == "💌 사연함(제보)":
    st.subheader("사연 제보 받기")

    colA, colB = st.columns([1, 2])
    with colA:
        story_nick = st.text_input("닉네임(또는 구독자명)", key="story_nick")
    with colB:
        story_tag = st.text_input("키워드(선택) - 예: 친구, 연락, 썸", key="story_tag")

    story_text = st.text_area("사연 내용", key="story_text", height=160)

    if st.button("제출(저장)", key="story_save"):
        t = safe_text(story_text)
        if not t:
            st.warning("사연 내용을 입력해주세요!")
        else:
            db.collection("stories").add(
                {
                    "nickname": safe_text(story_nick) or "익명",
                    "tag": safe_text(story_tag),
                    "story": t,
                    "status": "new",
                    "created_at": now_ts(),
                }
            )
            st.success("사연 저장 완료!")
            st.rerun()

    render_divider()

elif menu == "🧠 스크립트":
    st.subheader("촬영 스크립트 작성 (템플릿)")

    script_title = st.text_input("영상 제목", key="script_title")
    col1, col2 = st.columns(2)
    with col1:
        hook = st.text_area("오프닝(훅)", key="script_hook", height=90)
        summary = st.text_area("사연/주제 요약", key="script_summary", height=90)
    with col2:
        p1 = st.text_area("포인트 1 (ENFJ 시점)", key="script_p1", height=90)
        p2 = st.text_area("포인트 2 (ENFJ 시점)", key="script_p2", height=90)
        p3 = st.text_area("포인트 3 (ENFJ 시점)", key="script_p3", height=90)

    ending = st.text_area("엔딩 멘트(구독/댓글 유도)", key="script_ending", height=90)

    if st.button("저장", key="script_save"):
        t = safe_text(script_title)
        if not t:
            st.warning("영상 제목은 꼭 입력해주세요!")
        else:
            db.collection("scripts").add(
                {
                    "title": t,
                    "hook": safe_text(hook),
                    "summary": safe_text(summary),
                    "p1": safe_text(p1),
                    "p2": safe_text(p2),
                    "p3": safe_text(p3),
                    "ending": safe_text(ending),
                    "created_at": now_ts(),
                }
            )
            st.success("스크립트 저장 완료!")
            st.rerun()

    render_divider()

    st.subheader("저장된 스크립트")
    script_search = st.text_input("검색(제목)", key="script_search")

    docs = db.collection("scripts").order_by("created_at", direction=firestore.Query.DESCENDING).stream()
    shown = 0
    for d in docs:
        data = d.to_dict()
        title = data.get("title", "")
        if script_search and script_search.strip().lower() not in (title or "").lower():
            continue

        shown += 1
        with st.expander(f"📄 {title}", expanded=False):
            st.markdown("**오프닝(훅)**")
            st.write(data.get("hook", ""))

            st.markdown("**요약**")
            st.write(data.get("summary", ""))

            st.markdown("**ENFJ 포인트 3개**")
            st.write(f"1) {data.get('p1','')}")
            st.write(f"2) {data.get('p2','')}")
            st.write(f"3) {data.get('p3','')}")

            st.markdown("**엔딩**")
            st.write(data.get("ending", ""))

            if st.button("삭제", key=f"script_del_{d.id}"):
                db.collection("scripts").document(d.id).delete()
                st.rerun()

    if shown == 0:
        st.info("저장된 스크립트가 아직 없어요!")

# =========================================================
# 4) 업로드 체크
# =========================================================
elif menu == "✅ 업로드 체크":
    st.subheader("업로드 체크리스트")

    default_items = [
        "대본/핵심포인트 정리",
        "촬영 완료",
        "편집 완료",
        "썸네일 제작",
        "제목/설명 작성",
        "태그/해시태그",
        "업로드 완료",
        "고정댓글 작성",
    ]

    upload_title = st.text_input("영상 제목(업로드 관리용)", key="upload_title")

    if st.button("새 체크리스트 만들기", key="upload_new"):
        t = safe_text(upload_title)
        if not t:
            st.warning("영상 제목을 먼저 입력해주세요!")
        else:
            checklist = {item: False for item in default_items}
            db.collection("uploads").add(
                {"title": t, "checklist": checklist, "done": False, "created_at": now_ts()}
            )
            st.success("체크리스트 생성 완료!")
            st.rerun()

    render_divider()

    st.subheader("내 업로드 목록")
    docs = db.collection("uploads").order_by("created_at", direction=firestore.Query.DESCENDING).stream()

    shown = 0
    for d in docs:
        data = d.to_dict()
        shown += 1

        title = data.get("title", "제목없음")
        checklist = data.get("checklist", {})
        done = data.get("done", False)

        with st.expander(f"{'✅' if done else '🕒'} {title}", expanded=False):
            new_checklist = dict(checklist)

            for item in default_items:
                cur = bool(new_checklist.get(item, False))
                nxt = st.checkbox(item, value=cur, key=f"up_{d.id}_{item}")
                new_checklist[item] = nxt

            all_done = all(bool(new_checklist.get(item, False)) for item in default_items)

            colA, colB, colC = st.columns([1, 1, 3])
            with colA:
                if st.button("저장/반영", key=f"upload_save_{d.id}"):
                    db.collection("uploads").document(d.id).update(
                        {"checklist": new_checklist, "done": all_done}
                    )
                    st.success("반영 완료!")
                    st.rerun()

            with colB:
                if st.button("삭제", key=f"upload_del_{d.id}"):
                    db.collection("uploads").document(d.id).delete()
                    st.rerun()

            with colC:
                st.caption(f"완료 상태: {'완료' if all_done else '진행중'}")

    if shown == 0:
        st.info("업로드 체크리스트가 아직 없어요. 위에서 새로 만들어봐요!")