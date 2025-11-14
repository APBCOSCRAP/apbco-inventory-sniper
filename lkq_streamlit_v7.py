import streamlit as st
import requests
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime
import json

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

st.set_page_config(page_title="ABCO Inventory Sniper", layout="wide")
st.title("ABCO Inventory Sniper")

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


def infer_year_from_vin_10th(vin: str):
    """
    Infer model year from the 10th character of a VIN.
    Handles common years roughly 1990–2030.
    Returns an int year or None.
    """
    if not vin or len(vin) < 10:
        return None

    code = vin[9].upper()

    mapping = {
        # 1990–2000
        "L": 1990,
        "M": 1991,
        "N": 1992,
        "P": 1993,
        "R": 1994,
        "S": 1995,
        "T": 1996,
        "V": 1997,
        "W": 1998,
        "X": 1999,
        "Y": 2000,
        # 2001–2009
        "1": 2001,
        "2": 2002,
        "3": 2003,
        "4": 2004,
        "5": 2005,
        "6": 2006,
        "7": 2007,
        "8": 2008,
        "9": 2009,
        # 2010–2020
        "A": 2010,
        "B": 2011,
        "C": 2012,
        "D": 2013,
        "E": 2014,
        "F": 2015,
        "G": 2016,
        "H": 2017,
        "J": 2018,
        "K": 2019,
        "L": 2020,
        # you can extend further if needed
    }

    return mapping.get(code)


DATE_PATTERNS = [
    r"(\d{1,2})/(\d{1,2})/(\d{2,4})",
    r"(\d{4})-(\d{1,2})-(\d{1,2})",
]


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


