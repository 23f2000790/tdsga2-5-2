from fastapi import FastAPI, Request 
from fastapi.middleware.cors import CORSMiddleware 
import pandas as pd 
import numpy as np 
from pathlib import Path 
 
app = FastAPI() 
 
# Enable CORS for all origins 
app.add_middleware( 
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"], 
    expose_headers=["*"], 
) 
 
# Load the dataset once when the app starts 
DATA_FILE = Path(__file__).parent / "q-vercel-latency.json" 
df = pd.read_json(DATA_FILE) 
 
 
@app.get("/") 
async def root(): 
    return {"message": "Vercel Latency Analytics API is running."} 
 
 
@app.post("/api/latency") 
async def get_latency_stats(request: Request): 
    payload = await request.json() 
    regions_to_process = payload.get("regions", []) 
    threshold = payload.get("threshold_ms", 200) 
 
    result = {} 
 
    for region in regions_to_process: 
        # Filter region case-insensitively 
        region_df = df[df["region"].str.lower() == region.lower()] 
 
        if region_df.empty: 
            result[region] = { 
                "avg_latency": 0.00, 
                "p95_latency": 0.00, 
                "avg_uptime": 0.00, 
                "breaches": 0 
            } 
            continue 
 
        latencies = region_df["latency_ms"].astype(float) 
        uptimes = region_df["uptime_pct"].astype(float) 
 
        # Ensure exact 2 decimal places 
        avg_latency = round(latencies.mean() + 1e-8, 2) 
        p95_latency = round(np.percentile(latencies, 95) + 1e-8, 2) 
        avg_uptime = round(uptimes.mean() + 1e-8, 2) 
        breaches = int((latencies > threshold).sum()) 
 
        result[region] = { 
            "avg_latency": avg_latency, 
            "p95_latency": p95_latency, 
            "avg_uptime": avg_uptime, 
            "breaches": breaches 
        } 
 
    return {"regions": result}