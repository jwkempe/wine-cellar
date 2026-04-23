import datetime
import streamlit.components.v1 as components
import pandas as pd


def escape_js(s: str) -> str:
    """Escape a string for safe embedding in a JS string literal."""
    if not s:
        return ""
    return str(s).replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace("\n", " ").replace("\r", "")


def render_wine_table(df: pd.DataFrame, current_year: int | None = None) -> None:
    if current_year is None:
        current_year = datetime.datetime.now().year

    rows_html = ""
    for _, row in df.iterrows():
        vintage_str = "NV" if pd.isna(row["vintage"]) else str(int(row["vintage"]))
        wine_name_str = str(row["wine_name"]) if row["wine_name"] and not pd.isna(row["wine_name"]) else ""
        appellation_str = str(row["appellation"]) if row["appellation"] and not pd.isna(row["appellation"]) else ""
        varietal_str = str(row["varietal"]) if row["varietal"] and not pd.isna(row["varietal"]) else ""
        region_str = str(row["region"]) if row["region"] and not pd.isna(row["region"]) else ""
        expert_notes_str = str(row["expert_notes"]) if row["expert_notes"] and not pd.isna(row["expert_notes"]) else ""
        your_notes_str = str(row["your_notes"]) if row["your_notes"] and not pd.isna(row["your_notes"]) else ""

        display_name = str(row["winery"])
        if wine_name_str:
            display_name += f" {wine_name_str}"

        sub_parts = [p for p in [varietal_str or appellation_str, region_str] if p]
        sub_line = " · ".join(sub_parts)

        try:
            df_val = int(row["drink_from"])
            db_val = int(row["drink_by"])
            window_str = f"{df_val} – {db_val}"
            is_ready = df_val <= current_year <= db_val
            window_pct = max(0, min(100, int((db_val - current_year) / max(db_val - df_val, 1) * 100))) if is_ready else 0
        except (TypeError, ValueError):
            window_str = "—"
            is_ready = False
            window_pct = 0
            df_val = ""
            db_val = ""

        ready_badge = '<span class="badge-ready">Ready</span>' if is_ready else ""

        if pd.isna(row["your_rating"]):
            rating_html = '<span style="color:rgba(240,234,216,0.2);font-size:0.75rem;letter-spacing:0.1em;">Not rated</span>'
            rating_detail_html = '<span class="detail-empty">Not yet rated</span>'
        else:
            score = float(row["your_rating"])
            bar_width = int((score / 100) * 72)
            rating_html = f'<span class="rating-bar-bg"><span class="rating-bar-fill" style="width:{bar_width}px;"></span></span><span class="rating-score">{score:.0f}</span>'
            big_bar_width = int((score / 100) * 120)
            rating_detail_html = f'<div class="detail-rating-row"><span class="detail-rating-score">{score:.0f}</span><span class="detail-rating-bar-bg"><span class="detail-rating-bar-fill" style="width:{big_bar_width}px;"></span></span></div>'

        vintage_sort = str(int(row["vintage"])) if not pd.isna(row["vintage"]) else "0"
        window_sort = str(int(row["drink_from"])) if not pd.isna(row["drink_from"]) else "0"
        rating_sort = str(float(row["your_rating"])) if not pd.isna(row["your_rating"]) else "0"
        qty = int(row["quantity"]) if not pd.isna(row["quantity"]) else 0

        expert_html = f'<p class="detail-notes-text">{escape_js(expert_notes_str)}</p>' if expert_notes_str else '<span class="detail-empty">No expert notes</span>'
        your_notes_html = f'<p class="detail-notes-text">{escape_js(your_notes_str)}</p>' if your_notes_str else '<span class="detail-empty">No tasting notes added yet</span>'

        window_bar_html = ""
        if df_val and db_val:
            window_bar_html = f'''
            <div class="detail-window-bar-wrap">
                <div class="detail-window-bar-bg">
                    <div class="detail-window-bar-fill" style="width:{window_pct}%"></div>
                </div>
                <div class="detail-window-labels">
                    <span>{df_val}</span><span>{db_val}</span>
                </div>
            </div>
            '''

        detail_html = f'''
        <div class="detail-panel">
            <div class="detail-grid">
                <div class="detail-col">
                    <div class="detail-section-label">Expert Notes</div>
                    {expert_html}
                    <div class="detail-section-label" style="margin-top:1.25rem;">Your Notes</div>
                    {your_notes_html}
                    <div class="detail-section-label" style="margin-top:1.25rem;">Your Rating</div>
                    {rating_detail_html}
                </div>
                <div class="detail-col">
                    <div class="detail-section-label">Drink Window</div>
                    <div class="detail-window-str">{"Ready now" if is_ready else window_str}</div>
                    {window_bar_html}
                    <a class="detail-pairing-btn" href="#" onclick="return false;">Get Food Pairings &#8594;</a>
                </div>
            </div>
        </div>
        '''

        rows_html += f"""<tr class="data-row" onclick="toggleDetail(this)">
            <td class="td-expand">&#9654;</td>
            <td class="td-vintage" data-sort="{vintage_sort}">{vintage_str}</td>
            <td class="td-wine" data-sort="{display_name}">
                <span class="wine-name">{display_name}{ready_badge}</span>
                <span class="wine-meta">{sub_line}</span>
            </td>
            <td class="td-qty" data-sort="{qty}">{qty}</td>
            <td class="td-window" data-sort="{window_sort}">{window_str}</td>
            <td class="td-rating" data-sort="{rating_sort}">{rating_html}</td>
        </tr>
        <tr class="detail-row" style="display:none;">
            <td colspan="6">{detail_html}</td>
        </tr>"""

    table_id = f"winetable_{abs(hash(str(df.index.tolist()))) % 100000}"
    table_height = max(200, min(len(df) * 62 + 60, 1200))

    components.html(f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400&family=DM+Sans:wght@300;400;500&display=swap');
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: transparent; font-family: 'DM Sans', sans-serif; }}
    .wine-table-wrap {{ width: 100%; overflow-x: auto; }}
    .wine-table {{ width: 100%; border-collapse: collapse; font-family: 'DM Sans', sans-serif; font-size: 0.82rem; }}
    .wine-table thead tr {{ border-bottom: 1px solid #2e2a25; }}
    .wine-table thead th {{
        font-size: 0.62rem; letter-spacing: 0.18em; text-transform: uppercase;
        color: rgba(240,234,216,0.3); font-weight: 400; padding: 0 1.25rem 0.75rem 0;
        text-align: left; white-space: nowrap; cursor: pointer; user-select: none;
        transition: color 0.15s;
    }}
    .wine-table thead th:first-child {{ width: 20px; cursor: default; }}
    .wine-table thead th:hover {{ color: rgba(240,234,216,0.7); }}
    .wine-table thead th.sort-asc, .wine-table thead th.sort-desc {{ color: #c9a84c; }}
    .sort-arrow {{ display: inline-block; margin-left: 0.35rem; opacity: 0; font-size: 0.55rem; transition: opacity 0.15s; }}
    .wine-table thead th:hover .sort-arrow {{ opacity: 0.4; }}
    .wine-table thead th.sort-asc .sort-arrow, .wine-table thead th.sort-desc .sort-arrow {{ opacity: 1; }}
    .data-row {{ border-bottom: 1px solid #1f1c18; transition: background-color 0.15s; cursor: pointer; }}
    .data-row:hover {{ background-color: #1c1917; }}
    .data-row.expanded {{ background-color: #1c1917; border-bottom: none; }}
    .detail-row td {{ padding: 0; border-bottom: 1px solid #2e2a25; }}
    .wine-table tbody td {{ padding: 0.9rem 1.25rem 0.9rem 0; color: rgba(240,234,216,0.85); vertical-align: middle; white-space: nowrap; }}
    .td-expand {{ width: 20px; color: rgba(240,234,216,0.2); font-size: 0.5rem; transition: transform 0.2s, color 0.2s; padding-right: 0.5rem !important; }}
    .data-row.expanded .td-expand {{ transform: rotate(90deg); color: #c9a84c; }}
    .td-wine {{ white-space: normal; min-width: 200px; }}
    .wine-name {{ font-family: 'Cormorant Garamond', serif; font-size: 1rem; font-weight: 400; color: #f0ead8; display: block; line-height: 1.3; }}
    .wine-meta {{ font-size: 0.7rem; color: rgba(240,234,216,0.35); display: block; margin-top: 0.15rem; letter-spacing: 0.04em; }}
    .td-vintage {{ font-family: 'Cormorant Garamond', serif; font-size: 1.05rem; font-weight: 300; color: rgba(240,234,216,0.45); min-width: 56px; }}
    .td-qty {{ text-align: center; color: rgba(240,234,216,0.45); min-width: 40px; }}
    .td-window {{ min-width: 110px; color: rgba(240,234,216,0.4); font-size: 0.78rem; letter-spacing: 0.02em; }}
    .td-rating {{ min-width: 130px; }}
    .rating-bar-bg {{ background: #2e2a25; border-radius: 1px; height: 2px; width: 72px; display: inline-block; vertical-align: middle; margin-right: 0.6rem; position: relative; top: -1px; }}
    .rating-bar-fill {{ background: linear-gradient(90deg, #c9a84c, #e2c47a); border-radius: 1px; height: 2px; display: block; }}
    .rating-score {{ font-size: 0.8rem; color: rgba(240,234,216,0.55); vertical-align: middle; }}
    .badge-ready {{ display: inline-block; font-size: 0.55rem; letter-spacing: 0.14em; text-transform: uppercase; color: #5a8a5a; border: 1px solid rgba(90,138,90,0.5); border-radius: 2px; padding: 0.1rem 0.35rem; margin-left: 0.5rem; vertical-align: middle; position: relative; top: -1px; }}
    .detail-panel {{ padding: 1.5rem 1.5rem 1.75rem 2rem; background: #161412; animation: fadeIn 0.2s ease; }}
    @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(-4px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    .detail-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 2.5rem; }}
    .detail-section-label {{ font-size: 0.6rem; letter-spacing: 0.2em; text-transform: uppercase; color: rgba(240,234,216,0.25); margin-bottom: 0.5rem; }}
    .detail-notes-text {{ font-size: 0.85rem; line-height: 1.7; color: rgba(240,234,216,0.6); font-style: italic; white-space: normal; max-width: 480px; }}
    .detail-empty {{ font-size: 0.78rem; color: rgba(240,234,216,0.2); letter-spacing: 0.05em; }}
    .detail-rating-row {{ display: flex; align-items: center; gap: 0.75rem; margin-top: 0.25rem; }}
    .detail-rating-score {{ font-family: 'Cormorant Garamond', serif; font-size: 1.8rem; font-weight: 300; color: #c9a84c; line-height: 1; }}
    .detail-rating-bar-bg {{ background: #2e2a25; border-radius: 1px; height: 3px; width: 120px; display: inline-block; }}
    .detail-rating-bar-fill {{ background: linear-gradient(90deg, #c9a84c, #e2c47a); border-radius: 1px; height: 3px; display: block; }}
    .detail-window-str {{ font-family: 'Cormorant Garamond', serif; font-size: 1.4rem; font-weight: 300; color: rgba(240,234,216,0.7); margin-bottom: 0.75rem; }}
    .detail-window-bar-wrap {{ margin-top: 0.25rem; }}
    .detail-window-bar-bg {{ background: #2e2a25; border-radius: 1px; height: 3px; width: 100%; max-width: 180px; margin-bottom: 0.4rem; }}
    .detail-window-bar-fill {{ background: #5a8a5a; border-radius: 1px; height: 3px; transition: width 0.4s ease; }}
    .detail-window-labels {{ display: flex; justify-content: space-between; max-width: 180px; font-size: 0.65rem; color: rgba(240,234,216,0.25); letter-spacing: 0.08em; }}
    .detail-pairing-btn {{ display: inline-block; margin-top: 1.5rem; font-size: 0.7rem; letter-spacing: 0.15em; text-transform: uppercase; color: #c9a84c; text-decoration: none; border: 1px solid rgba(201,168,76,0.3); border-radius: 2px; padding: 0.45rem 0.9rem; transition: all 0.2s; }}
    .detail-pairing-btn:hover {{ background: rgba(201,168,76,0.1); border-color: #c9a84c; }}
    </style>
    </head>
    <body>
    <div class="wine-table-wrap">
        <table class="wine-table" id="{table_id}">
            <thead>
                <tr>
                    <th></th>
                    <th data-col="1" data-type="num">Vintage<span class="sort-arrow">&#9650;</span></th>
                    <th data-col="2" data-type="str">Wine<span class="sort-arrow">&#9650;</span></th>
                    <th data-col="3" data-type="num" style="text-align:center;">Qty<span class="sort-arrow">&#9650;</span></th>
                    <th data-col="4" data-type="num">Drink Window<span class="sort-arrow">&#9650;</span></th>
                    <th data-col="5" data-type="num">Rating<span class="sort-arrow">&#9650;</span></th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div>
    <script>
    function toggleDetail(row) {{
        row.classList.toggle("expanded");
        var detailRow = row.nextElementSibling;
        if (detailRow && detailRow.classList.contains("detail-row")) {{
            detailRow.style.display = detailRow.style.display === "none" ? "table-row" : "none";
        }}
    }}
    (function() {{
        var table = document.getElementById("{table_id}");
        if (!table) return;
        var sortState = {{ col: null, asc: true }};
        function getCellValue(row, colIdx) {{
            var cell = row.cells[colIdx];
            return cell ? (cell.getAttribute("data-sort") || cell.innerText.trim()) : "";
        }}
        function sortTable(th, colIdx, colType) {{
            var tbody = table.querySelector("tbody");
            var allRows = Array.from(tbody.querySelectorAll("tr"));
            var pairs = [];
            for (var i = 0; i < allRows.length; i++) {{
                if (allRows[i].classList.contains("data-row")) {{
                    pairs.push([allRows[i], allRows[i+1]]);
                }}
            }}
            var asc = (sortState.col === colIdx) ? !sortState.asc : true;
            pairs.sort(function(a, b) {{
                var aVal = getCellValue(a[0], colIdx);
                var bVal = getCellValue(b[0], colIdx);
                if (colType === "num") {{
                    aVal = parseFloat(aVal) || 0;
                    bVal = parseFloat(bVal) || 0;
                    return asc ? aVal - bVal : bVal - aVal;
                }} else {{
                    return asc ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
                }}
            }});
            pairs.forEach(function(pair) {{
                tbody.appendChild(pair[0]);
                tbody.appendChild(pair[1]);
            }});
            table.querySelectorAll("thead th[data-col]").forEach(function(h) {{
                h.classList.remove("sort-asc", "sort-desc");
                var arrow = h.querySelector(".sort-arrow");
                if (arrow) arrow.innerHTML = "&#9650;";
            }});
            th.classList.add(asc ? "sort-asc" : "sort-desc");
            var arrow = th.querySelector(".sort-arrow");
            if (arrow) arrow.innerHTML = asc ? "&#9650;" : "&#9660;";
            sortState = {{ col: colIdx, asc: asc }};
        }}
        table.querySelectorAll("thead th[data-col]").forEach(function(th) {{
            th.addEventListener("click", function() {{
                sortTable(th, parseInt(th.getAttribute("data-col")), th.getAttribute("data-type"));
            }});
        }});
    }})();
    </script>
    </body>
    </html>
    """, height=table_height, scrolling=True)
