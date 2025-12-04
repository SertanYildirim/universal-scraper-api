from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
from typing import List, Optional

app = FastAPI(
    title="Universal Web Scraper API",
    description="A high-performance, stateless API for extracting structured data from websites.",
    version="2.1.0"
)

# --- CORS (Streamlit Cloud Erişimi İçin Şart) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# DATA MODELS
# ==========================================

class FieldDefinition(BaseModel):
    field_name: str
    selector: str
    extraction_type: str = 'text'


class AdvancedScrapeRequest(BaseModel):
    url: str
    container_selector: str
    data_fields: List[FieldDefinition]


# ==========================================
# ENDPOINTS
# ==========================================

@app.get("/")
def home():
    return {
        "status": "Active",
        "service": "Universal Scraper API v2.1"
    }


@app.post("/scrape/advanced")
def scrape_advanced(request: AdvancedScrapeRequest):
    try:
        # Daha güçlü bir User-Agent
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

        # İsteği at
        response = requests.get(request.url, timeout=20, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Kapsayıcıları bul
        containers = soup.select(request.container_selector)

        if not containers:
            return {
                "status": "warning",
                "message": f"No containers found for selector: '{request.container_selector}'",
                "count": 0,
                "data": []
            }

        item_list = []

        for container in containers:
            item = {}
            for field in request.data_fields:
                target_element = container.select_one(field.selector)
                value = None

                if target_element:
                    if field.extraction_type == 'text':
                        value = target_element.get_text(strip=True)
                    elif field.extraction_type in ['href', 'src', 'data-id', 'alt']:
                        value = target_element.get(field.extraction_type)
                    else:
                        value = target_element.get_text(strip=True)

                item[field.field_name] = value if value else None

            # Sadece içi tamamen boş olmayan itemleri ekle (Opsiyonel temizlik)
            if any(item.values()):
                item_list.append(item)

        return {"status": "success", "count": len(item_list), "data": item_list}

    except requests.exceptions.HTTPError as h_err:
        raise HTTPException(status_code=400, detail=f"Target Site Error: {str(h_err)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")