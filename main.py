# main.py
import asyncio
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

CSV_PATH = "bin-list-data.csv"

app = FastAPI(title="BIN Lookup API", version="1.0.0")

# Global cache
INDEX = {}

@app.on_event("startup")
async def load_csv():
    """Load the CSV asynchronously into memory on startup."""
    def _load():
        df = pd.read_csv(CSV_PATH, dtype=str, keep_default_na=False)
        # Normalize BIN to string
        df["BIN"] = df["BIN"].astype(str).str.replace(r"\.0$", "", regex=True)
        return {row["BIN"]: row for row in df.to_dict(orient="records")}
    
    global INDEX
    INDEX = await asyncio.to_thread(_load)

@app.get("/")
async def root():
    return {
        "message": "BIN Lookup API is running 🚀",
        "endpoint": "GET /bin/{bin_number}"
    }

@app.get("/bin/{bin_number}")
async def get_bin_info(bin_number: str):
    """Fetch BIN info (exact match)."""
    data = INDEX.get(str(bin_number))
    if not data:
        raise HTTPException(status_code=404, detail="BIN not found")
    return JSONResponse(content=data)
