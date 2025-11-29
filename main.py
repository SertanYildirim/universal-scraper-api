from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
from typing import List, Dict

app = FastAPI(
    title="Universal Web Scraper API",
    description="A stateless API for simple web scraping and data extraction.",
    version="1.0.0"
)


# --- 1. Veri Modeli (İstek Tipi) ---
class ScrapeRequest(BaseModel):
    url: str
    css_selector: str = 'body'  # HTML'in hangi parçasını çekeceğimizi belirtir


# --- Yeni Veri Modeli ---
class StructuredScrapeRequest(BaseModel):
    url: str
    # 'data_fields' sözlüğü: Anahtar = Çekeceğin Verinin Adı, Değer = CSS Seçicisi
    data_fields: dict[str, str]


# class ListScrapeRequest(BaseModel): modelinde:
# Yeni bir alan ekliyoruz:
class ListScrapeRequest(BaseModel):
    url: str
    container_selector: str
    data_fields: dict[str, str]
    # YENİ ALAN: Bu alan "text" veya "href", "src" gibi attribute adını alabilir
    extraction_type: str = 'text' # Varsayılan olarak metin çekecek


# main.py dosyasının üst kısmına, diğer class'ların yanına ekle

# 1. Hangi veriyi, hangi seçici ile, nasıl çekeceğimizi tanımlar
class FieldDefinition(BaseModel):
    field_name: str
    selector: str
    extraction_type: str = 'text' # Varsayılan: metin

# 2. Ana İstek Modeli: Listeyi ve URL'yi tanımlar
class MultiTypeListScrapeRequest(BaseModel):
    url: str
    container_selector: str # Tüm ürünleri kapsayan ana seçici (Örn: .product-card-container)
    data_fields: List[FieldDefinition]


