import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
# שורות חדשות לטיפול בטקסט הפוך בגרף
import arabic_reshaper
from bidi.algorithm import get_display

# פונקציית עזר להפיכת טקסט עברי בשביל הגרף
def get_heb_text(text):
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    return bidi_text

# הגדרות דף
st.set_page_config(page_title="דאשבורד אזעקות - שומרון ובנימין", layout="wide")

st.title("🚨 השוואת אזעקות: פדואל, רבבה ועטרת")
st.subheader("נתוני אמת - ירי רקטי (30 ימים אחרונים)")

# משיכת נתונים מהמאגר הקהילתי (פתוח לכל העולם)
url = 'https://raw.githubusercontent.com/dleshem/israel-alerts-data/main/israel-alerts.csv'

@st.cache_data(ttl=600) # מרענן נתונים כל 10 דקות
def load_data():
    df = pd.read_csv(url, usecols=['data', 'alertDate', 'category'])
    df['alertDate'] = pd.to_datetime(df['alertDate'])
    return df

try:
    df = load_data()
    
    # הגדרות סינון
    cities = ['פדואל', 'רבבה', 'עטרת']
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    # סינון: יישובים, תאריך, ורק ירי רקטות (קטגוריה 1)
    mask = (df['data'].isin(cities)) & (df['alertDate'] >= thirty_days_ago) & (df['category'] == 1)
    filtered = df.loc[mask].copy()
    
    # איחוד מטחים (דקה אחת = אירוע אחד)
    filtered['round_time'] = filtered['alertDate'].dt.floor('min')
    clean_df = filtered.drop_duplicates(subset=['data', 'round_time'])
    
    counts = clean_df['data'].value_counts().reindex(cities, fill_value=0)

    # הכנת תוויות הפוכות עבור הגרף
    heb_labels = [get_heb_text(city) for city in counts.index]

    # הצגה בגרף
    col1, col2 = st.columns([2, 1])
    
    with col1:
        fig, ax = plt.subplots(figsize=(10, 5))
        # משתמשים בתוויות ההפוכות רק עבור התוויות (X-axis labels) של הגרף
        counts.plot(kind='bar', color=['#1f77b4', '#ff7f0e', '#2ca02c'], ax=ax)
        ax.set_ylabel(get_heb_text("מספר אזעקות")) # גם את הציר הזה צריך להפוך
        ax.set_xticklabels(heb_labels, rotation=0) # עדכון התוויות לצורה הנכונה
        st.pyplot(fig)

    with col2:
        st.metric("סה''כ אזעקות במרחב", int(counts.sum()))
        st.write("פירוט לפי יישוב:")
        st.table(counts) # בטבלה עצמה הכל בסדר, אין צורך בשינוי

except Exception as e:
    st.error(f"שגיאה בטעינת הנתונים: {e}")