import streamlit as st
import requests
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime
import json
import math
import os
import time

from io import BytesIO

# Optional: PDF generation for Puller list
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

st.markdown(
    """
    <style>
    :root {
        --ys-bg: #050608;
        --ys-panel: #0b0f16;
        --ys-accent: #39ff14;
        --ys-accent-soft: rgba(57, 255, 20, 0.35);
        --ys-danger: #ff3366;
        --ys-text-main: #f9fafb;
        --ys-text-muted: #9ca3af;
    }

    /* App background */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: var(--ys-bg) !important;
        color: var(--ys-text-main) !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #05060a !important;
        border-right: 1px solid #111827 !important;
    }

    /* Main container panels */
    [data-testid="stMain"] > div {
        padding-top: 0.5rem;
    }

    /* Header */
    .ys-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 14px 10px 20px 10px;
        margin: 0 -4px 0.75rem -4px;
        justify-content: flex-start;
        background: radial-gradient(circle at 0% 0%, rgba(57,255,20,0.18), #020617);
        border-bottom: 1px solid #16a34a;
        box-shadow: 0 8px 25px rgba(0,0,0,0.65);
    }

    .ys-logo {
        width: 58px;
        height: 58px;
        border-radius: 999px;
        border: 2px solid var(--ys-accent);
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        box-shadow: 0 0 18px var(--ys-accent-soft);
        background: radial-gradient(circle at 30% 30%, rgba(57,255,20,0.25), #020617);
    }

    .ys-logo::before,
    .ys-logo::after {
        content: "";
        position: absolute;
        border-radius: 999px;
    }

    /* crosshair vertical */
    .ys-logo::before {
        width: 2px;
        height: 70%;
        background: rgba(249,250,251,0.45);
    }

    /* crosshair horizontal */
    .ys-logo::after {
        width: 70%;
        height: 2px;
        background: rgba(249,250,251,0.45);
    }

    .ys-logo-eye {
        width: 12px;
        height: 12px;
        border-radius: 999px;
        background: radial-gradient(circle, #ff3366 0%, #7f1d1d 70%, transparent 100%);
        box-shadow: 0 0 12px rgba(255,51,102,0.9);
        z-index: 2;
    }

    .ys-text-block {
        display: flex;
        flex-direction: column;
        gap: 2px;
    }

    .ys-title {
        font-family: "SF Mono", Menlo, Consolas, monospace;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        font-size: 1.1rem;
        color: var(--ys-accent);
        text-shadow: 0 0 12px rgba(57,255,20,0.6);
    }

    .ys-sub {
        font-size: 0.85rem;
        color: var(--ys-text-muted);
    }

    /* Tabs styling */
    [data-testid="stTabs"] button {
        background: #020617 !important;
        border-radius: 999px !important;
        border: 1px solid #111827 !important;
        color: var(--ys-text-muted) !important;
        padding: 0.4rem 0.9rem !important;
        font-size: 0.8rem !important;
    }

    [data-testid="stTabs"] button[aria-selected="true"] {
        border-color: var(--ys-accent) !important;
        box-shadow: 0 0 14px var(--ys-accent-soft);
        color: var(--ys-accent) !important;
        background: radial-gradient(circle at 20% 0%, rgba(57,255,20,0.18), #020617) !important;
    }

    /* Scan Now button glow */
    div.stButton > button {
        background: linear-gradient(90deg, #15803d, #22c55e) !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
        border-radius: 999px !important;
        padding: 0.55rem 1.5rem !important;
        box-shadow: 0 0 20px rgba(34,197,94,0.65);
        transition: all 0.18s ease-out;
    }

    div.stButton > button:hover {
        transform: translateY(-1px) scale(1.02);
        box-shadow: 0 0 26px rgba(34,197,94,0.9);
        filter: brightness(1.05);
    }

        /* Tables - hard lock dark mode for all grid elements */
    .stDataFrame, .stDataEditor {
        border-radius: 0.75rem !important;
        border: 1px solid #111827 !important;
        background-color: #020617 !important;
    }

    /* Root containers */
    [data-testid="stDataFrame"],
    [data-testid="stDataEditor"] {
        background-color: #020617 !important;
        color: var(--ys-text-main) !important;
    }

    /* For the editor: make EVERY inner element dark/text-light */
    [data-testid="stDataEditor"] * {
        background-color: #020617 !important;
        color: var(--ys-text-main) !important;
        border-color: #111827 !important;
    }

    /* DataFrame (non-edit) tables also forced dark */
    [data-testid="stDataFrame"] table,
    [data-testid="stDataFrame"] tbody tr td,
    [data-testid="stDataFrame"] thead tr th {
        background-color: #020617 !important;
        color: var(--ys-text-main) !important;
        border-color: #111827 !important;
    }

    /* Sidebar yard multiselect pills (green instead of red) */
    [data-testid="stSidebar"] [data-baseweb="tag"] {
        background-color: #166534 !important;  /* dark green */
        border-radius: 999px !important;
        border: 1px solid #22c55e !important;
        color: #f9fafb !important;
        font-weight: 500 !important;
    }

    [data-testid="stSidebar"] [data-baseweb="tag"] span {
        color: #f9fafb !important;
    }

    [data-testid="stSidebar"] [data-baseweb="tag"] svg {
        color: #f97373 !important;  /* close icon a subtle red so it stands out */
    }

    /* MIL-OPS command bar under header (animated HUD nav) */
    .ys-nav-row {
        display: flex;
        gap: 0.4rem;
        padding: 6px 18px 10px 18px;
        margin: 0 -8px 0.75rem -8px;
        background: #020617;
        border-bottom: 1px solid #0f172a;
    }

    .ys-nav-pill {
        position: relative;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-family: "SF Mono", Menlo, Consolas, monospace;
        font-size: 0.75rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        padding: 0.28rem 0.9rem;
        border-radius: 999px;
        border: 1px solid #111827;
        color: var(--ys-text-muted);
        background: #020617;
        white-space: nowrap;
        overflow: hidden;
    }

    /* Draw the label and brackets via CSS so they never wrap */
    .ys-nav-pill::before {
        content: "[ " attr(data-label) " ]";
        color: currentColor;
    }

    .ys-nav-pill-active {
        border-color: var(--ys-accent);
        color: var(--ys-accent);
        background: #020617;
        box-shadow: 0 0 0 1px rgba(34,197,94,0.9), 0 0 18px rgba(34,197,94,0.45);
        animation: ysNavPulse 1.6s ease-in-out infinite;
    }

    @keyframes ysNavPulse {
        0% {
            box-shadow: 0 0 0 0 rgba(34,197,94,0.9), 0 0 18px rgba(34,197,94,0.6);
            transform: translateY(0);
        }
        50% {
            box-shadow: 0 0 0 10px rgba(34,197,94,0), 0 0 22px rgba(34,197,94,0.9);
            transform: translateY(-0.5px);
        }
        100% {
            box-shadow: 0 0 0 0 rgba(34,197,94,0), 0 0 18px rgba(34,197,94,0.5);
            transform: translateY(0);
        }
    }
    
    /* FINAL HARD OVERRIDE — NEW STREAMLIT GRID SELECTORS */
[data-grid="true"] * {
    background-color: #020617 !important;
    color: #f9fafb !important;
    border-color: #111827 !important;
}
[data-grid="true"] [role="columnheader"] {
    background-color: #020617 !important;
    color: #f9fafb !important;
    font-weight: 600 !important;
}
[data-grid="true"] [role="gridcell"] {
    background-color: #020617 !important;
    color: #f9fafb !important;
}
[data-grid="true"] input,
[data-grid="true"] textarea {
    background-color: #020617 !important;
    color: #f9fafb !important;
}
[data-grid="true"] [role="row"] [role="gridcell"] {
    background-color: #020617 !important;
}

    /* SAFARI FIX — relax WebKit native cell painting so our dark theme applies */
    @supports (-webkit-overflow-scrolling: touch) or (-webkit-appearance: none) {
        [data-grid="true"] [role="gridcell"],
        [data-grid="true"] [role="columnheader"] {
            -webkit-appearance: none !important;
            background-color: #020617 !important;
            color: #f9fafb !important;
        }

        [data-grid="true"] input,
        [data-grid="true"] textarea {
            -webkit-appearance: none !important;
            background-color: #020617 !important;
            color: #f9fafb !important;
        }

        [data-grid="true"] [role="row"] [role="gridcell"]:focus {
            outline: none !important;
            box-shadow: none !important;
        }
    }
    
    </style>
    """,
    unsafe_allow_html=True,
)

_last_count = (
    len(st.session_state.get("scan_rows", [])) if "scan_rows" in st.session_state else 0
)

# Decide which main view is active: SCAN, RESULTS, or MATRIX.
# Default: RESULTS if we already have rows, otherwise SCAN.
_default_tab = "RESULTS" if _last_count > 0 else "SCAN"
_active_tab = _default_tab

# Allow the HUD nav pills (links) to control the active view via ?view= param
try:
    qp = st.query_params
    if "view" in qp:
        v = qp["view"]
        # Newer Streamlit may give a string, older a list
        if isinstance(v, list):
            v = v[0]
        v = str(v).upper()
        if v in ("SCAN", "RESULTS", "MATRIX"):
            _active_tab = v
except Exception:
    # If anything goes wrong, fall back to default
    _active_tab = _default_tab

# Allow session to override the active tab (more reliable than query params alone)
if "active_tab" in st.session_state:
    sess_tab = st.session_state["active_tab"]
    if sess_tab in ("SCAN", "RESULTS", "MATRIX"):
        _active_tab = sess_tab

_scan_class = (
    "ys-nav-pill ys-nav-pill-active" if _active_tab == "SCAN" else "ys-nav-pill"
)
_results_class = (
    "ys-nav-pill ys-nav-pill-active" if _active_tab == "RESULTS" else "ys-nav-pill"
)
_matrix_class = (
    "ys-nav-pill ys-nav-pill-active" if _active_tab == "MATRIX" else "ys-nav-pill"
)

_header_html = f"""
    <div class="ys-header">
        <div class="ys-logo">
            <div class="ys-logo-eye"></div>
        </div>
        <div class="ys-text-block">
            <div class="ys-title">YARD SNIPER</div>
            <div class="ys-sub">MIL-OPS VEHICLE ACQUISITION SYSTEM — LOCKED TARGETS: {_last_count}</div>
        </div>
    </div>
    <div class="ys-nav-row">
        <a href="?view=SCAN" target="_self" class="{_scan_class}" data-label="SCAN"></a>
        <a href="?view=RESULTS" target="_self" class="{_results_class}" data-label="RESULTS"></a>
        <a href="?view=MATRIX" target="_self" class="{_matrix_class}" data-label="MATRIX"></a>
        <span class="ys-nav-pill" data-label="PULLERS"></span>
        <span class="ys-nav-pill" data-label="INVOICE"></span>
        <span class="ys-nav-pill" data-label="GEAR"></span>
    </div>
"""


st.markdown(_header_html, unsafe_allow_html=True)

############################################################
# HELPERS
############################################################


def load_yards(path="yards_config.json"):
    try:
        with open(path, "r") as f:
            data = json.load(f)
        return data.get("yards", [])
    except Exception as e:
        st.sidebar.error(f"Error loading yards_config.json: {e}")
        return []


# Lane B+ platform-specific feature modules for VIN arbitrage
def load_platform_feature_modules(path="platform_feature_modules.json"):
    """
    Optional: load platform-specific feature/option modules for VIN arbitrage (Lane B+).

    If a JSON file exists at `path`, it should look like:
        {
            "RANGE ROVER": [
                "adaptive cruise control module",
                "radar distance sensor",
                "air suspension control module"
            ],
            "RANGE ROVER SPORT": [
                "adaptive cruise control module",
                "air suspension control module"
            ]
        }

    Keys are matched against the decoded VIN model (uppercased). Values are lists of
    search phrases that will be appended to the eBay query for that VIN's platform.

    If the file is missing or invalid, we fall back to a small built-in default map.
    """
    # Try user-provided JSON first
    try:
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
            if isinstance(data, dict):
                # Normalize keys to uppercase so matching is case-insensitive
                return {str(k).upper(): list(v) for k, v in data.items()}
    except Exception:
        # If anything goes wrong, just fall back to defaults below
        pass

    # Built-in starter map: Range Rover platforms with high-value feature modules.
    default_map = {
        "RANGE ROVER": [
            "adaptive cruise control module",
            "adaptive cruise radar sensor",
            "radar distance sensor",
            "distance control module",
            "air suspension control module",
            "suspension ride height module",
            "blind spot monitor module",
            "park distance control module",
        ],
        "RANGE ROVER SPORT": [
            "adaptive cruise control module",
            "adaptive cruise radar sensor",
            "radar distance sensor",
            "air suspension control module",
            "blind spot monitor module",
            "park distance control module",
        ],
    }

    return {k.upper(): v for k, v in default_map.items()}


