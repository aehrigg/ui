import os
import time
from typing import Optional

import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field


# ---- Konfiguration aus Umgebungsvariablen ----
def get_env(name: str, default: Optional[str] = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Environment variable {name} is required")
    return value


N2YO_API_KEY = get_env("N2YO_API_KEY", None)
LAT = float(get_env("TRACK_LAT", "0"))
LNG = float(get_env("TRACK_LNG", "0"))
ALT = float(get_env("TRACK_ALT", "0"))
DEFAULT_SAT_ID = int(get_env("TRACK_SAT_ID", "25544"))
ABOVE_CATEGORY_ID = int(get_env("ABOVE_CATEGORY_ID", "3"))
ABOVE_RADIUS = float(get_env("ABOVE_RADIUS", "70"))
VISIBILITY_WINDOW = int(get_env("VISIBILITY_WINDOW", "900"))


# ---- Datenmodelle ----
class ModeRequest(BaseModel):
    mode: str


class TargetRequest(BaseModel):
    satellite_id: int = Field(..., gt=0)


class ManualCommand(BaseModel):
    command: str


# ---- App-Basis ----
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

# Einfacher Laufzeit-Status
state = {
    "mode": "geo",
    "satellite_id": DEFAULT_SAT_ID,
    "signal": None,
    "antenna": None,
}


# ---- Helper ----
def fetch_satellite_position(satellite_id: int, lat: float, lng: float, alt: float) -> dict:
    url = (
        f"https://api.n2yo.com/rest/v1/satellite/positions/"
        f"{satellite_id}/{lat}/{lng}/{alt}/1/&apiKey={N2YO_API_KEY}"
    )
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        positions = data.get("positions") or []
        if not positions:
            raise HTTPException(status_code=502, detail="No position data returned")
        return positions[0]
    except requests.HTTPError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"N2YO fetch failed: {exc}")


def fetch_satellites_above(category_id: int, lat: float, lng: float, alt: float, radius: float) -> dict:
    url = (
        f"https://api.n2yo.com/rest/v1/satellite/above/"
        f"{lat}/{lng}/{alt}/{radius}/{category_id}/&apiKey={N2YO_API_KEY}"
    )
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.HTTPError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"N2YO above fetch failed: {exc}")


def estimate_visibility_seconds(satellite_id: int, lat: float, lng: float, alt: float, window: int) -> Optional[int]:
    url = (
        f"https://api.n2yo.com/rest/v1/satellite/positions/"
        f"{satellite_id}/{lat}/{lng}/{alt}/{window}/&apiKey={N2YO_API_KEY}"
    )
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        positions = data.get("positions") or []
        now = time.time()
        visible = [p.get("timestamp") for p in positions if p.get("elevation", -90) > 0]
        if not visible:
            return 0
        last_visible = max(visible)
        remaining = int(last_visible - now)
        return remaining if remaining > 0 else 0
    except Exception:
        return None


# ---- Handler ----
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


def get_status():
    pos = fetch_satellite_position(state["satellite_id"], LAT, LNG, ALT)
    visibility = estimate_visibility_seconds(state["satellite_id"], LAT, LNG, ALT, VISIBILITY_WINDOW)
    return {
        "mode": state["mode"],
        "satellite_id": state["satellite_id"],
        "position": {
            "azimuth": pos.get("azimuth"),
            "elevation": pos.get("elevation"),
            "timestamp": pos.get("timestamp"),
        },
        "signal": state["signal"],
        "visibility_seconds": visibility,
        "antenna": state.get("antenna"),
    }


def set_mode(req: ModeRequest):
    state["mode"] = req.mode
    return {"mode": state["mode"]}


def set_target(req: TargetRequest):
    state["satellite_id"] = req.satellite_id
    return {"satellite_id": state["satellite_id"]}


def manual_command(req: ManualCommand):
    # Hier später UART/Arduino-Ansteuerung einbauen
    return {"command": req.command, "status": "queued"}


def ping():
    return {"status": "ok"}


def get_above(radius: float = ABOVE_RADIUS):
    return fetch_satellites_above(ABOVE_CATEGORY_ID, LAT, LNG, ALT, radius)


# ---- Routen registrieren (ohne @) ----
app.add_api_route("/", index, response_class=HTMLResponse, methods=["GET"])
app.add_api_route("/api/status", get_status, methods=["GET"])
app.add_api_route("/api/mode", set_mode, methods=["POST"])
app.add_api_route("/api/target", set_target, methods=["POST"])
app.add_api_route("/api/manual", manual_command, methods=["POST"])
app.add_api_route("/api/ping", ping, methods=["GET"])
app.add_api_route("/api/above", get_above, methods=["GET"])