@app.post("/scrape")
def scrape_data(request: ScrapeRequest):
    """
    Belirtilen URL'den HTML içeriğini çeker ve CSS Selector'a uyan ilk elementin temiz metnini döndürür.
    """
    try:
        # HTTP isteği gönder (10 saniye zaman aşımı)
        response = requests.get(request.url, timeout=10)

        # 4xx veya 5xx hatalarını yakala (Örn: 404 Not Found)
        response.raise_for_status()

        # HTML'i parse et
        soup = BeautifulSoup(response.content, 'html.parser')

        # CSS Selector ile hedef elementi bul
        element = soup.select_one(request.css_selector)

        if element:
            # Bulunan elementin temiz metnini döndür
            return {"status": "success", "data": element.get_text(strip=True)}
        else:
            # Element bulunamazsa 404 döndür
            raise HTTPException(status_code=404, detail=f"No element found with selector: {request.css_selector}")


    except requests.exceptions.RequestException as e:
        # Ağ veya bağlantı hatalarını yakala
        raise HTTPException(status_code=500, detail=f"Connection or HTTP request failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


# --- 2. Geliştirme: Çoklu Sonuç Çekme (Liste) ---
@app.post("/scrape/all")
def scrape_all_data(request: ScrapeRequest):
    """
    Belirtilen URL'den CSS Selector'a uyan TÜM elementlerin metinlerini liste olarak döndürür.
    """
    try:
        response = requests.get(request.url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # select() ile tüm eşleşmeleri bul
        elements = soup.select(request.css_selector)

        if not elements:
            raise HTTPException(status_code=404, detail=f"No elements found with selector: {request.css_selector}")

        # Tüm elementlerin temiz metinlerini listeye çevir
        data_list = [element.get_text(strip=True) for element in elements]

        return {"status": "success", "data": data_list, "count": len(data_list)}

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Connection or HTTP request failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


# --- Yeni Endpoint: Yapılandırılmış Veri Çekme ---
@app.post("/scrape/structured")
def scrape_structured_data(request: StructuredScrapeRequest):
    """
    Belirtilen URL'den birden fazla CSS seçicisine uyan ilk elementleri tek bir yapılandırılmış objede döndürür.
    """
    try:
        response = requests.get(request.url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        results = {}

        # Kullanıcının verdiği her bir alan (isim, fiyat) için döngü
        for field_name, selector in request.data_fields.items():
            element = soup.select_one(selector)

            if element:
                # Metin Çekme
                results[field_name] = element.get_text(strip=True)
            else:
                # Element bulunamazsa boş değer dön
                results[field_name] = "N/A (Selector not found)"

        if not results:
            raise HTTPException(status_code=404, detail="No selectors were processed or provided.")

        return {"status": "success", "data": results}

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Connection or HTTP request failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


# --- 3. Geliştirme: Yapılandırılmış Liste Çekme (GÜVENLİ VE DÜZELTİLMİŞ) ---
@app.post("/scrape/list")
def scrape_list_data(request: ListScrapeRequest):
    """
    Belirtilen URL'den TEK BIR SELEKTÖR altındaki tüm ürünleri/kayıtları çeker ve yapılandırılmış liste döndürür.
    Bu, çoklu ürün listesi çekmek için kullanılır.
    """
    try:
        # ⚠️ Uyari: Bu ornekte Javascript calistirmiyoruz, sadece Requests ile cekiyoruz!
        response = requests.get(request.url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. Tum ana urun kapsayicilarini bul
        containers = soup.select(request.container_selector)

        if not containers:
            raise HTTPException(status_code=404,
                                detail=f"No containers found with selector: {request.container_selector}")

        item_list = []

        # 2. Her bir kapsayicinin icindeki verileri cek
        for index, container in enumerate(containers):
            item = {}
            is_valid = True

            for field_name, selector in request.data_fields.items():
                # Kapsayiciya gore goreceli arama yap
                element = container.select_one(selector)

                value = None  # Çekilecek değer

                if element:
                    # Element bulundu, çekim tipine bak
                    if request.extraction_type == 'text':
                        value = element.get_text(strip=True)
                    else:
                        # Attribute çekme (örneğin 'href' veya 'src' için)
                        # Birden fazla attribute denemek yerine direkt parametreye bakiyoruz
                        value = element.get(request.extraction_type) or element.get("href") or element.get("src")

                # Değeri ata:
                item[field_name] = value if value is not None else "N/A"

            if is_valid:  # (is_valid mantığı şu an basit, geliştirilebilir)
                item_list.append(item)

        if not item_list:
            return {"status": "error", "message": "No valid products found after parsing containers.", "count": 0}

        return {"status": "success", "data": item_list, "count": len(item_list)}

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")
    except Exception as e:
        import traceback
        traceback.print_exc()  # Terminale hatayi yazdir
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@app.post("/scrape/multi-type-list")
def scrape_multi_type_list(request: MultiTypeListScrapeRequest):
    """
    Belirtilen URL'den TEK BIR CONTAINER altındaki tüm ürünleri çeker, her alan için ayrı extraction_type (text, href, src vb.) uygular.
    """
    try:
        response = requests.get(request.url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. Tüm ana ürün kapsayıcılarını bul
        containers = soup.select(request.container_selector)

        if not containers:
            raise HTTPException(status_code=404,
                                detail=f"No containers found with selector: {request.container_selector}")

        item_list = []

        # 2. Her bir kapsayıcının içindeki verileri çek
        for container in containers:
            item = {}

            for field in request.data_fields:
                # Kapsayıcıya göre göreceli arama yap
                element = container.select_one(field.selector)

                value = None

                if element:
                    # Çekim tipini kontrol et
                    if field.extraction_type == 'text':
                        value = element.get_text(strip=True)
                    else:
                        # Eğer tip 'text' değilse, attribute'u çek
                        value = element.get(field.extraction_type)

                # Değeri ata
                item[field.field_name] = value

            item_list.append(item)

        if not item_list:
            return {"status": "error", "message": "No data found in containers.", "count": 0}

        return {"status": "success", "data": item_list, "count": len(item_list)}

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@app.get("/")
def home():
    return {"status": "Active", "message": "Universal Scraper API is ready."}