import streamlit as st
import requests
import pandas as pd
import json

# --- AYARLAR ---
# Backend API adresinin doğru olduğundan emin olun (uvicorn çalışıyor olmalı)
API_URL = "http://127.0.0.1:8000/scrape/multi-type-list"
TEST_URL = "http://books.toscrape.com/"

st.set_page_config(page_title="Universal Scraper Terminal", layout="wide", page_icon="🕸️")

# --- BAŞLIK ---
col1, col2 = st.columns([1, 5])
with col1:
    st.image("https://cdn-icons-png.flaticon.com/512/2111/2111432.png", width=80)
with col2:
    st.title("Universal Scraper API Terminal")
    st.markdown("Complex data extraction made simple. Choose your input method below.")

st.markdown("---")

# --- YARDIMCI FONKSİYON: API İSTEĞİ ---
def fetch_data(payload):
    """Verilen JSON payload'u API'ye gönderir ve sonucu döner."""
    try:
        with st.spinner("🕸️ Scraping in progress..."):
            response = requests.post(API_URL, json=payload)
            response.raise_for_status()
            return response.json()
    except requests.exceptions.ConnectionError:
        st.error("⛔ API Connection Error. Is the backend running? (`uvicorn main:app --reload`)")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"HTTP Error ({response.status_code}): {response.text}")
        return None
    except Exception as e:
        st.error(f"Unexpected Error: {e}")
        return None

# --- ANA ARAYÜZ (TABS) ---
tab_visual, tab_json = st.tabs(["🛠️ Visual Builder (No-Code)", "📝 Raw JSON Input (Advanced)"])

# ==========================================
# MOD 1: GÖRSEL OLUŞTURUCU (VISUAL BUILDER)
# ==========================================
with tab_visual:
    st.subheader("🔹 Configure Scraping Task")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        target_url = st.text_input("Target URL", value=TEST_URL, help="The website you want to scrape.")
    
    with col_b:
        container_selector = st.text_input(
            "Container Selector", 
            value="article.product_pod", 
            help="The CSS selector for the main item card (e.g., .product-card)"
        )

    st.markdown("#### Data Fields Mapping")
    
    # Session State: Alanları tutmak için
    if 'fields' not in st.session_state:
        st.session_state.fields = [
            {'field_name': 'title', 'selector': 'h3 a', 'extraction_type': 'text'},
            {'field_name': 'price', 'selector': '.price_color', 'extraction_type': 'text'},
            {'field_name': 'link', 'selector': 'h3 a', 'extraction_type': 'href'}
        ]

    # Alanları Düzenleme Alanı
    for i, field in enumerate(st.session_state.fields):
        c1, c2, c3, c4 = st.columns([3, 3, 2, 1])
        with c1:
            field['field_name'] = st.text_input(f"Field Name #{i+1}", value=field['field_name'], key=f"name_{i}", placeholder="e.g., price")
        with c2:
            field['selector'] = st.text_input(f"CSS Selector #{i+1}", value=field['selector'], key=f"sel_{i}", placeholder="e.g., .price")
        with c3:
            field['extraction_type'] = st.selectbox(
                f"Type #{i+1}", 
                ['text', 'href', 'src', 'alt', 'data-id'], 
                index=['text', 'href', 'src', 'alt', 'data-id'].index(field['extraction_type']) if field['extraction_type'] in ['text', 'href', 'src', 'alt', 'data-id'] else 0,
                key=f"type_{i}"
            )
        with c4:
            st.write("") # Spacer
            st.write("") # Spacer
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state.fields.pop(i)
                st.rerun()

    if st.button("➕ Add New Field"):
        st.session_state.fields.append({'field_name': '', 'selector': '', 'extraction_type': 'text'})
        st.rerun()

    st.markdown("---")
    
    # Payload Önizleme (Kullanıcıya JSON'ın nasıl oluştuğunu öğretir)
    visual_payload = {
        "url": target_url,
        "container_selector": container_selector,
        "data_fields": st.session_state.fields
    }
    
    with st.expander("👀 View Generated JSON Config"):
        st.json(visual_payload)

    if st.button("🚀 Start Scraping (Visual Mode)", type="primary"):
        result = fetch_data(visual_payload)
        if result:
            st.session_state['last_result'] = result


# ==========================================
# MOD 2: RAW JSON GİRİŞİ (DEVELOPER MODE)
# ==========================================
with tab_json:
    st.subheader("🔹 Paste Your Configuration")
    st.markdown("Directly paste the JSON payload for the API. Useful for saving/loading configurations.")

    default_json = json.dumps({
        "url": "http://books.toscrape.com/",
        "container_selector": "article.product_pod",
        "data_fields": [
            {"field_name": "book_title", "selector": "h3 a", "extraction_type": "text"},
            {"field_name": "price", "selector": ".price_color", "extraction_type": "text"},
            {"field_name": "cover_image", "selector": "img.thumbnail", "extraction_type": "src"}
        ]
    }, indent=2)

    json_input = st.text_area("JSON Payload", value=default_json, height=300)

    if st.button("🚀 Start Scraping (JSON Mode)", type="primary"):
        try:
            # JSON'ı parse et ve API'ye gönder
            parsed_payload = json.loads(json_input)
            result = fetch_data(parsed_payload)
            if result:
                st.session_state['last_result'] = result
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON Format: {e}")


# ==========================================
# SONUÇLARI GÖSTERME ALANI (ORTAK)
# ==========================================
st.markdown("---")
st.header("📊 Results")

if 'last_result' in st.session_state and st.session_state['last_result']:
    data = st.session_state['last_result']
    
    if data.get("status") == "success":
        items = data.get("data", [])
        count = data.get("count", 0)
        
        st.success(f"Successfully scraped **{count}** items.")
        
        # DataFrame Gösterimi
        if items:
            df = pd.DataFrame(items)
            st.dataframe(df, use_container_width=True)
            
            # İndirme Butonları
            c1, c2 = st.columns(2)
            with c1:
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("⬇️ Download as CSV", data=csv, file_name="scraped_data.csv", mime="text/csv")
            with c2:
                json_str = df.to_json(orient="records", indent=2)
                st.download_button("⬇️ Download as JSON", data=json_str, file_name="scraped_data.json", mime="application/json")
        else:
            st.warning("No items found. Check your selectors.")
            
    else:
        st.error(f"API Error: {data.get('message')}")
else:
    st.info("No data scraped yet. Configure and click 'Start Scraping'.")
