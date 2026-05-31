import streamlit as st
import datetime

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="ACT 충동 조절 일기장", page_icon="🧠", layout="centered")

st.title("🧠 3세대 ACT 기반 충동 조절 일기장")
st.markdown("""
현재 마주한 감정과 충동을 관찰하고 문장과 자신을 분리하는 연습을 시작합니다.
질문에 답하며 전전두엽을 활성화해 보세요.
""")
st.divider()

# 2. 사용자 및 충동 컨텍스트 입력 영역
col1, col2 = st.columns(2)
with col1:
    current_date = st.date_input("날짜 선택", datetime.date.today())
with col2:
    impulse_tag = st.text_input("현재 마주한 충동 (예: 게임, 야식, SNS)", placeholder="여기에 입력")

st.divider()

# 3. 3세대 ACT 기반 질문 세트 정의
act_questions = [
    "Q1. 지금 마음속에서 소용돌이치는 충동이나 감정에 '이름(라벨)'을 붙여 가만히 적어보세요. (예: '게임하고 싶은 마음', '불안감')",
    "Q2. 그 충동을 억누르려 하지 말고, 몸 어디에서 어떤 느낌으로 존재하는지 관찰하여 설명해보세요.",
    "Q3. '나는 [충동]이라는 생각을 가지고 있구나'라고 문장을 바꾸어 적으며, 생각과 나를 분리해봅니다.",
    "Q4. 이 충동이 지나갈 때까지 지금 당장 내가 가치 있게 여길 수 있는 작은 행동(대안 활동)은 무엇인가요?"
]

# 4. 반복문을 통한 웹 입력 폼(Form) 생성
user_responses = []
with st.form(key="act_form"):
    for i, question in enumerate(act_questions, 1):
        st.write(f"**[{i}/{len(act_questions)}] {question}**")
        response = st.text_area(f"답변 입력란 {i}", label_visibility="collapsed", key=f"q_{i}")
        user_responses.append(response)
    
    # 제출 버튼
    submit_button = st.form_submit_button(label="📝 일기 저장하고 충동 넘기기")

# 5. 제출 이벤트 처리 및 파일 저장
if submit_button:
    if not impulse_tag.strip() or any(not resp.strip() for resp in user_responses):
        st.error("⚠️ 모든 질문에 답변을 입력해야 저장할 수 있습니다.")
    else:
        # 데이터 포맷팅
        log_entry = "============================================================\n"
        log_entry += f"[ACT 충동 조절 일기] 일시: {current_date} | 유형: {impulse_tag}\n"
        log_entry += "------------------------------------------------------------\n"
        for i in range(len(act_questions)):
            log_entry += f"{act_questions[i]}\n"
            log_entry += f"▶ 답변: {user_responses[i]}\n\n"
        log_entry += "============================================================\n\n"
        
        # 파일 저장
        with open("diary.txt", "a", encoding="utf-8") as file:
            file.write(log_entry)
            
        # 성공 메시지 출력
        st.success("✅ 오늘의 충동 조절 기록이 안전하게 저장되었습니다!")
        st.balloons() # 축하 효과 애니메이션
        st.info("💡 전전두엽이 활성화되었습니다. 당신의 충동은 단지 지나가는 생각일 뿐입니다.")