import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import extra_streamlit_components as stx

st.set_page_config(page_title="דשבורד התרעות", layout="wide", initial_sidebar_state="collapsed")

# CSS - עיצוב RTL וכרטיסי נתונים
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;700&display=swap');
    html, body, [data-testid="stAppViewContainer"] { font-family: 'Assistant', sans-serif; direction: rtl; text-align: right; }
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown { text-align: right !important; direction: rtl !important; }
    .metric-card {
        background: var(--secondary-background-color);
        border: 1px solid var(--divider-color);
        padding: 1.2rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        text-align: center;
        margin-bottom: 15px;
        min-height: 140px; 
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    .metric-label { font-size: 1rem; color: #888; min-height: 2.4em; display: flex; align-items: center; justify-content: center; }
    .metric-value { font-size: 2rem; font-weight: bold; color: #FF4B4B; }
    .stHorizontalBlock { direction: rtl; }
    /* עיצוב התאריכון שייראה טוב ב-RTL */
    div[data-baseweb="datepicker"] { direction: ltr; } 
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
    saved_range = cookie_manager.get(cookie="time_range")
    
    if saved_cities is None: saved_cities = []
    if saved_range is None: saved_range = "30 ימים"

    with st.expander("⚙️ הגדרות תצוגה וזמן", expanded=not bool(saved_cities)):
        col_c, col_t = st.columns([2, 1])
        with col_c:
            selected_cities = st.multiselect("יישובים להשוואה:", options=all_cities, default=saved_cities)
        with col_t:
            time_options = ["7 ימים", "30 ימים", "מתחילת המלחמה", "בחירה חופשית"]
            index_range = time_options.index(saved_range) if saved_range in time_options else 1
            selected_range = st.selectbox("טווח זמן:", options=time_options, index=index_range)

        # לוגיקת תאריכון (Date Picker)
        start_date = None
        end_date = datetime.now()
        
        if selected_range == "בחירה חופשית":
            custom_dates = st.date_input(
                "בחר טווח תאריכים:",
                value=(datetime.now() - timedelta(days=7), datetime.now()),
                max_value=datetime.now()
            )
            if isinstance(custom_dates, tuple) and len(custom_dates) == 2:
                start_date, end_date = custom_dates
                start_date = datetime.combine(start_date, datetime.min.time())
                end_date = datetime.combine(end_date, datetime.max.time())

        # שמירה לעוגיות
        if selected_cities != saved_cities or selected_range != saved_range:
            cookie_manager.set("selected_cities", selected_cities, key="save_v7")
            cookie_manager.set("time_range", selected_range, key="save_range_v7")

    if selected_cities:
        # חישוב התאריכים לפי הבחירה
        now = datetime.now()
        if selected_range == "7 ימים":
            start_date = now - timedelta(days=7)
        elif selected_range == "30 ימים":
            start_date = now - timedelta(days=30)
        elif selected_range == "מתחילת המלחמה":
            start_date = datetime(2025, 2, 28)
        # אם זה "בחירה חופשית" והמשתמש בחר תאריכים, start_date כבר מוגדר

        if start_date:
            mask = (df['data'].isin(selected_cities)) & \
                   (df['alertDate'] >= start_date) & \
                   (df['alertDate'] <= end_date) & \
                   (df['category'] == 1)
            
            clean_df = df.loc[mask].copy()
            clean_df['round_time'] = clean_df['alertDate'].dt.floor('min')
            clean_df = clean_df.drop_duplicates(subset=['data', 'round_time'])
            
            counts = clean_df['data'].value_counts().reindex(selected_cities, fill_value=0).reset_index()
            counts.columns = ['יישוב', 'מספר אזעקות']

            st.subheader(f"📊 תמונת מצב - {selected_range}")
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
            
            fig = px.bar(counts, x='יישוב', y='מספר אזעקות', color='מספר אזעקות', 
                         color_continuous_scale='Reds', text_auto=True)
            fig.update_layout(title=f"השוואה בין {start_date.strftime('%d.%m.%Y')} ל-{end_date.strftime('%d.%m.%Y')}", title_x=1)
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("בחר יישובים למעלה.")

except Exception as e:
    st.error(f"שגיאה: {e}")