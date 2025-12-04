import streamlit as st
import requests
import pandas as pd
import json

# --- AYARLAR ---
st.set_page_config(page_title="Universal Scraper Terminal", layout="wide", page_icon="🕸️")

# --- URL AYARLARI (DÜZELTİLDİ) ---
try:
    if "API_URL" in st.secrets:
        # 1. URL'yi al
        raw_url = st.secrets["API_URL"]
        # 2. Temizlik (Tırnakları, boşlukları ve sondaki slash'i sil)
        clean_url = raw_url.strip().strip('"').strip("'").rstrip('/')

        # 3. Başında http/https yoksa ekle
        if not clean_url.startswith("http"):
            clean_url = f"https://{clean_url}"

        BASE_URL = clean_url
    else:
        # Secret yoksa Localhost (Geliştirme modu)
        BASE_URL = "http://127.0.0.1:8000"
except Exception as e:
    st.warning(f"URL Config Error: {e}. Using Localhost.")
    BASE_URL = "http://127.0.0.1:8000"

# Endpoint'i ekle
API_URL = f"{BASE_URL}/scrape/advanced"
TEST_URL = "http://books.toscrape.com/"

# --- HEADER ---
col1, col2 = st.columns([1, 5])
with col1:
    # Resim linki bazen kırık olabiliyor, güvenli yükleme
    st.markdown("## 🕸️")
with col2:
    st.title("Universal Scraper API Terminal")
    st.caption(f"**Connected Backend:** `{API_URL}`")

st.markdown("---")


# --- YARDIMCI FONKSİYON ---
def fetch_data(payload):
    """Verilen JSON payload'u API'ye gönderir ve sonucu döner."""
    try:
        with st.spinner("🕸️ Scraping in progress..."):
            # Timeout süresini 30 saniye yaptık (Render uyku modu için)
            response = requests.post(API_URL, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
    except requests.exceptions.ConnectionError:
        st.error(f"⛔ Connection Error! Could not reach `{API_URL}`.")
        st.info("Ensure the Render backend is active and your Secrets file is correct.")
        return None
    except requests.exceptions.Timeout:
        st.error("⛔ Timeout: The server took too long to respond (Cold Start?). Try again.")
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
# MOD 1: GÖRSEL OLUŞTURUCU
# ==========================================
with tab_visual:
    st.subheader("🔹 Configure Scraping Task")

    col_a, col_b = st.columns(2)

    with col_a:
        target_url = st.text_input("Target URL", value=TEST_URL)

    with col_b:
        container_selector = st.text_input(
            "Container Selector",
            value="article.product_pod",
            help="The CSS selector for the main item card (e.g., .product-card)"
        )

    st.markdown("#### Data Fields Mapping")

    if 'fields' not in st.session_state:
        st.session_state.fields = [
            {'field_name': 'title', 'selector': 'h3 a', 'extraction_type': 'text'},
            {'field_name': 'price', 'selector': '.price_color', 'extraction_type': 'text'},
            {'field_name': 'link', 'selector': 'h3 a', 'extraction_type': 'href'}
        ]

    for i, field in enumerate(st.session_state.fields):
        c1, c2, c3, c4 = st.columns([3, 3, 2, 1])
        with c1:
            field['field_name'] = st.text_input(f"Field Name #{i + 1}", value=field['field_name'], key=f"name_{i}")
        with c2:
            field['selector'] = st.text_input(f"CSS Selector #{i + 1}", value=field['selector'], key=f"sel_{i}")
        with c3:
            # Selectbox index error fix
            options = ['text', 'href', 'src', 'alt', 'data-id']
            curr_val = field['extraction_type']
            idx = options.index(curr_val) if curr_val in options else 0

            field['extraction_type'] = st.selectbox(
                f"Type #{i + 1}", options, index=idx, key=f"type_{i}"
            )
        with c4:
            st.write("")
            st.write("")
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state.fields.pop(i)
                st.rerun()

    if st.button("➕ Add New Field"):
        st.session_state.fields.append({'field_name': '', 'selector': '', 'extraction_type': 'text'})
        st.rerun()

    st.markdown("---")

    visual_payload = {
        "url": target_url,
        "container_selector": container_selector,
        "data_fields": st.session_state.fields
    }

    if st.button("🚀 Start Scraping (Visual Mode)", type="primary"):
        result = fetch_data(visual_payload)
        if result:
            st.session_state['last_result'] = result

# ==========================================
# MOD 2: RAW JSON GİRİŞİ
# ==========================================
with tab_json:
    st.subheader("🔹 Paste Your Configuration")
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
            parsed_payload = json.loads(json_input)
            result = fetch_data(parsed_payload)
            if result:
                st.session_state['last_result'] = result
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON Format: {e}")

# ==========================================
# SONUÇLAR
# ==========================================
st.markdown("---")
st.header("📊 Results")

if 'last_result' in st.session_state and st.session_state['last_result']:
    data = st.session_state['last_result']

    if data.get("status") == "success":
        items = data.get("data", [])
        count = data.get("count", 0)

        st.success(f"Successfully scraped **{count}** items.")

        if items:
            df = pd.DataFrame(items)
            st.dataframe(df, use_container_width=True)

            c1, c2 = st.columns(2)
            with c1:
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("⬇️ Download as CSV", data=csv, file_name="scraped_data.csv", mime="text/csv")
            with c2:
                json_str = df.to_json(orient="records", indent=2)
                st.download_button("⬇️ Download as JSON", data=json_str, file_name="scraped_data.json",
                                   mime="application/json")
        else:
            st.warning("No items found. Check your selectors.")
    else:
        st.error(f"API Error: {data.get('message')}")
else:
    st.info("No data scraped yet. Configure and click 'Start Scraping'.")