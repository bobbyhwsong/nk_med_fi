import streamlit as st
from openai import OpenAI
# dotenv 제거
# from dotenv import load_dotenv
import os
import time
from datetime import datetime, timedelta

# 환경 변수 로딩 방식 변경
# load_dotenv()

# OpenAI 클라이언트 설정

try:
    api_key = st.secrets["OPENAI_API_KEY"]
except KeyError:
    st.error("API 키가 설정되지 않았습니다. Streamlit secrets를 확인하세요.")
    st.stop()

client = OpenAI(api_key=api_key)

# 페이지 설정
st.set_page_config(
    page_title="정보 찾기 연습",
    page_icon="🧠",
    layout="wide"
)

# 커스텀 CSS로 배경색 변경
st.markdown("""
    <style>
        /* 전체 앱 스타일 */
        .stApp {
            background-color: #000000;
            color: #ffffff;
        }
        
        /* 상단 영역 스타일 */
        .main > div:first-child {
            background-color: #000000;
        }
        .stApp > header {
            background-color: #000000;
        }
        
        /* 사이드바 스타일 */
        [data-testid="stSidebar"] {
            background-color: #000000;
            border-right: 1px solid #333333;
        }
        [data-testid="stSidebar"] .css-1d391kg {
            background-color: #000000;
        }
        
        /* 버튼 스타일 */
        .stButton>button {
            background-color: #1E1E1E;
            color: #ffffff;
            border: 1px solid #ffffff;
        }
        .stButton>button:hover {
            background-color: #2E2E2E;
        }
        
        /* 입력 필드 스타일 */
        .stTextInput>div>div>input {
            background-color: #1E1E1E;
            color: #ffffff;
        }
        .stTextArea>div>div>textarea {
            background-color: #1E1E1E;
            color: #ffffff;
        }
        
        /* 채팅 메시지 스타일 */
        .stChatMessage {
            padding: 0;
            margin: 8px 0;
        }
        .stChatMessage [data-testid="stChatMessageContent"] {
            color: #FFFFFF;
            padding: 0;
            margin: 0;
        }
        .stChatMessage [data-testid="stChatMessageContent"] > div {
            padding: 0;
            margin: 0;
        }
        
        /* 타이머 스타일 */
        .timer-container {
            text-align: center;
            padding: 10px;
            background-color: #1E1E1E;
            border-radius: 5px;
            margin-bottom: 20px;
            animation: pulse 1s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.8; }
            100% { opacity: 1; }
        }
    </style>
""", unsafe_allow_html=True)

# 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_task" not in st.session_state:
    st.session_state.selected_task = None
if "task_completed" not in st.session_state:
    st.session_state.task_completed = False
if "user_answer" not in st.session_state:
    st.session_state.user_answer = None
if "chat_completed" not in st.session_state:
    st.session_state.chat_completed = False
if "current_page" not in st.session_state:
    st.session_state.current_page = "intro"
if "timer_start" not in st.session_state:
    st.session_state.timer_start = None
if "time_left" not in st.session_state:
    st.session_state.time_left = 300  # 5분 = 300초
if "last_update" not in st.session_state:
    st.session_state.last_update = None

