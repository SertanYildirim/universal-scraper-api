import streamlit as st
import requests
import pandas as pd
import json

# --- AYARLAR ---
st.set_page_config(page_title="Universal Scraper Terminal", layout="wide", page_icon="🕸️")

# --- SIDEBAR: BAĞLANTI VE GÜVENLİK AYARLARI ---
with st.sidebar:
    st.header("🔌 Bağlantı Ayarları")
    
    st.info("✅ Hedef: Universal Scraper API (Port 8080)")

    # 1. URL YÖNETİMİ
    # Secrets dosyasında API_URL varsa oradan al, yoksa varsayılan IP'yi kullan.
    # Ancak kod içinde hassas olmayan IP kalabilir veya tamamen secrets'a taşıyabilirsiniz.
    if "API_URL" in st.secrets:
        default_url = st.secrets["API_URL"]
    else:
        default_url = "http://13.48.147.34:8080"
    
    # Kullanıcı değiştirmek isterse diye text_input bırakıyoruz
    BASE_URL = st.text_input("Sunucu URL", value=default_url).strip().rstrip('/')
    st.caption(f"Aktif Hedef: `{BASE_URL}`")

    st.markdown("---")

    # 2. API KEY YÖNETİMİ (GÜVENLİ)
    # Kod içinde ASLA hardcoded şifre bulunmaz.
    
    api_key_input = ""
    
    if "API_KEY" in st.secrets:
        # Eğer secrets.toml dosyasında tanımlıysa otomatik al
        st.success("🔑 API Anahtarı 'secrets' dosyasından yüklendi.")
        API_KEY = st.secrets["API_KEY"]
    else:
        # Secrets yoksa kullanıcıdan manuel iste
        st.warning("⚠️ Secrets bulunamadı. Anahtarı manuel girin.")
        API_KEY = st.text_input("API Key", type="password")

    st.markdown("---")
    
    # --- SUNUCU KONTROLÜ ---
    if st.button("📡 Bağlantıyı Test Et"):
        if not API_KEY:
            st.error("Lütfen önce API Anahtarını girin!")
        else:
            st.write("Kontrol ediliyor...")
            try:
                # Root endpoint'e istek atıp kimlik soruyoruz
                r = requests.get(BASE_URL, timeout=5)
                
                if r.status_code == 200:
                    data = r.json()
                    service_name = str(data.get("service", "")).lower()
                    
                    # Hangi servisin cevap verdiğini kontrol et
                    if "scraper" in service_name:
                        st.success("🎉 BAŞARILI: Universal Scraper API (v2.1) Bağlı!")
                        st.json(data)
                    elif "quantmath" in service_name:
                        st.error("🚨 HATA: Yanlış Port! (QuantMath API'ye bağlandınız)")
                        st.warning("Lütfen URL sonundaki portu :8080 olarak düzeltin.")
                        st.json(data)
                    else:
                        st.info(f"Servis Yanıtı: {service_name}")
                        st.json(data)
                else:
                    st.error(f"⚠️ Sunucu Hatası: {r.status_code}")
            except Exception as e:
                st.error(f"❌ Bağlantı Kurulamadı: {e}")

# --- ENDPOINT TANIMI ---
API_URL = f"{BASE_URL}/scrape"
TEST_URL = "http://books.toscrape.com/"

# --- HEADER KISMI ---
col_logo, col_title = st.columns([1, 5])

with col_logo:
    st.markdown("## 🕸️")
with col_title:
    st.title("Universal Scraper API Terminal")
    st.caption("v2.1 Client")

st.markdown("---")