DATE_PATTERNS = [
    r"(\d{1,2})/(\d{1,2})/(\d{2,4})",
    r"(\d{4})-(\d{1,2})-(\d{1,2})",
]
VIN_PATTERN = re.compile(r"\b[A-HJ-NPR-Z0-9]{17}\b", re.I)


# === Helper functions to load Hollander and Vendor lists ===
@st.cache_data
def load_hollander_list(path="APBCO - PART LIST-2.csv"):
    """
    Load Hollander options from column C of the Part List CSV.
    Columns A/B can stay in the file; we only use column C.
    """
    try:
        df = pd.read_csv(path)
        # Column C = 3rd column (0=A, 1=B, 2=C)
        codes = df.iloc[:, 2].dropna().astype(str).str.strip().unique()
        codes = sorted(codes)
        return codes
    except Exception as e:
        st.sidebar.warning(f"Could not load Hollander list: {e}")
        return []


def normalize_drive_label(raw: str) -> str:
    """
    Turn NHTSA drive strings into simple labels: AWD / FWD / RWD / 4WD.
    Fallback: '' if nothing useful.
    """
    if not raw:
        return ""
    d = raw.upper()
    if "FRONT" in d or "FWD" in d:
        return "FWD"
    if "REAR" in d or "RWD" in d:
        return "RWD"
    if "4X4" in d or "4WD" in d or "ALL" in d or "AWD" in d:
        return "AWD"
    return raw.strip()


def normalize_date(text: str) -> str:
    if not text:
        return ""
    text = text.strip()
    for pat in DATE_PATTERNS:
        m = re.search(pat, text)
        if m:
            parts = list(m.groups())
            try:
                # mm/dd/yy or mm/dd/yyyy
                if pat.startswith("("):
                    mm, dd, yy = map(int, parts)
                    if yy < 100:
                        yy += 2000
                    return f"{yy:04d}-{mm:02d}-{dd:02d}"
                else:
                    yy, mm, dd = map(int, parts)
                    return f"{yy:04d}-{mm:02d}-{dd:02d}"
            except Exception:
                pass
    return ""


def parse_budget_make_model(query: str):
    """
    Extract MAKE and MODEL tokens for Budget U Pull It
    from a query like:
        '2010-2013 Mazda 6'
        '2012 Mazda6'
        '2010-2013 Mazda 6 2.5L AWD'

    Returns (MAKE, MODEL) uppercased for URL:
        ('MAZDA', 'MAZDA6')
    """
    q = query.lower()
    q = re.sub(r"[^a-z0-9 \-]+", " ", q)
    tokens = q.split()

    # Remove pure year tokens and year ranges like 1998-2002
    tokens = [t for t in tokens if not re.fullmatch(r"\d{4}", t)]
    tokens = [t for t in tokens if not re.fullmatch(r"\d{4}-\d{4}", t)]
    # Drop tokens that have no letters (gets rid of lone '-' from '1998 - 2002')

    tokens = [t for t in tokens if re.search(r"[a-z]", t)]
    if not tokens:
        return None, None

    # ---- Special handling for Mazda 6-style queries ----
    # Cases:
    #   "mazda 6", "mazda6", "mazda-6", etc.
    joined = " ".join(tokens)

    if "mazda" in joined:
        make = "MAZDA"

        # If there's a separate "6" token
        if "mazda 6" in joined or "mazda6" in joined or "mazda  6" in joined:
            model = "MAZDA6"
            return make, model

        # Fallback: if any token startswith mazda and contains a 6
        for t in tokens:
            if t.startswith("mazda") and "6" in t:
                model = "MAZDA6"
                return make, model

    # ---- Generic fallback for other makes/models ----
    # Drop common noise tokens
    ignore = {"awd", "fwd", "4wd", "4x4", "rwd", "v6", "v8"}
    filtered = [t for t in tokens if t not in ignore]

    if len(filtered) < 2:
        return None, None

    make = filtered[0].upper()
    model = "".join(filtered[1:]).upper()  # join rest as compact model string

    return make, model


def decode_vin_nhtsa(vin: str):
    """
    Decode VIN using NHTSA API.
    Returns: year, make, model, engine, drive (some may be None/"").
    """
    vin = vin.strip()
    if len(vin) < 11:
        return {
            "year": None,
            "make": None,
            "model": None,
            "engine": None,
            "drive": "",
        }

    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevinvalues/{vin}?format=json"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        res = (data.get("Results") or [{}])[0]

        year = res.get("ModelYear") or None
        make = res.get("Make") or None
        model = res.get("Model") or None

        # Engine info: may appear in different fields
        engine = res.get("EngineModel") or ""
        if not engine:
            disp_l = res.get("DisplacementL") or ""
            cyl = res.get("EngineCylinders") or ""
            engine = f"{disp_l}L {cyl}cyl".strip()

        # Drivetrain info
        raw_drive = (
            res.get("DriveType")
            or res.get("DriveTypePrimary")
            or res.get("Drive Type")
            or res.get("Drive")
            or ""
        )
        drive = normalize_drive_label(raw_drive)

        return {
            "year": int(year) if (year and year.isdigit()) else None,
            "make": make,
            "model": model,
            "engine": engine or None,
            "drive": drive,
        }
    except Exception:
        return {
            "year": None,
            "make": None,
            "model": None,
            "engine": None,
            "drive": "",
        }


def clean_query_for_search(query: str) -> str:
    """
    Build a search string for pyp.com:
    - Remove drivetrain (AWD/FWD/etc)
    - Remove ALL 4-digit years (2011, 2012, etc.)
    So '2011-2013 Kia Sorento AWD' -> 'kia sorento'
    """
    q = query.lower()
    q = re.sub(r"[^a-z0-9 ]+", " ", q)
    tokens = q.split()

    ignore = {"awd", "fwd", "4wd", "4x4", "rwd", "v6", "v8"}
    kept = []
    for t in tokens:
        if re.fullmatch(r"\d{4}", t):  # drop pure years
            continue
        if t in ignore:
            continue
        kept.append(t)

    return " ".join(kept)


def build_url(slug: str, query: str) -> str:
    clean = clean_query_for_search(query)
    return f"https://www.pyp.com/inventory/{slug}/?search={quote_plus(clean)}"


def extract_keywords(query: str):
    """
    Keywords used to check make/model match in row text.
    Ignore drivetrain and pure years.
    """
    q = query.lower()
    q = re.sub(r"[^a-z0-9 ]+", " ", q)
    tokens = q.split()

    ignore = {"awd", "fwd", "4wd", "4x4", "rwd", "v6", "v8"}
    out = []
    for t in tokens:
        # Skip pure years like 1998
        if re.fullmatch(r"\d{4}", t):
            continue
        # Skip year ranges like 1998-2002
        if re.fullmatch(r"\d{4}-\d{4}", t):
            continue
        if len(t) <= 2:
            continue
        if t in ignore:
            continue
        out.append(t)
    return out


def parse_year_range(query: str):
    """
    From '2011-2013 Kia Sorento' or '2011 2013 Kia Sorento'
    return (min_year, max_year) or (None, None) if no years.
    """
    years = [int(y) for y in re.findall(r"\b(19\d{2}|20\d{2})\b", query)]
    if not years:
        return None, None
    if len(years) == 1:
        return years[0], years[0]
    return min(years), max(years)


def extract_year_from_row(row: dict):
    """
    Try to find a 4-digit year in title first, then raw_text.
    """
    for field in ["title", "raw_text"]:
        txt = (row.get(field) or "").strip()
        m = re.search(r"\b(19\d{2}|20\d{2})\b", txt)
        if m:
            try:
                return int(m.group(1))
            except Exception:
                pass
    return None


def expand_variant_lines(lines):
    """
    Expand lines with the pattern:
      '<base> : v1, v2, v3'
    or:
      '<base> : v1/v2/v3'
    into:
      '<base> v1'
      '<base> v2'
      '<base> v3'
    """
    expanded = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if ":" in line and ("," in line or "/" in line):
            base, var_str = line.split(":", 1)
            base = base.strip()
            parts = re.split(r"[,/]", var_str)
            for p in parts:
                p = p.strip()
                if not p:
                    continue
                expanded.append(f"{base} {p}")
        else:
            expanded.append(line)
    return expanded


# ==== eBay Integration Helpers ====
def build_ebay_query_from_row(row: dict) -> str:
    """
    Build an eBay search query from a result row.
    Prefer decoded year/make/model when available, otherwise fall back to title.
    """
    parts = []
    y = row.get("dec_year")
    make = row.get("dec_make") or ""
    model = row.get("dec_model") or ""
    title = row.get("title") or ""

    if y:
        parts.append(str(y))
    if make:
        parts.append(str(make))
    if model:
        parts.append(str(model))

    # If we couldn't get a clean decoded trio, fall back to the title text
    if not parts and title:
        parts.append(title)

    # 🔧 Part-specific keywords: steer toward subframes / cradles by default,
    # but allow targeting other hot, fast-moving parts via part_type.
    part_keywords = []

    part_type = (row.get("part_type") or "Cradle").lower()
    cradle = (row.get("cradle_position") or "").lower()

    if "cradle" in part_type:
        # Cradle remains the core play; still respect front/rear bias when present.
        if "rear" in cradle:
            # Rear cradle / AWD-style setups
            part_keywords.extend(
                [
                    "rear subframe",
                    "rear suspension subframe",
                    "rear crossmember",
                ]
            )
        elif "front" in cradle:
            # Front cradle / engine cradles
            part_keywords.extend(
                [
                    "front subframe",
                    "engine cradle",
                    "front suspension subframe",
                ]
            )
        else:
            # Generic K-frame / subframe targeting
            part_keywords.extend(
                [
                    "subframe",
                    "engine cradle",
                    "k frame",
                ]
            )
    elif "steering" in part_type:
        # Steering rack / rack-and-pinion style parts
        part_keywords.extend(
            [
                "steering rack",
                "rack and pinion",
                "power steering rack",
            ]
        )
    elif "pump" in part_type:
        # Power steering pump
        part_keywords.extend(
            [
                "power steering pump",
                "ps pump",
                "steering pump",
            ]
        )
    elif "engine" in part_type or "motor" in part_type:
        # Engines / motors — target complete engine assemblies and long blocks
        part_keywords.extend(
            [
                "complete engine",
                "engine long block",
                "engine assembly",
            ]
        )
    elif "trans" in part_type or "gearbox" in part_type:
        # Transmissions / gearboxes
        part_keywords.extend(
            [
                "automatic transmission",
                "transmission assembly",
                "gearbox",
            ]
        )
    elif "ecu" in part_type or "tcm" in part_type or "bcm" in part_type:
        # Electronics: ECU / TCM / BCM family
        part_keywords.extend(
            [
                "ECU",
                "engine control module",
                "engine computer",
                "PCM",
                "ECM",
                "TCM",
                "transmission control module",
                "BCM",
                "body control module",
            ]
        )
    else:
        # Fallback: treat as cradle-style part
        part_keywords.extend(
            [
                "subframe",
                "engine cradle",
                "k frame",
            ]
        )

    full_query_parts = [str(p) for p in parts if p] + part_keywords
    return " ".join(full_query_parts).strip()


def rewrite_airbag_query(raw_query: str) -> tuple[str, str]:
    """
    Lightly normalize and enrich airbag-related search phrases so that sloppy inputs like
    'camry driver bag' or '2018 rogue curtain bag' become stronger eBay queries, e.g.:

        '2018 Toyota Camry driver steering wheel airbag black'
        '2018 Nissan Rogue curtain airbag black'

    Returns (effective_query, note). If no airbag pattern is detected, returns (raw_query, "").
    """
    if not raw_query:
        return raw_query, ""

    q_lower = raw_query.lower()

    # Only touch queries that clearly look like airbag searches
    if not any(w in q_lower for w in ["airbag", "air bag", "air-bag", "bag"]):
        return raw_query, ""

    effective = raw_query

    # Normalize generic "bag" to "airbag" where possible
    if "air bag" in q_lower or "air-bag" in q_lower:
        effective = re.sub(
            r"\bair[\s\-]+bag\b", "airbag", effective, flags=re.IGNORECASE
        )
        q_lower = effective.lower()
    elif "airbag" not in q_lower and "bag" in q_lower:
        # Append 'airbag' if user only typed 'bag'
        effective = effective + " airbag"
        q_lower = effective.lower()

    # Driver airbag → steering wheel airbag
    if "driver" in q_lower and "steering" not in q_lower and "wheel" not in q_lower:
        effective = effective + " steering wheel"
        q_lower = effective.lower()

    # Passenger airbag → dash airbag
    if "passenger" in q_lower and "dash" not in q_lower:
        effective = effective + " dash"
        q_lower = effective.lower()

    # Curtain / side curtain airbags
    if "curtain" in q_lower and "airbag" not in q_lower:
        effective = effective + " airbag"
        q_lower = effective.lower()

    # Knee airbags
    if "knee" in q_lower and "airbag" not in q_lower:
        effective = effective + " airbag"
        q_lower = effective.lower()

    # Seat airbags
    if "seat" in q_lower and "airbag" not in q_lower:
        effective = effective + " airbag"
        q_lower = effective.lower()

    # If no obvious interior color is present, default to black (most common and safe)
    color_tokens = ["black", "gray", "grey", "tan", "beige", "brown", "red", "blue"]
    if not any(c in q_lower for c in color_tokens):
        effective = effective + " black"

    # Build a short note so the UI can show what we did
    note = (
        f"Airbag sniper rewrite: using enriched query '{effective.strip()}' "
        "for this profitability check."
    )
    return effective.strip(), note