# 연습 문제 정의
TASKS = {
    "하나의 정보로 하나의 답 찾기": {
        "description": "하나의 정보만 보고 정확한 답을 찾는 연습입니다.",
        "system_prompt": "여름철 바깥나들이 중 기운이 빠진 사람을 본 상황에서 사용자가 맞는 답을 고르게 도와주세요. 사용자에게 주어진 정보 하나는 '탈수 기운이 보이면, 바로 그늘진 곳으로 옮기고 물을 마시게 해야 합니다.'입니다. 사용자가 묻는 말에 답을 해주며, 옳은 대처법을 찾게 도와주세요. 답을 알려주지 말고, 답을 찾아가는 과정만을 함께 해주세요. 상대가 북한이탈주민이라는 점을 고려해서, 외래어 없이 쉬운 단어로만 설명하세요.",
        "task_info": "여름철 바깥나들이 중 기운이 빠진 사람을 보았습니다. 급한 손질 안내글을 보고 어떻게 해야 할지 답해보세요.",
        "cards": {
            "급한 손질 안내글": {
                "summary": "탈수 기운이 보이면, 바로 그늘진 곳으로 옮기고 물을 마시게 해야 합니다.",
                "source": "대한급손학회"
            }
        },
        "question": "아래 문장이 맞는지 아닌지 O/X로 답해주세요:\n탈수 환자는 그늘로 옮기고 물을 마시게 해야 합니다.",
        "correct_answer": "O",
        "explanation": {
            "correct": "잘하셨습니다! 탈수 환자는 체온을 낮추고 물을 천천히 마시는 것이 중요합니다.",
            "incorrect": "아쉽습니다. 탈수 환자는 반드시 그늘로 옮겨 체온을 낮추고 물을 마셔야 합니다."
        }
    },
    "여러 정보로 하나의 답 찾기": {
        "description": "여러 정보를 모아서 하나의 정확한 답을 찾는 연습입니다.",
        "system_prompt": "길에서 열로 지친 듯한 사람을 본 상황에서 사용자가 맞는 답을 고르게 도와주세요. 사용자에게 옳은 정보와 틀린 정보가 모두 주어졌어. 사용자에게 주어진 정보는 '(1)환자를 시원한 곳으로 옮기고, 몸을 적셔서 체온을 내려야 합니다.(2)따뜻한 차를 마시게 하면 좋습니다.(3)의식이 없으면 억지로 물을 먹이면 안 됩니다.'입니다. 사용자가 묻는 말에 답을 해주며, 옳은 대처법을 찾게 도와주세요. 답을 알려주지 말고, 답을 찾아가는 과정만을 함께 해주세요. 상대가 북한이탈주민이라는 점을 고려해서, 외래어 없이 쉬운 단어로만 설명하세요.",
        "task_info": "길에서 열로 지친 듯한 사람을 보았습니다. 여러 정보를 보고 어떻게 해야 할지 답해보세요.",
        "cards": {
            "급한 손질 공식책": {
                "summary": "환자를 시원한 곳으로 옮기고, 몸을 적셔서 체온을 내려야 합니다.",
                "source": "급손 공식 책자"
            },
            "건강 글모음 조언": {
                "summary": "따뜻한 차를 마시게 하면 좋습니다.",
                "source": "건강 기록글"
            },
            "소방청 급손 안내": {
                "summary": "의식이 없으면 억지로 물을 먹이면 안 됩니다.",
                "source": "소방청 안내"
            }
        },
        "actions": [
            "시원한 곳으로 옮기고 체온 낮추기",
            "따뜻한 차를 마시게 하기",
            "물을 억지로 먹이기"
        ],
        "correct_action": "시원한 곳으로 옮기고 체온 낮추기",
        "feedback": {
            "시원한 곳으로 옮기고 체온 낮추기": {
                "type": "success",
                "message": "✅ 잘하셨습니다! 열로 지친 사람은 즉시 몸을 식히는 것이 가장 중요합니다."
            },
            "따뜻한 차를 마시게 하기": {
                "type": "error",
                "message": "❌ 아쉽습니다. 뜨거운 음료는 몸을 더 덥게 할 수 있어 위험합니다."
            },
            "물을 억지로 먹이기": {
                "type": "error",
                "message": "❌ 아쉽습니다. 정신을 잃은 사람에게 억지로 물을 먹이면 기도가 막힐 수 있어 아주 위험합니다."
            }
        }
    },
    "여러 정보로 여러 답 찾기": {
        "description": "여러 정보를 보고 가능한 모든 답을 찾는 연습입니다.",
        "system_prompt": "큰 가게 안에서 사람이 쓰러져 정신이 없는 상황에서 사용자가 맞는 답을 고르게 도와주세요. 사용자에게 맞는 정보와 틀린 정보가 모두 주어졌어. 사용자에게 주어진 정보는 '(1)바로 119에 전화하고 자동 심장 충격기를 가져와야 합니다.(2)자동 심장 충격기는 안내 소리를 따라하면 누구나 쓸 수 있습니다.(3)손과 발을 따뜻하게 하면 회복됩니다.(4)귀를 세게 때리면 정신을 차립니다.(5)심장이 멈춘 것 같으면 의식과 숨 쉬는지 먼저 확인하고 가슴 눌러 숨쉬기를 해야 합니다.'입니다. 사용자가 묻는 말에 답을 해주며, 옳은 대처법을 찾게 도와주세요. 답을 알려주지 말고, 답을 찾아가는 과정만을 함께 해주세요. 상대가 북한이탈주민이라는 점을 고려해서, 외래어 없이 쉬운 단어로만 설명하세요. 북한어를 최대한 사용해서 응답하도록 하세요.",
        "task_info": "큰 가게 안에 사람이 쓰러져 정신이 없습니다. 여러 정보를 보고 어떻게 해야 할지 답해보세요.",
        "cards": {
            "대한응급의학회": {
                "summary": "심장이 멈춘 것 같으면, 가장 먼저 정신이 있는지와 숨을 쉬는지 살핀 뒤에 바로 가슴을 눌러주어야 합니다.",
                "source": "대한응급의학회"
            },
            "민간요법연구회": {
                "summary": "자동 심장 충격기는 기계가 시키는 대로 소리를 따라 하기만 하면 돼서, 처음 보는 사람도 쓸 수 있어요.",
                "source": "민간요법연구회"
            },
            "국립의료연구원": {
                "summary": "쓰러진 사람의 손과 발을 주물러 따뜻하게 해주면, 혈액순환이 좋아져 정신을 차리는 데 도움이 됩니다.",
                "source": "국립의료연구원"
            },
            "응급처치연구회": {
                "summary": "의식이 없는 사람에게 강한 힘을 주어 정신을 깨우기 위해, 귀를 강하게 때리는 방법이 효과적입니다.",
                "source": "1차치료연구회"
            },
            "편의점 알바": {
                "summary": "가게 안에서 긴급상황이 생기면, 제일 먼저 119에 알리고 가까운 곳에 있는 자동 심장 충격기를 찾아와야 합니다.",
                "source": "편의점 일군"
            }
        },
        "actions": [
            "119에 전화하기",
            "자동 심장 충격기 가져오기",
            "손발을 따뜻하게 하기",
            "귀를 세게 치기",
            "숨 쉬는지 확인하기"
        ],
        "correct_actions": ["119에 전화하기", "자동 심장 충격기 가져오기"],
        "feedback": {
            "119에 전화하기": "✅ 잘하셨습니다! 긴급할 때는 전문가에게 연락해야 합니다.",
            "자동 심장 충격기 가져오기": "✅ 잘하셨습니다! 자동 심장 충격기는 생명을 살리는 데 꼭 필요합니다.",
            "손발을 따뜻하게 하기": "❌ 손발을 따뜻하게 하는 민간요법은 도움이 되지 않습니다.",
            "귀를 세게 치기": "❌ 매우 위험한 행동입니다. 머리에 큰 해를 줄 수 있습니다.",
            "숨 쉬는지 확인하기": "⚠️ 중요한 절차이지만, 우선 119에 전화하고 자동 심장 충격기를 준비해야 합니다."
        }
    }
}

