import streamlit as st
import pandas as pd
import io
import zipfile
import xml.etree.ElementTree as ET
from datetime import date

st.set_page_config(page_title="MSafe Dead Inventory", page_icon="🏗️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
header[data-testid="stHeader"] { display: none; }
.block-container { padding-top: 1.2rem; }
.banner { background: #1E2D3A; color: #fff; padding: 1rem 1.4rem; border-radius: 8px; margin-bottom: 1.2rem; }
.banner h1 { font-size: 1.2rem; font-weight: 600; margin: 0; }
.banner .sub { font-size: 0.75rem; opacity: 0.55; font-family: 'DM Mono', monospace; margin-top: 3px; }
.kpi-row { display: flex; gap: 0.8rem; margin-bottom: 1.2rem; flex-wrap: wrap; }
.kpi { background: #fff; border: 1px solid #E0DBD5; border-radius: 7px; padding: 0.85rem 1.1rem; flex: 1; min-width: 120px; }
.kpi .lbl { font-size: 0.65rem; font-family: 'DM Mono', monospace; text-transform: uppercase; letter-spacing: 0.08em; color: #6A7A88; margin-bottom: 3px; }
.kpi .val { font-size: 1.5rem; font-weight: 600; color: #1E2D3A; line-height: 1; }
.kpi .sub { font-size: 0.68rem; color: #999; margin-top: 3px; }
.kpi.red .val { color: #C84B2F; }
.kpi.amber .val { color: #D97706; }
.sec { font-size: 0.68rem; font-family: 'DM Mono', monospace; text-transform: uppercase;
       letter-spacing: 0.1em; color: #4A5C6A; border-bottom: 1.5px solid #C84B2F;
       padding-bottom: 4px; margin: 1.1rem 0 0.7rem; }
.warn-box { background: #FEF3F0; border-left: 4px solid #C84B2F; border-radius: 0 6px 6px 0;
            padding: 0.6rem 0.9rem; font-size: 0.78rem; color: #7A2E1A; margin-bottom: 0.8rem; }
section[data-testid="stSidebar"] { background: #1E2D3A; }
section[data-testid="stSidebar"] * { color: #B0BEC5 !important; }
section[data-testid="stSidebar"] h2 { color: #fff !important; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)


# ── Pure stdlib xlsx reader (no openpyxl / xlrd needed for reading) ───────────
NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
RID_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def _col_index(ref):
    """Convert Excel column letters (A, B, ..., Z, AA, ...) to 0-based index."""
    letters = "".join(ch for ch in ref if ch.isalpha())
    idx = 0
    for ch in letters:
        idx = idx * 26 + (ord(ch.upper()) - ord("A") + 1)
    return idx - 1


def _read_sheet_rows(z, sheet_path, shared):
    """Read all rows of one worksheet XML into a list of value-lists.
    Each row list is sized to the row's own max column — NOT truncated,
    so labels sitting far to the right (e.g. column L or N) are preserved."""
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
    """
    Returns a dict {sheet_name: row_list} for every sheet/tab in the workbook,
    using only zipfile + xml.etree (Python stdlib — no openpyxl needed).
    """
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
    """
    The full godown/location name is written as a text label somewhere in row 1
    (often column L or N — well to the right of the data columns), e.g.
    'LOCATION _ NOIDA FACTORY 2 NF' or 'GODOWN_BANGLORE'.
    We scan the ENTIRE header row for a cell matching that pattern and clean it up.
    Column A is intentionally skipped — on at least one real sheet it contained a
    stray/incorrect label, while the correct one was further right.
    Falls back to the sheet tab name if nothing is found.
    """
    best = None
    for i, cell in enumerate(header_row):
        if i == 0:
            continue  # skip column A — can contain stray mislabeled text
        if cell and isinstance(cell, str):
            up = cell.upper()
            if any(k in up for k in ["LOCATION", "GODOWN", "FACTORY", "YARD", "DEPOT"]):
                clean = cell
                for s in ["LOCATION _", "LOCATION_", "LOCATION", "GODOWN_", "GODOWN _", "GODOWN"]:
                    clean = clean.replace(s, "").replace(s.lower(), "")
                clean = clean.strip(" _:-")
                if clean:
                    best = clean
                    break  # first match scanning left-to-right after column A
    return best if best else tab_name.strip()


def parse_location_sheet(rows, tab_name):
    """
    Parse one location's row-data into a dataframe.
    Row 0 (header)    : column titles, PLUS the full location label somewhere
                         far to the right (e.g. col L/N) — extracted separately.
    Row 1 (sub-header): Qty / Amount labels per bucket.
    Row 2+            : item data, until the first row with a blank Item Code
                         (= totals row). Everything after that is ignored.

    Bucket columns (0-indexed):
      2: Total Qty   3: Total Amt
      4: Qty 0-60    5: Amt 0-60
      6: Qty 60-120  7: Amt 60-120
      8: Qty 120-180 9: Amt 120-180
      10: Qty >180   11: Amt >180   (present on most location tabs, not all)
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
            break  # totals row reached — stop

        records.append({
            "Item Code"    : str(item_code).strip(),
            "Item Name"    : str(row[1]).strip() if row[1] else "",
            "Total Qty"    : to_num(row[2]),
            "Total Amt"    : to_num(row[3]),
            "Qty_0_60"     : to_num(row[4]),
            "Amt_0_60"     : to_num(row[5]),
            "Qty_60_120"   : to_num(row[6]),
            "Amt_60_120"   : to_num(row[7]),
            "Qty_120_180"  : to_num(row[8]),
            "Amt_120_180"  : to_num(row[9]),
            "Qty_Above_180": to_num(row[10]),
            "Amt_Above_180": to_num(row[11]),
            "Location"     : location_name,
            "Tab"          : tab_name,
        })

    if not records:
        return None

    df = pd.DataFrame(records)
    # Dead = zero movement in BOTH 0-60d and 60-120d buckets
    # (this automatically includes items sitting only in 120-180d or Above-180d)
    df["Is Dead"] = (df["Qty_0_60"] == 0) & (df["Qty_60_120"] == 0)
    return df


def parse_uploaded_file(file_bytes, filename):
    """
    Handles BOTH formats:
    1. Multi-sheet workbook — one tab per location (full name read from row 1)
    2. Single-sheet file — one location (older single-file-per-location format)
    Returns (list_of_dataframes, list_of_errors)
    """
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


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏗️ MSafe\nDead Inventory")
    st.markdown("---")
    uploaded = st.file_uploader(
        "Upload inventory file(s)",
        type=["xlsx"],
        accept_multiple_files=True,
        help="Upload either: one workbook with a tab per location, OR multiple single-location files."
    )
    st.markdown("---")
    st.caption(f"MSafe Equipments Pvt Ltd · {date.today().strftime('%d %b %Y')}")

# ── Banner ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="banner">
  <h1>🏗️ Dead Inventory Intelligence</h1>
  <div class="sub">Zero outward movement in 0–120 days · All locations · {date.today().strftime('%d %b %Y')}</div>
</div>
""", unsafe_allow_html=True)

if not uploaded:
    st.markdown("""
    <div style="background:#F7F5F2;border:1.5px dashed #C8BFB5;border-radius:8px;
                padding:2.5rem;text-align:center;color:#888;font-size:0.83rem;">
        <b>Upload your Vsoft inventory file in the sidebar to begin.</b><br><br>
        Works with a single workbook that has one tab per location (e.g. NF2, BG, HYD…),<br>
        or with separate single-location files uploaded together.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Parse uploads ──────────────────────────────────────────────────────────────
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
dead   = master[master["Is Dead"]].copy()

# ── Location filter ────────────────────────────────────────────────────────────
all_locs = sorted(master["Location"].unique())
sel_locs = st.sidebar.multiselect("Filter locations", all_locs, default=all_locs)
master_v = master[master["Location"].isin(sel_locs)]
dead_v   = dead[dead["Location"].isin(sel_locs)]

# ── KPIs ────────────────────────────────────────────────────────────────────────
total_items  = len(master_v)
dead_items   = len(dead_v)
dead_pct     = dead_items / total_items * 100 if total_items else 0
dead_qty     = int(dead_v["Total Qty"].sum())
dead_amt     = dead_v["Total Amt"].sum()
total_amt    = master_v["Total Amt"].sum()
dead_amt_pct = dead_amt / total_amt * 100 if total_amt else 0
locs_ct      = master_v["Location"].nunique()

st.markdown(f"""
<div class="kpi-row">
  <div class="kpi red">
    <div class="lbl">Dead SKUs</div>
    <div class="val">{dead_items}</div>
    <div class="sub">{dead_pct:.1f}% of {total_items} lines</div>
  </div>
  <div class="kpi red">
    <div class="lbl">Dead Units</div>
    <div class="val">{dead_qty:,}</div>
    <div class="sub">zero movement 0–120d</div>
  </div>
  <div class="kpi amber">
    <div class="lbl">Dead Value</div>
    <div class="val">₹{dead_amt/100000:.2f}L</div>
    <div class="sub">{dead_amt_pct:.1f}% of total value</div>
  </div>
  <div class="kpi">
    <div class="lbl">Total Inv Value</div>
    <div class="val">₹{total_amt/100000:.2f}L</div>
    <div class="sub">{locs_ct} location(s) loaded</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["💀 Dead by Location", "📦 Cross-Location View", "📋 Full Inventory"])


# ══════════════════════════════════
# TAB 1 — Dead by Location
# ══════════════════════════════════
with tab1:
    if len(dead_v) == 0:
        st.success("No dead stock found across selected locations.")
    else:
        st.markdown('<div class="sec">Location Summary</div>', unsafe_allow_html=True)

        loc_dead = dead_v.groupby("Location").agg(
            Dead_SKUs=("Item Code", "count"),
            Dead_Qty=("Total Qty", "sum"),
            Dead_Value=("Total Amt", "sum"),
        ).reset_index()
        loc_total = master_v.groupby("Location").agg(
            Total_SKUs=("Item Code", "count"),
            Total_Value=("Total Amt", "sum"),
        ).reset_index()
        loc_sum = loc_dead.merge(loc_total, on="Location")
        loc_sum["Dead SKU %"]   = (loc_sum["Dead_SKUs"] / loc_sum["Total_SKUs"] * 100).round(1)
        loc_sum["Dead Value %"] = (loc_sum["Dead_Value"] / loc_sum["Total_Value"] * 100).round(1)
        loc_sum["Dead Value ₹"] = loc_sum["Dead_Value"].apply(lambda x: f"₹{x:,.0f}")
        loc_sum["RAG"]          = loc_sum["Dead SKU %"].apply(
            lambda x: "🔴" if x >= 40 else ("🟡" if x >= 20 else "🟢")
        )
        loc_sum = loc_sum.sort_values("Dead_Value", ascending=False)

        st.dataframe(
            loc_sum[["RAG","Location","Dead_SKUs","Dead SKU %","Dead_Qty","Dead Value ₹","Dead Value %"]].rename(
                columns={"Dead_SKUs":"Dead SKUs","Dead_Qty":"Dead Qty (units)"}
            ),
            use_container_width=True, hide_index=True
        )

        st.markdown('<div class="sec">Dead Items per Location</div>', unsafe_allow_html=True)

        for loc in sorted(dead_v["Location"].unique()):
            loc_df = dead_v[dead_v["Location"] == loc].sort_values("Total Amt", ascending=False)
            with st.expander(
                f"📍 {loc}  —  {len(loc_df)} SKUs  ·  {int(loc_df['Total Qty'].sum())} units  ·  ₹{loc_df['Total Amt'].sum():,.0f}",
                expanded=False
            ):
                show = loc_df[["Item Code","Item Name","Total Qty","Total Amt",
                               "Qty_0_60","Qty_60_120","Qty_120_180","Qty_Above_180"]].copy()
                show["Total Amt"] = show["Total Amt"].apply(lambda x: f"₹{x:,.0f}")
                for c in ["Qty_0_60","Qty_60_120","Qty_120_180","Qty_Above_180"]:
                    show[c] = show[c].apply(lambda x: int(x) if x > 0 else "—")
                show = show.rename(columns={
                    "Total Qty":"Qty","Total Amt":"Value",
                    "Qty_0_60":"0–60d","Qty_60_120":"60–120d",
                    "Qty_120_180":"120–180d","Qty_Above_180":">180d"
                })
                st.dataframe(show.reset_index(drop=True), use_container_width=True, hide_index=True)


# ══════════════════════════════════
# TAB 2 — Cross-location
# ══════════════════════════════════
with tab2:
    st.markdown('<div class="sec">Items Dead Across Multiple Locations</div>', unsafe_allow_html=True)

    if len(dead_v) == 0:
        st.success("No dead items.")
    else:
        cross = dead_v.groupby(["Item Code","Item Name"]).agg(
            Locations_Dead=("Location","nunique"),
            Location_Names=("Location", lambda x: ", ".join(sorted(x.unique()))),
            Total_Dead_Qty=("Total Qty","sum"),
            Total_Dead_Value=("Total Amt","sum"),
        ).reset_index().sort_values("Total_Dead_Value", ascending=False)

        multi = cross[cross["Locations_Dead"] > 1]
        if len(multi):
            st.markdown(f"""
            <div class="warn-box">⚠️ <b>{len(multi)} SKUs</b> are dead across 2+ locations simultaneously —
            systemic underutilisation. Review for disposal or redistribution.</div>
            """, unsafe_allow_html=True)

        cross["RAG"]   = cross["Locations_Dead"].apply(lambda x: "🔴" if x>=3 else ("🟡" if x>=2 else "⚪"))
        cross["Value"] = cross["Total_Dead_Value"].apply(lambda x: f"₹{x:,.0f}")

        st.dataframe(
            cross[["RAG","Item Code","Item Name","Locations_Dead","Location_Names","Total_Dead_Qty","Value"]].rename(
                columns={"Locations_Dead":"# Locations","Location_Names":"Dead In","Total_Dead_Qty":"Dead Qty"}
            ),
            use_container_width=True, hide_index=True
        )

        # Download
        st.markdown('<div class="sec">Download</div>', unsafe_allow_html=True)
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            loc_sum.drop(columns=["RAG"]).to_excel(w, sheet_name="Location Summary", index=False)
            dead_v[["Location","Item Code","Item Name","Total Qty","Total Amt",
                    "Qty_0_60","Amt_0_60","Qty_60_120","Amt_60_120",
                    "Qty_120_180","Amt_120_180","Qty_Above_180","Amt_Above_180"]].to_excel(
                w, sheet_name="Dead Items", index=False)
            cross.drop(columns=["RAG","Value"]).to_excel(w, sheet_name="Cross-Location", index=False)
        buf.seek(0)
        st.download_button(
            "⬇️  Download Dead Inventory Report (.xlsx)",
            data=buf,
            file_name=f"MSafe_DeadInventory_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


# ══════════════════════════════════
# TAB 3 — Full inventory
# ══════════════════════════════════
with tab3:
    st.markdown('<div class="sec">Complete Inventory — All Items</div>', unsafe_allow_html=True)

    c1, c2 = st.columns([3,1])
    with c1:
        search = st.text_input("Search item name or code", placeholder="e.g. Prop jack, MSF5SF…")
    with c2:
        show_filter = st.selectbox("Show", ["All","Dead only","Active only"])

    view_df = master_v.copy()
    if search:
        mask = (view_df["Item Name"].str.contains(search, case=False, na=False) |
                view_df["Item Code"].str.contains(search, case=False, na=False))
        view_df = view_df[mask]
    if show_filter == "Dead only":
        view_df = view_df[view_df["Is Dead"]]
    elif show_filter == "Active only":
        view_df = view_df[~view_df["Is Dead"]]

    view_df = view_df.copy()
    view_df["Status"] = view_df["Is Dead"].apply(lambda x: "🔴 Dead" if x else "🟢 Active")
    view_df["Value"]  = view_df["Total Amt"].apply(lambda x: f"₹{x:,.0f}")
    for c in ["Qty_0_60","Qty_60_120","Qty_120_180","Qty_Above_180"]:
        view_df[c] = view_df[c].apply(lambda x: int(x) if x > 0 else "—")

    st.dataframe(
        view_df[["Status","Location","Item Code","Item Name","Total Qty","Value",
                 "Qty_0_60","Qty_60_120","Qty_120_180","Qty_Above_180"]].rename(columns={
            "Total Qty":"Qty","Qty_0_60":"0–60d","Qty_60_120":"60–120d",
            "Qty_120_180":"120–180d","Qty_Above_180":">180d"
        }).sort_values(["Location","Status"]).reset_index(drop=True),
        use_container_width=True, hide_index=True
    )