def fetch_ebay_sold_stats(query: str, max_items: int = 15) -> dict:
    """
    Hybrid eBay sold stats with local file cache, robust scraping, and SerpAPI fallback.
    """
    if not query:
        return {"avg_price": None, "count": 0}

    # --- Retry tracker for eBay HTML failures ---
    if "ebay_fail_count" not in st.session_state:
        st.session_state["ebay_fail_count"] = {}
    if query not in st.session_state["ebay_fail_count"]:
        st.session_state["ebay_fail_count"][query] = 0

    cache_file = "ebay_cache.json"
    cache: dict = {}
    now = datetime.now().timestamp()

    # Load cache (best effort)
    try:
        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                cache = json.load(f)
    except Exception:
        cache = {}

    # Use cache if data < 24h old
    if query in cache:
        entry = cache[query]
        if now - entry.get("timestamp", 0) < 86400:
            # Silent cache hit; just return the stored stats.
            return {
                "avg_price": entry.get("avg_price"),
                "count": entry.get("count", 0),
            }

    prices: list[float] = []

    try:
        # --- Primary: quick HTML scrape of eBay sold/completed page ---
        base_url = "https://www.ebay.com/sch/i.html"
        params = {"_nkw": query, "LH_Sold": "1", "LH_Complete": "1"}
        headers = {"User-Agent": "Mozilla/5.0"}

        html_text = ""
        try:
            r = requests.get(base_url, params=params, headers=headers, timeout=10)
            if r.status_code == 200 and "captcha" not in r.text.lower():
                html_text = r.text
        except Exception:
            # HTML fetch failed; we'll fall back to API without extra chatter.
            html_text = ""

        # --- HTML failcount logic: if failed twice, we consider HTML unreliable ---
        if not html_text:
            st.session_state["ebay_fail_count"][query] += 1
            if st.session_state["ebay_fail_count"][query] >= 2:
                html_text = ""
                # Second miss: treat HTML as dead and rely on API (no extra text).
            else:
                # First miss: allow next stage to decide if API is needed.
                pass

        # If we have HTML, try to scrape prices
        if html_text:
            soup = BeautifulSoup(html_text, "html.parser")

            selectors = [
                ".s-item__price",
                ".x-price-approx__price",
                "[itemprop='price']",
            ]
            for sel in selectors:
                for price_el in soup.select(sel):
                    txt = price_el.get_text(" ", strip=True)
                    m = re.search(r"([\d,.]+)", txt)
                    if not m:
                        continue
                    try:
                        val = float(m.group(1).replace(",", ""))
                    except Exception:
                        continue
                    if val > 0 and math.isfinite(val):
                        prices.append(val)
                        if len(prices) >= max_items:
                            break
                if prices:
                    break

            # Fallback: scan whole page text for $price patterns
            if not prices:
                text_block = soup.get_text(" ", strip=True)
                for m in re.finditer(r"\$([\d,.]+)", text_block):
                    try:
                        val = float(m.group(1).replace(",", ""))
                    except Exception:
                        continue
                    if val > 0 and math.isfinite(val):
                        prices.append(val)
                        if len(prices) >= max_items:
                            break

        # --- SerpAPI fallback if still no prices ---
        if not prices:
            try:
                serp_key = os.environ.get("SERPAPI_KEY")
                if not serp_key:
                    st.warning(
                        "SerpAPI key not found in environment (SERPAPI_KEY). "
                        "Set this environment variable to enable eBay comps fallback."
                    )
                else:
                    serp_url = "https://serpapi.com/search.json"
                    serp_params = {
                        "engine": "ebay",
                        "api_key": serp_key,
                        "ebay_domain": "ebay.com",
                        "_nkw": query,
                        "show_only": "Sold",
                        "_ipg": "50",
                    }
                    serp_resp = requests.get(serp_url, params=serp_params, timeout=15)
                    if serp_resp.status_code == 200:
                        serp_data = serp_resp.json()
                        # SerpAPI eBay engine returns results in 'organic_results'
                        for item in serp_data.get("organic_results", []):
                            price_obj = item.get("price")
                            val = None
                            if isinstance(price_obj, dict):
                                if isinstance(price_obj.get("extracted"), (int, float)):
                                    val = float(price_obj["extracted"])
                                elif isinstance(price_obj.get("raw"), str):
                                    raw = re.sub(r"[^\d.]", "", price_obj["raw"])
                                    try:
                                        val = float(raw)
                                    except Exception:
                                        val = None
                            elif isinstance(price_obj, str):
                                raw = re.sub(r"[^\d.]", "", price_obj)
                                try:
                                    val = float(raw)
                                except Exception:
                                    val = None

                            if val and val > 0 and math.isfinite(val):
                                prices.append(val)
                    else:
                        st.warning(
                            f"SerpAPI HTTP {serp_resp.status_code} for query '{query}'."
                        )
            except Exception as e:
                st.warning(f"SerpAPI fallback error: {e}")

        # ✅ Finalize results if any prices were found (HTML or API)
        if prices:
            avg_price = sum(prices) / len(prices)
            result = {"avg_price": avg_price, "count": len(prices)}
            st.info(f"eBay sold stats: {len(prices)} items, avg ${avg_price:.2f}")

            # Update cache
            cache[query] = {
                "avg_price": avg_price,
                "count": len(prices),
                "timestamp": now,
            }
            try:
                with open(cache_file, "w") as f:
                    json.dump(cache, f)
            except Exception as e:
                st.warning(f"eBay cache write error: {e}")

            return result

        # No prices found anywhere
        return {"avg_price": None, "count": 0}

    except Exception as e:
        st.warning(f"eBay fetch error: {e}")
        return {"avg_price": None, "count": 0}


############################################################
# SCRAPER CORE
############################################################


def scan_central_pickandpay(yard_name, query, want_drive):
    """
    Scrape Central Florida Pick & Pay vehicle inventory:
    https://centralfloridapickandpay.com/vehicle-inventory/

    We:
      - Pull full page text
      - Find all VINs
      - Look at a small snippet of text around each VIN
      - Keep only VINs whose nearby text matches the query keywords (e.g. "honda", "accord")
      - VIN-decode only those candidates and filter by year range
    """
    url = "https://centralfloridapickandpay.com/vehicle-inventory/"

    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")

        # Get all visible text
        text = soup.get_text("\n", strip=True)
        text_lower = text.lower()

        rows_out = []
        ymin, ymax = parse_year_range(query)
        kw = extract_keywords(query)
        cf_make, cf_model = parse_budget_make_model(query)

        candidate_vins = set()

        # First pass — scan around each VIN and see if nearby text matches our keywords
        for m in VIN_PATTERN.finditer(text):
            vin_txt = m.group(0)
            start = max(0, m.start() - 120)
            end = min(len(text_lower), m.end() + 120)
            snippet = text_lower[start:end]

            # Must contain all query keywords (e.g. "honda", "accord")
            if kw and not all(k in snippet for k in kw):
                continue

            candidate_vins.add(vin_txt)

        # st.write(
        #   f"CFPP DEBUG: narrowed to {len(candidate_vins)} candidate VINs after snippet filter"
        # )

        # Second pass — VIN-decode only filtered candidate VINs
        for vin_txt in candidate_vins:
            vin_info = decode_vin_nhtsa(vin_txt)
            year_dec = vin_info["year"]
            make_dec = (vin_info["make"] or "").lower()
            model_dec = (vin_info["model"] or "").lower()

            # First, enforce decoded make/model against the parsed query make/model
            if cf_make:
                if cf_make.lower() not in make_dec:
                    continue
            if cf_model:
                # Normalize by stripping spaces so 'MAZDA6' matches 'MAZDA 6'
                if cf_model.lower().replace(" ", "") not in model_dec.replace(" ", ""):
                    continue

            # Additional safety: decoded make/model label must still roughly match all keywords
            label = f"{make_dec} {model_dec}".strip()
            if kw and not all(k in label for k in kw):
                continue

            # Year range check (use decoded year)
            y_final = year_dec
            if ymin is not None and ymax is not None:
                if y_final is None or not (ymin <= y_final <= ymax):
                    continue

            title = f"{year_dec or ''} {vin_info['make'] or ''} {vin_info['model'] or ''}".strip()

            rows_out.append(
                {
                    "yard": yard_name,
                    "slug": "centralfloridapickandpay",
                    "query": query,
                    "title": title,
                    "link": url,
                    "date_found": normalize_date(text),
                    "drivetrain": vin_info.get("drive", "") or "",
                    "raw_text": vin_txt,
                    "stock": "",
                    "row": "",
                    "vin": vin_txt,
                    "yard_label": yard_name,
                    "dec_year": year_dec,
                    "dec_make": vin_info["make"],
                    "dec_model": vin_info["model"],
                    "dec_engine": vin_info["engine"],
                }
            )

        return rows_out

    except Exception as e:
        st.error(f"{yard_name} (Central Florida Pick & Pay) error: {e}")
        return []


def scan_budget_upullit(yard_name, query, want_drive):
    """
    Scrape Budget U Pull It current inventory:
    https://budgetupullit.com/current-inventory/?make=...&model=...

    The page is plain text, not real <tr>/<td> rows, so we parse lines.
    """
    make, model = parse_budget_make_model(query)
    if not make or not model:
        st.warning(f"{yard_name}: could not parse make/model from query '{query}'.")
        return []

    url = f"https://budgetupullit.com/current-inventory/?make={make}&model={model}"

    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")

        # Get all visible text and extract VINs page-wide
        text = soup.get_text("\n", strip=True)
        vin_list = VIN_PATTERN.findall(text)

        rows_out = []
        ymin, ymax = parse_year_range(query)

        for vin_txt in set(vin_list):
            vin_info = decode_vin_nhtsa(vin_txt)
            year_dec = vin_info["year"]
            make_dec = (vin_info["make"] or "").upper()
            model_dec = (vin_info["model"] or "").upper()

            # basic sanity: decoded make/model should roughly match requested
            if make and make_dec and make not in make_dec:
                continue
            if model and model_dec and model not in model_dec.replace(" ", ""):
                continue

            y_final = year_dec
            if ymin is not None and ymax is not None:
                if y_final is None or not (ymin <= y_final <= ymax):
                    continue

            title = f"{year_dec or ''} {vin_info['make'] or ''} {vin_info['model'] or ''}".strip()

            rows_out.append(
                {
                    "yard": yard_name,
                    "slug": "budgetupullit",
                    "query": query,
                    "title": title,
                    "link": url,
                    "date_found": normalize_date(text),  # best-effort
                    "drivetrain": vin_info.get("drive", "") or "",
                    "raw_text": vin_txt,
                    "stock": "",
                    "row": "",
                    "vin": vin_txt,
                    "yard_label": yard_name,
                    "dec_year": year_dec,
                    "dec_make": vin_info["make"],
                    "dec_model": vin_info["model"],
                    "dec_engine": vin_info["engine"],
                }
            )

        return rows_out

    except Exception as e:
        st.error(f"{yard_name} (Budget U Pull It) error: {e}")
        return []


