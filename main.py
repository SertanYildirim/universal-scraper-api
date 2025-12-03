from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
from typing import List, Dict

app = FastAPI(
    title="Universal Web Scraper API",
    description="A high-performance, stateless API for extracting structured data from websites.",
    version="2.0.0"
)

# ==========================================
# DATA MODELS (Veri Modelleri)
# ==========================================

# 1. Basit Çekim Modeli
class SimpleScrapeRequest(BaseModel):
    url: str
    css_selector: str

# 2. Gelişmiş Çekim Modelleri
class FieldDefinition(BaseModel):
    field_name: str  # Örn: "fiyat"
    selector: str  # Örn: ".price"
    extraction_type: str = 'text'  # "text", "href", "src", "data-id" vb.

class AdvancedScrapeRequest(BaseModel):
    url: str
    container_selector: str  # Örn: ".product-card" (Tüm ürünleri kapsayan kutu)
    data_fields: List[FieldDefinition]  # Çekilecek alanlar listesi

# ==========================================
# ENDPOINTS (API Uç Noktaları)
# ==========================================

@app.get("/")
def home():
    return {
        "status": "Active",
        "service": "Universal Scraper API v2",
        "endpoints": {
            "simple": "/scrape/simple (POST)",
            "advanced": "/scrape/advanced (POST)"
        }
    }

@app.post("/scrape/simple")
def scrape_simple(request: SimpleScrapeRequest):
    """
    [HIZLI MOD] Tek bir CSS seçicisine ait veriyi çeker.
    Örn: Sadece sayfa başlığını (h1) almak için.
    """
    try:
        response = requests.get(request.url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        element = soup.select_one(request.css_selector)

        if element:
            return {"status": "success", "data": element.get_text(strip=True)}
        else:
            raise HTTPException(status_code=404, detail=f"Element not found: {request.css_selector}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scrape/advanced")
def scrape_advanced(request: AdvancedScrapeRequest):
    """
    [PROFESYONEL MOD] Bir sayfadaki liste yapısını (Ürünler, Haberler) yapılandırılmış olarak çeker.
    Resim linki (src), Bağlantı (href) ve Metin (text) aynı anda çekilebilir.
    """
    try:
        # Anti-Bot önlemi için basit bir User-Agent
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        response = requests.get(request.url, timeout=15, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. Tüm kapsayıcıları (Kartları) bul
        containers = soup.select(request.container_selector)

        if not containers:
            return {"status": "warning", "message": f"No containers found with selector: {request.container_selector}",
                    "count": 0, "data": []}

        item_list = []

        # 2. Her kartın içini gez
        for container in containers:
            item = {}

            for field in request.data_fields:
                # Karta özel arama yap
                target_element = container.select_one(field.selector)

                value = None
                if target_element:
                    if field.extraction_type == 'text':
                        value = target_element.get_text(strip=True)
                    else:
                        # İstenen özelliği (href, src) al
                        value = target_element.get(field.extraction_type)

                # Bulunamazsa 'N/A' yaz
                item[field.field_name] = value if value else "N/A"

            item_list.append(item)

        return {"status": "success", "count": len(item_list), "data": item_list}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")