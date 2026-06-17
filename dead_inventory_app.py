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

/* ══════════════════════════════════════════════════════════════════
   FORCE THE WHOLE APP TO A FIXED LIGHT THEME — independent of any
   Streamlit Cloud theme setting, browser dark mode, or system
   preference. Every rule below targets Streamlit's actual root
   containers directly with !important, so this dashboard cannot
   end up dark-background-with-dark-text no matter where it's hosted.
   ══════════════════════════════════════════════════════════════════ */
html, body { background-color: #FFFFFF !important; }

[data-testid="stAppViewContainer"],
[data-testid="stApp"],
[data-testid="stMain"],
.stApp {
    background-color: #FFFFFF !important;
    color: #1A2B3C !important;
}

[data-testid="stHeader"] { background-color: transparent !important; }

/* Every generic text-bearing element in the main content area defaults
   to dark text on the white background above, unless a specific rule
   below (KPI cards, banner, sidebar, etc.) overrides it intentionally. */
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

/* Streamlit's native widgets (selectbox, multiselect, text input, etc.)
   in the main area — force light surfaces so dropdowns/inputs never
   render as dark-on-dark either. */
[data-testid="stMain"] [data-baseweb="select"] > div,
[data-testid="stMain"] input,
[data-testid="stMain"] textarea {
    background-color: #FFFFFF !important;
    color: #1A2B3C !important;
    border-color: #E5E0D8 !important;
}

/* Dataframes / tables */
[data-testid="stDataFrame"] { background-color: #FFFFFF !important; }

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
header[data-testid="stHeader"] { display: none; }
.block-container { padding-top: 1.4rem; max-width: 1200px; }

/* ── Banner ─────────────────────────────────────────────── */
.banner {
    background: linear-gradient(135deg, #1A2B3C 0%, #0F1B26 100%);
    color: #fff;
    padding: 1.6rem 2rem;
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
.explain-box b { color: #1A2B3C !important; }

/* ── KPI cards ─────────────────────────────────────────────── */
.kpi-row { display: flex; gap: 1rem; margin-bottom: 1.6rem; flex-wrap: wrap; }
.kpi {
    background: #fff;
    border: 1px solid #E5E0D8;
    border-radius: 10px;
    padding: 1.1rem 1.3rem;
    flex: 1;
    min-width: 160px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.kpi .lbl {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #8A8378 !important;
    margin-bottom: 6px;
}
.kpi .val { font-family: 'Fraunces', serif; font-size: 1.9rem; font-weight: 600; color: #1A2B3C !important; line-height: 1; }
.kpi .sub { font-size: 0.76rem; color: #9B9488 !important; margin-top: 5px; }
.kpi.danger .val { color: #B5562B !important; }
.kpi.warn .val { color: #C8923A !important; }

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

/* ── Sidebar ───────────────────────────────────────────────── */
section[data-testid="stSidebar"] { background: #1A2B3C !important; }
section[data-testid="stSidebar"] * { color: #C7CDD3 !important; }
section[data-testid="stSidebar"] h2 { color: #fff !important; font-family: 'Fraunces', serif; font-size: 1rem; }
section[data-testid="stSidebar"] [data-baseweb="select"] > div,
section[data-testid="stSidebar"] input {
    background-color: #243648 !important;
    color: #fff !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 4px; background: transparent; }
.stTabs [data-baseweb="tab"] {
    font-weight: 600; font-size: 0.88rem; color: #6B6458 !important;
    background: #F4F1EA; border-radius: 8px 8px 0 0; padding: 0.5rem 1rem;
}
.stTabs [aria-selected="true"] {
    color: #1A2B3C !important; background: #fff !important;
    border-bottom: 3px solid #B5562B !important;
}
.stTabs [data-baseweb="tab"] p { color: inherit !important; }
</style>
""", unsafe_allow_html=True)



# ── Pure stdlib xlsx reader (no openpyxl / xlrd needed for reading) ───────────
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
    """Full godown name sits somewhere in row 1, often column L or N. Column A
    is skipped — at least one real sheet had a stray/incorrect label there."""
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
    """
    Every row in this export is ALREADY non-moving stock (60+ days idle) —
    the file itself is pre-filtered by the ERP. The age buckets tell us HOW
    idle each item is, not whether it's idle at all.

    Columns (0-indexed):
      2: Total Qty (= idle qty)   3: Total Amt (= idle value)
      4/5  : Qty/Amt idle 0-60 days
      6/7  : Qty/Amt idle 60-120 days
      8/9  : Qty/Amt idle 120-180 days
      10/11: Qty/Amt idle 180+ days   (present on most tabs, missing on 3 of them)
    """
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
            break  # totals row reached

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

    # Worst (oldest) bucket an item falls into — this is its age classification
    def _age_bucket(r):
        if r["Qty_180_plus"] > 0:
            return "180+ days"
        if r["Qty_120_180"] > 0:
            return "120–180 days"
        if r["Qty_60_120"] > 0:
            return "60–120 days"
        if r["Qty_0_60"] > 0:
            return "0–60 days"
        return "180+ days"  # fallback: NF2/NF3/NU4 sheets with no >180 column,
                              # qty present but bucket columns all blank/zero

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


# ── Minimal stdlib xlsx writer (no openpyxl needed) ────────────────────────────
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
    """
    A clean, easy-to-read horizontal bar chart — longest bar on top, value labels
    printed at the end of each bar, sized up for readability. Uses Altair (ships
    with Streamlit, no extra install) instead of st.bar_chart, since vertical bars
    with long product names become unreadable.

    Full item/yard names are always shown — never truncated — since directors
    need to read the exact product name without hovering for a tooltip.

    Value labels sit just past the end of each bar, on the chart's own fixed
    light background — this keeps them legible regardless of whether the
    surrounding page is light or dark themed, and avoids the failure case where
    a short bar (e.g. Punjab: ₹44,650) is too thin to fit text inside it next to
    a long bar (e.g. Mumbai: ₹1.2 Cr).
    """
    chart_df = df.copy()
    chart_df["_label_full"] = chart_df[label_col].astype(str)
    chart_df["_value_label"] = chart_df[value_col].apply(lambda v: value_format.format(v))

    # Pad the x-axis scale so labels printed past the bar end always have room
    # and never get clipped at the right edge of the chart.
    max_val = chart_df[value_col].max()
    x_scale = alt.Scale(domain=[0, max_val * 1.35])

    # Widest label in this chart determines how much left-side room to reserve —
    # long product names (up to ~70 characters) need real width, not a fixed cap.
    longest_label_chars = chart_df["_label_full"].str.len().max()
    label_limit_px = min(max(longest_label_chars * 7, 140), 480)

    bars = alt.Chart(chart_df).mark_bar(color=accent_color, cornerRadiusEnd=3).encode(
        x=alt.X(f"{value_col}:Q", title=None, scale=x_scale,
                axis=alt.Axis(labels=False, grid=False, ticks=False, domain=False)),
        y=alt.Y("_label_full:N", sort="-x", title=None,
                axis=alt.Axis(labelLimit=label_limit_px, labelFontSize=13,
                               labelColor="#3A3530", labelFontWeight=500)),
        tooltip=[alt.Tooltip("_label_full:N", title="Item"),
                 alt.Tooltip(f"{value_col}:Q", title="Value", format=",.0f")],
    )
    text = bars.mark_text(
        align="left", dx=8, fontSize=14, fontWeight="bold", color="#1A2B3C",
    ).encode(text="_value_label:N")

    chart = (bars + text).properties(
        height=max(34 * len(chart_df), 140)
    ).configure_view(strokeWidth=0, fill="#FAF8F4").configure(background="#FAF8F4")

    st.altair_chart(chart, width="stretch", theme=None)


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏗️ MSafe\nNon-Moving Stock")
    st.markdown("---")
    uploaded = st.file_uploader(
        "Upload inventory file",
        type=["xlsx"],
        accept_multiple_files=True,
        help="ERP export of stock not moved in 60+ days. One tab per yard, or separate files per yard."
    )
    st.markdown("---")
    st.caption(f"MSafe Equipments Pvt Ltd · {date.today().strftime('%d %b %Y')}")

# Dead Stock standard, fixed at 180+ days — the threshold directors use.
# Age Rank: 0 = 0-60d, 1 = 60-120d, 2 = 120-180d, 3 = 180+d.
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
        one tab per yard, or separate files per yard, both work.
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

# ── Explainer strip — plain language for directors ────────────────────────────
st.markdown(f"""
<div class="explain-box">
  <b>What you're looking at:</b> every item below is equipment that has been sitting unused
  for at least 60 days — it isn't earning rental income. The longer it sits, the more it's
  costing us in locked-up capital. Anything idle <b>{threshold_days}+ days</b> is counted as
  <b>"Dead Stock"</b> — money tied up with no return. This is the company-wide standard used
  throughout this report.
</div>
""", unsafe_allow_html=True)

# ── Location filter ────────────────────────────────────────────────────────────
all_locs = sorted(master["Location"].unique())
sel_locs = st.sidebar.multiselect("Filter yards", all_locs, default=all_locs)
master_v = master[master["Location"].isin(sel_locs)].copy()

master_v["Is Dead"] = master_v["Age Rank"] >= dead_rank_cutoff
dead_v = master_v[master_v["Is Dead"]].copy()

# ── KPIs ────────────────────────────────────────────────────────────────────────
# KPI 1 — the single product that has been sitting the longest (180+ days bucket),
# aggregated across every yard it appears in. This answers "what's our worst single
# write-off candidate" directly, by both quantity and value.
if len(dead_v) > 0:
    worst_product = (
        dead_v.groupby(["Item Code", "Item Name"])
        .agg(Qty=("Idle Qty", "sum"), Value=("Idle Value", "sum"), Yards=("Location", "nunique"))
        .reset_index()
        .sort_values("Value", ascending=False)
        .iloc[0]
    )
    worst_name = worst_product["Item Name"]
    worst_name_short = worst_name if len(worst_name) <= 30 else worst_name[:29] + "…"
    worst_qty = int(worst_product["Qty"])
    worst_value = worst_product["Value"]
    worst_yards = int(worst_product["Yards"])
    worst_yard_note = "in 1 yard" if worst_yards == 1 else f"combined across {worst_yards} yards"
else:
    worst_name_short, worst_qty, worst_value, worst_yard_note = "—", 0, 0, ""

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
    <div class="val" style="font-size:1.1rem; line-height:1.3;">{worst_name_short}</div>
    <div class="sub">{worst_qty:,} units · ₹{worst_value:,.0f} · {worst_yard_note}</div>
  </div>
  <div class="kpi danger">
    <div class="lbl">Total Dead Stock (180+ days)</div>
    <div class="val">₹{dead_value/100000:.1f}L</div>
    <div class="sub">{dead_skus} items · {dead_qty:,} units · {dead_value_pct:.0f}% of all non-moving stock</div>
  </div>
  <div class="kpi warn">
    <div class="lbl">All Non-Moving Stock (0–60d + 60–120d + 120–180d + 180+d combined)</div>
    <div class="val">₹{total_idle_value/100000:.1f}L</div>
    <div class="sub">{total_idle_qty:,} units · every age bucket added together</div>
  </div>
  <div class="kpi">
    <div class="lbl">Yards Reviewed</div>
    <div class="val">{locs_ct}</div>
    <div class="sub">{len(master_v)} item-lines checked</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Severity legend ────────────────────────────────────────────────────────────
st.markdown("""
<div class="legend-row">
  <span class="chip c-green"><span class="dot c-green"></span>0–60 days — Just starting to slow</span>
  <span class="chip c-yellow"><span class="dot c-yellow"></span>60–120 days — Worth watching</span>
  <span class="chip c-orange"><span class="dot c-orange"></span>120–180 days — Needs action</span>
  <span class="chip c-red"><span class="dot c-red"></span>180+ days — Dead stock</span>
</div>
""", unsafe_allow_html=True)

RAG_COLOR = {"0–60 days": "🟢", "60–120 days": "🟡", "120–180 days": "🟠", "180+ days": "🔴"}


# ── Tabs ────────────────────────────────────────────────────────────────────────
tab0, tab1, tab2 = st.tabs([
    "📊 Director Summary", "🏭 By Yard", "🔁 Repeat Offenders"
])


# ══════════════════════════════════════════════
# TAB 0 — Director Summary (split by age band)
# ══════════════════════════════════════════════
with tab0:
    st.markdown('<div class="sec-title">Dead stock, split by how long it has been sitting</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Two age bands below — each shows which yard is worst, and which product is worst, by units and by value</div>', unsafe_allow_html=True)

    def render_age_band_section(band_df, band_label, band_key, accent_color):
        """Renders: yard chart+table, then product chart+table, both units & value, high to low."""
        st.markdown(f'<div class="sec-title">{band_label}</div>', unsafe_allow_html=True)

        if len(band_df) == 0:
            st.info(f"No items fall in the {band_label.lower()} band.")
            return

        band_qty   = int(band_df["Idle Qty"].sum())
        band_value = band_df["Idle Value"].sum()
        st.markdown(f"""
        <div class="kpi-row" style="margin-bottom:1.1rem;">
          <div class="kpi">
            <div class="lbl">Items in this band</div>
            <div class="val">{len(band_df)}</div>
            <div class="sub">{band_qty:,} units</div>
          </div>
          <div class="kpi">
            <div class="lbl">Value locked up</div>
            <div class="val">₹{band_value/100000:.1f}L</div>
            <div class="sub">in this age band alone</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Yard-wise: units and value, both high to low ───────────────────────
        st.markdown(f'<div class="chart-heading">Which yard has the most dead inventory</div>', unsafe_allow_html=True)

        yard_units = band_df.groupby("Location")["Idle Qty"].sum().sort_values(ascending=False)
        yard_value = band_df.groupby("Location")["Idle Value"].sum().sort_values(ascending=False)

        yc1, yc2 = st.columns(2)
        with yc1:
            st.caption("By units — highest first")
            chart1 = yard_units.reset_index()
            chart1.columns = ["Yard", "Units"]
            horizontal_bar_chart(chart1, "Yard", "Units", accent_color, value_format="{:,.0f} units")
        with yc2:
            st.caption("By value (₹) — highest first")
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

        # ── Product-wise: units and value, both high to low ────────────────────
        st.markdown(f'<div class="chart-heading">Which product is dead the most</div>', unsafe_allow_html=True)

        prod_grp = band_df.groupby(["Item Code", "Item Name"]).agg(
            Units=("Idle Qty", "sum"),
            Value=("Idle Value", "sum"),
            Yards=("Location", "nunique"),
        ).reset_index()

        prod_units_top = prod_grp.sort_values("Units", ascending=False).head(10)
        prod_value_top = prod_grp.sort_values("Value", ascending=False).head(10)

        pc1, pc2 = st.columns(2)
        with pc1:
            st.caption("Top 10 by units — highest first")
            horizontal_bar_chart(prod_units_top, "Item Name", "Units", accent_color, value_format="{:,.0f} units")
        with pc2:
            st.caption("Top 10 by value (₹) — highest first")
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

        # ── Download for this band ──────────────────────────────────────────────
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

    band_120_180 = master_v[master_v["Age Bucket"] == "120–180 days"].copy()
    band_180_plus = master_v[master_v["Age Bucket"] == "180+ days"].copy()

    render_age_band_section(band_180_plus, "🔴 180+ Days — Dead Stock", "180plusdays", "#B5562B")
    st.markdown("<hr style='margin:2rem 0; border-color:#E5E0D8;'>", unsafe_allow_html=True)
    render_age_band_section(band_120_180, "🟠 120–180 Days — Needs Action", "120-180days", "#C8923A")


# ══════════════════════════════════════════════
# TAB 1 — By Yard
# ══════════════════════════════════════════════
with tab1:
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
        loc_all = master_v.groupby("Location").agg(All_Items=("Item Code", "count")).reset_index()
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
            loc_df = dead_v[dead_v["Location"] == loc].sort_values(["Age Rank", "Idle Value"], ascending=[False, False])
            with st.expander(f"📍 {loc}  —  {len(loc_df)} dead items  ·  ₹{loc_df['Idle Value'].sum():,.0f}", expanded=False):
                show = loc_df[["Item Code", "Item Name", "Age Bucket", "Idle Qty", "Idle Value"]].copy()
                show["RAG"] = show["Age Bucket"].map(RAG_COLOR)
                show["Idle Value"] = show["Idle Value"].apply(lambda x: f"₹{x:,.0f}")
                show = show.rename(columns={"Idle Qty": "Qty"})
                st.dataframe(
                    show[["RAG", "Item Code", "Item Name", "Age Bucket", "Qty", "Idle Value"]],
                    width="stretch", hide_index=True
                )


# ══════════════════════════════════════════════
# TAB 2 — Repeat Offenders (multi-yard dead items)
# ══════════════════════════════════════════════
with tab2:
    st.markdown('<div class="sec-title">Items dead in many yards at once</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">These point to a company-wide issue with the item — not just one yard\'s problem</div>', unsafe_allow_html=True)

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
              This usually means the item itself is overstocked or losing demand company-wide —
              worth reviewing centrally rather than yard by yard.
            </div>
            """, unsafe_allow_html=True)

        cross["RAG"] = cross["Yards"].apply(lambda x: "🔴" if x >= 5 else ("🟠" if x >= 3 else "🟡"))
        cross["Value ₹"] = cross["Value"].apply(lambda x: f"₹{x:,.0f}")

        st.dataframe(
            cross[["RAG", "Item Code", "Item Name", "Yards", "Yard_List", "Qty", "Value ₹"]].rename(
                columns={"Yards": "# Yards", "Yard_List": "Found In"}
            ),
            width="stretch", hide_index=True
        )

        export_sheets2 = {"Repeat Offenders": df_to_rows(cross[["Item Code","Item Name","Yards","Yard_List","Qty","Value"]])}
        buf2 = write_xlsx_stdlib(export_sheets2)
        st.download_button(
            "⬇️  Download this list (.xlsx)",
            data=buf2,
            file_name=f"MSafe_RepeatOffenders_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


# ══════════════════════════════════════════════
