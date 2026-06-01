import os
import json
import hashlib
import streamlit as st
import datetime
import re
from collections import defaultdict

DATA_DIR = "data"
USER_DB_FILE = os.path.join(DATA_DIR, "users.json")

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="ACT 충동 조절 일기장", page_icon="🧠", layout="wide")

st.title("🧠 충동 조절 일기장")
st.markdown("""
현재 마주한 감정과 충동을 관찰하고 자신의 충동을 기록해 유형을 알 수 있는 테스트를 시작합니다.
질문에 답하며 이성의 영역 전전두엽을 활성화해 보세요.
""")
st.divider()

# 탭 생성
tab1, tab2 = st.tabs(["📝 입력하기", "📊 기록 조회"])

# 2. 3세대 ACT 기반 질문 세트 정의
act_questions = [
    "Q1. 지금 내 마음을 꽉 채운 충동이나 기분을 한 단어로 요약해 볼까요? 내 마음의 현재 날씨나 상태에 이름을 붙여주세요.",
    "Q2. 자, 이제 문장을 바꾸어 적어볼게요. '나는 00을 해야만 해'가 아니라, '나는 지금 [00을 하고 싶다는 생각/감정]을 느끼고 있구나'라고 문장을 완성해 보세요. 느낌이 어떻게 달라지나요?",
    "Q3. 숨을 깊게 크게 한 번 쉬어보세요. 그리고 지금 내가 무엇을 하고 있고 내 주위에는 무엇이 보이는지, 지금 시간은 몇 시이고 오늘 날짜와 요일은 어떻게 되는지 차분하게 적어보세요.",
    "Q4. 친한 친구가 나와 똑같은 상황에서 똑같은 감정을 느끼며 괴로워하고 있다면, 제3자의 시선에서 그 친구의 상황을 어떻게 냉정하게 요약해 줄 수 있을까요?",
    "Q5. 순간의 유혹이나 쾌락을 한 걸음 뒤에서 바라보았을 때, 내 인생에서 정말로 중요하게 여기는 가치나 내가 닮고 싶은 멋진 나의 모습은 어떤 쪽인가요?",
    "Q6. 방금 떠올린 소중한 가치와 모습을 지키기 위해, 지금 이 충동이 지나갈 동안 내가 당장 실천할 수 있는 작고 구체적인 행동(대안 활동) 한 가지는 무엇인가요? (예: 물 한 잔 마시기, 좋아하는 노래 한 곡 듣고 오기)"
]

