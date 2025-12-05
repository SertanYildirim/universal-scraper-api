import streamlit as st
import requests
import pandas as pd
import json

# --- CONFIGURATION ---
st.set_page_config(page_title="Universal Scraper Terminal", layout="wide", page_icon="🕸️")

# --- SIDEBAR: CONNECTION SETTINGS ---
with st.sidebar:
    st.header("Connection Settings")

    # 1. URL MANAGEMENT
    # Prioritize secrets, fallback to default IP
    if "API_URL" in st.secrets:
        default_url = st.secrets["API_URL"]
    else:
        default_url = "http://13.48.147.34:8080"
    
    # Clean input for Server URL
    BASE_URL = st.text_input("Server URL", value=default_url).strip().rstrip('/')
    
    # Auto-append port 8080 if missing (Silent correction)
    if len(BASE_URL.split(":")) < 3 and "localhost" not in BASE_URL:
        BASE_URL = f"{BASE_URL}:8080"

    # 2. API KEY MANAGEMENT
    # Silent loading from secrets
    api_key_val = ""
    if "API_KEY" in st.secrets:
        api_key_val = st.secrets["API_KEY"]
    
    # Input field overrides secrets if edited, otherwise acts as placeholder
    API_KEY = st.text_input("API Key", value=api_key_val, type="password")

    st.markdown("---")
    
    # Simple Connection Check
    if st.button("Check Connection"):
        try:
            r = requests.get(BASE_URL, timeout=5)
            if r.status_code == 200:
                st.success(f"Connected: {r.json().get('service', 'Unknown Service')}")
            else:
                st.error(f"Connection Failed: {r.status_code}")
        except Exception as e:
            st.error("Server Unreachable")

# --- ENDPOINT DEFINITION ---
API_URL = f"{BASE_URL}/scrape"
TEST_URL = "http://books.toscrape.com/"

# --- HEADER ---
col_logo, col_title = st.columns([1, 5])

with col_logo:
    st.markdown("## 🕸️")
with col_title:
    st.title("Universal Scraper API Terminal")
    st.caption("Professional Client v2.1")

st.markdown("---")

# --- HELPER: API FETCH ---
def fetch_data(url, payload):
    if not API_KEY:
        st.error("API Key is missing.")
        return None

    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }

    try:
        with st.spinner("Processing..."):
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            
            if response.status_code == 403:
                st.error("Access Denied: Invalid API Key.")
                return None
            
            if response.status_code == 404:
                st.error("Endpoint Not Found (404)")
                # Minimal hint for debugging purposes only if needed
                st.caption(f"Target: {url}") 
                return None

            response.raise_for_status()
            return response.json()

    except requests.exceptions.ConnectionError:
        st.error("Network Error: Could not connect to server.")
        return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

# --- MAIN INTERFACE (TABS) ---
tab_visual, tab_json, tab_simple = st.tabs(["🛠️ Visual Builder", "📝 JSON Input", "⚡ Quick Scrape"])

# ==========================================
# TAB 1: VISUAL BUILDER
# ==========================================
with tab_visual:
    st.subheader("Configure Task")
    col_a, col_b = st.columns(2)
    with col_a:
        target_url = st.text_input("Target URL", value=TEST_URL)
    with col_b:
        container_selector = st.text_input("Container Selector", value="article.product_pod")

    st.markdown("#### Data Fields")
    if 'fields' not in st.session_state:
        st.session_state.fields = [
            {'field_name': 'title', 'selector': 'h3 a', 'extraction_type': 'text'},
            {'field_name': 'price', 'selector': '.price_color', 'extraction_type': 'text'}
        ]

    for i, field in enumerate(st.session_state.fields):
        c1, c2, c3, c4 = st.columns([3, 3, 2, 1])
        with c1:
            field['field_name'] = st.text_input(f"Field Name", value=field['field_name'], key=f"name_{i}", label_visibility="collapsed")
        with c2:
            field['selector'] = st.text_input(f"CSS Selector", value=field['selector'], key=f"sel_{i}", label_visibility="collapsed")
        with c3:
            field['extraction_type'] = st.selectbox(f"Type", ['text', 'href', 'src'], key=f"type_{i}", index=['text', 'href', 'src'].index(field['extraction_type']), label_visibility="collapsed")
        with c4:
            if st.button("✕", key=f"del_{i}"):
                st.session_state.fields.pop(i); st.rerun()

    if st.button("+ Add Field"):
        st.session_state.fields.append({'field_name': '', 'selector': '', 'extraction_type': 'text'})
        st.rerun()

    st.markdown("---")
    
    # Mapping to match backend requirements
    visual_payload = {
        "url": target_url, 
        "render_js": False, 
        "selectors": [f['selector'] for f in st.session_state.fields]
    }
    
    if st.button("🚀 Start Scraping", type="primary"):
        result = fetch_data(API_URL, visual_payload)
        if result: st.session_state['last_result'] = result

# ==========================================
# TAB 2: JSON INPUT
# ==========================================
with tab_json:
    st.subheader("Raw Configuration")
    default_json = json.dumps({"url": "http://books.toscrape.com/", "render_js": False, "selectors": ["h3 a", ".price_color"]}, indent=2)
    json_input = st.text_area("JSON Payload", value=default_json, height=300)
    
    if st.button("🚀 Send Request", type="primary"):
        try:
            parsed = json.loads(json_input)
            result = fetch_data(API_URL, parsed)
            if result: st.session_state['last_result'] = result
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON format: {e}")

# ==========================================
# TAB 3: QUICK SCRAPE
# ==========================================
with tab_simple:
    st.subheader("Single Element Extraction")
    s_url = st.text_input("Page URL", "https://example.com")
    s_sel = st.text_input("CSS Selector", "h1")
    if st.button("🚀 Fetch"):
        payload = {"url": s_url, "selectors": [s_sel]}
        result = fetch_data(API_URL, payload)
        if result: st.session_state['last_result'] = result

# ==========================================
# RESULTS SECTION
# ==========================================
st.markdown("---")
st.header("Output")
if 'last_result' in st.session_state and st.session_state['last_result']:
    st.json(st.session_state['last_result'])
