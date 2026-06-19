import streamlit as st
import pandas as pd
import altair as alt
import io
import zipfile
import xml.etree.ElementTree as ET
from datetime import date

st.set_page_config(page_title="MSafe Non-Moving Stock", page_icon="🏗️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500..700&family=DM+Mono:wght@400;500&family=Inter:wght@400;500;600;700&display=swap');

html, body { background-color: #FFFFFF !important; }

[data-testid="stAppViewContainer"],
[data-testid="stApp"],
[data-testid="stMain"],
.stApp {
    background-color: #FFFFFF !important;
    color: #1A2B3C !important;
}

[data-testid="stHeader"] { background-color: transparent !important; }

.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
    padding-left: 2.2rem;
    padding-right: 2.2rem;
    max-width: 100% !important;
}

[data-testid="stMain"] p,
[data-testid="stMain"] span,
[data-testid="stMain"] div,
[data-testid="stMain"] label,
[data-testid="stMain"] li,
[data-testid="stMain"] h1,
[data-testid="stMain"] h2,
[data-testid="stMain"] h3,
[data-testid="stMain"] h4 {
    color: #1A2B3C;
}

[data-testid="stMain"] [data-baseweb="select"] > div,
[data-testid="stMain"] input,
[data-testid="stMain"] textarea {
    background-color: #FFFFFF !important;
    color: #1A2B3C !important;
    border-color: #E5E0D8 !important;
}

[data-baseweb="popover"] [data-baseweb="menu"],
[data-baseweb="popover"] ul,
[role="listbox"] {
    background-color: #FFFFFF !important;
}
[data-baseweb="popover"] [data-baseweb="menu"] li,
[role="listbox"] li,
[role="option"] {
    background-color: #FFFFFF !important;
    color: #1A2B3C !important;
}
[role="option"]:hover, [role="option"][aria-selected="true"] {
    background-color: #F4F1EA !important;
    color: #1A2B3C !important;
}

[data-testid="stDataFrame"] { background-color: #FFFFFF !important; }
[data-testid="stDataFrame"] * { color: #1A2B3C !important; }
[data-testid="stDataFrame"] [data-testid="stDataFrameResizable"] {
    background-color: #FFFFFF !important;
}

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
header[data-testid="stHeader"] { display: none; }

/* ── Sidebar toggle — nuclear option: every possible selector Streamlit
   has ever used for the collapse/expand chevron button, across all
   versions from 1.20 to 1.35+. One of these will always match. ────── */
[data-testid="collapsedControl"],
[data-testid="baseButton-headerNoPadding"],
button[kind="header"],
.st-emotion-cache-1dp5vir,
section[data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarCollapsedControl"] {
    background-color: #1A2B3C !important;
    border-radius: 0 8px 8px 0 !important;
    width: 2rem !important;
    min-height: 3rem !important;
    box-shadow: 3px 0 8px rgba(0,0,0,0.25) !important;
    border: none !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}
[data-testid="collapsedControl"] svg,
[data-testid="baseButton-headerNoPadding"] svg,
[data-testid="stSidebarCollapsedControl"] svg,
button[kind="header"] svg {
    fill: #FFFFFF !important;
    stroke: #FFFFFF !important;
    color: #FFFFFF !important;
}
[data-testid="collapsedControl"]:hover,
[data-testid="stSidebarCollapsedControl"]:hover,
button[kind="header"]:hover {
    background-color: #B5562B !important;
}

/* ── Banner ─────────────────────────────────────────────── */
.banner {
    background: linear-gradient(135deg, #1A2B3C 0%, #0F1B26 100%);
    color: #fff;
    padding: 1.6rem 2.2rem;
    border-radius: 10px;
    margin-bottom: 1.6rem;
}
.banner-title {
    font-family: 'Fraunces', serif;
    font-size: 1.6rem;
    font-weight: 600;
    margin: 0 0 4px 0;
    color: #fff !important;
    line-height: 1.3;
}
.banner .sub {
    font-size: 0.85rem;
    opacity: 0.65;
    font-weight: 400;
    color: #fff !important;
}

/* ── Plain-language explainer strip ───────────────────────── */
.explain-box {
    background: #F4F1EA;
    border-radius: 10px;
    padding: 1rem 1.4rem;
    margin-bottom: 1.4rem;
    font-size: 0.88rem;
    color: #3A3530 !important;
    line-height: 1.55;
    border-left: 4px solid #B5562B;
}
.explain-box * { color: #3A3530 !important; }
.explain-box b { color: #1A2B3C !important; }

/* ── KPI cards ───────────────────────────────────────────── */
.kpi-row { display: flex; gap: 1rem; margin-bottom: 1.6rem; flex-wrap: wrap; }
.kpi {
    background: #fff;
    border: 1px solid #E5E0D8;
    border-left: 4px solid #D8D2C6;
    border-radius: 10px;
    padding: 1.15rem 1.3rem;
    flex: 1;
    min-width: 220px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.kpi .lbl {
    font-size: 0.74rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: #8A8378 !important;
    margin-bottom: 8px;
}
.kpi .val {
    font-family: 'DM Mono', monospace;
    font-size: 2.1rem;
    font-weight: 500;
    color: #1A2B3C !important;
    line-height: 1.05;
    font-variant-numeric: tabular-nums;
}
.kpi .val-name {
    font-family: 'Fraunces', serif;
    font-size: 1.15rem;
    font-weight: 600;
    color: #1A2B3C !important;
    line-height: 1.3;
}
.kpi .sub { font-size: 0.8rem; color: #6B6458 !important; margin-top: 7px; }
.kpi .sub b { color: #3A3530 !important; }
.kpi.danger { border-left-color: #B5562B; }
.kpi.danger .val, .kpi.danger .val-name { color: #B5562B !important; }
.kpi.warn { border-left-color: #C8923A; }
.kpi.warn .val { color: #C8923A !important; }
.kpi.neutral { border-left-color: #4C7A9A; }
.kpi.neutral .val { color: #2D5573 !important; }

/* ── Section headers ───────────────────────────────────────── */
.sec-title {
    font-family: 'Fraunces', serif;
    font-size: 1.15rem;
    font-weight: 600;
    color: #1A2B3C !important;
    background: #F4F1EA;
    padding: 0.55rem 1rem;
    border-radius: 8px;
    margin: 1.8rem 0 0.5rem 0;
}
.sec-sub {
    font-size: 0.82rem;
    color: #6B6458 !important;
    margin-bottom: 0.9rem;
}
.chart-heading {
    font-family: 'Fraunces', serif;
    font-size: 1.05rem;
    font-weight: 700;
    color: #1A2B3C !important;
    margin: 1.3rem 0 0.7rem 0;
}
.chart-caption {
    font-size: 0.8rem;
    font-weight: 600;
    color: #6B6458 !important;
    margin-bottom: 0.4rem;
}

/* ── Severity legend chips ─────────────────────────────────── */
.legend-row { display: flex; gap: 0.6rem; margin-bottom: 1rem; flex-wrap: wrap; }
.chip {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 5px 12px; border-radius: 20px;
    font-size: 0.76rem; font-weight: 600;
}
.chip.c-green  { background: #E3EFE3; color: #2D6A2D !important; }
.chip.c-yellow { background: #FBF0DA; color: #9A6B12 !important; }
.chip.c-orange { background: #FCE4D4; color: #B5562B !important; }
.chip.c-red    { background: #F8D7D7; color: #B02A2A !important; }
.dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.dot.c-green  { background: #4C9A4C; }
.dot.c-yellow { background: #D9A536; }
.dot.c-orange { background: #DD7A40; }
.dot.c-red    { background: #C23B3B; }

/* ── Alert / callout box ──────────────────────────────────── */
.alert-box {
    background: #FCE9E3; border-left: 4px solid #B5562B; border-radius: 0 8px 8px 0;
    padding: 0.85rem 1.1rem; font-size: 0.85rem; color: #6B3119 !important; margin-bottom: 1rem;
}
.alert-box * { color: #6B3119 !important; }

/* ── Sidebar ─────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: #1A2B3C !important;
    min-width: 280px !important;
}
section[data-testid="stSidebar"] * { color: #C7CDD3 !important; }
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #fff !important; font-family: 'Fraunces', serif; font-size: 1rem; }
section[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background-color: #243648 !important;
    color: #fff !important;
    border-color: #354A60 !important;
}
section[data-testid="stSidebar"] input {
    background-color: #243648 !important;
    color: #fff !important;
}
section[data-testid="stSidebar"] [data-baseweb="tag"] {
    background-color: #B5562B !important;
    border-color: #B5562B !important;
}
section[data-testid="stSidebar"] [data-baseweb="tag"] * {
    color: #fff !important;
    fill: #fff !important;
}
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
    background-color: #243648 !important;
    border-color: #354A60 !important;
}
section[data-testid="stSidebar"] [data-testid="stFileUploaderFile"] {
    background-color: #243648 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 4px; background: transparent; }
.stTabs [data-baseweb="tab"] {
    font-weight: 600; font-size: 0.92rem; color: #6B6458 !important;
    background: #F4F1EA; border-radius: 8px 8px 0 0; padding: 0.55rem 1.1rem;
}
.stTabs [aria-selected="true"] {
    color: #1A2B3C !important; background: #fff !important;
    border-bottom: 3px solid #B5562B !important;
}
.stTabs [data-baseweb="tab"] p { color: inherit !important; }

/* Expander headers */
[data-testid="stExpander"] summary { color: #1A2B3C !important; }
</style>
""", unsafe_allow_html=True)

# ── JS: force sidebar toggle button visible regardless of Streamlit version ────
# Polls every 300ms until it finds the button, then styles it permanently.
# This is the only reliable cross-version approach since Streamlit changes
# the data-testid and class names of this button between minor releases.
st.components.v1.html("""
<script>
(function() {
  function styleToggle() {
    // All known selectors across Streamlit versions
    var selectors = [
      '[data-testid="collapsedControl"]',
      '[data-testid="stSidebarCollapsedControl"]',
      'button[data-testid="baseButton-headerNoPadding"]',
      'section[data-testid="stSidebar"] ~ div button',
      '.st-emotion-cache-1dp5vir',
    ];
    var found = false;
    for (var i = 0; i < selectors.length; i++) {
      // Search in parent document (this script runs inside an iframe)
      var els = window.parent.document.querySelectorAll(selectors[i]);
      for (var j = 0; j < els.length; j++) {
        var el = els[j];
        // Only target the actual toggle (it contains a chevron SVG, small button)
        if (el.querySelector('svg') || el.tagName === 'BUTTON') {
          el.style.setProperty('background-color', '#1A2B3C', 'important');
          el.style.setProperty('border-radius', '0 8px 8px 0', 'important');
          el.style.setProperty('min-width', '2rem', 'important');
          el.style.setProperty('min-height', '3rem', 'important');
          el.style.setProperty('box-shadow', '3px 2px 8px rgba(0,0,0,0.3)', 'important');
          el.style.setProperty('border', 'none', 'important');
          var svgs = el.querySelectorAll('svg, path');
          for (var k = 0; k < svgs.length; k++) {
            svgs[k].style.setProperty('fill', '#ffffff', 'important');
            svgs[k].style.setProperty('stroke', '#ffffff', 'important');
            svgs[k].style.setProperty('color', '#ffffff', 'important');
          }
          el.addEventListener('mouseenter', function() {
            this.style.setProperty('background-color', '#B5562B', 'important');
          });
          el.addEventListener('mouseleave', function() {
            this.style.setProperty('background-color', '#1A2B3C', 'important');
          });
          found = true;
        }
      }
    }
    return found;
  }

  // Try immediately, then keep retrying every 300ms for up to 10 seconds
  // (Streamlit renders async so the button may not exist on first run)
  var attempts = 0;
  var interval = setInterval(function() {
    attempts++;
    if (styleToggle() || attempts > 33) {
      clearInterval(interval);
    }
  }, 300);
})();
</script>
""", height=0)


# ── Pure stdlib xlsx reader ────────────────────────────────────────────────────
NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
RID_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def _col_index(ref):
    letters = "".join(ch for ch in ref if ch.isalpha())
    idx = 0
    for ch in letters:
        idx = idx * 26 + (ord(ch.upper()) - ord("A") + 1)
    return idx - 1


def _col_letter(idx):
    letters = ""
    idx += 1
    while idx > 0:
        idx, rem = divmod(idx - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


def _escape_xml(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;"))


def _read_sheet_rows(z, sheet_path, shared):
    with z.open(sheet_path) as f:
        tree = ET.parse(f)
    rows = []
    for row_el in tree.findall(f".//{{{NS}}}row"):
        cells = row_el.findall(f"{{{NS}}}c")
        if not cells:
            rows.append([])
            continue
        max_col = max(_col_index(c.get("r", "A")) for c in cells)
        row_vals = [None] * (max_col + 1)
        for c in cells:
            ci = _col_index(c.get("r", "A1"))
            t = c.get("t", "")
            v_el = c.find(f"{{{NS}}}v")
            val = None
            if v_el is not None and v_el.text is not None:
                if t == "s":
                    try:
                        val = shared[int(v_el.text)]
                    except (IndexError, ValueError):
                        val = v_el.text
                else:
                    try:
                        val = float(v_el.text)
                    except ValueError:
                        val = v_el.text
            row_vals[ci] = val
        rows.append(row_vals)
    return rows


def get_workbook_sheets(file_bytes):
    with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
        names = z.namelist()
        shared = []
        if "xl/sharedStrings.xml" in names:
            with z.open("xl/sharedStrings.xml") as f:
                tree = ET.parse(f)
                for si in tree.findall(f".//{{{NS}}}si"):
                    parts = [t.text or "" for t in si.findall(f".//{{{NS}}}t")]
                    shared.append("".join(parts))

        rid_to_path = {}
        if "xl/_rels/workbook.xml.rels" in names:
            with z.open("xl/_rels/workbook.xml.rels") as f:
                tree = ET.parse(f)
                for rel in tree.findall(f".//{{{REL_NS}}}Relationship"):
                    target = rel.get("Target", "")
                    if target.startswith("worksheets/"):
                        rid_to_path[rel.get("Id")] = "xl/" + target

        sheet_order = []
        with z.open("xl/workbook.xml") as f:
            tree = ET.parse(f)
            for sheet_el in tree.findall(f".//{{{NS}}}sheet"):
                sname = sheet_el.get("name")
                rid = sheet_el.get(f"{{{RID_NS}}}id")
                sheet_order.append((sname, rid))

        result = {}
        for sname, rid in sheet_order:
            path = rid_to_path.get(rid)
            if not path or path not in names:
                continue
            result[sname] = _read_sheet_rows(z, path, shared)
    return result


def to_num(v):
    if v is None:
        return 0.0
    try:
        return float(v)
    except (ValueError, TypeError):
        return 0.0


def extract_full_location_name(header_row, tab_name):
    best = None
    for i, cell in enumerate(header_row):
        if i == 0:
            continue
        if cell and isinstance(cell, str):
            up = cell.upper()
            if any(k in up for k in ["LOCATION", "GODOWN", "FACTORY", "YARD", "DEPOT"]):
                clean = cell
                for s in ["LOCATION _", "LOCATION_", "LOCATION", "GODOWN_", "GODOWN _", "GODOWN"]:
                    clean = clean.replace(s, "").replace(s.lower(), "")
                clean = clean.strip(" _:-")
                if clean:
                    best = clean
                    break
    return best if best else tab_name.strip()


def parse_location_sheet(rows, tab_name):
    if len(rows) < 3:
        return None

    header_row = rows[0]
    location_name = extract_full_location_name(header_row, tab_name)

    data_rows = rows[2:]
    records = []

    for row in data_rows:
        row = list(row) + [None] * max(0, 12 - len(row))
        item_code = row[0]
        if item_code is None or str(item_code).strip() == "":
            break

        records.append({
            "Item Code"   : str(item_code).strip(),
            "Item Name"   : str(row[1]).strip() if row[1] else "",
            "Idle Qty"    : to_num(row[2]),
            "Idle Value"  : to_num(row[3]),
            "Qty_0_60"    : to_num(row[4]),
            "Amt_0_60"    : to_num(row[5]),
            "Qty_60_120"  : to_num(row[6]),
            "Amt_60_120"  : to_num(row[7]),
            "Qty_120_180" : to_num(row[8]),
            "Amt_120_180" : to_num(row[9]),
            "Qty_180_plus": to_num(row[10]),
            "Amt_180_plus": to_num(row[11]),
            "Location"    : location_name,
        })

    if not records:
        return None

    df = pd.DataFrame(records)

    def _age_bucket(r):
        if r["Qty_180_plus"] > 0:
            return "180+ days"
        if r["Qty_120_180"] > 0:
            return "120–180 days"
        if r["Qty_60_120"] > 0:
            return "60–120 days"
        if r["Qty_0_60"] > 0:
            return "0–60 days"
        return "180+ days"

    df["Age Bucket"] = df.apply(_age_bucket, axis=1)
    bucket_rank = {"0–60 days": 0, "60–120 days": 1, "120–180 days": 2, "180+ days": 3}
    df["Age Rank"] = df["Age Bucket"].map(bucket_rank)
    return df


def parse_uploaded_file(file_bytes, filename):
    try:
        sheets = get_workbook_sheets(file_bytes)
    except Exception as e:
        return [], [f"❌ **{filename}**: cannot read file — {e}"]
    if not sheets:
        return [], [f"❌ **{filename}**: no worksheets found."]

    dfs, errs = [], []
    for sheet_name, rows in sheets.items():
        df = parse_location_sheet(rows, sheet_name.strip())
        if df is not None:
            dfs.append(df)
        else:
            errs.append(f"⚠️ Sheet **{sheet_name}** in {filename} had no readable item rows — skipped.")
    return dfs, errs


# ── Minimal stdlib xlsx writer ─────────────────────────────────────────────────
def _sheet_xml(rows):
    out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
           '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
           '<sheetData>']
    for r_idx, row in enumerate(rows, start=1):
        out.append(f'<row r="{r_idx}">')
        for c_idx, val in enumerate(row):
            if val is None or val == "":
                continue
            ref = f"{_col_letter(c_idx)}{r_idx}"
            if isinstance(val, (int, float)):
                out.append(f'<c r="{ref}"><v>{val}</v></c>')
            else:
                out.append(f'<c r="{ref}" t="inlineStr"><is><t xml:space="preserve">{_escape_xml(val)}</t></is></c>')
        out.append("</row>")
    out.append("</sheetData></worksheet>")
    return "".join(out)


def write_xlsx_stdlib(sheets_dict):
    buf = io.BytesIO()
    sheet_names = list(sheets_dict.keys())

    content_types = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>']
    for i in range(len(sheet_names)):
        content_types.append(
            f'<Override PartName="/xl/worksheets/sheet{i+1}.xml" '
            f'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        )
    content_types.append("</Types>")

    root_rels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>',
        '</Relationships>']

    workbook_xml = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">',
        '<sheets>']
    for i, name in enumerate(sheet_names):
        safe_name = _escape_xml(name)[:31]
        workbook_xml.append(f'<sheet name="{safe_name}" sheetId="{i+1}" r:id="rId{i+1}"/>')
    workbook_xml.append("</sheets></workbook>")

    workbook_rels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">']
    for i in range(len(sheet_names)):
        workbook_rels.append(
            f'<Relationship Id="rId{i+1}" '
            f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            f'Target="worksheets/sheet{i+1}.xml"/>'
        )
    workbook_rels.append("</Relationships>")

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", "".join(content_types))
        z.writestr("_rels/.rels", "".join(root_rels))
        z.writestr("xl/workbook.xml", "".join(workbook_xml))
        z.writestr("xl/_rels/workbook.xml.rels", "".join(workbook_rels))
        for i, name in enumerate(sheet_names):
            z.writestr(f"xl/worksheets/sheet{i+1}.xml", _sheet_xml(sheets_dict[name]))
    buf.seek(0)
    return buf


def df_to_rows(df):
    rows = [list(df.columns)]
    for _, r in df.iterrows():
        rows.append([None if pd.isna(v) else v for v in r.tolist()])
    return rows


def horizontal_bar_chart(df, label_col, value_col, accent_color, value_format="₹{:,.0f}"):
    chart_df = df.copy()
    chart_df["_label_full"] = chart_df[label_col].astype(str)
    chart_df["_value_label"] = chart_df[value_col].apply(lambda v: value_format.format(v))

    max_val = chart_df[value_col].max()
    x_scale = alt.Scale(domain=[0, max_val * 1.45])

    longest_label_chars = chart_df["_label_full"].str.len().max()
    label_limit_px = min(max(longest_label_chars * 7, 140), 480)

    bars = alt.Chart(chart_df).mark_bar(color=accent_color, cornerRadiusEnd=3).encode(
        x=alt.X(f"{value_col}:Q", title=None, scale=x_scale,
                axis=alt.Axis(labels=False, grid=False, ticks=False, domain=False)),
        y=alt.Y("_label_full:N", sort="-x", title=None,
                axis=alt.Axis(labelLimit=label_limit_px, labelFontSize=13,
                               labelColor="#1A2B3C", labelFontWeight=500)),
        tooltip=[alt.Tooltip("_label_full:N", title="Item"),
                 alt.Tooltip(f"{value_col}:Q", title="Value", format=",.0f")],
    )
    text = bars.mark_text(
        align="left", dx=8, fontSize=14, fontWeight="bold", color="#1A2B3C",
    ).encode(text="_value_label:N")

    chart = (bars + text).properties(
        height=max(34 * len(chart_df), 140), width="container",
        padding={"top": 6, "right": 12, "bottom": 4, "left": 4}
    ).configure_view(strokeWidth=0, fill="#FAF8F4", clip=False).configure(
        background="#FAF8F4"
    ).configure_axis(
        labelColor="#1A2B3C", titleColor="#1A2B3C"
    ).configure_text(
        color="#1A2B3C"
    )

    st.altair_chart(chart, width="stretch", theme=None)


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏗️ MSafe\nNon-Moving Stock")
    st.markdown("---")
    uploaded = st.file_uploader(
        "Upload inventory file",
        type=["xlsx"],
        accept_multiple_files=True,
        help="ERP export of stock not moved in 60+ days. This dashboard reports on the 120+ day subset only."
    )
    st.markdown("---")
    st.caption(f"MSafe Equipments Pvt Ltd · {date.today().strftime('%d %b %Y')}")

threshold_days = 180
dead_rank_cutoff = 3

# ── Banner ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="banner">
  <div class="banner-title">🏗️ Non-Moving Stock Report</div>
  <div class="sub">Equipment sitting unused across all yards · As of {date.today().strftime('%d %B %Y')}</div>
</div>
""", unsafe_allow_html=True)

if not uploaded:
    st.markdown("""
    <div style="background:#F7F5F2;border:1.5px dashed #C8BFB5;border-radius:10px;
                padding:2.5rem;text-align:center;color:#888;font-size:0.85rem;">
        <b>Upload the ERP non-moving stock file in the sidebar to begin.</b><br><br>
        This file already contains only equipment that hasn't moved in 60+ days —<br>
        this dashboard reports on the 120+ day subset · one tab per yard, or separate files per yard.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

all_dfs, errors = [], []
for f in uploaded:
    dfs, errs = parse_uploaded_file(f.read(), f.name)
    all_dfs.extend(dfs)
    errors.extend(errs)
for e in errors:
    st.warning(e)
if not all_dfs:
    st.error("No usable data found in the uploaded file(s).")
    st.stop()

master = pd.concat(all_dfs, ignore_index=True)
master = master[master["Age Rank"] >= 2].copy()

if master.empty:
    st.success("No items are currently idle 120+ days across the uploaded yards.")
    st.stop()

st.markdown(f"""
<div class="explain-box">
  <b>What you're looking at:</b> every item below is equipment that has been sitting unused
  for at least <b>120 days</b> — it isn't earning rental income. The longer it sits, the more
  it's costing us in locked-up capital. Anything idle <b>{threshold_days}+ days</b> is counted as
  <b>"Dead Stock"</b> — money tied up with no return. This is the company-wide standard used
  throughout this report.
</div>
""", unsafe_allow_html=True)

all_locs = sorted(master["Location"].unique())
sel_locs = st.sidebar.multiselect("Filter yards", all_locs, default=all_locs)
master_v = master[master["Location"].isin(sel_locs)].copy()

master_v["Is Dead"] = master_v["Age Rank"] >= dead_rank_cutoff
dead_v = master_v[master_v["Is Dead"]].copy()

# ── KPIs ───────────────────────────────────────────────────────────────────────
if len(dead_v) > 0:
    worst_product = (
        dead_v.groupby(["Item Code", "Item Name"])
        .agg(Qty=("Idle Qty", "sum"), Value=("Idle Value", "sum"), Yards=("Location", "nunique"))
        .reset_index()
        .sort_values("Value", ascending=False)
        .iloc[0]
    )
    worst_name = worst_product["Item Name"]
    worst_name_short = worst_name if len(worst_name) <= 34 else worst_name[:33] + "…"
    worst_qty = int(worst_product["Qty"])
    worst_value = worst_product["Value"]
    worst_yards = int(worst_product["Yards"])
    worst_yard_note = "1 yard" if worst_yards == 1 else f"{worst_yards} yards"
else:
    worst_name_short, worst_qty, worst_value, worst_yard_note = "—", 0, 0, "—"

total_idle_qty   = int(master_v["Idle Qty"].sum())
total_idle_value = master_v["Idle Value"].sum()
dead_qty         = int(dead_v["Idle Qty"].sum())
dead_value       = dead_v["Idle Value"].sum()
dead_value_pct   = dead_value / total_idle_value * 100 if total_idle_value else 0
dead_skus        = len(dead_v)
locs_ct          = master_v["Location"].nunique()

st.markdown(f"""
<div class="kpi-row">
  <div class="kpi danger">
    <div class="lbl">Worst single product</div>
    <div class="val-name">{worst_name_short}</div>
    <div class="sub">₹{worst_value:,.0f} locked up · <b>{worst_qty:,} units</b> · in {worst_yard_note}</div>
  </div>
  <div class="kpi danger">
    <div class="lbl">Dead stock value (180+ days)</div>
    <div class="val">₹{dead_value/100000:.1f}L</div>
    <div class="sub"><b>{dead_skus} items</b> · {dead_qty:,} units · {dead_value_pct:.0f}% of all non-moving stock</div>
  </div>
  <div class="kpi warn">
    <div class="lbl">Total stock idle 120+ days</div>
    <div class="val">₹{total_idle_value/100000:.1f}L</div>
    <div class="sub"><b>{total_idle_qty:,} units</b> · 120–180d + 180+d combined</div>
  </div>
  <div class="kpi neutral">
    <div class="lbl">Yards reviewed</div>
    <div class="val">{locs_ct}</div>
    <div class="sub"><b>{len(master_v):,} item-lines</b> checked in total</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="legend-row">
  <span class="chip c-orange"><span class="dot c-orange"></span>120–180 days — Needs action</span>
  <span class="chip c-red"><span class="dot c-red"></span>180+ days — Dead stock</span>
</div>
""", unsafe_allow_html=True)

RAG_COLOR = {"120–180 days": "🟠", "180+ days": "🔴"}


def render_age_band_body(band_df, band_label, band_key, accent_color):
    if len(band_df) == 0:
        st.info(f"No items fall in the {band_label.lower()} band.")
        return

    band_qty   = int(band_df["Idle Qty"].sum())
    band_value = band_df["Idle Value"].sum()
    st.markdown(f"""
    <div class="kpi-row" style="margin-bottom:1.1rem;">
      <div class="kpi">
        <div class="lbl">Items in this band</div>
        <div class="val">{len(band_df):,}</div>
        <div class="sub"><b>{band_qty:,} units</b></div>
      </div>
      <div class="kpi">
        <div class="lbl">Value locked up</div>
        <div class="val">₹{band_value/100000:.1f}L</div>
        <div class="sub">in this age band alone</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="chart-heading">Which yard has the most dead inventory</div>', unsafe_allow_html=True)

    yard_units = band_df.groupby("Location")["Idle Qty"].sum().sort_values(ascending=False)
    yard_value = band_df.groupby("Location")["Idle Value"].sum().sort_values(ascending=False)

    yc1, yc2 = st.columns(2)
    with yc1:
        st.markdown('<div class="chart-caption">By units — highest first</div>', unsafe_allow_html=True)
        chart1 = yard_units.reset_index()
        chart1.columns = ["Yard", "Units"]
        horizontal_bar_chart(chart1, "Yard", "Units", accent_color, value_format="{:,.0f} units")
    with yc2:
        st.markdown('<div class="chart-caption">By value (₹) — highest first</div>', unsafe_allow_html=True)
        chart2 = yard_value.reset_index()
        chart2.columns = ["Yard", "Value"]
        horizontal_bar_chart(chart2, "Yard", "Value", accent_color, value_format="₹{:,.0f}")

    yard_table = pd.DataFrame({
        "Yard": yard_value.index,
        "Value ₹": yard_value.values,
    }).merge(
        pd.DataFrame({"Yard": yard_units.index, "Units": yard_units.values}),
        on="Yard"
    ).sort_values("Value ₹", ascending=False)
    yard_table["Value ₹"] = yard_table["Value ₹"].apply(lambda x: f"₹{x:,.0f}")
    yard_table["Units"] = yard_table["Units"].astype(int)
    yard_table.insert(0, "Rank", range(1, len(yard_table) + 1))

    st.dataframe(yard_table[["Rank", "Yard", "Units", "Value ₹"]], width="stretch", hide_index=True)

    st.markdown('<div class="chart-heading">Which product is dead the most</div>', unsafe_allow_html=True)

    prod_grp = band_df.groupby(["Item Code", "Item Name"]).agg(
        Units=("Idle Qty", "sum"),
        Value=("Idle Value", "sum"),
        Yards=("Location", "nunique"),
    ).reset_index()

    prod_units_top = prod_grp.sort_values("Units", ascending=False).head(10)
    prod_value_top = prod_grp.sort_values("Value", ascending=False).head(10)

    pc1, pc2 = st.columns(2)
    with pc1:
        st.markdown('<div class="chart-caption">Top 10 by units — highest first</div>', unsafe_allow_html=True)
        horizontal_bar_chart(prod_units_top, "Item Name", "Units", accent_color, value_format="{:,.0f} units")
    with pc2:
        st.markdown('<div class="chart-caption">Top 10 by value (₹) — highest first</div>', unsafe_allow_html=True)
        horizontal_bar_chart(prod_value_top, "Item Name", "Value", accent_color, value_format="₹{:,.0f}")

    prod_table = prod_grp.sort_values("Value", ascending=False).head(20).copy()
    prod_table["Value ₹"] = prod_table["Value"].apply(lambda x: f"₹{x:,.0f}")
    prod_table["Units"] = prod_table["Units"].astype(int)
    prod_table.insert(0, "Rank", range(1, len(prod_table) + 1))

    st.dataframe(
        prod_table[["Rank", "Item Code", "Item Name", "Yards", "Units", "Value ₹"]].rename(
            columns={"Yards": "# Yards Affected"}
        ),
        width="stretch", hide_index=True
    )

    export_sheets = {
        f"{band_key} - By Yard": df_to_rows(yard_table[["Rank", "Yard", "Units", "Value ₹"]]),
        f"{band_key} - By Product": df_to_rows(
            prod_table[["Rank", "Item Code", "Item Name", "Yards", "Units", "Value ₹"]]
        ),
    }
    buf = write_xlsx_stdlib(export_sheets)
    st.download_button(
        f"⬇️  Download {band_label} report (.xlsx)",
        data=buf,
        file_name=f"MSafe_{band_key}_{date.today()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=f"download_{band_key}",
    )


def _insight_card(icon, headline, body):
    st.markdown(f"""
    <div style="background:#fff; border:1px solid #E5E0D8; border-left:4px solid #B5562B;
                border-radius:10px; padding:1rem 1.2rem; margin-bottom:0.8rem;">
      <div style="font-family:'Fraunces',serif; font-weight:700; font-size:1rem;
                  color:#1A2B3C; margin-bottom:4px;">
        {icon} {headline}
      </div>
      <div style="font-size:0.86rem; color:#3A3530; line-height:1.5;">{body}</div>
    </div>
    """, unsafe_allow_html=True)


def render_analysis_tab(master_v, dead_v, band_120_180, band_180_plus, threshold_days):
    st.markdown('<div class="sec-title">🧭 What this data is telling us</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Auto-generated from the current upload — a starting point for discussion, not a final verdict</div>', unsafe_allow_html=True)

    if len(master_v) == 0:
        st.info("No 120+ day idle stock in the current selection.")
        return

    total_value = master_v["Idle Value"].sum()
    dead_value  = dead_v["Idle Value"].sum()
    n_yards     = master_v["Location"].nunique()

    yard_dead_value  = dead_v.groupby("Location")["Idle Value"].sum().sort_values(ascending=False)
    yard_total_value = master_v.groupby("Location")["Idle Value"].sum().sort_values(ascending=False)

    if len(yard_dead_value) > 0:
        top_yard       = yard_dead_value.index[0]
        top_yard_value = yard_dead_value.iloc[0]
        top_yard_pct   = top_yard_value / dead_value * 100 if dead_value else 0
        top3_pct       = yard_dead_value.head(3).sum() / dead_value * 100 if dead_value else 0
        n_yards_with_dead = (yard_dead_value > 0).sum()
        _insight_card(
            "🏭", f"{top_yard} is the single biggest concentration of dead stock",
            f"It alone accounts for <b>₹{top_yard_value/100000:.1f}L</b> — "
            f"<b>{top_yard_pct:.0f}%</b> of all Dead Stock value across "
            f"{n_yards_with_dead} affected yards. The top 3 yards together hold "
            f"<b>{top3_pct:.0f}%</b> of it."
        )

    if len(dead_v) > 0:
        prod_dead = dead_v.groupby(["Item Code", "Item Name"]).agg(
            Value=("Idle Value", "sum"), Yards=("Location", "nunique")
        ).reset_index().sort_values("Value", ascending=False)
        top_prod      = prod_dead.iloc[0]
        top5_prod_pct = prod_dead.head(5)["Value"].sum() / dead_value * 100 if dead_value else 0
        _insight_card(
            "📦", f"{top_prod['Item Name']} is the single worst product by value",
            f"Responsible for <b>₹{top_prod['Value']:,.0f}</b> of Dead Stock, sitting idle across "
            f"<b>{int(top_prod['Yards'])} yard(s)</b>. Top 5 products together = "
            f"<b>{top5_prod_pct:.0f}%</b> of all Dead Stock value."
        )

    if len(dead_v) > 0:
        cross      = dead_v.groupby(["Item Code", "Item Name"])["Location"].nunique().reset_index(name="Yards")
        multi_yard = cross[cross["Yards"] >= 3]
        if len(multi_yard) > 0:
            _insight_card(
                "🔁", f"{len(multi_yard)} products are dead in 3+ yards simultaneously",
                "When the same item is dead in multiple yards, it's rarely a local problem — "
                "it usually points to overstocking or weak demand company-wide. "
                "See the <b>Repeat Offenders</b> tab."
            )

    if len(band_120_180) > 0:
        tip_value = band_120_180["Idle Value"].sum()
        tip_items = len(band_120_180)
        tip_pct   = tip_value / total_value * 100 if total_value else 0
        _insight_card(
            "⏳", f"₹{tip_value/100000:.1f}L is one step away from becoming Dead Stock",
            f"<b>{tip_items} items</b> are in the 120–180 day band ({tip_pct:.0f}% of total "
            f"tracked value). Without action in the next 1–2 months, this crosses the "
            f"{threshold_days}-day line."
        )

    dead_pct_of_total = dead_value / total_value * 100 if total_value else 0
    _insight_card(
        "💰", f"Dead Stock is {dead_pct_of_total:.0f}% of all tracked idle value",
        f"Across <b>{n_yards} yards</b>, <b>₹{total_value/100000:.1f}L</b> is tied up in "
        f"equipment idle 120+ days. Of that, <b>₹{dead_value/100000:.1f}L</b> has already "
        f"crossed the {threshold_days}-day Dead Stock line."
    )

    st.markdown('<div class="chart-heading">Dead Stock value by yard — where to focus first</div>', unsafe_allow_html=True)
    if len(yard_dead_value) > 0:
        chart_df = yard_dead_value.reset_index()
        chart_df.columns = ["Yard", "Value"]
        horizontal_bar_chart(chart_df, "Yard", "Value", "#B5562B", value_format="₹{:,.0f}")
    else:
        st.info("No Dead Stock (180+ days) in the current selection.")

    st.markdown('<div class="chart-heading">Top 10 worst products by Dead Stock value</div>', unsafe_allow_html=True)
    if len(dead_v) > 0:
        top_prods_chart = (
            dead_v.groupby(["Item Code", "Item Name"])["Idle Value"].sum()
            .sort_values(ascending=False).head(10).reset_index()
        )
        horizontal_bar_chart(top_prods_chart, "Item Name", "Idle Value", "#B5562B", value_format="₹{:,.0f}")
    else:
        st.info("No Dead Stock (180+ days) in the current selection.")


band_120_180  = master_v[master_v["Age Bucket"] == "120–180 days"].copy()
band_180_plus = master_v[master_v["Age Bucket"] == "180+ days"].copy()

tab_analysis, tab_180, tab_120, tab_byyard, tab_repeat = st.tabs([
    "🧭 Analysis", "🔴 180+ Days — Dead Stock", "🟠 120–180 Days — Needs Action",
    "🏭 By Yard (All Bands)", "🔁 Repeat Offenders (All Bands)"
])

with tab_analysis:
    render_analysis_tab(master_v, dead_v, band_120_180, band_180_plus, threshold_days)

with tab_180:
    st.markdown('<div class="sec-title">🔴 180+ Days — Dead Stock</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Money tied up the longest — company-wide write-off candidates</div>', unsafe_allow_html=True)
    render_age_band_body(band_180_plus, "180+ Days — Dead Stock", "180plusdays", "#B5562B")

with tab_120:
    st.markdown('<div class="sec-title">🟠 120–180 Days — Needs Action</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">About to cross into Dead Stock — the window to act is closing</div>', unsafe_allow_html=True)
    render_age_band_body(band_120_180, "120–180 Days — Needs Action", "120-180days", "#C8923A")

with tab_byyard:
    st.markdown('<div class="sec-title">Dead stock, yard by yard</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sec-sub">Worst yards first — based on the {threshold_days}-day cutoff</div>', unsafe_allow_html=True)

    if len(dead_v) == 0:
        st.success(f"No yard currently has stock idle {threshold_days}+ days.")
    else:
        loc_dead = dead_v.groupby("Location").agg(
            Items=("Item Code", "count"),
            Qty=("Idle Qty", "sum"),
            Value=("Idle Value", "sum"),
        ).reset_index()
        loc_all  = master_v.groupby("Location").agg(All_Items=("Item Code", "count")).reset_index()
        loc_dead = loc_dead.merge(loc_all, on="Location")
        loc_dead["% of yard's idle items"] = (loc_dead["Items"] / loc_dead["All_Items"] * 100).round(0)
        loc_dead = loc_dead.sort_values("Value", ascending=False)
        loc_dead["RAG"] = loc_dead["% of yard's idle items"].apply(
            lambda x: "🔴" if x >= 60 else ("🟠" if x >= 35 else ("🟡" if x >= 15 else "🟢"))
        )
        loc_dead["Value ₹"] = loc_dead["Value"].apply(lambda x: f"₹{x:,.0f}")

        st.dataframe(
            loc_dead[["RAG", "Location", "Items", "Qty", "Value ₹", "% of yard's idle items"]].rename(
                columns={"Location": "Yard", "Qty": "Units"}
            ),
            width="stretch", hide_index=True
        )

        st.markdown('<div class="sec-title">Item-level detail per yard</div>', unsafe_allow_html=True)
        for loc in loc_dead["Location"]:
            loc_df = dead_v[dead_v["Location"] == loc].sort_values(
                ["Age Rank", "Idle Value"], ascending=[False, False]
            )
            with st.expander(
                f"📍 {loc}  —  {len(loc_df)} dead items  ·  ₹{loc_df['Idle Value'].sum():,.0f}",
                expanded=False
            ):
                show = loc_df[["Item Code", "Item Name", "Age Bucket", "Idle Qty", "Idle Value"]].copy()
                show["RAG"] = show["Age Bucket"].map(RAG_COLOR)
                show["Idle Value"] = show["Idle Value"].apply(lambda x: f"₹{x:,.0f}")
                show = show.rename(columns={"Idle Qty": "Qty"})
                st.dataframe(
                    show[["RAG", "Item Code", "Item Name", "Age Bucket", "Qty", "Idle Value"]],
                    width="stretch", hide_index=True
                )

with tab_repeat:
    st.markdown('<div class="sec-title">Items dead in many yards at once</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">These point to a company-wide issue — not just one yard\'s problem</div>', unsafe_allow_html=True)

    if len(dead_v) == 0:
        st.success("No dead stock at the current threshold.")
    else:
        cross = dead_v.groupby(["Item Code", "Item Name"]).agg(
            Yards=("Location", "nunique"),
            Yard_List=("Location", lambda x: ", ".join(sorted(x.unique()))),
            Qty=("Idle Qty", "sum"),
            Value=("Idle Value", "sum"),
        ).reset_index().sort_values(["Yards", "Value"], ascending=[False, False])

        multi = cross[cross["Yards"] >= 3]
        if len(multi):
            st.markdown(f"""
            <div class="alert-box">
              <b>{len(multi)} items</b> are dead stock in <b>3 or more yards at the same time.</b>
              Worth reviewing centrally rather than yard by yard.
            </div>
            """, unsafe_allow_html=True)

        cross["RAG"]     = cross["Yards"].apply(lambda x: "🔴" if x >= 5 else ("🟠" if x >= 3 else "🟡"))
        cross["Value ₹"] = cross["Value"].apply(lambda x: f"₹{x:,.0f}")

        st.dataframe(
            cross[["RAG", "Item Code", "Item Name", "Yards", "Yard_List", "Qty", "Value ₹"]].rename(
                columns={"Yards": "# Yards", "Yard_List": "Found In"}
            ),
            width="stretch", hide_index=True
        )

        export_sheets2 = {
            "Repeat Offenders": df_to_rows(
                cross[["Item Code", "Item Name", "Yards", "Yard_List", "Qty", "Value"]]
            )
        }
        buf2 = write_xlsx_stdlib(export_sheets2)
        st.download_button(
            "⬇️  Download this list (.xlsx)",
            data=buf2,
            file_name=f"MSafe_RepeatOffenders_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
