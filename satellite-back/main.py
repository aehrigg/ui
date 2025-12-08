import os
import time
from typing import Literal, Optional

import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
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
ABOVE_CATEGORY_ID = int(get_env("ABOVE_CATEGORY_ID", "3"))  # weather sats
ABOVE_RADIUS = float(get_env("ABOVE_RADIUS", "70"))  # degrees
VISIBILITY_WINDOW = int(get_env("VISIBILITY_WINDOW", "900"))  # seconds ahead to predict


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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

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


def fetch_satellites_above(
    category_id: int, lat: float, lng: float, alt: float, radius: float
) -> dict:
    url = (
        f"https://api.n2yo.com/rest/v1/satellite/above/"
        f"{lat}/{lng}/{alt}/{radius}/{category_id}/&apiKey={N2YO_API_KEY}"
    )
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.HTTPError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"N2YO above fetch failed: {exc}")


def estimate_visibility_seconds(
    satellite_id: int, lat: float, lng: float, alt: float, window: int = VISIBILITY_WINDOW
) -> Optional[int]:
    url = (
        f"https://api.n2yo.com/rest/v1/satellite/positions/"
        f"{satellite_id}/{lat}/{lng}/{alt}/{window}/&apiKey={N2YO_API_KEY}"
    )
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        positions = data.get("positions") or []
        if not positions:
            return None
        now = time.time()
        # Finde den letzten Zeitpunkt innerhalb des Fensters, an dem Elevation > 0 ist
        visible_times = [p.get("timestamp") for p in positions if p.get("elevation", -90) > 0]
        if not visible_times:
            return 0
        last_visible = max(visible_times)
        remaining = int(last_visible - now)
        return remaining if remaining > 0 else 0
    except requests.HTTPError:
        return None
    except Exception:
        return None


@app.get("/api/status")
def get_status():
    position = fetch_satellite_position(
        satellite_id=state["satellite_id"], lat=LAT, lng=LNG, alt=ALT
    )
    visibility = estimate_visibility_seconds(
        satellite_id=state["satellite_id"], lat=LAT, lng=LNG, alt=ALT
    )
    return {
        "mode": state["mode"],
        "satellite_id": state["satellite_id"],
        "position": position,
        "signal": state["signal"],
        "visibility_seconds": visibility,
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


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/above")
def get_above(radius: float = ABOVE_RADIUS):
    data = fetch_satellites_above(
        category_id=ABOVE_CATEGORY_ID, lat=LAT, lng=LNG, alt=ALT, radius=radius
    )
    return data
