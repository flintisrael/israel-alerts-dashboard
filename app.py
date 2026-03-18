import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import arabic_reshaper
from bidi.algorithm import get_display
import extra_streamlit_components as stx # הספרייה היציבה החדשה

def get_heb_text(text):
    return get_display(arabic_reshaper.reshape(text))

st.set_page_config(page_title="השוואת אזעקות - זיכרון חכם", layout="wide")

# אתחול מנהל העוגיות
cookie_manager = stx.CookieManager()

st.title("🚨 דאשבורד השוואת אזעקות")

url = 'https://raw.githubusercontent.com/dleshem/israel-alerts-data/main/israel-alerts.csv'

@st.cache_data(ttl=600)
def load_data():
    df = pd.read_csv(url, usecols=['data', 'alertDate', 'category'])
    df['alertDate'] = pd.to_datetime(df['alertDate'])
    all_cities = sorted(df['data'].unique().tolist())
    return df, all_cities

try:
    df, all_cities = load_data()

    # שליפת הערים מהעוגייה של המשתמש
    saved_cities = cookie_manager.get(cookie="selected_cities")
    
    # אם אין עוגייה, נתחיל מרשימה ריקה
    if saved_cities is None:
        saved_cities = []

    # שדה הבחירה
    selected_cities = st.multiselect(
        "בחר יישובים להשוואה (הבחירה תישמר לביקור הבא):",
        options=all_cities,
        default=saved_cities
    )

    # שמירה לעוגייה בכל פעם שהבחירה משתנה
    if selected_cities != saved_cities:
        cookie_manager.set("selected_cities", selected_cities, key="save_cookies")

    if selected_cities:
        thirty_days_ago = datetime.now() - timedelta(days=30)
        mask = (df['data'].isin(selected_cities)) & (df['alertDate'] >= thirty_days_ago) & (df['category'] == 1)
        filtered = df.loc[mask].copy()
        
        filtered['round_time'] = filtered['alertDate'].dt.floor('min')
        clean_df = filtered.drop_duplicates(subset=['data', 'round_time'])
        
        counts = clean_df['data'].value_counts().reindex(selected_cities, fill_value=0)
        heb_labels = [get_heb_text(city) for city in counts.index]

        col1, col2 = st.columns([2, 1])
        with col1:
            fig, ax = plt.subplots(figsize=(10, 5))
            counts.plot(kind='bar', color='#3498db', ax=ax, edgecolor='black')
            ax.set_ylabel(get_heb_text("מספר אזעקות"))
            ax.set_xticklabels(heb_labels, rotation=45)
            st.pyplot(fig)

        with col2:
            st.write("### נתונים מספריים:")
            st.table(counts)
    else:
        st.info("בחר יישובים כדי להתחיל.")

except Exception as e:
    st.error(f"שגיאה: {e}")