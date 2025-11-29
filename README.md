# 🕸️ Universal Web Scraper API (Multi-Type Extraction)

A robust, **stateless Python API** designed for high-performance data extraction from public websites. This solution is ideal for businesses and freelancers needing a reliable backend for continuous data scraping tasks.

## 🚀 Key Features

* **Advanced Parsing:** Supports both **text extraction** and **attribute extraction** (pulling `href`, `src`, or any custom HTML attribute). This allows structured data extraction from complex e-commerce sites.
* **Multi-Item Support:** Efficiently scrapes and returns lists of structured data objects (e.g., all products in a category) from a single API call.
* **Lightweight Backend:** Built on **FastAPI** for asynchronous speed and easy deployment.
* **Robust Error Handling:** Implements automatic status code checks (404, 500) and connection timeout logic.

## 🛠️ Tech Stack

* **Backend:** Python 3.10+, FastAPI (Uvicorn)
* **Scraping Core:** Requests, BeautifulSoup4
* **Data Processing:** Pandas (implied by usage)
* **Documentation:** Swagger UI (OpenAPI)

## 📦 How to Run

1.  **Clone the repository.**
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Start Server:**
    ```bash
    uvicorn main:app --reload
    ```
4.  **Access Docs:**
    Open `http://localhost:8000/docs` to test via Swagger UI.

## 🔍 Example Usage (List Extraction)

The API accepts a list of fields, allowing you to pull structured data in one call:

```json
{
  "url": "http://books.toscrape.com/",
  "container_selector": "article.product_pod",
  "data_fields": [
    { "field_name": "title", "selector": "h3 a", "extraction_type": "text" },
    { "field_name": "price", "selector": ".price_color", "extraction_type": "text" },
    { "field_name": "link", "selector": "h3 a", "extraction_type": "href" }
  ]
}