# --- Budget U Pull It S3 Location scraper ---
def scan_budget_s3(yard_name, query, want_drive):
    """
    Scrape Budget U Pull It second location (S3 Software Solutions inventory):
    http://budgetupullit.s3softwaresolutions.com/inventory.aspx

    This site appears to only show inventory AFTER a Make/Model search,
    so we try to simulate that by calling inventory.aspx with Make/Model
    query parameters derived from the search string.
    """
    base_url = "http://budgetupullit.s3softwaresolutions.com/inventory.aspx"

    # Try to parse MAKE/MODEL from the user's query (reusing Budget helper)
    make, model = parse_budget_make_model(query)
    if not make or not model:
        st.warning(f"{yard_name}: could not parse make/model from query '{query}'.")
        return []

    try:
        rows_out = []
        ymin, ymax = parse_year_range(query)
        kw = extract_keywords(query)

        # Step 1: initial GET to grab dynamic ASP.NET hidden fields
        try:
            r_init = requests.get(
                base_url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=20,
            )
            soup_init = BeautifulSoup(r_init.text, "html.parser")

            def get_hidden(name):
                inp = soup_init.find("input", {"name": name})
                return inp.get("value", "") if inp else ""

            viewstate = get_hidden("__VIEWSTATE")
            viewstate_gen = get_hidden("__VIEWSTATEGENERATOR")
            event_validation = get_hidden("__EVENTVALIDATION")

        except Exception:
            # If we can't fetch hidden fields, we'll still try with empty ones
            viewstate = ""
            viewstate_gen = ""
            event_validation = ""

        # Step 2: POST exactly like the browser does, but with our make/model
        payload = {
            "__EVENTTARGET": "ddlModel",
            "__EVENTARGUMENT": "",
            "__LASTFOCUS": "",
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstate_gen,
            "__EVENTVALIDATION": event_validation,
            "ddlMake": make,
            "ddlModel": model,
        }

        r = requests.post(
            base_url,
            data=payload,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            timeout=20,
        )

        soup = BeautifulSoup(r.text, "html.parser")

        # Find the main results table – it should contain the Year / Make / Model / Row / Arrival Date header
        tables = soup.find_all("table")
        for table in tables:
            header_text = table.get_text(" ", strip=True).lower()
            if (
                "year" in header_text
                and "make" in header_text
                and "model" in header_text
            ):
                # This looks like the inventory table
                for tr in table.find_all("tr"):
                    tds = tr.find_all("td")
                    if len(tds) < 3:
                        continue

                    cells = [td.get_text(" ", strip=True) for td in tds]
                    line = " ".join(cells)
                    low = line.lower()

                    # Keyword filter (make/model words like "honda", "accord")
                    if kw and not all(k in low for k in kw):
                        continue

                    # Try to extract a year from the first cell or anywhere in the line
                    year_val = None
                    ym = (
                        re.search(r"\b(19\d{2}|20\d{2})\b", cells[0]) if cells else None
                    )
                    if ym:
                        try:
                            year_val = int(ym.group(1))
                        except Exception:
                            year_val = None
                    if year_val is None:
                        ym = re.search(r"\b(19\d{2}|20\d{2})\b", line)
                        if ym:
                            try:
                                year_val = int(ym.group(1))
                            except Exception:
                                year_val = None

                    # Only enforce year range if we actually found a 4-digit year
                    if ymin is not None and ymax is not None and year_val is not None:
                        if not (ymin <= year_val <= ymax):
                            continue

                    # Basic title: Year + Make + Model from first 3 columns
                    title = " ".join(cells[:3]).strip()
                    if not title:
                        title = line[:80]

                    # Attempt to detect drivetrain string from row text
                    drive = ""
                    for kwd in ["AWD", "4WD", "4x4", "FWD", "RWD"]:
                        if re.search(rf"\b{kwd}\b", line, re.IGNORECASE):
                            drive = kwd
                            break

                    # Arrival Date is typically the last column
                    date_found = ""
                    if cells:
                        for c in reversed(cells):
                            date_found = normalize_date(c)
                            if date_found:
                                break

                    rows_out.append(
                        {
                            "yard": yard_name,
                            "slug": "budget-s3",
                            "query": query,
                            "title": title,
                            "link": base_url,
                            "date_found": date_found,
                            "drivetrain": drive,
                            "raw_text": line,
                            "stock": "",
                            "row": "",
                            "vin": None,
                            "yard_label": yard_name,
                            "dec_year": year_val,
                            "dec_make": None,
                            "dec_model": None,
                            "dec_engine": None,
                        }
                    )

        return rows_out

    except Exception as e:
        st.error(f"{yard_name} (Budget U Pull It S3) error: {e}")
        return []


# --- U-Pull-&-Pay Orlando scraper ---
def scan_upull_orlando(yard_name, query, want_drive):
    """
    NOTE (2025-11): U-Pull-&-Pay's Orlando inventory page is a fully client-side
    React/JS app. The Make dropdown and the search results are loaded dynamically
    with JavaScript after the initial HTML. Because our scraper runs purely with
    `requests` + `BeautifulSoup` (no browser engine), we can't reliably see or
    interact with that dynamic inventory from this environment.

    To avoid confusing errors like "could not find MakeID for make 'HONDA'",
    we currently short-circuit here. The yard will stay in your list, but this
    function will just warn once and return no rows.

    If you want true U-Pull-&-Pay support on your Mac later, we can add a
    Playwright/Selenium-based version that spins up a headless browser locally.
    """

    st.warning(
        f"{yard_name}: U-Pull-&-Pay Orlando uses a dynamic JS inventory. "
        "From this Streamlit scraper we can't read it reliably yet, so this "
        "yard is skipped for now."
    )
    return []


def extract_cards(soup: BeautifulSoup):
    cards = []

    # Links that look like inventory detail pages
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/inventory/" in href and (
            "vehicle" in href or "details" in href or "stock" in href
        ):
            card = a.find_parent(["div", "article", "li"])
            cards.append(card or a)

    # generic card/result containers
    for div in soup.find_all(
        "div", class_=re.compile(r"(card|result|vehicle|inventory)", re.I)
    ):
        cards.append(div)

    # de-dupe
    unique = []
    seen = set()
    for c in cards:
        if c and id(c) not in seen:
            seen.add(id(c))
            unique.append(c)
    return unique


def card_to_row(card, yard_name, slug, query, want_drive, search_url):
    text = " ".join(card.get_text(" ", strip=True).split())

    # Try to grab a VIN from the card text
    vin = None
    dec_year = dec_make = dec_model = dec_engine = None
    dec_drive = ""
    m = VIN_PATTERN.search(text)
    if m:
        vin = m.group(0)
        vin_info = decode_vin_nhtsa(vin)
        dec_year = vin_info["year"]
        dec_make = vin_info["make"]
        dec_model = vin_info["model"]
        dec_engine = vin_info["engine"]
        dec_drive = vin_info.get("drive", "") or ""

    # link from card
    link = ""
    a = card.find("a", href=True)
    if a:
        link = a["href"]
        if link.startswith("/"):
            link = "https://www.pyp.com" + link

    # If link is missing, is an image/CDN, or doesn't point to inventory,
    # fall back to the search URL that actually shows the result list.
    if (
        not link
        or "cdn.lkqcorp.com" in link
        or re.search(r"\.(?:jpe?g|png|gif)(?:\?|$)", link, re.IGNORECASE)
        or "/inventory/" not in link
    ):
        link = search_url

    # title extraction
    title = ""
    for tag in ["h1", "h2", "h3", "h4"]:
        h = card.find(tag)
        if h:
            title = h.get_text(" ", strip=True)
            break
    if not title:
        title = text[:80]

    # date extraction
    date_found = normalize_date(text)

    # AWD/FWD detection from raw text (fallback)
    drive = ""
    if want_drive:
        for kw in ["AWD", "4WD", "4x4", "FWD", "RWD"]:
            if re.search(rf"\b{kw}\b", text, re.I):
                drive = kw
                break

    # If VIN decode gave us a drivetrain, override text-based guess
    if dec_drive:
        drive = dec_drive

    return {
        "yard": yard_name,
        "slug": slug,
        "query": query,
        "title": title,
        "link": link,
        "date_found": date_found,
        "drivetrain": drive,
        "raw_text": text,
        "vin": vin,
        "dec_year": dec_year,
        "dec_make": dec_make,
        "dec_model": dec_model,
        "dec_engine": dec_engine,
        "dec_drive": dec_drive,
    }


def scan_yard(yard_name, slug, query, want_drive):
    # Special-case Budget U Pull It (Winter Garden)
    if slug == "budgetupullit":
        return scan_budget_upullit(yard_name, query, want_drive)

    # Special-case Budget U Pull It second location (S3 system)
    if slug == "budget-s3":
        return scan_budget_s3(yard_name, query, want_drive)

    # Special-case U-Pull-&-Pay Orlando
    if slug == "upullandpay-orlando":
        return scan_upull_orlando(yard_name, query, want_drive)

    # Special-case Central Florida Pick & Pay
    if slug == "centralfloridapickandpay":
        return scan_central_pickandpay(yard_name, query, want_drive)

    url = build_url(slug, query)
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
        cards = extract_cards(soup)
        rows = [card_to_row(c, yard_name, slug, query, want_drive, url) for c in cards]
        rows = [r for r in rows if r["link"]]

        # keyword filter (make/model words)
        kw = extract_keywords(query)
        if kw:
            filtered = []
            for row in rows:
                hay = (row.get("title", "") + " " + row.get("raw_text", "")).lower()
                if all(k in hay for k in kw):
                    filtered.append(row)
            rows = filtered

        # year range filter (e.g. 2011–2013)
        ymin, ymax = parse_year_range(query)
        if ymin is not None and ymax is not None:
            filtered = []
            for row in rows:
                y = extract_year_from_row(row)
                if y is None:
                    continue
                if ymin <= y <= ymax:
                    filtered.append(row)
            rows = filtered

        # refine link per row for LKQ yards (not Budget)
        base_search = clean_query_for_search(query)
        if base_search and rows and slug != "budgetupullit":
            for row in rows:
                y = extract_year_from_row(row)
                if y is not None:
                    row["link"] = (
                        f"https://www.pyp.com/inventory/{slug}/"
                        f"?search={y}+{quote_plus(base_search)}"
                    )

        return rows

    except Exception as e:
        st.error(f"{yard_name} error: {e}")
        return []


############################################################
# UI
############################################################


yards = load_yards()
yard_names = [y["name"] for y in yards]
yard_map = {y["name"]: y for y in yards}

st.sidebar.header("Yards")
default_enabled = [y["name"] for y in yards if y.get("enabled")]
selected_yards = st.sidebar.multiselect(
    "Choose yards", yard_names, default=default_enabled
)

# Auto-expand filters once we have scan results (choice D: hidden until SCAN, then open)
expanded_flag = bool(st.session_state.get("scan_rows"))

with st.sidebar.expander("Filters & presets (advanced)", expanded=expanded_flag):
    want_drive = st.checkbox("Flag AWD/FWD", True)

    preset = st.selectbox(
        "Quick sniper preset",
        [
            "None",
            "Kia Sorento AWD V6",
            "Nissan Murano AWD 3.5L",
            "Mazda 6 2.5L (I4)",
        ],
        index=0,
    )

    # ---- preset defaults (must exist BEFORE dropdowns use them) ----
    drive_default_index = 0  # index for "Any"
    engine_default = ""

    if preset in ("Kia Sorento AWD V6", "Nissan Murano AWD 3.5L"):
        drive_default_index = 1  # AWD preset

    if preset == "Kia Sorento AWD V6":
        engine_default = "V6"
    elif preset == "Nissan Murano AWD 3.5L":
        engine_default = "3.5L"
    elif preset == "Mazda 6 2.5L (I4)":
        engine_default = "2.5L"

    # ---- drivetrain selector (preset overrides index only) ----
    drive_filter = st.selectbox(
        "Filter by drivetrain (VIN or tag)",
        ["Any", "AWD", "FWD", "RWD", "4WD/4x4"],
        index=drive_default_index,
    )

    # ---- engine trim input (preset overrides default only) ----
    engine_filter = st.text_input(
        "Filter by engine (e.g. 2.5L, 3.5L, V6, 4CYL)",
        engine_default,
    )

    # ---- NEW ARRIVAL FILTER ----
    arrival_filter = st.selectbox(
        "Only show vehicles from last:",
        ["Any", "3 days", "7 days", "14 days", "30 days"],
        index=0,
    )

    limit = st.number_input("Max display rows", 5, 1000, 200)

# eBay comps toggle (pulled out of advanced presets)
ebay_toggle = st.sidebar.checkbox(
    "eBay Comps",
    value=False,
    help="Add eBay SOLD comps (avg price + count) using completed listings.",
)

# Part focus mode: cradles only vs cradles + hot conservative movers
part_focus = st.sidebar.selectbox(
    "Part focus",
    [
        "Cradles only (K-frames)",
        "Cradles + hot quick movers (conservative)",
    ],
    index=0,
    help=(
        "Cradles only = subframes / K-frames. "
        "Cradles + hot quick movers = also consider steering racks, power steering pumps, "
        "and ECUs/TCMs/BCMs when building comps."
    ),
)
# Keep the current choice in session so helpers (like eBay query builder) can read it
st.session_state["part_focus"] = part_focus

st.sidebar.markdown("---")

# --- Scan History Sidebar Expander ---
with st.sidebar.expander("Scan History"):
    if os.path.exists("scan_history.csv"):
        try:
            hist_df = pd.read_csv("scan_history.csv")
            st.sidebar.dataframe(hist_df, height=200)
            if st.sidebar.button("Clear history"):
                os.remove("scan_history.csv")
                st.rerun()
        except Exception as e:
            st.sidebar.error(f"Could not load scan history: {e}")
    else:
        st.sidebar.info("No scan history yet.")

# Only render the Query Builder + SCAN controls when we're on the SCAN tab
top_scan = False

