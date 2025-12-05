import streamlit as st
import requests
import pandas as pd
import json
import time

# --- AYARLAR ---
st.set_page_config(page_title="Universal Scraper Terminal", layout="wide", page_icon="🕸️")

# --- BAĞLANTI VE GÜVENLİK AYARLARI ---
try:
    # 1. API URL
    if "API_URL" in st.secrets:
        raw_url = st.secrets["API_URL"]
        clean_url = raw_url.strip().strip('"').strip("'").rstrip('/')
        if not clean_url.startswith("http"):
            clean_url = f"https://{clean_url}"
        BASE_URL = clean_url
    else:
        # Localhost (Geliştirme)
        BASE_URL = "http://127.0.0.1:8000"

    # 2. API KEY (GİZLİ TUTULMALI)
    if "API_KEY" in st.secrets:
        API_KEY = st.secrets["API_KEY"]
    else:
        # Kod içinde gerçek şifre YAZMIYORUZ.
        # Eğer secrets yoksa demo anahtar atanır (Çalışmaz, güvenlidir)
        API_KEY = "demo-key-placeholder" 

except Exception:
    BASE_URL = "http://127.0.0.1:8000"
    API_KEY = "demo-key-placeholder"

# Endpoint Tanımı
API_URL = f"{BASE_URL}/scrape"
TEST_URL = "http://books.toscrape.com/"

# --- HEADER KISMI ---
# Kodunuzun bu kısmı doğrudur, st.columns kullanımı günceldir.
col_logo, col_title = st.columns([1, 5])

with col_logo:
    st.markdown("## 🕸️")
with col_title:
    st.title("Universal Scraper API Terminal")
    
    # Bağlantı durumunu göster
    status_label = "Cloud API" if "127.0.0.1" not in BASE_URL else "Localhost"
    st.caption(f"**Target Backend:** `{BASE_URL}` ({status_label})")

st.markdown("---")

# --- HELPER: API FETCH ---
def fetch_data(url, payload):
    """
    API'ye güvenli istek atar.
    """
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }

    try:
        with st.spinner("🕸️ Scraping in progress..."):
            # 30 saniye timeout
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            # 403 Hatası
            if response.status_code == 403:
                st.error("⛔ ACCESS DENIED: Invalid API Key.")
                return None
            
            # 404 Hatası (Endpoint yanlışsa)
            if response.status_code == 404:
                st.error(f"⛔ 404 Not Found: '{url}' adresi sunucuda bulunamadı.")
                return None

            response.raise_for_status()
            return response.json()

    except requests.exceptions.ConnectionError:
        st.error(f"⛔ API Connection Error. Cannot reach `{BASE_URL}`.")
        st.warning("👉 If Local: Check if 'uvicorn' is running.\n👉 If Cloud: Check AWS/Firewall settings.")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"HTTP Error ({response.status_code}): {response.text}")
        return None
    except Exception as e:
        st.error(f"Unexpected Error: {e}")
        return None

# --- ANA ARAYÜZ (TABS) ---
tab_visual, tab_json, tab_simple = st.tabs(["🛠️ Visual Builder", "📝 JSON Input", "⚡ Simple Scrape"])

# ==========================================
# MOD 1: GÖRSEL OLUŞTURUCU
# ==========================================
with tab_visual:
    st.subheader("🔹 Configure Scraping Task")
    
    col_a, col_b = st.columns(2)
    with col_a:
        target_url = st.text_input("Target URL", value=TEST_URL)
    with col_b:
        # main.py şu an bu parametreyi desteklemiyor ama ileride kullanabilir
        container_selector = st.text_input("Container Selector", value="article.product_pod")

    st.markdown("#### Data Fields Mapping")
    
    if 'fields' not in st.session_state:
        st.session_state.fields = [
            {'field_name': 'title', 'selector': 'h3 a', 'extraction_type': 'text'},
            {'field_name': 'price', 'selector': '.price_color', 'extraction_type': 'text'}
        ]

    # Dinamik Alan Ekleme/Silme
    for i, field in enumerate(st.session_state.fields):
        c1, c2, c3, c4 = st.columns([3, 3, 2, 1])
        with c1:
            field['field_name'] = st.text_input(f"Field #{i+1}", value=field['field_name'], key=f"name_{i}")
        with c2:
            field['selector'] = st.text_input(f"Selector #{i+1}", value=field['selector'], key=f"sel_{i}")
        with c3:
            field['extraction_type'] = st.selectbox(f"Type #{i+1}", ['text', 'href', 'src'], key=f"type_{i}", index=['text', 'href', 'src'].index(field['extraction_type']))
        with c4:
            st.write(""); st.write("")
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state.fields.pop(i)
                st.rerun()

    if st.button("➕ Add Field"):
        st.session_state.fields.append({'field_name': '', 'selector': '', 'extraction_type': 'text'})
        st.rerun()

    st.markdown("---")
    
    # Not: main.py şu an sadece 'selectors' listesi alıyor. 
    # Bu gelişmiş yapıyı backend tarafında işlemeniz gerekecek.
    # Şimdilik backend'in hata vermemesi için yapıyı koruyup isteği atıyoruz.
    visual_payload = {
        "url": target_url,
        "render_js": False,
        "selectors": [f['selector'] for f in st.session_state.fields] # main.py ile uyumlu hale getirdik
    }
    
    if st.button("🚀 Start Scraping (Visual)", type="primary"):
        result = fetch_data(API_URL, visual_payload)
        if result: st.session_state['last_result'] = result

# ==========================================
# MOD 2: JSON INPUT
# ==========================================
with tab_json:
    st.subheader("🔹 Paste JSON Configuration")
    # main.py ile uyumlu varsayılan JSON
    default_json = json.dumps({
        "url": "http://books.toscrape.com/",
        "render_js": False,
        "selectors": ["h3 a", ".price_color"]
    }, indent=2)
    
    json_input = st.text_area("JSON Payload", value=default_json, height=300)
    
    if st.button("🚀 Start Scraping (JSON)", type="primary"):
        try:
            parsed = json.loads(json_input)
            result = fetch_data(API_URL, parsed)
            if result: st.session_state['last_result'] = result
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON: {e}")

# ==========================================
# MOD 3: SIMPLE SCRAPE
# ==========================================
with tab_simple:
    st.subheader("⚡ Single Element Scrape")
    s_url = st.text_input("URL", "https://example.com")
    s_sel = st.text_input("Selector", "h1")
    
    if st.button("🚀 Scrape One"):
        # Payload yapısı main.py'deki ScrapeRequest modeline uygun hale getirildi
        payload = {
            "url": s_url, 
            "selectors": [s_sel] # Backend List[str] bekliyor
        }
        
        result = fetch_data(API_URL, payload) # SIMPLE_API_URL yerine API_URL kullanıldı
        if result:
             st.session_state['last_result'] = result

# ==========================================
# RESULTS
# ==========================================
st.markdown("---")
st.header("📊 Results")

if 'last_result' in st.session_state and st.session_state['last_result']:
    data = st.session_state['last_result']
    
    # main.py şimdilik sadece "data" objesi dönüyor, "count" veya liste dönmüyor.
    # Bu yüzden response yapısına göre esnek bir gösterim yapalım:
    st.json(data)
