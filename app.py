import streamlit as st
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import pandas as pd

# --- 페이지 설정 ---
st.set_page_config(page_title="유튜브 떡상 탐지기 Pro", page_icon="🚀", layout="wide")

st.title("🚀 유튜브 떡상 탐지기 (Pro Ver.)")
st.markdown("특정 기간, **영상 길이**, 조회수를 만족하는 '알고리즘의 선택'을 받은 영상을 찾아냅니다.")

# --- 사이드바: 설정값 입력 ---
with st.sidebar:
    st.header("⚙️ 검색 설정")
    
    # 1. API 키
    api_key = st.text_input("YouTube API Key", type="password")
    
    # 2. 키워드
    keyword = st.text_input("검색 키워드", value="재테크")
    
    # 3. 기간 설정 (이미지의 '업로드 날짜' 대응)
    days_ago = st.slider("최근 며칠 이내?", 1, 30, 10)
    
    # 4. 영상 길이 선택 (이미지의 '영상 길이 선택' 대응)
    duration_option = st.selectbox(
        "영상 길이 선택",
        ("모든 길이", "4분 미만 (Short)", "4분 ~ 20분 (Medium)", "20분 초과 (Long)")
    )
    
    # API 파라미터로 변환
    duration_map = {
        "모든 길이": None,
        "4분 미만 (Short)": "short",
        "4분 ~ 20분 (Medium)": "medium",
        "20분 초과 (Long)": "long"
    }
    video_duration = duration_map[duration_option]

    # 5. 최소 조회수 (이미지의 '최소 조회수' 대응)
    min_views = st.number_input("최소 조회수 (회 이상)", min_value=1000, value=10000, step=1000)
    
    # 6. 가져올 개수 (이미지의 '가져올 영상 개수' 대응)
    max_results = st.number_input("가져올 영상 개수 (최대 50)", min_value=10, max_value=50, value=20)
    
    search_btn = st.button("분석 시작하기")

# --- 핵심 로직 ---
def get_video_data(api_key, keyword, days_ago, min_views_filter, duration, max_res):
    youtube = build('youtube', 'v3', developerKey=api_key)
    
    now = datetime.utcnow()
    start_date = (now - timedelta(days=days_ago)).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # 검색 요청에 'videoDuration' 파라미터 추가
    search_args = {
        'part': 'id,snippet',
        'q': keyword,
        'type': 'video',
        'publishedAfter': start_date,
        'maxResults': max_res
    }
    
    if duration:  # 길이 필터가 선택되었으면 추가
        search_args['videoDuration'] = duration

    search_response = youtube.search().list(**search_args).execute()
    
    video_ids = [item['id']['videoId'] for item in search_response['items']]
    
    if not video_ids:
        return []

    # 통계 조회
    video_response = youtube.videos().list(
        part='statistics,snippet',
        id=','.join(video_ids)
    ).execute()
    
    channel_ids = [item['snippet']['channelId'] for item in video_response['items']]
    
    channel_response = youtube.channels().list(
        part='statistics',
        id=','.join(channel_ids)
    ).execute()
    
    channel_subs = {}
    for item in channel_response['items']:
        subs = int(item['statistics'].get('subscriberCount', 0))
        channel_subs[item['id']] = subs
        
    final_data = []
    
    for video in video_response['items']:
        views = int(video['statistics'].get('viewCount', 0))
        
        if views < min_views_filter:
            continue
            
        channel_id = video['snippet']['channelId']
        subs = channel_subs.get(channel_id, 0)
        
        if subs > 100:
            performance = (views / subs) * 100
        else:
            performance = 0
            
        final_data.append({
            '썸네일': video['snippet']['thumbnails']['medium']['url'],
            '제목': video['snippet']['title'],
            '채널명': video['snippet']['channelTitle'],
            '조회수': views,
            '구독자수': subs,
            '성과율(%)': round(performance, 1),
            '게시일': video['snippet']['publishedAt'][:10],
            '링크': f"https://www.youtube.com/watch?v={video['id']}"
        })
        
    return sorted(final_data, key=lambda x: x['성과율(%)'], reverse=True)

# --- 실행 ---
if search_btn:
    if not api_key:
        st.error("API 키를 입력해주세요.")
    else:
        with st.spinner("분석 중입니다..."):
            try:
                results = get_video_data(api_key, keyword, days_ago, min_views, video_duration, max_results)
                
                if not results:
                    st.warning("조건에 맞는 영상이 없습니다.")
                else:
                    st.success(f"분석 완료! {len(results)}개의 영상을 찾았습니다.")
                    df = pd.DataFrame(results)
                    
                    st.subheader("🏆 성과율 TOP 3")
                    cols = st.columns(3)
                    for i in range(min(3, len(results))):
                        video = results[i]
                        with cols[i]:
                            st.image(video['썸네일'], use_container_width=True)
                            st.markdown(f"**[{video['제목']}]({video['링크']})**")
                            st.caption(f"성과율: {video['성과율(%)']}% | 조회수: {video['조회수']:,}")

                    st.divider()
                    st.dataframe(
                        df[['제목', '성과율(%)', '조회수', '구독자수', '링크']],
                        column_config={
                            "링크": st.column_config.LinkColumn("링크"),
                            "성과율(%)": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=max(df['성과율(%)'])),
                        },
                        hide_index=True,
                        use_container_width=True
                    )
            except Exception as e:
                st.error(f"오류: {e}")