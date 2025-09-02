# main.py
import os
import asyncio
import pandas as pd
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

# CSV settings
CSV_URL = "https://filetolink-6i55.onrender.com/dl/792792?code=f5b303d2ce056bc4be519b8a-1783730975"
CSV_PATH = "/data/bin-list-data.csv"  # Mounted Render Persistent Disk path

app = FastAPI(title="BIN Lookup API", version="1.0.0")

# In-memory cache
INDEX = {}


@app.on_event("startup")
async def load_csv():
    """Load BIN CSV from disk or download if missing."""
    global INDEX

    # Ensure /data directory exists
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)

    # Download file if not already present
    if not os.path.exists(CSV_PATH):
        print("CSV not found locally. Downloading...")
        async with httpx.AsyncClient(timeout=None) as client:
            resp = await client.get(CSV_URL)
            resp.raise_for_status()
            with open(CSV_PATH, "wb") as f:
                f.write(resp.content)
        print("✅ CSV downloaded and saved to /data")

    # Load into pandas
    df = pd.read_csv(CSV_PATH, dtype=str, keep_default_na=False)
    df["BIN"] = df["BIN"].astype(str).str.replace(r"\.0$", "", regex=True)

    INDEX = {row["BIN"]: row for row in df.to_dict(orient="records")}
    print(f"✅ Loaded {len(INDEX)} BIN records into memory")


@app.get("/")
async def root():
    return {
        "message": "BIN Lookup API is running 🚀",
        "endpoint": "GET /bin/{bin_number}",
        "records_loaded": len(INDEX)
    }


@app.get("/bin/{bin_number}")
async def get_bin_info(bin_number: str):
    """Fetch BIN info (exact match)."""
    data = INDEX.get(str(bin_number))
    if not data:
        raise HTTPException(status_code=404, detail="BIN not found")
    return JSONResponse(content=data)
