import os
import streamlit as st
import datetime
import re
from collections import defaultdict

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="ACT 충동 조절 일기장", page_icon="🧠", layout="wide")

st.title("🧠 충동 조절 일기장")
st.markdown("""
현재 마주한 감정과 충동을 관찰하고 문장과 자신을 분리하는 연습을 시작합니다.
질문에 답하며 전전두엽을 활성화해 보세요.
""")
st.divider()

# 탭 생성
tab1, tab2 = st.tabs(["📝 입력하기", "📊 기록 조회"])

# 2. 3세대 ACT 기반 질문 세트 정의
act_questions = [
    "Q1. 지금 마음속에서 강하게 일어나는 충동이나 불편한 감정을 없애거나 회피하려 하지 말고, 있는 그대로 집중해 보세요. 그 감정에 어울리는 이름을 붙여준다면 무엇인가요?",
    "Q2. 나는 지금 이 충동을 합리화하기 위해 어떤 핑계나 이유를 대고 있나요?",
    "Q3. 숨을 깊게 크게 한 번 쉬어보세요. 그리고 지금 내가 무엇을 하고 있고 내 주위에는 무엇이 보이는지, 지금 시간은 몇 시이고 오늘 날짜와 요일은 어떻게 되는지 차분하게 적어보세요.",
    "Q4. 자, 이제 문장을 바꾸어 적어볼게요. '나는 00을 해야만 해'가 아니라, '나는 지금 [00을 하고 싶다는 생각/감정]을 느끼고 있구나'라고 문장을 완성해 보세요. 느낌이 어떻게 달라지나요?",
    "Q5. 순간의 유혹이나 쾌락을 한 걸음 뒤에서 바라보았을 때, 내 인생에서 정말로 중요하게 여기는 가치나 내가 닮고 싶은 멋진 나의 모습은 어떤 쪽인가요?",
    "Q6. 방금 떠올린 소중한 가치와 모습을 지키기 위해, 지금 이 충동이 지나갈 동안 내가 당장 실천할 수 있는 작고 구체적인 행동(대안 활동) 한 가지는 무엇인가요? (예: 물 한 잔 마시기, 좋아하는 노래 한 곡 듣고 오기, 방 정리하기)"
]

# 3. diary 파일 파싱 및 사용자 파일 경로 처리 함수
def sanitize_username(name):
    return re.sub(r"[^0-9a-zA-Z_-]", "_", name.strip())


def get_user_file():
    user_name = st.session_state.get("user_name", "").strip()
    if not user_name:
        return None
    safe_name = sanitize_username(user_name)
    os.makedirs("data", exist_ok=True)
    return os.path.join("data", f"diary_{safe_name}.txt")


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

# 4. 간단한 AI 조언 생성 함수
def generate_ai_advice(impulse_tag, responses):
    combined = " ".join([impulse_tag] + responses).lower()
    advices = []
    
    if any(term in combined for term in ["자고 싶", "졸려", "잠", "휴식", "피곤", "쉬고 싶"]):
        advices.append("지금은 몸과 마음이 쉬어야 한다고 말하고 있어요. 짧은 낮잠이나 편안한 휴식으로 충동을 다독여 보세요.")
    if any(term in combined for term in ["게임", "겜", "유튜브", "sns", "인스타", "틱톡", "페북"]):
        advices.append("충동을 억누르기보다 잠깐 멈추고 호흡을 깊게 해보세요. 5분 후에도 같은 충동인지 관찰해보는 연습이 도움이 됩니다.")
    if any(term in combined for term in ["야식", "먹고 싶", "간식", "과자", "초콜릿", "배고프"]):
        advices.append("물을 먼저 한 잔 마시고, 진짜 배고픔인지 감정 충동인지 하나씩 관찰해보세요. 작은 대안 활동이 도움이 될 수 있어요.")
    if any(term in combined for term in ["불안", "불편", "긴장", "초조", "스트레스", "우울", "슬프", "걱정"]):
        advices.append("지금 느끼는 감정을 있는 그대로 인정해보세요. 생각과 나를 분리하고, 내가 가치 있게 여기는 행동에 작은 한 걸음을 두는 것이 중요합니다.")
    if not advices:
        advices.append("지금 느끼는 충동과 감정을 받아들이는 것 자체가 이미 의미 있는 시작입니다. 작은 행동부터 시도해보세요.")
    
    advice_text = advices[0]
    support_text = "당신은 이미 자신의 충동을 관찰하고 적어보는 연습을 했습니다. 그 자체로 충분히 잘해내고 있어요."
    return advice_text, support_text

# 4. Session state 초기화
if "current_step" not in st.session_state:
    st.session_state.current_step = 0
    st.session_state.user_name = ""
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
                elif not st.session_state.impulse_tag.strip():
                    st.error("⚠️ 충동 유형을 입력해주세요.")
                else:
                    st.session_state.setup_complete = True
                    st.session_state.current_step = 1
                    st.session_state.record_saved = False
                    st.rerun()

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
        user_file = get_user_file()
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
        advice_text, support_text = generate_ai_advice(st.session_state.impulse_tag, st.session_state.responses)
        st.markdown("### 🤖 ACT 맞춤 조언")
        st.info(advice_text)
        st.write(support_text)
        
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
    
    if not st.session_state.user_name.strip():
        st.info("📌 먼저 입력하기 탭에서 사용자 이름을 입력한 후 기록을 조회하세요.")
    else:
        user_file = get_user_file()
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
                st.metric("서로 다른 충동", unique_impulses)s))
                st.metric("서로 다른 충동", unique_impulses)
