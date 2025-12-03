import streamlit as st
import requests
import pandas as pd
import json

# --- SABİTLER ---
API_URL = "http://127.0.0.1:8000/scrape/multi-type-list"
TEST_URL = "http://books.toscrape.com/"
st.set_page_config(page_title="Universal Scraper API Terminal", layout="wide", page_icon="🕸️")

st.title("🕸️ Universal Web Scraper API Terminal")
st.markdown("FastAPI tabanlı, çoklu alan ve attribute (src/href) çekme yeteneği.")


# --- API Test İletişimi ---
def get_scraped_data(data):
    try:
        response = requests.post(API_URL, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("⛔ API Bağlantı Hatası: Lütfen 'uvicorn main:app --reload' komutunun çalıştığından emin olun.")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"HTTP Hatası ({response.status_code}): Site engelliyor olabilir veya URL/Selector hatalı.")
        st.code(response.text)
        return None
    except Exception as e:
        st.error(f"Beklenmeyen Hata: {e}")
        return None


# --- UI ve Input Alanları ---
st.subheader("1. Hedef ve Seçici Tanımlama")

# Ana ayarlar
target_url = st.text_input("Hedef URL", value=TEST_URL)
container_selector = st.text_input("Ana Ürün Kapsayıcı Seçici (Container Selector)", value="article.product_pod")

st.markdown("---")
st.subheader("2. Çekilecek Alanlar (Fields)")

# FieldDefinition listesini tutacak state
if 'fields' not in st.session_state:
    # Başlangıç için örnek alanlar
    st.session_state.fields = [
        {'field_name': 'title', 'selector': 'h3 a', 'extraction_type': 'text'},
        {'field_name': 'price', 'selector': '.price_color', 'extraction_type': 'text'},
        {'field_name': 'link', 'selector': 'h3 a', 'extraction_type': 'href'}
    ]

# Alanları düzenleme (Dynamic Form)
fields_to_remove = []
for i, field in enumerate(st.session_state.fields):
    col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 2, 0.5])

    with col1:
        st.markdown(f"**Field {i + 1}**")
    with col2:
        field['field_name'] = st.text_input("Alan Adı", value=field['field_name'], key=f"name_{i}")
    with col3:
        field['selector'] = st.text_input("CSS Selector", value=field['selector'], key=f"selector_{i}")
    with col4:
        field['extraction_type'] = st.selectbox(
            "Tip",
            ['text', 'href', 'src', 'alt'],
            index=['text', 'href', 'src', 'alt'].index(field['extraction_type']),
            key=f"type_{i}"
        )
    with col5:
        if st.button("❌", key=f"remove_{i}"):
            fields_to_remove.append(i)

# Alan silme
if fields_to_remove:
    new_fields = [f for i, f in enumerate(st.session_state.fields) if i not in fields_to_remove]
    st.session_state.fields = new_fields
    st.rerun()  # Değişikliği hemen uygula

# Yeni alan ekle
if st.button("➕ Yeni Alan Ekle"):
    st.session_state.fields.append({'field_name': '', 'selector': '', 'extraction_type': 'text'})
    st.rerun()

st.markdown("---")

# --- Analizi Başlat ---
if st.button("🚀 Veriyi Çek ve Yapılandır", type="primary"):

    # Payload oluşturma (FastAPI'nin beklediği List[FieldDefinition] formatına çevir)
    payload = {
        "url": target_url,
        "container_selector": container_selector,
        "data_fields": st.session_state.fields
    }

    # API'yi çağır
    with st.spinner("Veri çekiliyor ve yapılandırılıyor..."):
        analysis_result = get_scraped_data(payload)

    if analysis_result and analysis_result.get("status") == "success":

        st.subheader(f"✅ Başarılı Sonuç ({analysis_result['count']} Kayıt)")

        # JSON'ı DataFrame'e çevirip göster
        if analysis_result['data']:
            df_result = pd.DataFrame(analysis_result['data'])
            st.dataframe(df_result, use_container_width=True)

            # İndirme butonu
            csv_export = df_result.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="💾 CSV Olarak İndir",
                data=csv_export,
                file_name='scraped_data.csv',
                mime='text/csv'
            )

        # Ham JSON
        with st.expander("🔍 API'den Gelen Ham JSON Yanıtı"):
            st.json(analysis_result)

    elif analysis_result:
        st.error(f"İşlem Hatası: {analysis_result.get('message', 'Bilinmeyen Hata')}")
