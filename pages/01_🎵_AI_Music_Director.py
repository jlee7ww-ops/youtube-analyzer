import streamlit as st
import pandas as pd
from openai import OpenAI
import json

# --- 페이지 설정 ---
st.set_page_config(page_title="AI 뮤직 디렉터 Pro", page_icon="🎧", layout="wide")

st.title("🎧 AI 뮤직 & 아트 디렉터 Pro")
st.markdown("""
**Suno(음악) + Midjourney(이미지)** 기획을 한 번에!
3분 이상의 꽉 찬 곡 구조와 고퀄리티 프롬프트를 생성합니다.
""")

# --- 탭 설정 ---
mode = st.radio("모드 선택", ["🤖 ChatGPT Plus 붙여넣기 (무료)", "🔑 API 키 사용 (유료)"], horizontal=True)

# --- 결과 처리 함수 ---
def process_data(json_input):
    try:
        # JSON 파싱
        if isinstance(json_input, str):
            data = json.loads(json_input)
        else:
            data = json_input
            
        # 리스트 찾기 (playlist 또는 songs 키)
        playlist = data.get('playlist', data.get('songs', []))
        
        if not playlist:
            st.error("데이터를 찾을 수 없습니다. JSON 형식을 확인해주세요.")
            return

        st.success(f"🎉 총 {len(playlist)}곡의 프로젝트가 생성되었습니다!")
        
        # 탭 생성
        tabs = st.tabs([f"{i+1}. {song.get('title', 'Track')}" for i, song in enumerate(playlist)])
        
        export_data = []

        for i, song in enumerate(playlist):
            with tabs[i]:
                # 상단: 제목
                st.subheader(f"🎵 {song.get('title')}")
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown("### 🎹 Suno Style")
                    st.info(song.get('style'))
                    st.code(song.get('style'), language="text")
                
                with col2:
                    st.markdown("### 🎨 Midjourney Prompt")
                    st.warning(song.get('midjourney'))
                    st.code(song.get('midjourney'), language="text")

                st.markdown("### 📝 Lyrics & Structure (3분+)")
                st.text_area("Suno 가사창에 붙여넣으세요", song.get('lyrics'), height=400, key=f"lyrics_{i}")
                
                # 엑셀 저장을 위한 데이터 수집
                export_data.append({
                    "Track": i+1,
                    "Title": song.get('title'),
                    "Style (Suno)": song.get('style'),
                    "Lyrics": song.get('lyrics'),
                    "Image Prompt (Midjourney)": song.get('midjourney')
                })

        # 엑셀 다운로드
        df = pd.DataFrame(export_data)
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 전체 기획안 엑셀 다운로드", csv, "project_suno_mj.csv", "text/csv")

    except json.JSONDecodeError:
        st.error("JSON 해석 실패! ChatGPT 코드를 끝까지 복사했는지 확인해주세요.")
    except Exception as e:
        st.error(f"오류 발생: {e}")

# ==========================================
# [모드 1] 수동 모드 (프롬프트 제공)
# ==========================================
if mode == "🤖 ChatGPT Plus 붙여넣기 (무료)":
    with st.expander("📌 이 프롬프트를 복사해서 ChatGPT에게 보내세요! (클릭)", expanded=True):
        st.code("""
당신은 Suno AI (v3.5/v5)와 Midjourney 전문 'AI 크리에이티브 디렉터'입니다.
사용자 요청 주제에 맞춰 5곡의 플레이리스트를 기획하세요.

### [필수 작성 규칙]
1. **모드 판단:** 가사 요청 시 Lyrical, BGM 요청 시 Instrumental 모드로 작성.
2. **언어:** 별도 요청 없으면 영어(English) 기본. 한국어 요청 시 "한국어 제목 + 한국어 가사" 작성.
3. **Midjourney:** 곡 분위기에 맞는 썸네일 프롬프트 작성 (--ar 16:9 포함, 영어 작성).
4. **Suno 스타일:** 장르, 분위기, 악기, BPM 등을 영어 태그로 작성.
5. **구조 (중요):** 3분 이상 길이를 위해 반드시 아래 구조를 준수하여 가사 작성.
   [Intro] -> [Verse 1] -> [Chorus] -> [Verse 2] -> [Chorus] -> [Bridge] -> [Guitar Solo/Interlude] -> [Chorus] -> [Outro] -> [End]

### [출력 형식]
반드시 아래 JSON 포맷으로만 출력하세요. (설명 금지, 코드블록 안에 작성)

{
  "playlist": [
    {
      "title": "곡 제목",
      "style": "Suno Style Tags (English)",
      "midjourney": "Midjourney Prompt (English, --ar 16:9)",
      "lyrics": "[Intro]\n..."
    }
  ]
}
        """, language="text")
    
    user_input = st.text_area("ChatGPT가 만든 JSON 코드를 여기에 붙여넣으세요:", height=300)
    if st.button("변환 시작 ✨"):
        if user_input:
            process_data(user_input)
        else:
            st.warning("코드를 붙여넣어 주세요.")

# ==========================================
# [모드 2] 자동 모드 (API)
# ==========================================
else:
    api_key = st.text_input("OpenAI API Key", type="password")
    topic = st.text_input("주제/키워드 (예: 비 오는 날 듣는 재즈, 한국어 가사)")
    
    if st.button("AI 자동 기획 🚀"):
        if not api_key:
            st.error("API 키를 입력하세요.")
        else:
            with st.spinner("3분짜리 곡 구조와 미드저니 프롬프트를 설계 중입니다..."):
                client = OpenAI(api_key=api_key)
                
                system_prompt = """
                당신은 Suno AI와 Midjourney 전문 디렉터입니다. 
                사용자 주제로 5곡을 기획하되, 3분 이상의 곡 길이를 위해 
                [Intro]-[Verse]-[Chorus]-[Verse]-[Chorus]-[Bridge]-[Solo]-[Chorus]-[Outro] 구조를 
                반드시 지켜서 JSON으로 출력하세요.
                """
                
                user_msg = f"주제: {topic}. 위 규칙에 맞춰 JSON으로 출력해."
                
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_msg}
                        ],
                        response_format={"type": "json_object"}
                    )
                    process_data(response.choices[0].message.content)
                except Exception as e:
                    st.error(f"API 오류: {e}")