# --- HELPER: API FETCH ---
def fetch_data(url, payload):
    # API Key yoksa işlemi durdur
    if not API_KEY:
        st.error("⛔ API Key eksik! Lütfen sol menüden anahtarı girin veya secrets dosyasını kontrol edin.")
        return None

    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }

    try:
        with st.spinner("🕸️ Veri çekiliyor..."):
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            
            if response.status_code == 403:
                st.error("⛔ YETKİSİZ (403): API Anahtarı hatalı.")
                return None
            
            if response.status_code == 404:
                st.error(f"⛔ 404 BULUNAMADI: '{url}'")
                st.info("Sunucuda Scraper API yerine başka bir servis (örn: QuantMath) çalışıyor olabilir. Portu kontrol edin (8080 olmalı).")
                return None

            response.raise_for_status()
            return response.json()

    except requests.exceptions.ConnectionError:
        st.error(f"⛔ Bağlantı Hatası: `{BASE_URL}` adresine ulaşılamıyor.")
        return None
    except Exception as e:
        st.error(f"Hata: {e}")
        return None

# --- ANA ARAYÜZ (TABS) ---
tab_visual, tab_json, tab_simple = st.tabs(["🛠️ Görsel Oluşturucu", "📝 JSON", "⚡ Basit"])

# ==========================================
# MOD 1: GÖRSEL OLUŞTURUCU
# ==========================================
with tab_visual:
    st.subheader("🔹 Kazıma Görevi Oluştur")
    col_a, col_b = st.columns(2)
    with col_a:
        target_url = st.text_input("Hedef URL", value=TEST_URL)
    with col_b:
        container_selector = st.text_input("Kapsayıcı Seçici", value="article.product_pod")

    st.markdown("#### Veri Alanları")
    if 'fields' not in st.session_state:
        st.session_state.fields = [
            {'field_name': 'title', 'selector': 'h3 a', 'extraction_type': 'text'},
            {'field_name': 'price', 'selector': '.price_color', 'extraction_type': 'text'}
        ]

    for i, field in enumerate(st.session_state.fields):
        c1, c2, c3, c4 = st.columns([3, 3, 2, 1])
        with c1:
            field['field_name'] = st.text_input(f"Alan #{i+1}", value=field['field_name'], key=f"name_{i}")
        with c2:
            field['selector'] = st.text_input(f"Seçici #{i+1}", value=field['selector'], key=f"sel_{i}")
        with c3:
            field['extraction_type'] = st.selectbox(f"Tür #{i+1}", ['text', 'href', 'src'], key=f"type_{i}", index=['text', 'href', 'src'].index(field['extraction_type']))
        with c4:
            st.write(""); st.write("")
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state.fields.pop(i); st.rerun()

    if st.button("➕ Alan Ekle"):
        st.session_state.fields.append({'field_name': '', 'selector': '', 'extraction_type': 'text'})
        st.rerun()

    st.markdown("---")
    visual_payload = {
        "url": target_url, 
        "render_js": False, 
        "selectors": [f['selector'] for f in st.session_state.fields]
    }
    
    if st.button("🚀 Başlat (Görsel)", type="primary"):
        result = fetch_data(API_URL, visual_payload)
        if result: st.session_state['last_result'] = result

# ==========================================
# MOD 2: JSON INPUT
# ==========================================
with tab_json:
    st.subheader("🔹 JSON Yapılandırması")
    default_json = json.dumps({"url": "http://books.toscrape.com/", "render_js": False, "selectors": ["h3 a", ".price_color"]}, indent=2)
    json_input = st.text_area("JSON Payload", value=default_json, height=300)
    
    if st.button("🚀 Başlat (JSON)", type="primary"):
        try:
            parsed = json.loads(json_input)
            result = fetch_data(API_URL, parsed)
            if result: st.session_state['last_result'] = result
        except json.JSONDecodeError as e:
            st.error(f"Geçersiz JSON: {e}")

# ==========================================
# MOD 3: SIMPLE SCRAPE
# ==========================================
with tab_simple:
    st.subheader("⚡ Tekil Eleman Getir")
    s_url = st.text_input("URL", "https://example.com")
    s_sel = st.text_input("Seçici", "h1")
    if st.button("🚀 Getir"):
        payload = {"url": s_url, "selectors": [s_sel]}
        result = fetch_data(API_URL, payload)
        if result: st.session_state['last_result'] = result

# ==========================================
# SONUÇLAR
# ==========================================
st.markdown("---")
st.header("📊 Sonuçlar")
if 'last_result' in st.session_state and st.session_state['last_result']:
    st.json(st.session_state['last_result'])