if _active_tab == "SCAN":
    st.markdown("#### Target Search — Query Builder")

    current_year = datetime.today().year
    years = list(range(current_year + 1, 1974, -1))

    col_y1, col_y2 = st.columns(2)
    with col_y1:
        year_from = st.selectbox("From year", years, index=years.index(2011))
    with col_y2:
        year_to = st.selectbox("To year", years, index=years.index(2013))

    makes = [
        "",
        "Acura",
        "Alfa Romeo",
        "Audi",
        "BMW",
        "Buick",
        "Cadillac",
        "Chevrolet",
        "Chrysler",
        "Dodge",
        "Fiat",
        "Ford",
        "GMC",
        "Genesis",
        "Honda",
        "Hyundai",
        "Infiniti",
        "Isuzu",
        "Jaguar",
        "Jeep",
        "Kia",
        "Land Rover",
        "Lexus",
        "Lincoln",
        "Mazda",
        "Mercedes-Benz",
        "Mini",
        "Mitsubishi",
        "Nissan",
        "Pontiac",
        "Porsche",
        "Ram",
        "Saab",
        "Saturn",
        "Scion",
        "Subaru",
        "Suzuki",
        "Tesla",
        "Toyota",
        "Volkswagen",
        "Volvo",
        "Other",
    ]
    make_choice = st.selectbox("Make", makes, index=0)

    if make_choice == "Other":
        make_text = st.text_input("Custom make")
    else:
        make_text = make_choice

    # Load make-model mapping
    try:
        with open("make_model_map.json", "r") as f:
            make_to_models = json.load(f)
    except Exception:
        make_to_models = {}

    available_models = make_to_models.get(make_text, [])
    if available_models:
        model_text = st.selectbox(
            "Model",
            available_models,
            key="model_select",
            help="Type to search models",
            format_func=lambda x: x,
        )
    else:
        model_text = st.text_input("Model (e.g. Accord, Sorento, MAZDA6)")

    builder_query = ""
    if year_from and year_to and make_text and model_text:
        builder_query = f"{year_from}-{year_to} {make_text} {model_text}".strip()

    st.markdown(f"**Built query preview:** `{builder_query}`")

    # Cradle bias for this target (applied when adding the query)
    cradle_bias_choice = st.radio(
        "Cradle bias for this target",
        ["Auto", "Front", "Rear", "Front AWD", "Rear AWD"],
        horizontal=True,
        index=0,
    )

    # Store builder-generated queries across interactions
    if "builder_queries" not in st.session_state:
        st.session_state["builder_queries"] = []

    if "builder_cradle_bias" not in st.session_state:
        st.session_state["builder_cradle_bias"] = {}

    # Place "Add built query", "Reset Scanner", and "SCAN NOW" on the same row
    col_add, col_reset, col_scan = st.columns([1, 1, 1])
    with col_add:
        add_builder = st.button(
            "➕ Add built query to list",
            disabled=not builder_query.strip(),
        )
    with col_reset:
        reset_scan = st.button("🔄 Reset Scanner", key="reset_scan")
    with col_scan:
        top_scan = st.button("⦿  SCAN NOW", key="tac_scan")

    if reset_scan:
        st.session_state["scan_rows"] = []
        st.session_state["builder_queries"] = []
        st.session_state["builder_cradle_bias"] = {}
        st.session_state["edited_df"] = None
        st.rerun()

    if add_builder and builder_query.strip():
        q_clean = builder_query.strip()
        if q_clean not in st.session_state["builder_queries"]:
            st.session_state["builder_queries"].append(q_clean)

        # Map cradle bias choice for this query – store the exact cradle_position label
        bias_map = st.session_state.get("builder_cradle_bias", {})
        if cradle_bias_choice == "Front":
            bias_map[q_clean] = "Front cradle"
        elif cradle_bias_choice == "Rear":
            bias_map[q_clean] = "Rear cradle"
        elif cradle_bias_choice == "Front AWD":
            bias_map[q_clean] = "Front cradle AWD"
        elif cradle_bias_choice == "Rear AWD":
            bias_map[q_clean] = "Rear cradle AWD"
        else:
            # Auto = no forced bias for this query
            bias_map.pop(q_clean, None)
        st.session_state["builder_cradle_bias"] = bias_map

    # Show active sniper targets under the builder, with a multiselect remover
    active_targets = [
        q.strip() for q in st.session_state.get("builder_queries", []) if q.strip()
    ]
    if active_targets:
        st.markdown("**Active sniper targets:**")
        bias_map = st.session_state.get("builder_cradle_bias", {})

        # Render the list with bias labels (no per-row buttons)
        for t in active_targets:
            bias = bias_map.get(t, "")
            if bias == "Front cradle":
                bias_text = " (Front cradle bias)"
            elif bias == "Rear cradle":
                bias_text = " (Rear cradle bias)"
            elif bias == "Front cradle AWD":
                bias_text = " (Front AWD cradle bias)"
            elif bias == "Rear cradle AWD":
                bias_text = " (Rear AWD cradle bias)"
            else:
                bias_text = ""
            st.markdown(f"- `{t}`{bias_text}")

        # Multiselect to choose which targets to remove
        remove_choices = st.multiselect(
            "Select sniper targets to remove",
            options=active_targets,
            key="remove_targets_ms",
        )

        if remove_choices and st.button("Remove selected targets"):
            # Update queries list
            st.session_state["builder_queries"] = [
                q
                for q in st.session_state.get("builder_queries", [])
                if q not in remove_choices
            ]

            # Also drop their cradle bias entries
            bias_map = st.session_state.get("builder_cradle_bias", {})
            for q in remove_choices:
                if q in bias_map:
                    del bias_map[q]
            st.session_state["builder_cradle_bias"] = bias_map

            st.rerun()

    # ---------- Queries (from Query Builder only) ----------
    queries = [
        q.strip() for q in st.session_state.get("builder_queries", []) if q.strip()
    ]

    # expand variants (Option A multi-variety handling)
    queries = expand_variant_lines(queries)

    # Keep last scan results in session so table edits don't clear them
    if "scan_rows" not in st.session_state:
        st.session_state["scan_rows"] = []

    # Single-scan control: use the top HUD "SCAN NOW" button
    if top_scan:
        effective_queries = queries

        if not selected_yards:
            st.error("Choose at least one yard.")
            st.session_state["scan_rows"] = []
        elif not effective_queries:
            st.error("Add at least one target with the Query Builder above.")
            st.session_state["scan_rows"] = []
        else:
            all_rows = []
            total = len(selected_yards) * len(effective_queries)
            step = 0
            prog = st.progress(0.0)
            # --- Scan history tracking ---
            history_entries = []

            for yname in selected_yards:
                yard = yard_map[yname]
                slug = yard["slug"]
                for q in effective_queries:
                    rows = scan_yard(
                        yard_name=yname,
                        slug=slug,
                        query=q,
                        want_drive=want_drive,
                    )
                    # Log this scan to history
                    history_entries.append(
                        {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "query": q,
                            "yard": yname,
                            "count": len(rows),
                        }
                    )
                    all_rows.extend(rows)
                    step += 1
                    prog.progress(step / total)

            st.session_state["scan_rows"] = all_rows
            # Write scan history to CSV
            if history_entries:
                hist_df = pd.DataFrame(history_entries)
                hist_df.to_csv(
                    "scan_history.csv",
                    mode="a",
                    header=not os.path.exists("scan_history.csv"),
                    index=False,
                )

            # Quick summary so you can see the scan actually returned rows
            st.success(
                f"Scan complete: {len(all_rows)} matches across {len(selected_yards)} yard(s)."
            )

            # If you want to sanity-check results immediately, show a small preview in SCAN tab
            if all_rows:
                try:
                    preview_df = pd.DataFrame(all_rows).head(50)
                    st.dataframe(preview_df, use_container_width=True)
                except Exception:
                    # If DataFrame construction fails for any reason, just skip the preview
                    pass
            else:
                st.warning("No results found. Try broader queries or check yard slugs.")

            # After a scan, force the UI to flip to RESULTS using session state + rerun
            st.session_state["active_tab"] = "RESULTS"
            st.rerun()

#
# Use last scan results from session state to build the table and downloads
#
all_rows = st.session_state.get("scan_rows", [])

############################################################
# RESULTS TAB — Display scan results and Parts Matrix bridge
############################################################

# Show scan results (editable table) if we're on the RESULTS tab
if _active_tab == "RESULTS":
    st.markdown("### Scan Results")

    if all_rows:
        try:
            display_df = pd.DataFrame(all_rows)
            # Show editable table for results
            st.data_editor(
                display_df, use_container_width=True, key="results_editor_raw"
            )
        except Exception:
            # If DataFrame construction fails, fallback to raw table
            inv_df = pd.DataFrame(all_rows)
            st.dataframe(inv_df, use_container_width=True)

        # --- Parts Matrix integration: analyze top scan results with eBay comps ---
        if "display_df" in locals():
            matrix_source_df = display_df.copy()
        else:
            matrix_source_df = inv_df.copy() if "inv_df" in locals() else None

        if matrix_source_df is not None and not matrix_source_df.empty:
            st.markdown("#### Parts Matrix bridge — analyze these results")

            max_rows_pm = st.number_input(
                "How many top rows to analyze with Parts Matrix?",
                min_value=1,
                max_value=int(len(matrix_source_df)),
                value=int(min(10, len(matrix_source_df))),
                step=1,
                key="pm_from_scan_limit",
            )

            if st.button(
                "Analyze top rows with Parts Matrix", key="pm_from_scan_button"
            ):
                candidates = matrix_source_df.head(int(max_rows_pm)).to_dict("records")
                pm_profiles_from_scan = []

                for row in candidates:
                    ebay_q = build_ebay_query_from_row(row)
                    stats = fetch_ebay_sold_stats(ebay_q, max_items=20)
                    avg_price = stats.get("avg_price")
                    sold_count = stats.get("count", 0)

                    if avg_price is None or sold_count == 0:
                        flip_eta = "N/A"
                        confidence = 0
                    else:
                        if sold_count >= 15:
                            flip_eta = "7–14 days"
                            confidence = 90
                        elif sold_count >= 8:
                            flip_eta = "14–30 days"
                            confidence = 80
                        elif sold_count >= 4:
                            flip_eta = ">30 days"
                            confidence = 65
                        else:
                            flip_eta = ">30 days"
                            confidence = 50

                    your_cost = float(row.get("Your Cost", 0.0) or 0.0)
                    ship_estimate = float(row.get("Ship Estimate", 0.0) or 0.0)

                    FEE_RATE_PM = 0.1495
                    fee_est = (avg_price or 0.0) * FEE_RATE_PM if avg_price else 0.0

                    # Assume buyer-paid shipping for scan-based analysis by default,
                    # so we do not subtract ship_estimate from profit.
                    net_profit = (avg_price or 0.0) - your_cost - fee_est

                    profit_margin_pct = (
                        (net_profit / avg_price * 100.0) if avg_price else 0.0
                    )

                    # Auto-buy now requires speed, confidence, and non-negative profit.
                    auto_buy = (
                        confidence >= 70
                        and flip_eta
                        in (
                            "7–14 days",
                            "14–30 days",
                        )
                        and net_profit >= 0
                    )

                    pm_profiles_from_scan.append(
                        {
                            "yard": row.get("yard", row.get("yard_label", "")),
                            "title": row.get("title", ""),
                            "part_type": row.get("Part Type", row.get("part_type", "")),
                            "ebay_query": ebay_q,
                            "avg_price": round(avg_price, 2) if avg_price else None,
                            "sold_count": sold_count,
                            "flip_eta": flip_eta,
                            "confidence": confidence,
                            "your_cost": your_cost,
                            "ship_estimate": ship_estimate,
                            "market_fees_est": round(fee_est, 2),
                            "net_profit_est": round(net_profit, 2),
                            "profit_margin_pct": round(profit_margin_pct, 1),
                            "auto_buy": auto_buy,
                        }
                    )

                st.session_state["pm_scan_profiles"] = pm_profiles_from_scan
                st.success(
                    f"Analyzed {len(pm_profiles_from_scan)} rows. "
                    "Switch to the MATRIX tab to review them in Parts Matrix."
                )
    else:
        st.info("No scan results found. Go to the SCAN tab and run a search.")

# ============================================================
# PARTS MATRIX LAB — FREE PLAY (independent of yard scanning)
# ============================================================

