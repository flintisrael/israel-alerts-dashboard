import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import extra_streamlit_components as stx

# הגדרות דף
st.set_page_config(page_title="דשבורד התרעות", layout="wide", initial_sidebar_state="collapsed")

# CSS "אלים" ליישור RTL מלא של כל רכיבי ה-Markdown והכותרות
st.markdown("""
    <style>
    /* יישור כללי של האפליקציה */
    [data-testid="stAppViewContainer"], .main {
        direction: rtl;
        text-align: right;
    }

    /* הכרחת יישור לימין לכל הכותרות והטקסטים */
    h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown {
        text-align: right !important;
        direction: rtl !important;
    }

    /* טיפול ספציפי בכותרות של דשבורד */
    [data-testid="stHeader"] {
        direction: rtl;
    }

    /* יישור רכיב ה-Metric (המספרים הגדולים) */
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {
        text-align: right !important;
        direction: rtl !important;
        justify-content: flex-start !important;
    }

    /* יישור כרטיסי המטריקות */
    [data-testid="stMetric"] {
        border: 1px solid #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        background-color: #fafafa;
        text-align: right;
    }

    /* יישור הטבלה והגרף */
    [data-testid="stDataFrame"], .plotly-graph-div {
        direction: rtl;
    }

    /* ביטול השוליים המיותרים בשמאל שנוצרים בגלל ה-LTR המקורי */
    .stHorizontalBlock {
        direction: rtl;
    }
    </style>
    """, unsafe_allow_html=True)

cookie_manager = stx.CookieManager()

# כותרת - שים לב לשימוש ב-Dashboard בלי א'
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

    # ניהול עוגיות
    saved_cities = cookie_manager.get(cookie="selected_cities")
    if saved_cities is None: saved_cities = []

    # בחירת יישובים
    with st.expander("🔍 הגדרות חיפוש ובחירת יישובים", expanded=not bool(saved_cities)):
        selected_cities = st.multiselect(
            "הוסף יישובים להשוואה:",
            options=all_cities,
            default=saved_cities
        )
        if selected_cities != saved_cities:
            cookie_manager.set("selected_cities", selected_cities, key="save_cities_v3")

    if selected_cities:
        # עיבוד נתונים עם סינון כפילויות (Deduplication)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        mask = (df['data'].isin(selected_cities)) & (df['alertDate'] >= thirty_days_ago) & (df['category'] == 1)
        clean_df = df.loc[mask].copy()
        clean_df['round_time'] = clean_df['alertDate'].dt.floor('min')
        clean_df = clean_df.drop_duplicates(subset=['data', 'round_time'])
        
        counts = clean_df['data'].value_counts().reindex(selected_cities, fill_value=0).reset_index()
        counts.columns = ['יישוב', 'מספר אזעקות']

        # שורת מטריקות
        st.subheader("📊 תמונת מצב")
        cols = st.columns(len(selected_cities))
        for i, city in enumerate(selected_cities):
            city_count = counts[counts['יישוב'] == city]['מספר אזעקות'].values[0]
            cols[i].metric(label=city, value=int(city_count))

        st.markdown("---")

        # גרף וטבלה
        col_graph, col_table = st.columns([2, 1])

        with col_graph:
            fig = px.bar(counts, x='יישוב', y='מספר אזעקות', 
                         title="השוואת אזעקות (30 ימים אחרונים)",
                         color='מספר אזעקות', 
                         color_continuous_scale='Reds',
                         template='plotly_white')
            
            fig.update_layout(
                xaxis_title="יישוב", 
                yaxis_title="כמות אזעקות",
                title_x=1,
                font=dict(size=14)
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_table:
            st.subheader("📝 פירוט מלא")
            st.dataframe(counts, hide_index=True, use_container_width=True)

    else:
        st.info("אנא בחר יישובים מתיבת החיפוש למעלה.")

except Exception as e:
    st.error(f"שגיאה: {e}")