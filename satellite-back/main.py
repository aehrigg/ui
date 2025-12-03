import os
from typing import Literal, Optional

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


def get_env(name: str, default: Optional[str] = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Environment variable {name} is required")
    return value


N2YO_API_KEY = get_env("N2YO_API_KEY", None)
LAT = float(get_env("TRACK_LAT", "0"))
LNG = float(get_env("TRACK_LNG", "0"))
ALT = float(get_env("TRACK_ALT", "0"))
DEFAULT_SAT_ID = int(get_env("TRACK_SAT_ID", "25544"))  # ISS as default


class ModeRequest(BaseModel):
    mode: Literal["geo", "polar", "manual"]


class TargetRequest(BaseModel):
    satellite_id: int = Field(..., gt=0)


class ManualCommand(BaseModel):
    command: Literal["up", "down", "left", "right", "stop"]


app = FastAPI(title="Satellite Control API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory state placeholder until Arduino wiring exists
state = {
    "mode": "geo",
    "satellite_id": DEFAULT_SAT_ID,
    "signal": None,  # placeholder for RSSI
}


def fetch_satellite_position(
    satellite_id: int, lat: float, lng: float, alt: float, seconds: int = 1
) -> dict:
    url = (
        f"https://api.n2yo.com/rest/v1/satellite/positions/"
        f"{satellite_id}/{lat}/{lng}/{alt}/{seconds}/&apiKey={N2YO_API_KEY}"
    )
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        positions = data.get("positions") or []
        if not positions:
            raise HTTPException(status_code=502, detail="No position data returned")
        pos = positions[0]
        return {
            "azimuth": pos.get("azimuth"),
            "elevation": pos.get("elevation"),
            "timestamp": pos.get("timestamp"),
            "satellite_id": satellite_id,
            "lat": lat,
            "lng": lng,
            "alt": alt,
        }
    except requests.HTTPError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"N2YO fetch failed: {exc}")


@app.get("/api/status")
def get_status():
    position = fetch_satellite_position(
        satellite_id=state["satellite_id"], lat=LAT, lng=LNG, alt=ALT
    )
    return {
        "mode": state["mode"],
        "satellite_id": state["satellite_id"],
        "position": position,
        "signal": state["signal"],
    }


@app.post("/api/mode")
def set_mode(req: ModeRequest):
    state["mode"] = req.mode
    return {"mode": state["mode"]}


@app.post("/api/target")
def set_target(req: TargetRequest):
    state["satellite_id"] = req.satellite_id
    return {"satellite_id": state["satellite_id"]}


@app.post("/api/manual")
def manual_command(req: ManualCommand):
    # Placeholder: integrate with Arduino command queue
    return {"command": req.command, "status": "queued"}


@app.get("/api/ping")
def ping():
    return {"status": "ok"}
