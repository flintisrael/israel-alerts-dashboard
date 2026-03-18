import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import extra_streamlit_components as stx

# הגדרות דף
st.set_page_config(page_title="דשבורד התרעות", layout="wide", initial_sidebar_state="collapsed")

# CSS מעודכן עם גובה קבוע לקוביות למראה אחיד
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Assistant', sans-serif;
        direction: rtl;
        text-align: right;
    }

    /* יישור RTL לכל הכותרות והטקסטים */
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown {
        text-align: right !important;
        direction: rtl !important;
    }

    /* עיצוב כרטיסי המטריקות - עם גובה קבוע */
    .metric-card {
        background: var(--secondary-background-color);
        border: 1px solid var(--divider-color);
        padding: 1.2rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        text-align: center;
        margin-bottom: 15px;
        
        /* התיקון כאן: גובה קבוע כדי שכל הקוביות יהיו זהות */
        min-height: 140px; 
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    
    .metric-label {
        font-size: 1rem;
        color: #888;
        line-height: 1.2;
        margin-bottom: 8px;
        min-height: 2.4em; /* מבטיח מקום ל-2 שורות טקסט גם אם יש רק אחת */
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #FF4B4B;
    }

    /* יישור עמודות */
    .stHorizontalBlock {
        direction: rtl;
    }
    </style>
    """, unsafe_allow_html=True)

cookie_manager = stx.CookieManager()

st.title("🛡️ דשבורד התרעות בזמן אמת")
st.markdown("---")

url = 'https://raw.githubusercontent.com/dleshem/israel-alerts-data/main/israel-alerts.csv'

@st.cache_data(ttl=600)
def load_data():
    df = pd.read_csv(url, usecols=['data', 'alertDate', 'category'])
    df['alertDate'] = pd.to_datetime(df['alertDate'])
    all_cities = sorted(df['data'].unique().tolist())
    return df, all_cities

try:
    df, all_cities = load_data()

    saved_cities = cookie_manager.get(cookie="selected_cities")
    if saved_cities is None: saved_cities = []

    with st.expander("🔍 הגדרות בחירה", expanded=not bool(saved_cities)):
        selected_cities = st.multiselect(
            "יישובים להשוואה:",
            options=all_cities,
            default=saved_cities
        )
        if selected_cities != saved_cities:
            cookie_manager.set("selected_cities", selected_cities, key="save_v_final_aligned")

    if selected_cities:
        thirty_days_ago = datetime.now() - timedelta(days=30)
        mask = (df['data'].isin(selected_cities)) & (df['alertDate'] >= thirty_days_ago) & (df['category'] == 1)
        clean_df = df.loc[mask].copy()
        clean_df['round_time'] = clean_df['alertDate'].dt.floor('min')
        clean_df = clean_df.drop_duplicates(subset=['data', 'round_time'])
        
        counts = clean_df['data'].value_counts().reindex(selected_cities, fill_value=0).reset_index()
        counts.columns = ['יישוב', 'מספר אזעקות']

        st.subheader("📊 תמונת מצב")
        cols = st.columns(len(selected_cities))
        for i, city in enumerate(selected_cities):
            city_count = counts[counts['יישוב'] == city]['מספר אזעקות'].values[0]
            with cols[i]:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">{city}</div>
                        <div class="metric-value">{int(city_count)}</div>
                    </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        col_graph, col_table = st.columns([2, 1])
        with col_graph:
            fig = px.bar(counts, x='יישוב', y='מספר אזעקות', 
                         title="השוואת אזעקות (30 ימים אחרונים)",
                         color='מספר אזעקות', color_continuous_scale='Reds')
            fig.update_layout(xaxis_title=None, yaxis_title="כמות אזעקות", title_x=1)
            st.plotly_chart(fig, use_container_width=True, theme="streamlit")

        with col_table:
            st.subheader("📝 פירוט מלא")
            st.dataframe(counts, hide_index=True, use_container_width=True)
    else:
        st.info("בחר יישובים למעלה.")

except Exception as e:
    st.error(f"שגיאה: {e}")