def get_gpt_response(messages):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"문제가 생겼습니다: {str(e)}"

# 사이드바
with st.sidebar:
    st.title("📋 메뉴")
    
    # 메인 메뉴
    if st.button("🏠 소개", use_container_width=True):
        st.session_state.current_page = "intro"
        st.rerun()
    
    st.markdown("---")
    
    # 태스크 선택
    st.subheader("연습할 문제 고르기")
    for task_name in TASKS.keys():
        if st.button(task_name, use_container_width=True):
            st.session_state.selected_task = task_name
            st.session_state.messages = [
                {"role": "system", "content": TASKS[task_name]["system_prompt"]},
                {"role": "assistant", "content": "같이 옳은 답을 찾아보아요."}
            ]
            st.session_state.current_page = "chat"
            st.session_state.chat_completed = False
            st.session_state.task_completed = False
            st.rerun()
    
    st.markdown("---")
    
    # 현재 상태 표시
    if st.session_state.selected_task:
        st.subheader("현재 연습")
        st.info(st.session_state.selected_task)
        
        if st.session_state.current_page == "chat":
            st.markdown("1. ✨ **대화하기**")
            st.markdown("2. 📝 답 고르기")
            st.markdown("3. 📊 결과 보기")
        elif st.session_state.current_page == "answer":
            st.markdown("1. ✓ ~~대화하기~~")
            st.markdown("2. ✨ **답 고르기**")
            st.markdown("3. 📊 결과 보기")
        elif st.session_state.current_page == "feedback":
            st.markdown("1. ✓ ~~대화하기~~")
            st.markdown("2. ✓ ~~답 고르기~~")
            st.markdown("3. ✨ **결과 보기**")