# 3. diary 파일 파싱 및 사용자 파일 경로 처리 함수
def sanitize_username(name):
    return re.sub(r"[^0-9a-zA-Z_-]", "_", name.strip())


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def load_user_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        with open(USER_DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_user_db(db):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(USER_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def get_user_file(user_name):
    safe_name = sanitize_username(user_name)
    os.makedirs(DATA_DIR, exist_ok=True)
    return os.path.join(DATA_DIR, f"diary_{safe_name}.txt")


def verify_or_register_user(user_name, password):
    if not user_name or not password:
        return False
    db = load_user_db()
    hashed = hash_password(password)
    if user_name in db:
        return db[user_name] == hashed
    db[user_name] = hashed
    save_user_db(db)
    return True


def parse_diary_file(file_path):
    """지정된 사용자 파일을 읽어 월별로 정리된 데이터 반환"""
    if not file_path:
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return {}
    
    # 엔트리별로 분리 (구분선 기준)
    entries = re.split(r"={60}\n\n", content)
    
    monthly_data = defaultdict(list)
    
    for entry in entries:
        if not entry.strip():
            continue
        
        # 날짜와 충동 유형 추출
        header_match = re.search(r"\[ACT 충동 조절 일기\] 일시: (\d{4})-(\d{2})-(\d{2}) \| 유형: (.+?)\n", entry)
        if not header_match:
            continue
        
        year, month, day, impulse_type = header_match.groups()
        month_key = f"{year}-{month}"
        
        # 질문과 답변 추출
        qa_pairs = []
        for i, question in enumerate(act_questions, 1):
            pattern = rf"{re.escape(question)}\n▶ 답변: (.+?)\n\n"
            answer_match = re.search(pattern, entry, re.DOTALL)
            if answer_match:
                qa_pairs.append((question, answer_match.group(1).strip()))
        
        monthly_data[month_key].append({
            "date": f"{year}-{month}-{day}",
            "impulse_type": impulse_type,
            "qa_pairs": qa_pairs
        })
    
    return dict(sorted(monthly_data.items(), reverse=True))

# 4. 간단한 AI 조언 및 캐릭터 생성 함수
def generate_ai_advice(impulse_tag, responses):
    combined = " ".join([impulse_tag] + responses).lower()
    advices = []
    char_type = ""
    icon = ""  # 이미지 파일 경로('bear.png')나 이모지를 넣을 수 있습니다.
    
    # 1. 에너지 방전형
    if any(term in combined for term in ["자고 싶", "졸려", "잠", "휴식", "피곤", "쉬고 싶"]):
        char_type = "겨울잠 자는 곰"
        icon = "🐻‍❄️"  
        advices.append("지금은 몸과 마음이 쉬어야 한다고 말하고 있어요. 짧은 낮잠이나 편안한 휴식으로 충동을 다독여 보세요.")
        
    # 2. 도파민 탐색형
    elif any(term in combined for term in ["게임", "겜", "유튜브", "sns", "인스타", "틱톡", "트위터"]):
        char_type = "도파민 중독 개구리"
        icon = "🐸"
        advices.append("충동을 억누르기보다 잠깐 멈추고 호흡을 깊게 해보세요. 5분 후에도 같은 충동인지 관찰해보는 연습이 도움이 됩니다.")
        
    # 3. 가짜 배고픔형
    elif any(term in combined for term in ["야식", "먹고 싶", "간식", "과자", "초콜릿", "배고프"]):
        char_type = "배고픈 햄스터"
        icon = "🐹"
        advices.append("물을 먼저 한 잔 마시고, 진짜 배고픔인지 감정 충동인지 하나씩 관찰해보세요. 작은 대안 활동이 도움이 될 수 있어요.")
        
    # 4. 생각 과부하형
    elif any(term in combined for term in ["불안", "불편", "긴장", "초조", "스트레스", "우울", "슬프", "걱정", "예민"]):
        char_type = "생각 많은 고슴도치"
        icon = "🦔"
        advices.append("지금 느끼는 감정을 있는 그대로 인정해보세요. 생각과 나를 분리하고, 내가 가치 있게 여기는 행동에 작은 한 걸음을 두는 것이 중요합니다.")
    
    # 5. 둥지 회귀형 
    elif any(term in combined for term in ["집에 가고 싶", "집 갈래", "집에 보내줘", "집", "엄마", "집가고싶"]):
        char_type = "알을 찾는 병아리"
        icon = "🐣"
        advices.append("지금 공간이 답답해서 가장 안전한 곳을 찾고 있네요. 잠시 눈을 감고 편안한 방을 상상하며 숨을 고른 뒤, 남은 시간을 견뎌봐요.")

    # 6. 압박감 회피형 
    elif any(term in combined for term in ["학원", "학원 가기 싫", "학원 패스", "수업 빼고"]):
        char_type = "도망치고 싶은 치타"
        icon = "🐆"
        advices.append("가야 할 곳이 주는 압박감 때문에 마음이 도망치고 싶어 하네요. 그 불편함을 인정하되, 생각에 휘둘리지 말고 발걸음을 옮겨봐요.")

    # 7. 진로 탐색형 
    elif any(term in combined for term in ["직업", "대학", "학과", "공부", "성적", "진로", "진학"]):
        char_type = "탐색 중인 사자"
        icon = "🦁"
        advices.append("진로 고민으로 불안하고 답답한 건 네가 인생을 진지하게 잘 살고 싶어 한다는 멋진 증거입니다. 좋아하는 것, 잘하는 것을 생각하며 이 감정을 받아들여 보아요.")
        
    # 8. 기타
    else:
        char_type = "생각이 깊은 유니콘"
        icon = "🦄"
        advices.append("지금 느끼는 충동과 감정을 받아들이는 것 자체가 이미 의미 있는 시작입니다. 작은 행동부터 시도해보세요.")
    
    advice_text = advices[0]
    support_text = "당신은 이미 자신의 충동을 관찰하고 적어보는 연습을 했습니다. 그 자체로 충분히 잘해내고 있어요."
    
    # 캐릭터 유형과 아이콘 정보를 함께 반환합니다.
    return advice_text, support_text, char_type, icon

# 4. Session state 초기화
if "current_step" not in st.session_state:
    st.session_state.current_step = 0
    st.session_state.user_name = ""
    st.session_state.user_password = ""
    st.session_state.logged_in = False
    st.session_state.impulse_tag = ""
    st.session_state.current_date = datetime.date.today()
    st.session_state.responses = [""] * len(act_questions)
    st.session_state.setup_complete = False
    st.session_state.record_saved = False

# 5. TAB 1: 입력하기
with tab1:
    # 4. 첫 번째 화면: 날짜 및 충동 유형 입력
    if st.session_state.current_step == 0:
        st.subheader("📋 시작하기")
        st.markdown("먼저 기본 정보를 입력해주세요.")
        
        st.session_state.user_name = st.text_input("사용자 이름", value=st.session_state.user_name, placeholder="기록을 구분할 이름을 입력하세요.")
        st.session_state.user_password = st.text_input("비밀번호", type="password", value=st.session_state.user_password, placeholder="기록을 보호할 비밀번호")
        
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.current_date = st.date_input("날짜 선택", datetime.date.today())
        with col2:
            st.session_state.impulse_tag = st.text_input("현재 마주한 충동 (예: 게임, 야식, SNS)", placeholder="여기에 입력")
        
        st.divider()
        
        col1, col2 = st.columns([1, 4])
        with col2:
            if st.button("✅ 시작하기", key="start_button", use_container_width=True):
                if not st.session_state.user_name.strip():
                    st.error("⚠️ 사용자 이름을 입력해주세요.")
                elif not st.session_state.user_password.strip():
                    st.error("⚠️ 비밀번호를 입력해주세요.")
                elif not st.session_state.impulse_tag.strip():
                    st.error("⚠️ 충동 유형을 입력해주세요.")
                else:
                    if verify_or_register_user(st.session_state.user_name, st.session_state.user_password):
                        st.session_state.logged_in = True
                        st.session_state.setup_complete = True
                        st.session_state.current_step = 1
                        st.session_state.record_saved = False
                        st.success("✅ 사용자 인증에 성공했습니다. 기록을 안전하게 저장합니다.")
                        st.rerun()
                    else:
                        st.error("⚠️ 사용자 이름과 비밀번호가 일치하지 않습니다.")

    # 5. 질문별 화면: 하나씩 질문에 답변하기
    elif st.session_state.current_step >= 1 and st.session_state.current_step <= len(act_questions):
        question_index = st.session_state.current_step - 1
        current_question = act_questions[question_index]
        
        st.subheader(f"질문 {st.session_state.current_step}/{len(act_questions)}")
        st.write(f"**{current_question}**")
        st.divider()
        
        # 텍스트 입력 (항상 빈 상태로 표시)
        response = st.text_area(
            "답변 입력",
            value="",
            height=200,
            label_visibility="collapsed",
            key=f"response_{st.session_state.current_step}"
        )
        
        # 세션 상태에 저장
        if response:
            st.session_state.responses[question_index] = response
        
        st.divider()
        
        # 네비게이션 버튼
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.session_state.current_step > 1:
                if st.button("⬅️ 이전", use_container_width=True):
                    st.session_state.current_step -= 1
                    st.rerun()
            else:
                st.write("")
        
        with col3:
            button_label = "✅ 제출 및 저장" if st.session_state.current_step == len(act_questions) else "다음 ➡️"
            if st.button(button_label, key=f"next_button_{st.session_state.current_step}", use_container_width=True, type="primary"):
                if st.session_state.responses[question_index].strip():
                    if st.session_state.current_step == len(act_questions):
                        st.session_state.current_step = len(act_questions) + 1
                        st.session_state.record_saved = False
                        st.rerun()
                    else:
                        # 다음 질문의 답변 필드 초기화
                        next_index = st.session_state.current_step
                        if next_index < len(st.session_state.responses):
                            st.session_state.responses[next_index] = ""
                        st.session_state.current_step += 1
                        st.rerun()
                else:
                    st.error("⚠️ 이 질문에 대한 답변을 입력해주세요.")

    # 6. 완료 화면: 저장 및 완료
    elif st.session_state.current_step == len(act_questions) + 1:
        # 데이터 저장
        log_entry = "============================================================\n"
        log_entry += f"[ACT 충동 조절 일기] 일시: {st.session_state.current_date} | 유형: {st.session_state.impulse_tag}\n"
        log_entry += "------------------------------------------------------------\n"
        for i in range(len(act_questions)):
            log_entry += f"{act_questions[i]}\n"
            log_entry += f"▶ 답변: {st.session_state.responses[i]}\n\n"
        log_entry += "============================================================\n\n"
        
        # 파일 저장 (한 번만)
        user_file = get_user_file(st.session_state.user_name)
        if not user_file:
            st.error("⚠️ 사용자 이름을 먼저 입력한 뒤 다시 시도해주세요.")
        elif not st.session_state.record_saved:
            with open(user_file, "a", encoding="utf-8") as file:
                file.write(log_entry)
            st.session_state.record_saved = True
        
        # 완료 화면
        st.success("✅ 오늘의 충동 조절 기록이 안전하게 저장되었습니다!")
        st.balloons()
        st.info("💡 전전두엽이 활성화되었습니다. 당신의 충동은 단지 지나가는 생각일 뿐입니다.")
        
        # AI 조언 출력
        advice_text, support_text, char_type, img_path = generate_ai_advice(st.session_state.impulse_tag, st.session_state.responses)

        st.write("") # 약간의 공백
        st.markdown(f"### {img_path} 현재 내면 유형: **[{char_type}]**")
        
        # 화면을 2개의 칸으로 나누어 왼쪽에는 아이콘, 오른쪽에는 조언 배치
        col1, col2 = st.columns([1, 4])
        
        with col1:
            # 이모지 크기를 70px로 크게 키워 캐릭터 느낌을 냄
            st.markdown(f"<h1 style='text-align: center; font-size: 70px; margin: 0;'>{img_path}</h1>", unsafe_allow_html=True)
            
        with col2:
            st.info(advice_text)
            st.caption(f"🌱 {support_text}")

        
        st.divider()
        
        if st.button("🔄 새로 시작하기", key="reset_button", use_container_width=True):
            st.session_state.current_step = 0
            st.session_state.impulse_tag = ""
            st.session_state.current_date = datetime.date.today()
            st.session_state.responses = [""] * len(act_questions)
            st.session_state.setup_complete = False
            st.session_state.record_saved = False
            st.rerun()

with tab2:
    st.subheader("📊 월별 기록 조회")
    
    if not st.session_state.logged_in:
        st.info("📌 먼저 입력하기 탭에서 사용자 이름과 비밀번호로 로그인한 후 기록을 조회하세요.")
    else:
        user_file = get_user_file(st.session_state.user_name)
        monthly_data = parse_diary_file(user_file)
        
        if not monthly_data:
            st.info("📭 아직 저장된 기록이 없습니다. 입력하기 탭에서 답변을 입력해주세요.")
        else:
            # 월별 선택
            months = list(monthly_data.keys())
            selected_month = st.selectbox("조회할 월을 선택하세요", months)
            
            if selected_month:
                entries = monthly_data[selected_month]
                
                st.markdown(f"### 📅 {selected_month} 기록 ({len(entries)}개)")
                st.divider()
                
                # 날짜별 기록 표시
                for idx, entry in enumerate(entries, 1):
                    with st.expander(f"🔖 {entry['date']} - {entry['impulse_type']}", expanded=False):
                        for question, answer in entry['qa_pairs']:
                            st.markdown(f"**{question}**")
                            st.text(answer)
                            st.divider()
                
                # 통계 정보
                st.divider()
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("총 기록 수", len(entries))
                with col2:
                    impulse_types = [e['impulse_type'] for e in entries]
                    if impulse_types:
                        most_common = max(set(impulse_types), key=impulse_types.count)
                    else:
                        most_common = "-"
                    st.metric("가장 많은 충동", most_common)
                
                with col3:
                    unique_impulses = len(set(impulse_types)) if impulse_types else 0
                    st.metric("서로 다른 충동", unique_impulses)