if _active_tab == "MATRIX":
    st.markdown("### Parts Matrix Lab — Free Play")

    with st.expander(
        "Test any part using eBay sold comps (independent of your yard scan)",
        expanded=False,
    ):
        pm_query = st.text_input(
            "eBay search text or VIN (ex: '2012-2015 Civic electric power steering rack' or a 17-char VIN)",
            key="pm_query",
            help=(
                "You can paste a plain eBay-style search (engines, transmissions, racks, BCMs, pumps, etc.), "
                "or paste a full 17-character VIN to quickly estimate a cradle/subframe play for that exact vehicle. "
                "We'll look at sold listings on eBay and estimate profitability and flip speed."
            ),
        )

        col_pm_cost, col_pm_ship = st.columns(2)
        with col_pm_cost:
            pm_cost = st.number_input(
                "Your cost for this part",
                min_value=0.0,
                value=0.0,
                step=5.0,
                key="pm_cost",
            )
        with col_pm_ship:
            # Most eBay listings for these parts are buyer-paid shipping; allow override.
            buyer_pays_shipping = st.checkbox(
                "Buyer pays shipping (don’t subtract shipping from profit)",
                value=True,
                help=(
                    "If checked, shipping is assumed to be paid by the buyer, so it is not "
                    "subtracted from your profit. Uncheck if you typically cover shipping."
                ),
                key="pm_buyer_pays_shipping",
            )
            if buyer_pays_shipping:
                # When buyer pays shipping, we don't need a shipping input; treat as 0 in profit math.
                pm_ship = 0.0
            else:
                pm_ship = st.number_input(
                    "Estimated shipping cost",
                    min_value=0.0,
                    value=0.0,
                    step=5.0,
                    key="pm_ship",
                )

    # Store top-part profiles in session so they persist across interactions
    if "pm_profiles" not in st.session_state:
        st.session_state["pm_profiles"] = []

    analyze_click = st.button("Analyze Part with Parts Matrix", key="pm_analyze")

    pm_last_profile = None

    if analyze_click and pm_query.strip():
        raw_pm_query = pm_query.strip()
        vin_match = VIN_PATTERN.search(raw_pm_query)
        is_pure_vin = bool(vin_match and len(raw_pm_query.replace(" ", "")) == 17)

        # Clear any previous VIN-side profiles by default
        st.session_state.pop("pm_last_vin_side_profiles", None)

        if is_pure_vin:
            # VIN MATRIX MODE C:
            # If the input is a 17-character VIN, decode it and build cradle-focused
            # queries for the appropriate cradle sides (front/rear/AWD) and evaluate
            # them separately. If both sides are profitable, surface a BUY BOTH signal.
            vin_clean = vin_match.group(0).upper()
            vin_info = decode_vin_nhtsa(vin_clean)
            year = vin_info.get("year")
            make = vin_info.get("make") or ""
            model = vin_info.get("model") or ""
            drive = vin_info.get("drive", "") or ""

            ym_label_parts = []
            if year:
                ym_label_parts.append(str(year))
            if make:
                ym_label_parts.append(str(make))
            if model:
                ym_label_parts.append(str(model))

            ym_label = " ".join(ym_label_parts).strip()

            vin_note = ""
            if ym_label:
                drive_str = f" ({drive})" if drive else ""
                vin_note = (
                    f"VIN decoded as {ym_label}{drive_str}. "
                    "Evaluating cradle plays from this VIN for front/rear/AWD where applicable."
                )

            if vin_note:
                st.info(vin_note)

            # Build cradle-side queries based on drivetrain
            cradle_queries = []
            if ym_label:
                if drive == "AWD":
                    cradle_queries.append(
                        (
                            "Front AWD cradle",
                            f"{ym_label} front subframe engine cradle k frame",
                        )
                    )
                    cradle_queries.append(
                        (
                            "Rear AWD cradle",
                            f"{ym_label} rear subframe engine cradle k frame",
                        )
                    )
                elif drive == "FWD":
                    cradle_queries.append(
                        (
                            "Front cradle",
                            f"{ym_label} front subframe engine cradle k frame",
                        )
                    )
                elif drive == "RWD":
                    cradle_queries.append(
                        (
                            "Rear cradle",
                            f"{ym_label} rear subframe engine cradle k frame",
                        )
                    )
                else:
                    cradle_queries.append(
                        ("Cradle", f"{ym_label} subframe engine cradle k frame")
                    )

            vin_side_profiles = []

            for cradle_side, q in cradle_queries:
                stats = fetch_ebay_sold_stats(q, max_items=20)
                avg_price = stats.get("avg_price")
                sold_count = stats.get("count", 0)

                if avg_price is None or sold_count == 0:
                    flip_eta = "N/A"
                    confidence = 0
                else:
                    # Basic flip ETA + confidence based purely on public eBay activity.
                    # This does not use any of your personal sales data.
                    if sold_count >= 15:
                        flip_eta = "7–14 days"
                        confidence = 90
                    elif sold_count >= 8:
                        flip_eta = "14–30 days"
                        confidence = 80
                    elif sold_count >= 4:
                        flip_eta = ">30 days"
                        confidence = 65
                    else:
                        flip_eta = ">30 days"
                        confidence = 50

                # Profit math for each cradle-side play
                FEE_RATE_PM = 0.1495  # same 14.95% fee assumption
                fee_est = (avg_price or 0.0) * FEE_RATE_PM if avg_price else 0.0

                if buyer_pays_shipping:
                    net_profit = (avg_price or 0.0) - pm_cost - fee_est
                else:
                    net_profit = (avg_price or 0.0) - pm_cost - pm_ship - fee_est

                profit_margin_pct = (
                    (net_profit / avg_price) * 100.0 if avg_price else 0.0
                )

                auto_buy = (
                    confidence >= 70
                    and flip_eta in ("7–14 days", "14–30 days")
                    and net_profit >= 0
                )

                vin_side_profiles.append(
                    {
                        "part_query": raw_pm_query,
                        "cradle_side": cradle_side,
                        "ebay_query": q,
                        "avg_price": round(avg_price, 2) if avg_price else 0.0,
                        "sold_count": sold_count,
                        "flip_eta": flip_eta,
                        "confidence": confidence,
                        "your_cost": pm_cost,
                        "ship_estimate": pm_ship,
                        "market_fees_est": round(fee_est, 2),
                        "net_profit_est": round(net_profit, 2),
                        "profit_margin_pct": round(profit_margin_pct, 1),
                        "auto_buy": auto_buy,
                    }
                )

            if not vin_side_profiles:
                st.warning(
                    "No reliable sold data found for this VIN-based cradle search. "
                    "Try testing a manual search phrase instead of the VIN."
                )
            else:
                # Choose the best cradle-side profile by net profit
                best_profile = max(
                    vin_side_profiles, key=lambda p: p.get("net_profit_est", -1e9)
                )

                # BUY BOTH: if 2+ cradle sides are auto-buy, mark this so the UI can show it
                buy_both = sum(1 for p in vin_side_profiles if p["auto_buy"]) >= 2
                best_profile["buy_both"] = buy_both

                pm_last_profile = best_profile
                st.session_state["pm_last_profile"] = pm_last_profile
                st.session_state["pm_last_vin_side_profiles"] = vin_side_profiles

        else:
            # Non-VIN path: treat pm_query as a normal eBay search phrase,
            # but allow special sniper rewrites for certain categories (e.g. airbags).
            effective_query = raw_pm_query

            # Airbag sniper: normalize sloppy airbag phrasing into a stronger eBay query.
            effective_query, airbag_note = rewrite_airbag_query(effective_query)
            if airbag_note:
                st.info(airbag_note)

            stats = fetch_ebay_sold_stats(effective_query, max_items=20)
            avg_price = stats.get("avg_price")
            sold_count = stats.get("count", 0)

            if avg_price is None or sold_count == 0:
                st.warning(
                    "No reliable sold data found for this query. Try broadening the wording "
                    "or removing very specific trim/options."
                )
            else:
                # Basic flip ETA + confidence based purely on public eBay activity.
                # This does not use any of your personal sales data.
                if sold_count >= 15:
                    flip_eta = "7–14 days"
                    confidence = 90
                elif sold_count >= 8:
                    flip_eta = "14–30 days"
                    confidence = 80
                elif sold_count >= 4:
                    flip_eta = ">30 days"
                    confidence = 65
                else:
                    flip_eta = ">30 days"
                    confidence = 50

                # Profit math for the free-play part
                FEE_RATE_PM = 0.1495  # same 14.95% fee assumption
                fee_est = avg_price * FEE_RATE_PM

                # If the buyer pays shipping, do not subtract pm_ship from profit.
                if buyer_pays_shipping:
                    net_profit = avg_price - pm_cost - fee_est
                else:
                    net_profit = avg_price - pm_cost - pm_ship - fee_est

                if avg_price != 0:
                    profit_margin_pct = (net_profit / avg_price) * 100.0
                else:
                    profit_margin_pct = 0.0

                # Auto-buy now also requires non-negative profit, not just speed/confidence.
                auto_buy = (
                    confidence >= 70
                    and flip_eta in ("7–14 days", "14–30 days")
                    and net_profit >= 0
                )
                pm_last_profile = {
                    "part_query": pm_query.strip(),
                    "ebay_query": effective_query,
                    "avg_price": round(avg_price, 2),
                    "sold_count": sold_count,
                    "flip_eta": flip_eta,
                    "confidence": confidence,
                    "your_cost": pm_cost,
                    "ship_estimate": pm_ship,
                    "market_fees_est": round(fee_est, 2),
                    "net_profit_est": round(net_profit, 2),
                    "profit_margin_pct": round(profit_margin_pct, 1),
                    "auto_buy": auto_buy,
                    # Non-VIN free-play parts have no cradle-side multi-lane logic
                    "buy_both": False,
                }
                st.session_state["pm_last_profile"] = pm_last_profile

    # If we have a last-analyzed profile (from this run or previous), show it
    pm_last_profile = st.session_state.get("pm_last_profile", pm_last_profile)

    if pm_last_profile:
        st.markdown("#### Last analyzed part")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric(
                "Avg sold price",
                f"${pm_last_profile['avg_price']:.2f}",
                help="Based on recent eBay sold listings.",
            )
        with c2:
            st.metric(
                "Sold count (samples)",
                f"{pm_last_profile['sold_count']}",
                help="How many sold examples we used for this estimate.",
            )
        with c3:
            st.metric(
                "Net profit (est.)",
                f"${pm_last_profile['net_profit_est']:.2f}",
                help="After your cost, shipping, and estimated marketplace fees.",
            )

        c4, c5, c6 = st.columns(3)
        with c4:
            st.metric(
                "Flip ETA (days)",
                pm_last_profile["flip_eta"],
                help="Shorter windows indicate faster-moving parts.",
            )
        with c5:
            st.metric(
                "Confidence",
                f"{pm_last_profile['confidence']}%",
                help="Higher = more reliable estimate based on more sold data.",
            )
        with c6:
            st.metric(
                "Profit margin %",
                f"{pm_last_profile['profit_margin_pct']:.1f}%",
                help="Net profit as a percentage of the average sold price.",
            )

            # Auto-buy messaging, including BUY BOTH signal when both cradle sides
            # are profitable for VIN-based cradle searches.
            if pm_last_profile.get("buy_both"):
                auto_buy_label = (
                    "YES — BOTH front and rear cradle plays are profitable (BUY BOTH)."
                )
            elif pm_last_profile["auto_buy"]:
                auto_buy_label = "YES — Meets 70% / ≤30-day / profit ≥ 0 rule"
            else:
                auto_buy_label = "NO — Below speed/confidence/profit thresholds"
        st.write(f"**Auto-buy signal:** {auto_buy_label}")

        # If we know which cradle side this profile refers to, show it.
        cradle_side_label = pm_last_profile.get("cradle_side")
        if cradle_side_label:
            st.write(f"**Best cradle play:** {cradle_side_label}")

        # Allow saving into the Top Parts list
        if st.button("Save to Top Parts (Parts Matrix)", key="pm_save_profile"):
            profiles = st.session_state.get("pm_profiles", [])
            # Avoid duplicate entries by query + lane-independent profile
            existing_queries = {p.get("part_query") for p in profiles}
            if pm_last_profile["part_query"] not in existing_queries:
                profiles.append(pm_last_profile)
                st.session_state["pm_profiles"] = profiles
                st.success("Saved this part profile into your Top Parts list.")
            else:
                st.info("This part is already in your Top Parts list.")

        # Show saved top-performer profiles if any
        profiles = st.session_state.get("pm_profiles", [])
        if profiles:
            st.markdown("#### Saved Top Parts Profiles")
            st.dataframe(pd.DataFrame(profiles), use_container_width=True)

    # ============================================================
    # VIN MODULE RADAR — Tech modules from a single VIN (B lane)
    # ============================================================

    st.markdown("### VIN Module Radar — Tech Modules (beta)")

    with st.expander(
        "Scan a VIN for hot electronic modules (BCM / PCM / TCM / ABS / EPS)",
        expanded=False,
    ):
        vin_input = st.text_input(
            "Enter VIN",
            key="vin_module_input",
            help=(
                "Paste a full 17-character VIN to identify year/make/model and probe "
                "demand for key control modules on that exact vehicle."
            ),
        )

        run_vin_modules = st.button("Analyze VIN modules", key="vin_module_analyze")

        if run_vin_modules and vin_input.strip():
            vin_clean = vin_input.strip().upper()
            vin_info = decode_vin_nhtsa(vin_clean)
            year = vin_info.get("year")
            make = vin_info.get("make") or ""
            model = vin_info.get("model") or ""

            if not year or not make or not model:
                st.warning(
                    "Could not decode this VIN into a clear year/make/model. "
                    "Double-check the VIN or try another vehicle."
                )
            else:
                st.write(f"**Decoded VIN:** {year} {make} {model}")

                # Define which core tech modules we want to probe from eBay sold data
                base_module_defs = [
                    ("BCM", "body control module"),
                    ("PCM / ECU", "engine control module"),
                    ("TCM", "transmission control module"),
                    ("ABS module", "ABS module"),
                    ("EPS module", "electric power steering module"),
                ]

                # Lane B+ start: platform-specific feature modules (e.g. adaptive cruise)
                platform_features = load_platform_feature_modules()
                model_key = (model or "").upper().strip()
                feature_terms = platform_features.get(model_key, [])

                # Start with base core modules, then extend with any feature modules
                module_defs = list(base_module_defs)
                for feat in feature_terms:
                    if isinstance(feat, str) and feat.strip():
                        module_defs.append((f"Feature: {feat.strip()}", feat.strip()))

                rows_mod = []
                for label, keyword in module_defs:
                    q = f"{year} {make} {model} {keyword}"
                    stats = fetch_ebay_sold_stats(q, max_items=20)
                    avg_price = stats.get("avg_price")
                    sold_count = stats.get("count", 0)

                    # Basic flip ETA + confidence based only on public eBay activity
                    if avg_price is None or sold_count == 0:
                        flip_eta = "N/A"
                        confidence = 0
                    else:
                        if sold_count >= 15:
                            flip_eta = "7–14 days"
                            confidence = 90
                        elif sold_count >= 8:
                            flip_eta = "14–30 days"
                            confidence = 80
                        elif sold_count >= 4:
                            flip_eta = ">30 days"
                            confidence = 65
                        else:
                            flip_eta = ">30 days"
                            confidence = 50

                    rows_mod.append(
                        {
                            "module": label,
                            "ebay_query": q,
                            "ebay_url": f"https://www.ebay.com/sch/i.html?_nkw={quote_plus(q)}&LH_Sold=1&LH_Complete=1",
                            "avg_sold_price": (
                                round(avg_price, 2)
                                if isinstance(avg_price, (int, float))
                                else None
                            ),
                            "sold_count": sold_count,
                            "flip_eta": flip_eta,
                            "confidence": confidence,
                        }
                    )

                df_mod = pd.DataFrame(rows_mod)

                if not df_mod.empty:
                    # Rank modules: highest sold_count first, then higher average price
                    df_mod_sorted = df_mod.sort_values(
                        by=["sold_count", "avg_sold_price"],
                        ascending=[False, False],
                    ).reset_index(drop=True)

                    # Top 3 quick view
                    st.markdown("#### Top 3 hot modules for this VIN")
                    top3 = df_mod_sorted.head(3)
                    for _, r in top3.iterrows():
                        avg_val = (
                            r["avg_sold_price"]
                            if r["avg_sold_price"] is not None
                            else 0.0
                        )
                        ebay_url = r.get("ebay_url", "")
                        link_str = f" — [View on eBay]({ebay_url})" if ebay_url else ""
                        st.markdown(
                            f"- **{r['module']}** — "
                            f"{r['sold_count']} sold, "
                            f"avg ${avg_val:.2f}, "
                            f"ETA: {r['flip_eta']}, "
                            f"confidence {r['confidence']}%"
                            f"{link_str}"
                        )

                    # Full ranked table so you can dig deeper if you want
                    st.markdown("#### Full module ranking")
                    st.dataframe(df_mod_sorted, use_container_width=True)
                else:
                    st.info(
                        "No clear module demand signal detected from eBay sold data for this VIN."
                    )
        else:
            st.info(
                "Enter a VIN and click 'Analyze VIN modules' to see demand for key modules."
            )

    # ============================================================
    # OVERNIGHT SNIPER REPORT — AUTO-SCANNED VIN HITS
    # ============================================================

    st.markdown("### Overnight Sniper — Auto-Scanned VIN Hits")

    overnight_path = "overnight_sniper_latest.csv"
    if not os.path.exists(overnight_path):
        st.info(
            "No overnight sniper report found yet. "
            "Once your night job writes 'overnight_sniper_latest.csv', "
            "you'll see your top VIN/module opportunities here."
        )
    else:
        try:
            on_df = pd.read_csv(overnight_path)
        except Exception as e:
            st.warning(f"Could not read overnight sniper file: {e}")
            on_df = None

        if on_df is not None and not on_df.empty:
            # Basic filters: yard, make, auto_buy
            col_y, col_m, col_a = st.columns([1, 1, 1])
            with col_y:
                if "yard" in on_df.columns:
                    yards_avail = sorted(on_df["yard"].dropna().unique().tolist())
                else:
                    yards_avail = []
                yard_sel = st.multiselect(
                    "Filter by yard", yards_avail, default=yards_avail
                )
            with col_m:
                if "dec_make" in on_df.columns:
                    makes_avail = sorted(
                        on_df["dec_make"].dropna().astype(str).unique().tolist()
                    )
                else:
                    makes_avail = []
                make_sel = st.multiselect(
                    "Filter by make", makes_avail, default=makes_avail
                )
            with col_a:
                auto_only = st.checkbox(
                    "Auto-buy only",
                    value=True,
                    help="Show only rows where auto_buy is True.",
                )

            df_view = on_df.copy()

            if yard_sel:
                df_view = df_view[df_view["yard"].isin(yard_sel)]
            if make_sel:
                df_view = df_view[df_view["dec_make"].astype(str).isin(make_sel)]
            if auto_only and "auto_buy" in df_view.columns:
                df_view["auto_buy"] = df_view["auto_buy"].astype(bool)
                df_view = df_view[df_view["auto_buy"]]

            if df_view.empty:
                st.info("No overnight hits match these filters yet.")
            else:
                # Sort by best_module_sold_count then best_module_avg_price if present
                sort_cols = []
                sort_asc = []
                if "best_module_sold_count" in df_view.columns:
                    sort_cols.append("best_module_sold_count")
                    sort_asc.append(False)
                if "best_module_avg_price" in df_view.columns:
                    sort_cols.append("best_module_avg_price")
                    sort_asc.append(False)
                if sort_cols:
                    df_view = df_view.sort_values(by=sort_cols, ascending=sort_asc)

                # Limit to top 20
                df_view = df_view.head(20)

                display_cols = [
                    c
                    for c in [
                        "yard",
                        "dec_year",
                        "dec_make",
                        "dec_model",
                        "vin",
                        "best_module",
                        "best_module_avg_price",
                        "best_module_sold_count",
                        "best_module_flip_eta",
                        "best_module_confidence",
                        "auto_buy",
                        "link",
                    ]
                    if c in df_view.columns
                ]

                st.dataframe(df_view[display_cols], use_container_width=True)
        else:
            st.info("Overnight sniper file is present but empty.")