# 소개 페이지
if st.session_state.current_page == "intro":
    st.markdown("""
    ## 📚 이 손전화 앱은 어떤 목적을 가지고 있나요?
    
    이것은 우리가 평소에 마주할 수 있는, 1차 치료가 필요한 상황에 대응하는 방법을 배우기 위한 앱입니다.
    
    ### 🎯 어떻게 쓰나요?
                
    1. 왼쪽 차림표에서 연습할 문제를 고르세요.
    2. 그 후, 우리가 다룰 긴급상황에 대한 설명을 읽으세요.
    3. 설명 아래에 안내되어있는 안내글을 모두 읽으세요. (안내글에는 정확한 정보와 틀린 정보가 섞여있습니다.)
    4. 창 아래의 이야기 인간과 대화하며 정보를 얻으세요.
    5. 이야기 인간이 제시한 정보를 바탕으로 답을 고르세요. (시간제한 5분)
    6. 답을 고르고 제출하면 결과를 확인할 수 있습니다.
                
    ### 어떤 연습문제가 있나요?
    
    1. **하나의 정보로 하나의 답 찾기**
       - 하나의 정보만 보고 정확한 답을 찾는 연습입니다.
    
    2. **여러 정보로 하나의 답 찾기**
       - 여러 정보를 보면서 하나의 정확한 답을 찾는 연습입니다.
    
    3. **여러 정보로 여러 답 찾기**
       - 여러 정보를 보고 가능한 모든 답을 찾는 연습입니다.
    
    ### ⭐ 시작하기
    
    왼쪽 차림표에서 연습하고 싶은 문제를 고르면서 시작해보세요!
    """)

# 태스크 선택 화면
elif st.session_state.current_page == "task_select":
    st.subheader("연습할 문제를 고르세요:")
    for task_name, task_info in TASKS.items():
        if st.button(f"{task_name}\n{task_info['description']}"):
            st.session_state.selected_task = task_name
            st.session_state.messages = [
                {"role": "system", "content": task_info["system_prompt"]},
                {"role": "assistant", "content": task_info["task_info"]}
            ]
            st.session_state.current_page = "chat"
            st.rerun()

