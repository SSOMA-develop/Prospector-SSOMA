from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from search_engine import SearchEngine
import uvicorn

app = FastAPI(title="Prospector SSOMA API", version="1.0.0")
engine = SearchEngine()

class SearchRequest(BaseModel):
    sector: str
    location: str
    deep_search: bool = False

class Prospect(BaseModel):
    name: str
    source: str
    location: str
    contact_info: Optional[str] = None
    role_detected: Optional[str] = None
    confidence_score: float = 0.0

@app.get("/")
def read_root():
    return {"status": "online", "message": "Prospector SSOMA API Ready"}

@app.post("/search", response_model=List[Prospect])
def search_prospects(request: SearchRequest):
    """
    Ejecuta una búsqueda de prospectos basada en sector y ubicación.
    Si deep_search es True, intenta buscar contactos específicos.
    """
    try:
        results = engine.search(request.sector, request.location, request.deep_search)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