def augment_lkq_row_with_vin(row: dict):
    """
    For LKQ rows, try to fetch the vehicle detail page, extract VIN,
    decode it with NHTSA, and add VIN-based fields to the row.

    Adds:
        row["vin"]
        row["dec_year"]
        row["dec_make"]
        row["dec_model"]
        row["dec_engine"]
        row["dec_drive"]
        row["drivetrain_vin"] (preferred drive string)
    """
    link = row.get("link") or ""
    # Only attempt on LKQ inventory detail-ish URLs
    if "/inventory/" not in link:
        return row
    if not any(x in link for x in ["vehicle", "stock", "details"]):
        # Likely just a search page, not a detail page
        return row

    try:
        r = requests.get(link, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        s_detail = BeautifulSoup(r.text, "html.parser")
        text = s_detail.get_text(" ", strip=True)

        # Find a 17-character VIN pattern
        m = re.search(r"\b[A-HJ-NPR-Z0-9]{17}\b", text)
        if not m:
            return row

        vin = m.group(0)
        vin_info = decode_vin_nhtsa(vin)

        row["vin"] = vin
        row["dec_year"] = vin_info["year"]
        row["dec_make"] = vin_info["make"]
        row["dec_model"] = vin_info["model"]
        row["dec_engine"] = vin_info["engine"]
        row["dec_drive"] = vin_info.get("drive")

        # Prefer VIN drive over scraped text if present
        if vin_info.get("drive"):
            row["drivetrain_vin"] = vin_info["drive"]

        return row

    except Exception:
        # If anything fails, just leave the row as-is
        return row


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
    q = re.sub(r"[^a-z0-9 ]+", " ", q)
    tokens = q.split()

    # Remove pure year tokens
    tokens = [t for t in tokens if not re.fullmatch(r"\d{4}", t)]

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
    Returns: year, make, model, engine, drive (some may be None).
    """
    vin = vin.strip()
    if len(vin) < 11:
        return {
            "year": None,
            "make": None,
            "model": None,
            "engine": None,
            "drive": None,
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

        # Try to find a drive/drivetrain field
        drive = None
        # Common direct keys
        for key in ["DriveType", "Drive", "Drive Configuration"]:
            if key in res and res.get(key):
                drive = res.get(key)
                break
        # Fallback: search any key containing 'drive'
        if not drive:
            for k, v in res.items():
                if "drive" in k.lower() and v:
                    drive = v
                    break

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
            "drive": None,
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
        if re.fullmatch(r"\d{4}", t):
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


############################################################
# SCRAPER CORE
############################################################


def scan_central_pickandpay(yard_name, query, want_drive):
    """
    Scrape Central Florida Pick & Pay vehicle inventory:
    https://centralfloridapickandpay.com/vehicle-inventory/

    The page shows a plain text table with columns:
        Year Make Model Color Engine Row Arrival Date VIN
    We parse each data line, then filter by query keywords and year range.
    """
    url = "https://centralfloridapickandpay.com/vehicle-inventory/"

    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")

        # Get all visible text as lines
        text = soup.get_text("\n", strip=True)
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

        rows_out = []
        ymin, ymax = parse_year_range(query)
        kw = extract_keywords(query)

        # Try to locate header line (Year Make Model Color Engine Row Arrival Date VIN)
        header_idx = None
        for i, ln in enumerate(lines):
            normalized = " ".join(ln.split())
            if normalized.startswith(
                "Year Make Model Color Engine Row Arrival Date VIN"
            ):
                header_idx = i
                break

        start_idx = header_idx + 1 if header_idx is not None else 0

        # Each vehicle appears on a single line like:
        # 2011 MAZDA MAZDA6 WHITE L4, 2.5L 99 07/30/25 1YVHZ8BH2B5M22295
        for ln in lines[start_idx:]:
            parts = ln.split()
            # Need at least: year make model color ... row date vin
            if len(parts) < 8:
                continue

            year_txt = parts[0]
            # Require the first token to look like a 4-digit year
            if not re.fullmatch(r"\d{4}", year_txt):
                continue

            make_txt = parts[1]
            model_txt = parts[2]
            color_txt = parts[3]

            # Last three tokens are: row, arrival date, VIN
            vin_txt = parts[-1]
            date_txt = parts[-2]
            row_txt = parts[-3]

            # Everything between color and row is engine description
            engine_txt = " ".join(parts[4:-3]) if len(parts) > 7 else ""

            title = f"{year_txt} {make_txt} {model_txt}".strip()
            raw_text = ln

            # keyword filter (make/model words)
            hay = (title + " " + raw_text).lower()
            if kw and not all(k in hay for k in kw):
                continue

            # VIN decode (optional but useful)
            vin_info = decode_vin_nhtsa(vin_txt)
            year_dec = vin_info["year"]

            # year range filtering: prefer decoded year, fallback to line year
            y_row = None
            try:
                y_row = int(year_txt)
            except Exception:
                pass

            y_final = year_dec or y_row

            if ymin is not None and ymax is not None:
                if y_final is None or not (ymin <= y_final <= ymax):
                    continue

            link = url  # no per-car page, so link to main inventory

            rows_out.append(
                {
                    "yard": yard_name,
                    "slug": "centralfloridapickandpay",
                    "query": query,
                    "title": title,
                    "link": link,
                    "date_found": normalize_date(date_txt),
                    "drivetrain": "",  # unknown from this page
                    "raw_text": raw_text,
                    "stock": "",  # not provided separately
                    "row": row_txt,
                    "vin": vin_txt,
                    "yard_label": yard_name,
                    "dec_year": year_dec,
                    "dec_make": vin_info["make"],
                    "dec_model": vin_info["model"],
                    "dec_engine": vin_info["engine"],
                    "dec_drive": vin_info.get("drive"),
                }
            )

        return rows_out

    except Exception as e:
        st.error(f"{yard_name} (Central Florida Pick & Pay) error: {e}")
        return []


def scan_budget_upullit(yard_name, query, want_drive):
    """
    Scrape Budget U Pull It using Playwright (full JS-rendered inventory).
    Very simple version:
      - Load page with Playwright
      - Extract all VINs via regex
      - Infer year from VIN
      - Return one row per VIN (no year filtering)
    """

    # On cloud (no Playwright installed), just skip Budget for now
    if sync_playwright is None:
        st.warning("Budget U Pull It scanning is disabled on this deployment.")
        return []

    make, model = parse_budget_make_model(query)
    if not make or not model:
        st.warning(f"{yard_name}: could not parse make/model from query '{query}'.")
        return []

    url = f"https://budgetupullit.com/current-inventory/?make={make}&model={model}"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=60000)
            page.wait_for_timeout(2500)
            html = page.content()
            browser.close()

        soup = BeautifulSoup(html, "html.parser")

        text = soup.get_text("\n", strip=True)
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

        vin_pattern = re.compile(r"\b[A-HJ-NPR-Z0-9]{17}\b")
        vins = []
        for ln in lines:
            matches = vin_pattern.findall(ln)
            vins.extend(matches)

        vins = sorted(set(vins))

        rows_out = []
        for vin in vins:
            vin_info = decode_vin_nhtsa(vin)

            # Try to infer year from VIN first
            year_dec = None
            try:
                year_dec = infer_year_from_vin_10th(vin)
            except NameError:
                year_dec = vin_info.get("year")

            make_dec = vin_info.get("make") or make
            model_dec = vin_info.get("model") or model

            title_parts = []
            if year_dec:
                title_parts.append(str(year_dec))
            if make_dec:
                title_parts.append(str(make_dec))
            if model_dec:
                title_parts.append(str(model_dec))
            title = " ".join(title_parts) or vin

            rows_out.append(
                {
                    "yard": yard_name,
                    "slug": "budgetupullit",
                    "query": query,
                    "title": title,
                    "link": url,
                    "date_found": "",
                    "drivetrain": "",
                    "raw_text": vin,
                    "stock": "",
                    "row": "",
                    "vin": vin,
                    "yard_label": yard_name,
                    "dec_year": year_dec,
                    "dec_make": make_dec,
                    "dec_model": model_dec,
                    "dec_engine": vin_info.get("engine"),
                }
            )

        return rows_out

    except Exception as e:
        st.error(f"{yard_name} (Budget U Pull It) error: {e}")
        return []

def card_to_row(card, yard_name, slug, query, want_drive, search_url):
    text = " ".join(card.get_text(" ", strip=True).split())

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

    # AWD/FWD detection (LKQ only, by text)
    drive = ""
    if want_drive:
        for kw in ["AWD", "4WD", "4x4", "FWD", "RWD"]:
            if re.search(rf"\b{kw}\b", text, re.I):
                drive = kw
                break

    return {
        "yard": yard_name,
        "slug": slug,
        "query": query,
        "title": title,
        "link": link,
        "date_found": date_found,
        "drivetrain": drive,
        "raw_text": text,
    }


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

    # link from card
    link = ""
    a = card.find("a", href=True)
    if a:
        link = a["href"]
        if link.startswith("/"):
            link = "https://www.pyp.com" + link

    # fallback if image/CDN or missing
    if (
        not link
        or "cdn.lkqcorp.com" in link
        or re.search(r"\.(?:jpe?g|png|gif)(?:\?|$)", link, re.IGNORECASE)
        or "/inventory/" not in link
    ):
        link = search_url

    # title
    title = ""
    for tag in ["h1", "h2", "h3", "h4"]:
        h = card.find(tag)
        if h:
            title = h.get_text(" ", strip=True)
            break
    if not title:
        title = text[:80]

    date_found = normalize_date(text)

    drive = ""
    if want_drive:
        for kw in ["AWD", "4WD", "4x4", "FWD", "RWD"]:
            if re.search(rf"\b{kw}\b", text, re.I):
                drive = kw
                break

    return {
        "yard": yard_name,
        "slug": slug,
        "query": query,
        "title": title,
        "link": link,
        "date_found": date_found,
        "drivetrain": drive,
        "raw_text": text,
    }


def scan_yard(yard_name, slug, query, want_drive):
    # Special-case Budget U Pull It
    if slug == "budgetupullit":
        return scan_budget_upullit(yard_name, query, want_drive)

    # Special-case Central Florida Pick & Pay
    if slug == "centralfloridapickandpay":
        return scan_central_pickandpay(yard_name, query, want_drive)

    # DEFAULT path = LKQ yards (PYP)
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

        # refine link per row for LKQ yards (not Budget / CFPP)
        base_search = clean_query_for_search(query)
        if (
            base_search
            and rows
            and slug not in ("budgetupullit", "centralfloridapickandpay")
        ):
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

st.title("LKQ Florida Inventory Scraper v7")
st.write("Search multiple LKQ Pick-Your-Part Florida yards at once.")

yards = load_yards()
yard_names = [y["name"] for y in yards]
yard_map = {y["name"]: y for y in yards}

st.sidebar.header("Yards")
default_enabled = [y["name"] for y in yards if y.get("enabled")]
selected_yards = st.sidebar.multiselect(
    "Choose yards", yard_names, default=default_enabled
)

want_drive = st.sidebar.checkbox("Flag AWD/FWD", True)
limit = st.sidebar.number_input("Max display rows", 5, 1000, 200)

st.sidebar.markdown("---")
st.sidebar.caption("Add or edit yards in yards_config.json")

st.subheader("Search Queries")

default_text = """2011-2013 Kia Sorento AWD
2011-2013 Saturn S: SL2, SW2, SC2
2009-2012 Mazda 6 2.5L
"""

queries_raw = st.text_area("Enter one query per line:", default_text, height=150)
queries = [q.strip() for q in queries_raw.splitlines() if q.strip()]

uploaded = st.file_uploader("Or upload CSV with a 'query' column", type="csv")
if uploaded is not None:
    try:
        df_up = pd.read_csv(uploaded)
        if "query" in df_up.columns:
            queries = [
                str(x).strip()
                for x in df_up["query"].dropna().tolist()
                if str(x).strip()
            ]
        else:
            st.error("CSV must have a 'query' column.")
    except Exception as e:
        st.error(f"Error reading CSV: {e}")

# expand variants (Option A multi-variety handling)
queries = expand_variant_lines(queries)

if st.button("Scan Now"):
    if not selected_yards:
        st.error("Choose at least one yard.")
    elif not queries:
        st.error("Enter at least one query.")
    else:
        all_rows = []
        total = len(selected_yards) * len(queries)
        step = 0
        prog = st.progress(0.0)

        for yname in selected_yards:
            yard = yard_map[yname]
            slug = yard["slug"]
            for q in queries:
                rows = scan_yard(yname, slug, q, want_drive)
                all_rows.extend(rows)
                step += 1
                prog.progress(step / total)

        if not all_rows:
            st.warning("No results found. Try broader queries or check yard slugs.")
        else:
            df = pd.DataFrame(all_rows)

        if "vin" in df.columns:
            df = df.drop_duplicates(subset=["yard", "vin"])
        else:
            df = df.drop_duplicates(subset=["link"])
            if len(df) > limit:
                st.info(f"Showing first {limit} of {len(df)} rows (total: {len(df)}).")
                df_show = df.head(limit)
            else:
                df_show = df

            st.dataframe(df_show, use_container_width=True)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download CSV",
                data=csv,
                file_name="lkq_results_v7.csv",
                mime="text/csv",
            )