# 채팅 화면
elif st.session_state.current_page == "chat":
    st.subheader(f"현재 연습: {st.session_state.selected_task}")
    
    # 문제 안내와 답 고르기 버튼을 같은 행에 배치
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # 문제 안내
        st.info(TASKS[st.session_state.selected_task]["task_info"])
    
    with col2:
        # 답 고르기로 이동
        if st.button("답 고르러 가기", use_container_width=True):
            st.session_state.current_page = "answer"
            st.rerun()
    
    # 타이머 시작
    if st.session_state.timer_start is None:
        st.session_state.timer_start = datetime.now()
        st.session_state.time_left = 300  # 5분으로 초기화
        st.session_state.last_update = None
    
    # 타이머 표시
    if st.session_state.timer_start:
        elapsed = (datetime.now() - st.session_state.timer_start).total_seconds()
        time_left = max(0, 300 - elapsed)  # 5분에서 경과 시간을 뺌
        
        minutes = int(time_left // 60)
        seconds = int(time_left % 60)
        
        # 타이머 컨테이너
        st.markdown(f"""<div class="timer-container"><p style='color: #FFFFFF; font-size: 0.8em; margin-top: 5px;'>

아래의 안내글 {len(TASKS[st.session_state.selected_task]["cards"])}개를 보고나서, 이야기 인간이랑 대화를 하고나서, 답을 고르세요. 맞는 안내글도 있고, 틀린 안내글도 있습니다.

(제한시간 5분, 이야기 인간과 말을 하나 주고받을 때마다, 아래 시계에 남은 시간이 보여지게 됩니다.)</p><h3 style='color: {"#FF0000" if time_left < 60 else "#FFFFFF"};'>⏰ 남은 시간: {minutes:02d}:{seconds:02d}</h3></div>""", unsafe_allow_html=True)
        
        # 시간이 다 되면 자동으로 다음 단계로
        if time_left <= 0:
            st.session_state.chat_completed = True
            st.session_state.current_page = "answer"
            st.rerun()
    
    # 정보 카드 보여주기
    for card_name, card_info in TASKS[st.session_state.selected_task]["cards"].items():
        with st.expander(f"📄 {card_name}"):
            st.write(f"**요약:** {card_info['summary']}")
            st.caption(f"출처: {card_info['source']}")
    
    # 대화 내용 보여주기
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(f"""
                    <div style="color: #FFFFFF; background-color: #1E1E1E; padding: 10px; border-radius: 5px;">
                        {message["content"]}
                    </div>
                """, unsafe_allow_html=True)
    
    # 질문하기
    if prompt := st.chat_input("질문을 입력하세요"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(f"""
                <div style="color: #FFFFFF; background-color: #1E1E1E; padding: 10px; border-radius: 5px;">
                    {prompt}
                </div>
            """, unsafe_allow_html=True)
            
        # 답변하기
        with st.chat_message("assistant"):
            response = get_gpt_response(st.session_state.messages)
            st.markdown(f"""
                <div style="color: #FFFFFF; background-color: #1E1E1E; padding: 10px; border-radius: 5px;">
                    {response}
                </div>
            """, unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # 채팅 후 답 선택 안내
            if len(st.session_state.messages) > 2:  # 초기 안내 메시지 이후에만 표시
                st.info("💡 이제 충분한 정보를 얻으셨다면, 위의 '답 고르러 가기' 버튼을 눌러 답을 선택해보세요.")
        
        # 타이머 업데이트를 위해 페이지 새로고침
        st.rerun()

# 답 선택 화면
elif st.session_state.current_page == "answer":
    st.subheader(f"현재 연습: {st.session_state.selected_task}")
    
    # 문제 안내
    st.info(TASKS[st.session_state.selected_task]["task_info"])
    
    # 답 제출하기
    st.subheader("답 제출하기")
    
    if st.session_state.selected_task == "하나의 정보로 하나의 답 찾기":
        st.markdown(f"""
            <div style="color: #FFFFFF; background-color: #1E1E1E; padding: 10px; border-radius: 5px; margin-bottom: 20px;">
                <h3>문제:</h3>
                {TASKS[st.session_state.selected_task]["question"]}
            </div>
        """, unsafe_allow_html=True)
        user_answer = st.radio(
            "답을 고르세요:",
            options=['O', 'X'],
            horizontal=True,
            label_visibility="visible"
        )
    else:
        if st.session_state.selected_task == "여러 정보로 여러 답 찾기":
            st.markdown("""
                <div style="color: #FFFFFF; background-color: #1E1E1E; padding: 10px; border-radius: 5px; margin-bottom: 20px;">
                    <strong>⚠️ 여러 행동을 함께 고를 수 있습니다</strong>
                </div>
            """, unsafe_allow_html=True)
            user_answer = []
            for action in TASKS[st.session_state.selected_task]["actions"]:
                if st.checkbox(action, key=action):
                    user_answer.append(action)
        else:
            user_answer = [st.radio(
                "당신의 선택:",
                TASKS[st.session_state.selected_task]["actions"],
                label_visibility="visible"
            )]
    
    # 커스텀 CSS로 라디오 버튼과 멀티셀렉트 스타일 변경
    st.markdown("""
        <style>
            /* 라벨 스타일 */
            .stRadio > label, .stMultiSelect > label {
                color: #FFFFFF;
            }
            /* 선택된 항목 스타일 */
            .stRadio > div > div[data-baseweb="radio"] > div[aria-checked="true"] {
                background-color: #FFFFFF;
                color: #000000;
            }
            .stMultiSelect > div > div[data-baseweb="select"] > div[aria-selected="true"] {
                background-color: #FFFFFF;
                color: #000000;
            }
            /* 선택되지 않은 항목 스타일 */
            .stRadio > div > div[data-baseweb="radio"] > div[aria-checked="false"] {
                color: #FFFFFF;
            }
            .stMultiSelect > div > div[data-baseweb="select"] > div[aria-selected="false"] {
                color: #FFFFFF;
            }
        </style>
    """, unsafe_allow_html=True)
    
    if st.button("답 제출하기", use_container_width=True):
        st.session_state.user_answer = user_answer
        st.session_state.current_page = "feedback"
        st.rerun()

# 답 확인 화면
elif st.session_state.current_page == "feedback":
    st.subheader("답 확인하기")
    st.markdown(f"""
        <div style="color: #FFFFFF; background-color: #1E1E1E; padding: 10px; border-radius: 5px; margin-bottom: 20px;">
            <h3>당신의 답:</h3>
            {st.session_state.user_answer}
        </div>
    """, unsafe_allow_html=True)
    
    is_correct = True  # 정답 여부를 추적하는 변수
    
    if st.session_state.selected_task == "하나의 정보로 하나의 답 찾기":
        correct_answer = TASKS[st.session_state.selected_task]["correct_answer"]
        if st.session_state.user_answer == correct_answer:
            st.markdown(f"""
                <div style="color: #FFFFFF; background-color: #1E1E1E; padding: 10px; border-radius: 5px; margin-bottom: 20px;">
                    <h3 style="color: #00FF00;">✅ 맞았습니다!</h3>
                    {TASKS[st.session_state.selected_task]["explanation"]["correct"]}
                </div>
            """, unsafe_allow_html=True)
        else:
            is_correct = False
            st.markdown(f"""
                <div style="color: #FFFFFF; background-color: #1E1E1E; padding: 10px; border-radius: 5px; margin-bottom: 20px;">
                    <h3 style="color: #FF0000;">❌ 틀렸습니다.</h3>
                    {TASKS[st.session_state.selected_task]["explanation"]["incorrect"]}
                </div>
            """, unsafe_allow_html=True)
    else:
        # 정답 표시
        if st.session_state.selected_task == "여러 정보로 하나의 답 찾기":
            correct_answer = TASKS[st.session_state.selected_task]["correct_action"]
            st.markdown(f"""
                <div style="color: #FFFFFF; background-color: #1E1E1E; padding: 10px; border-radius: 5px; margin-bottom: 20px;">
                    <h3>정답:</h3>
                    {correct_answer}
                </div>
            """, unsafe_allow_html=True)
            if st.session_state.user_answer[0] != correct_answer:
                is_correct = False
        else:
            correct_actions = TASKS[st.session_state.selected_task]["correct_actions"]
            st.markdown(f"""
                <div style="color: #FFFFFF; background-color: #1E1E1E; padding: 10px; border-radius: 5px; margin-bottom: 20px;">
                    <h3>정답:</h3>
                    {', '.join(correct_actions)}
                </div>
            """, unsafe_allow_html=True)
            # 모든 정답을 선택했는지 확인
            if not all(action in st.session_state.user_answer for action in correct_actions):
                is_correct = False
                st.markdown("""
                    <div style="color: #FFFFFF; background-color: #1E1E1E; padding: 10px; border-radius: 5px; margin-bottom: 20px;">
                        <h3 style="color: #FFA500;">⚠️ 모든 정답을 찾지 못했습니다.</h3>
                        <p>모든 정답을 찾아보세요!</p>
                    </div>
                """, unsafe_allow_html=True)
        
        # 피드백 표시
        for action in st.session_state.user_answer:
            feedback = TASKS[st.session_state.selected_task]["feedback"][action]
            if "✅" in feedback:
                st.markdown(f"""
                    <div style="color: #FFFFFF; background-color: #1E1E1E; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                        <span style="color: #00FF00;">{feedback}</span>
                    </div>
                """, unsafe_allow_html=True)
            elif "❌" in feedback:
                st.markdown(f"""
                    <div style="color: #FFFFFF; background-color: #1E1E1E; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                        <span style="color: #FF0000;">{feedback}</span>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div style="color: #FFFFFF; background-color: #1E1E1E; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                        <span style="color: #FFA500;">{feedback}</span>
                    </div>
                """, unsafe_allow_html=True)
    
    # 오답이거나 모든 정답을 찾지 못한 경우 다시 답 고르기 버튼 표시
    if not is_correct:
        st.button("다시 답 고르기", use_container_width=True, on_click=lambda: setattr(st.session_state, 'current_page', 'answer'))
    
    # 새로 시작하기
    if st.button("새로운 연습 시작하기", use_container_width=True):
        st.session_state.current_page = "task_select"
        st.session_state.selected_task = None
        st.session_state.messages = []
        st.session_state.task_completed = False
        st.session_state.user_answer = None
        st.session_state.timer_start = None  # 타이머 초기화
        st.session_state.time_left = 300  # 5분으로 초기화
        st.session_state.last_update = None
        st.rerun() 