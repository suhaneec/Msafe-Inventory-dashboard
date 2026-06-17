import streamlit as st
import pandas as pd
import io
import zipfile
import xml.etree.ElementTree as ET
from datetime import date

st.set_page_config(page_title="MSafe Non-Moving Stock", page_icon="🏗️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500..700&family=DM+Mono:wght@400;500&family=Inter:wght@400;500;600;700&display=swap');

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
.banner h1 {
    font-family: 'Fraunces', serif;
    font-size: 1.6rem;
    font-weight: 600;
    margin: 0 0 4px 0;
}
.banner .sub {
    font-size: 0.85rem;
    opacity: 0.65;
    font-weight: 400;
}

/* ── Plain-language explainer strip ───────────────────────── */
.explain-box {
    background: #F4F1EA;
    border-radius: 10px;
    padding: 1rem 1.4rem;
    margin-bottom: 1.4rem;
    font-size: 0.88rem;
    color: #3A3530;
    line-height: 1.55;
    border-left: 4px solid #B5562B;
}
.explain-box b { color: #1A2B3C; }

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
    color: #8A8378;
    margin-bottom: 6px;
}
.kpi .val { font-family: 'Fraunces', serif; font-size: 1.9rem; font-weight: 600; color: #1A2B3C; line-height: 1; }
.kpi .sub { font-size: 0.76rem; color: #9B9488; margin-top: 5px; }
.kpi.danger .val { color: #B5562B; }
.kpi.warn .val { color: #C8923A; }

/* ── Section headers ───────────────────────────────────────── */
.sec-title {
    font-family: 'Fraunces', serif;
    font-size: 1.15rem;
    font-weight: 600;
    color: #1A2B3C;
    margin: 1.8rem 0 0.3rem 0;
}
.sec-sub {
    font-size: 0.82rem;
    color: #8A8378;
    margin-bottom: 0.9rem;
}

/* ── Severity legend chips ─────────────────────────────────── */
.legend-row { display: flex; gap: 0.6rem; margin-bottom: 1rem; flex-wrap: wrap; }
.chip {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 5px 12px; border-radius: 20px;
    font-size: 0.76rem; font-weight: 600;
}
.chip.c-green  { background: #E3EFE3; color: #2D6A2D; }
.chip.c-yellow { background: #FBF0DA; color: #9A6B12; }
.chip.c-orange { background: #FCE4D4; color: #B5562B; }
.chip.c-red    { background: #F8D7D7; color: #B02A2A; }
.dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.dot.c-green  { background: #4C9A4C; }
.dot.c-yellow { background: #D9A536; }
.dot.c-orange { background: #DD7A40; }
.dot.c-red    { background: #C23B3B; }

/* ── Alert / callout box ──────────────────────────────────── */
.alert-box {
    background: #FCE9E3; border-left: 4px solid #B5562B; border-radius: 0 8px 8px 0;
    padding: 0.85rem 1.1rem; font-size: 0.85rem; color: #6B3119; margin-bottom: 1rem;
}

/* ── Sidebar ───────────────────────────────────────────────── */
section[data-testid="stSidebar"] { background: #1A2B3C; }
section[data-testid="stSidebar"] * { color: #C7CDD3 !important; }
section[data-testid="stSidebar"] h2 { color: #fff !important; font-family: 'Fraunces', serif; font-size: 1rem; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 4px; }
.stTabs [data-baseweb="tab"] { font-weight: 600; font-size: 0.88rem; }
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
    dead_threshold = st.select_slider(
        "Treat as 'Dead Stock' from:",
        options=["60 days", "120 days", "180 days"],
        value="180 days",
        help="Directors typically use 180 days. Move the slider to see the impact at other thresholds."
    )
    st.markdown("---")
    st.caption(f"MSafe Equipments Pvt Ltd · {date.today().strftime('%d %b %Y')}")

threshold_days = int(dead_threshold.split()[0])
threshold_rank_map = {60: 0, 120: 1, 180: 2}  # an item is "dead" if its Age Rank >= this
dead_rank_cutoff = threshold_rank_map[threshold_days]

# ── Banner ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="banner">
  <h1>🏗️ Non-Moving Stock Report</h1>
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
  costing us in locked-up capital. Right now, anything idle <b>{threshold_days}+ days</b> is being
  counted as <b>"Dead Stock"</b> — money tied up with no return. You can adjust this cutoff using
  the slider in the left panel.
</div>
""", unsafe_allow_html=True)

# ── Location filter ────────────────────────────────────────────────────────────
all_locs = sorted(master["Location"].unique())
sel_locs = st.sidebar.multiselect("Filter yards", all_locs, default=all_locs)
master_v = master[master["Location"].isin(sel_locs)].copy()

master_v["Is Dead"] = master_v["Age Rank"] >= dead_rank_cutoff
dead_v = master_v[master_v["Is Dead"]].copy()

# ── KPIs ────────────────────────────────────────────────────────────────────────
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
    <div class="lbl">Dead Stock Value</div>
    <div class="val">₹{dead_value/100000:.1f}L</div>
    <div class="sub">idle {threshold_days}+ days · {dead_value_pct:.0f}% of all non-moving stock</div>
  </div>
  <div class="kpi danger">
    <div class="lbl">Dead Stock Items</div>
    <div class="val">{dead_skus}</div>
    <div class="sub">{dead_qty:,} units across {locs_ct} yards</div>
  </div>
  <div class="kpi warn">
    <div class="lbl">All Non-Moving Stock</div>
    <div class="val">₹{total_idle_value/100000:.1f}L</div>
    <div class="sub">{total_idle_qty:,} units, every age bucket</div>
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
tab0, tab1, tab2, tab3 = st.tabs([
    "📊 Director Summary", "🏭 By Yard", "🔁 Repeat Offenders", "📋 Full Detail"
])


# ══════════════════════════════════════════════
# TAB 0 — Director Summary (charts + top offenders)
# ══════════════════════════════════════════════
with tab0:
    st.markdown('<div class="sec-title">Where is the money stuck?</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Value of dead stock by yard — worst yards first</div>', unsafe_allow_html=True)

    yard_chart_data = dead_v.groupby("Location")["Idle Value"].sum().sort_values(ascending=False)
    if len(yard_chart_data) > 0:
        chart_df = yard_chart_data.reset_index()
        chart_df.columns = ["Yard", "Dead Stock Value"]
        st.bar_chart(chart_df.set_index("Yard"), use_container_width=True, color="#B5562B")
    else:
        st.info(f"No items are idle {threshold_days}+ days at the current threshold.")

    st.markdown('<div class="sec-title">How old is the problem?</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Value of ALL non-moving stock, split by how long it has been sitting</div>', unsafe_allow_html=True)

    age_order = ["0–60 days", "60–120 days", "120–180 days", "180+ days"]
    age_chart_data = master_v.groupby("Age Bucket")["Idle Value"].sum().reindex(age_order).fillna(0)
    age_chart_df = age_chart_data.reset_index()
    age_chart_df.columns = ["Age", "Value"]
    st.bar_chart(age_chart_df.set_index("Age"), use_container_width=True, color="#C8923A")

    if dead_skus > 0:
        st.markdown('<div class="sec-title">Top 15 single biggest write-off candidates</div>', unsafe_allow_html=True)
        st.markdown('<div class="sec-sub">The individual items locking up the most capital, worst first</div>', unsafe_allow_html=True)

        top15 = dead_v.sort_values(["Age Rank", "Idle Value"], ascending=[False, False]).head(15).copy()
        top15["RAG"] = top15["Age Bucket"].map(RAG_COLOR)
        top15["Value"] = top15["Idle Value"].apply(lambda x: f"₹{x:,.0f}")
        top15_disp = top15[["RAG", "Item Code", "Item Name", "Location", "Age Bucket", "Idle Qty", "Value"]].rename(
            columns={"Idle Qty": "Qty", "Location": "Yard"}
        )
        st.dataframe(top15_disp, use_container_width=True, hide_index=True)

        # Download
        export_sheets = {
            "Top 15 Items": df_to_rows(
                top15[["Item Code","Item Name","Location","Age Bucket","Idle Qty","Idle Value"]]
            ),
        }
        buf = write_xlsx_stdlib(export_sheets)
        st.download_button(
            "⬇️  Download this summary (.xlsx)",
            data=buf,
            file_name=f"MSafe_DeadStock_Summary_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


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
            use_container_width=True, hide_index=True
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
                    use_container_width=True, hide_index=True
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
            use_container_width=True, hide_index=True
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
# TAB 3 — Full Detail
# ══════════════════════════════════════════════
with tab3:
    st.markdown('<div class="sec-title">Every non-moving item</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-sub">Search or filter to find a specific item or yard</div>', unsafe_allow_html=True)

    c1, c2 = st.columns([3, 1])
    with c1:
        search = st.text_input("Search item name or code", placeholder="e.g. Prop jack, Scissor lift…")
    with c2:
        age_filter = st.selectbox("Age bucket", ["All"] + age_order)

    view_df = master_v.copy()
    if search:
        mask = (view_df["Item Name"].str.contains(search, case=False, na=False) |
                view_df["Item Code"].str.contains(search, case=False, na=False))
        view_df = view_df[mask]
    if age_filter != "All":
        view_df = view_df[view_df["Age Bucket"] == age_filter]

    view_df = view_df.copy()
    view_df["RAG"] = view_df["Age Bucket"].map(RAG_COLOR)
    view_df["Value"] = view_df["Idle Value"].apply(lambda x: f"₹{x:,.0f}")

    st.dataframe(
        view_df[["RAG", "Location", "Item Code", "Item Name", "Age Bucket", "Idle Qty", "Value", "Age Rank"]]
        .sort_values(["Location", "Age Rank"], ascending=[True, False])
        .drop(columns=["Age Rank"])
        .rename(columns={"Location": "Yard", "Idle Qty": "Qty"})
        .reset_index(drop=True),
        use_container_width=True, hide_index=True
    )