if _active_tab == "RESULTS" and all_rows:
    df = pd.DataFrame(all_rows)

    # Prefer VIN-based dedupe so Budget rows don't collapse into 1
    if "vin" in df.columns:
        df = df.drop_duplicates(subset=["yard", "vin"])
    else:
        df = df.drop_duplicates(subset=["link"])

    # Remove raw text column
    if "raw_text" in df.columns:
        df = df.drop(columns=["raw_text"])

    # Add clickable hyperlink column for Excel / Google Sheets
    if "link" in df.columns:
        df["view"] = df["link"].apply(lambda x: f'=HYPERLINK("{x}", "Open Link")')

    # 🔹 Drivetrain filter (Any / AWD / FWD / RWD / 4WD/4x4)
    if "drivetrain" in df.columns and drive_filter != "Any":
        drv = df["drivetrain"].fillna("").str.upper()
        if drive_filter == "4WD/4x4":
            df = df[drv.isin(["4WD", "4X4"])]
        else:
            df = df[drv == drive_filter]

    # 🔹 Engine trim filter (uses VIN-decoded dec_engine where available)
    if engine_filter:
        filt = engine_filter.upper().strip()
        if "dec_engine" in df.columns:
            eng = df["dec_engine"].fillna("").str.upper()
            df = df[eng.str.contains(filt, na=False)]
        else:
            # fallback: try a generic 'engine' column if it ever exists
            engine_cols = [c for c in df.columns if "engine" in c.lower()]
            if engine_cols:
                col = engine_cols[0]
                eng = df[col].fillna("").str.upper()
                df = df[eng.str.contains(filt, na=False)]

    # 🔹 Arrival age filter (e.g. last 3/7/14/30 days)
    if "date_found" in df.columns and arrival_filter != "Any":
        days_map = {
            "3 days": 3,
            "7 days": 7,
            "14 days": 14,
            "30 days": 30,
        }
        max_age = days_map.get(arrival_filter)
        if max_age is not None:
            dates = pd.to_datetime(df["date_found"], errors="coerce")
            today = pd.to_datetime(datetime.today().date())
            age_days = (today - dates).dt.days
            df = df[age_days <= max_age]

    if df.empty:
        st.warning("No matches found for this scan with current filters.")
    else:
        # Respect display limit
        if len(df) > limit:
            st.info(f"Showing first {limit} of {len(df)} rows (total: {len(df)}).")
            df_show = df.head(limit).copy()
        else:
            df_show = df.copy()

        # Add a 'buy' column for shortlist selection (if not already present)
        if "buy" not in df_show.columns:
            df_show.insert(0, "buy", False)

        # Add a Hollander column so you can assign the correct code per row
        if "hollander" not in df_show.columns:
            df_show.insert(1, "hollander", "")

        # Add a Puller Notes column for instructions to the yard pullers
        if "puller_notes" not in df_show.columns:
            df_show["puller_notes"] = ""

        # Add a cradle position column so you can tag FRONT vs REAR cradle for pullers
        if "cradle_position" not in df_show.columns:
            df_show["cradle_position"] = ""

        # Profit input columns (your cost & shipping estimate)
        if "your_cost" not in df_show.columns:
            df_show["your_cost"] = 0.0
        if "ship_estimate" not in df_show.columns:
            df_show["ship_estimate"] = 0.0

        # Part type column so you can switch between cradle, rack, pump, and ECU/TCM/BCM
        if "part_type" not in df_show.columns:
            df_show["part_type"] = "Cradle"

        # Auto-tag cradle position based on query-level cradle bias and drivetrain.
        # Only apply this on a fresh scan (no prior edited_df), so we don't
        # override any manual choices the user already made.
        if "edited_df" not in st.session_state or st.session_state["edited_df"] is None:
            # 1) Apply query-level cradle bias from the builder, if present
            bias_map = st.session_state.get("builder_cradle_bias", {})
            if "query" in df_show.columns and bias_map:
                q_series = df_show["query"].astype(str)
                mask_empty = df_show["cradle_position"].astype(str).eq("")
                bias_series = q_series.map(bias_map).fillna("")
                # For any row with an empty cradle_position and a non-empty bias,
                # copy the stored label directly into cradle_position.
                mask_any = mask_empty & bias_series.ne("")
                df_show.loc[mask_any, "cradle_position"] = bias_series[mask_any]

            # 2) AWD-style auto-tag for any rows still untagged (default rear AWD)
            if "drivetrain" in df_show.columns:
                drv_series = df_show["drivetrain"].fillna("").str.upper()
                mask_empty2 = df_show["cradle_position"].astype(str).eq("")
                mask_awd_like = drv_series.isin(["AWD", "4WD", "4X4"])
                df_show.loc[mask_empty2 & mask_awd_like, "cradle_position"] = (
                    "Rear cradle AWD"
                )

        # If we have a previous edited_df from the Results tab, use it to
        # restore buy/hollander/puller_notes/cradle_position state so changes aren't lost
        prev_edited = st.session_state.get("edited_df")
        if prev_edited is not None and len(prev_edited) == len(df_show):
            if "buy" in prev_edited.columns:
                df_show["buy"] = prev_edited["buy"].values
            if "hollander" in prev_edited.columns:
                df_show["hollander"] = prev_edited["hollander"].astype(str).values
            if "puller_notes" in prev_edited.columns:
                df_show["puller_notes"] = prev_edited["puller_notes"].astype(str).values
            if "cradle_position" in prev_edited.columns:
                df_show["cradle_position"] = (
                    prev_edited["cradle_position"].astype(str).values
                )
            if "your_cost" in prev_edited.columns and "your_cost" in df_show.columns:
                df_show["your_cost"] = pd.to_numeric(
                    prev_edited["your_cost"], errors="coerce"
                ).fillna(0.0)
            if (
                "ship_estimate" in prev_edited.columns
                and "ship_estimate" in df_show.columns
            ):
                df_show["ship_estimate"] = pd.to_numeric(
                    prev_edited["ship_estimate"], errors="coerce"
                ).fillna(0.0)

            if "part_type" in prev_edited.columns and "part_type" in df_show.columns:
                df_show["part_type"] = prev_edited["part_type"].astype(str).values

        # 🔹 eBay SOLD comps enrichment (optional, per visible row)
        if ebay_toggle:
            # Initialize columns if they don't exist yet
            if "ebay_avg_sold" not in df_show.columns:
                df_show["ebay_avg_sold"] = None
            if "ebay_sold_count" not in df_show.columns:
                df_show["ebay_sold_count"] = 0

            # Only fetch stats for up to `limit` visible rows
            sample_df = df_show.head(limit).copy()
            for idx, row in sample_df.iterrows():
                q = build_ebay_query_from_row(row.to_dict())
                stats = fetch_ebay_sold_stats(q, max_items=10)
                df_show.at[idx, "ebay_avg_sold"] = stats.get("avg_price")
                df_show.at[idx, "ebay_sold_count"] = stats.get("count", 0)

        # 🔹 Profit metrics based on eBay comps and your cost/shipping
        FEE_RATE = 0.1495  # 14.95% marketplace fee assumption

        # Ensure profit-related columns exist
        if "market_fees" not in df_show.columns:
            df_show["market_fees"] = None
        if "net_profit" not in df_show.columns:
            df_show["net_profit"] = None
        if "profit_margin_pct" not in df_show.columns:
            df_show["profit_margin_pct"] = None
        if "profit_band" not in df_show.columns:
            df_show["profit_band"] = ""

        if "ebay_avg_sold" in df_show.columns:
            rev = pd.to_numeric(df_show["ebay_avg_sold"], errors="coerce")
            cost = pd.to_numeric(df_show["your_cost"], errors="coerce").fillna(0.0)
            ship = pd.to_numeric(df_show["ship_estimate"], errors="coerce").fillna(0.0)

            fee = rev * FEE_RATE
            net = rev - cost - ship - fee

            # Avoid divide-by-zero for margin
            rev_nonzero = rev.where(rev != 0)
            margin = (net / rev_nonzero) * 100

            df_show["market_fees"] = fee.round(2)
            df_show["net_profit"] = net.round(2)
            df_show["profit_margin_pct"] = margin.round(1)

            # Emoji "heatmap" band for quick scanning
            bands = []
            for v in df_show["profit_margin_pct"]:
                try:
                    if pd.isna(v):
                        bands.append("")
                    elif v > 50:
                        bands.append("🔥")
                    elif v >= 25:
                        bands.append("🟢")
                    elif v >= 10:
                        bands.append("🟡")
                    elif v > 0:
                        bands.append("🟠")
                    else:
                        bands.append("🔴")
                except Exception:
                    bands.append("")
            df_show["profit_band"] = bands

        # Load Hollander dropdown options from your CSV file
        hollander_options = load_hollander_list()

        # Make sure key categorical columns are strings so they play nice with SelectboxColumn
        df_show["hollander"] = df_show["hollander"].astype(str)
        df_show["cradle_position"] = df_show["cradle_position"].astype(str)
        if "part_type" in df_show.columns:
            df_show["part_type"] = df_show["part_type"].astype(str)

        column_config = {}
        if hollander_options:
            column_config["hollander"] = st.column_config.SelectboxColumn(
                "Hollander",
                options=list(hollander_options),
                help="Pick Hollander code for this row.",
                required=False,
            )

        # Bilingual cradle position for pullers (Front/Rear in English & Spanish)
        column_config["cradle_position"] = st.column_config.SelectboxColumn(
            "Cradle (Front/Rear) / Cuna (delantera/trasera)",
            options=[
                "",
                "Front cradle",
                "Rear cradle",
                "Front cradle AWD",
                "Rear cradle AWD",
            ],
            help="Mark if this is a front or rear cradle – English & Español.",
            required=False,
        )

        # Part type selector so you can target different high-value parts on the same vehicle
        column_config["part_type"] = st.column_config.SelectboxColumn(
            "Part Type",
            options=[
                "Cradle",
                "Steering rack",
                "Power steering pump",
                "ECU / TCM / BCM",
            ],
            help=(
                "Which part this row's eBay comps and profit math should target. "
                "Cradle remains the default; switch to racks, pumps, or ECUs as needed."
            ),
            required=True,
        )

        # Profit-related numeric columns
        column_config["your_cost"] = st.column_config.NumberColumn(
            "Your Cost",
            help="What you expect to pay the yard for this vehicle/part.",
            min_value=0.0,
            step=1.0,
        )
        column_config["ship_estimate"] = st.column_config.NumberColumn(
            "Ship Estimate",
            help="Your estimated shipping cost for this pull.",
            min_value=0.0,
            step=1.0,
        )
        column_config["market_fees"] = st.column_config.NumberColumn(
            "Marketplace Fees (14.95%)",
            format="%.2f",
            help="Estimated marketplace fees based on eBay average sold price.",
        )
        column_config["net_profit"] = st.column_config.NumberColumn(
            "Net Profit",
            format="%.2f",
            help="Estimated profit after cost, shipping, and marketplace fees.",
        )
        column_config["profit_margin_pct"] = st.column_config.NumberColumn(
            "Profit Margin %",
            format="%.1f",
            help="Net profit as a percentage of the average sold price.",
        )

        # Create tabs for Results, Buy List, Puller List, and Invoice
        tab_results, tab_buy, tab_puller, tab_invoice = st.tabs(
            ["Results", "Buy List", "Puller", "Invoice"]
        )

        with tab_results:
            # Quick controls to mark all rows as BUY or clear them
            col_sa, col_ca = st.columns(2)
            with col_sa:
                if st.button("Select ALL as BUY"):
                    df_show["buy"] = True
            with col_ca:
                if st.button("Clear ALL BUY"):
                    df_show["buy"] = False

            # Editable table so you can tick which cars you want to buy
            edited = st.data_editor(
                df_show,
                use_container_width=True,
                num_rows="fixed",
                key="results_editor",
                column_config=column_config,
            )

            # Save edited grid into session_state so the Buy / Puller / Invoice tabs can use it
            st.session_state["edited_df"] = edited

            # Full CSV (all filtered results, no 'buy' column and no raw link)
            df_full_export = df.copy()
            drop_cols = [c for c in ["buy", "link"] if c in df_full_export.columns]
            if drop_cols:
                df_full_export = df_full_export.drop(columns=drop_cols)

            csv_all = df_full_export.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download ALL results CSV",
                data=csv_all,
                file_name="lkq_results_v7.csv",
                mime="text/csv",
                key="download_csv_main",
            )

        with tab_buy:
            edited_for_buy = st.session_state.get("edited_df")

            if (
                edited_for_buy is None
                or "buy" not in edited_for_buy.columns
                or not edited_for_buy["buy"].any()
            ):
                st.info(
                    "Mark some rows as 'buy' in the Results tab to build a Buy List."
                )
            else:
                st.markdown("### 🛒 Buy List")

                buy_df = edited_for_buy[edited_for_buy["buy"]].copy()
                drop_cols = [c for c in ["buy", "link"] if c in buy_df.columns]
                if drop_cols:
                    buy_df = buy_df.drop(columns=drop_cols)

                # Show Buy List table so it's visible in the UI
                st.dataframe(buy_df, use_container_width=True)

                # ---- Invoice-friendly fields for Google Sheets / APBCO flow ----
                # Default quantity is 1 per row/VIN
                buy_df["qty"] = 1

                # Wholesale unit price to be filled in manually in Sheets
                buy_df["unit_price"] = ""

                # Status field for your workflow (READY / ORDERED / PULLED / INVOICED, etc.)
                buy_df["status"] = "READY"

                # Optional: reorder columns so invoice fields are at the front
                front_cols = ["hollander", "qty", "unit_price", "status"]
                remaining = [c for c in buy_df.columns if c not in front_cols]
                buy_df = buy_df[front_cols + remaining]

                buy_csv = buy_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "Download BUY LIST CSV",
                    data=buy_csv,
                    file_name="lkq_buy_list.csv",
                    mime="text/csv",
                    key="download_buylist",
                )

        with tab_puller:
            edited_for_puller = st.session_state.get("edited_df")

            if (
                edited_for_puller is None
                or "buy" not in edited_for_puller.columns
                or not edited_for_puller["buy"].any()
            ):
                st.info(
                    "Mark some rows as 'buy' in the Results tab to build a Puller list."
                )
            else:
                st.markdown("### 🧰 Puller List")

                puller_df = edited_for_puller[edited_for_puller["buy"]].copy()

                # Keep only the columns needed for the pullers
                desired_cols = [
                    "yard",
                    "vin",
                    "dec_year",
                    "dec_make",
                    "dec_model",
                    "dec_engine",
                    "dec_drive",
                    "view",
                    "row",
                    "cradle_position",
                    "puller_notes",
                ]
                existing_cols = [c for c in desired_cols if c in puller_df.columns]
                puller_df = puller_df[existing_cols]

                # Show the slimmed-down table
                st.dataframe(puller_df, use_container_width=True)

                # Downloadable CSV for emailing pullers
                puller_csv = puller_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "Download PULLER CSV",
                    data=puller_csv,
                    file_name="lkq_puller_list.csv",
                    mime="text/csv",
                    key="download_puller",
                )

                # Optional: downloadable PDF for pullers who can't open CSV
                if REPORTLAB_AVAILABLE:
                    pdf_buffer = BytesIO()
                    c = canvas.Canvas(pdf_buffer, pagesize=letter)
                    width, height = letter

                    text_obj = c.beginText(40, height - 40)
                    text_obj.textLine("Puller List")
                    text_obj.textLine("")
                    # Header row
                    header_line = " | ".join(puller_df.columns.astype(str).tolist())
                    text_obj.textLine(header_line)
                    text_obj.textLine("-" * min(len(header_line), 110))

                    # Simple row rendering (truncates long lines to 110 chars)
                    for _, row in puller_df.iterrows():
                        line = " | ".join(str(v) for v in row.tolist())
                        line = line[:110]
                        text_obj.textLine(line)
                        # Start a new page if we get too low
                        if text_obj.getY() < 40:
                            c.drawText(text_obj)
                            c.showPage()
                            text_obj = c.beginText(40, height - 40)

                    c.drawText(text_obj)
                    c.showPage()
                    c.save()
                    pdf_buffer.seek(0)

                    st.download_button(
                        "Download PULLER PDF",
                        data=pdf_buffer,
                        file_name="lkq_puller_list.pdf",
                        mime="application/pdf",
                        key="download_puller_pdf",
                    )
                else:
                    st.info(
                        "PDF export for the Puller list is available if the "
                        "'reportlab' package is installed. Add 'reportlab' to "
                        "requirements.txt and reinstall to enable the PDF button."
                    )

        with tab_invoice:
            edited_for_invoice = st.session_state.get("edited_df")

            if (
                edited_for_invoice is None
                or "buy" not in edited_for_invoice.columns
                or not edited_for_invoice["buy"].any()
            ):
                st.info(
                    "Mark some rows as 'buy' in the Results tab to build an Invoice."
                )
            else:
                st.markdown("### 📄 Invoice View")

                inv_df = edited_for_invoice[edited_for_invoice["buy"]].copy()
                drop_cols = [c for c in ["buy", "link"] if c in inv_df.columns]
                if drop_cols:
                    inv_df = inv_df.drop(columns=drop_cols)

                # Quantity and unit price fields (same idea as Buy List)
                if "qty" not in inv_df.columns:
                    inv_df["qty"] = 1
                if "unit_price" not in inv_df.columns:
                    inv_df["unit_price"] = ""

                # Status for your workflow
                if "status" not in inv_df.columns:
                    inv_df["status"] = "READY"

                # Compute numeric unit price and line total
                inv_df["unit_price_num"] = pd.to_numeric(
                    inv_df["unit_price"], errors="coerce"
                ).fillna(0)
                inv_df["line_total"] = inv_df["qty"] * inv_df["unit_price_num"]

                # Optional reordering: invoice-facing fields first
                front_cols = [
                    "hollander",
                    "dec_year",
                    "dec_make",
                    "dec_model",
                    "qty",
                    "unit_price",
                    "line_total",
                    "status",
                ]
                existing_front = [c for c in front_cols if c in inv_df.columns]
                remaining = [
                    c
                    for c in inv_df.columns
                    if c not in existing_front and c != "unit_price_num"
                ]
                inv_df = inv_df[existing_front + remaining]

                # Show invoice-style table (non-editable here; edits belong in Results/Buy)
                st.dataframe(inv_df, use_container_width=True)

                # Display grand total at the bottom
                grand_total = float(inv_df["line_total"].sum())
                st.markdown(f"**Grand total:** ${grand_total:,.2f}")

                # CSV export for actual invoicing
                export_inv_df = inv_df.drop(columns=["unit_price_num"], errors="ignore")
                invoice_csv = export_inv_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "Download INVOICE CSV",
                    data=invoice_csv,
                    file_name="lkq_invoice.csv",
                    mime="text/csv",
                    key="download_invoice",
                )
