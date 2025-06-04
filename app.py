import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="정보 찾기 연습",
    page_icon="🧠",
    layout="wide"
)

# 커스텀 CSS
st.markdown("""
    <style>
        .stApp {
            background-color: #000000;
            color: #FFFFFF;
        }
        
        .stButton>button {
            width: 100%;
            margin-top: 10px;
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
        }
        
        .stButton>button:hover {
            background-color: #45a049;
        }
        
        h1, h2, h3, p {
            color: #FFFFFF;
        }
    </style>
""", unsafe_allow_html=True)

# 메인 컨텐츠
st.title("정보 찾기 연습")
st.write("원하시는 버전을 선택해주세요:")

# 두 개의 컬럼 생성
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
        <div style='text-align: center;'>
            <h2>Medium Fidelity 버전</h2>
            <p>기존의 다크 테마 기반 인터페이스</p>
        </div>
    """, unsafe_allow_html=True)
    if st.button("Medium Fidelity 버전 시작하기", key="med_fi"):
        st.switch_page("pages/med_fi.py")

with col2:
    st.markdown("""
        <div style='text-align: center;'>
            <h2>High Fidelity 버전</h2>
            <p>휴리스틱 평가를 거쳐서 수정한 인터페이스</p>
        </div>
    """, unsafe_allow_html=True)
    if st.button("High Fidelity 버전 시작하기", key="high_fi"):
        st.switch_page("pages/high_fi.py") 