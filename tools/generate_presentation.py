#!/usr/bin/env python3
from __future__ import annotations

import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "theatrodb.sqlite"
OUTPUT_PATH = ROOT / "presentation" / "index.html"
ROOT_OUTPUT_PATH = ROOT / "index.html"

TYPE_LABELS = {
    "cinema": "Kino",
    "concert_hall": "Koncertní sál",
    "cultural_house": "Kulturní dům",
    "outdoor_theatre": "Venkovní divadlo",
    "sokol_hall": "Sokolovna",
    "theatre": "Divadlo",
    "unknown": "Nezařazeno",
}


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_rows(conn: sqlite3.Connection, query: str, params: tuple = ()) -> list[dict]:
    return [dict(row) for row in conn.execute(query, params)]


def build_data() -> dict:
    conn = connect()
    venues = fetch_rows(
        conn,
        """
        SELECT
            v.id,
            v.city,
            v.name,
            v.country,
            v.venue_type,
            v.status,
            v.source_folder,
            v.original_source_folder,
            v.web_url,
            vo.source_file_count,
            vo.document_count,
            vo.photo_count
        FROM venues v
        JOIN venue_overview vo ON vo.id = v.id
        ORDER BY v.country, v.city, v.name
        """,
    )

    for venue in venues:
        venue["type_label"] = TYPE_LABELS.get(venue["venue_type"], venue["venue_type"])
        venue["files"] = fetch_rows(
            conn,
            """
            SELECT filename, path, extension, file_kind, size_bytes
            FROM source_files
            WHERE venue_id = ?
            ORDER BY file_kind, filename
            """,
            (venue["id"],),
        )
        venue["web_sources"] = fetch_rows(
            conn,
            """
            SELECT title, url, source_type, note
            FROM web_sources
            WHERE venue_id = ?
            ORDER BY source_type, title
            """,
            (venue["id"],),
        )
        venue["tasks"] = fetch_rows(
            conn,
            """
            SELECT task_type, status, priority
            FROM extraction_tasks
            WHERE venue_id = ?
            ORDER BY priority, task_type
            """,
            (venue["id"],),
        )
        venue["hero_image"] = next(
            (file["path"] for file in venue["files"] if file["file_kind"] == "photo"),
            None,
        )

    return {
        "generated_from": str(DB_PATH.relative_to(ROOT)),
        "venues": venues,
        "type_labels": TYPE_LABELS,
    }


def public_data(data: dict) -> dict:
    safe = json.loads(json.dumps(data, ensure_ascii=False))
    for venue in safe["venues"]:
        venue["hero_image"] = None
        venue["files"] = []
    return safe


def html_template(data: dict, asset_prefix: str, public_mode: bool = False) -> str:
    data_json = json.dumps(data, ensure_ascii=False)
    file_section_title = "Lokální soubory" if public_mode else "Soubory"
    empty_file_text = "Lokální dokumenty a fotografie nejsou v online verzi publikované." if public_mode else "Bez souborů."
    return f"""<!doctype html>
<html lang="cs">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TheatroDB</title>
  <style>
    :root {{
      --bg: #f7f4ef;
      --panel: #ffffff;
      --ink: #252525;
      --muted: #696b70;
      --line: #d8d2c9;
      --accent: #0f766e;
      --accent-dark: #134e4a;
      --warn: #b45309;
      --blue: #234f87;
      --shadow: 0 14px 34px rgba(37, 37, 37, 0.11);
    }}

    * {{ box-sizing: border-box; }}

    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.45;
    }}

    a {{ color: var(--accent-dark); }}

    .shell {{
      min-height: 100vh;
      display: grid;
      grid-template-columns: 360px minmax(0, 1fr);
    }}

    aside {{
      position: sticky;
      top: 0;
      height: 100vh;
      overflow: auto;
      border-right: 1px solid var(--line);
      background: #fcfaf6;
      padding: 24px;
    }}

    main {{
      min-width: 0;
      padding: 28px;
    }}

    .brand {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 22px;
    }}

    h1 {{
      margin: 0;
      font-size: 30px;
      line-height: 1.1;
      letter-spacing: 0;
    }}

    .db-pill {{
      border: 1px solid var(--line);
      color: var(--muted);
      padding: 6px 8px;
      font-size: 12px;
      white-space: nowrap;
      background: #fff;
    }}

    .stats {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      margin-bottom: 20px;
    }}

    .stat {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      min-height: 72px;
    }}

    .stat strong {{
      display: block;
      font-size: 24px;
      line-height: 1;
      margin-bottom: 8px;
    }}

    .stat span {{
      color: var(--muted);
      font-size: 13px;
    }}

    .controls {{
      display: grid;
      gap: 12px;
      margin: 20px 0;
    }}

    input,
    select {{
      width: 100%;
      min-height: 40px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--ink);
      padding: 8px 10px;
      font: inherit;
    }}

    .venue-list {{
      display: grid;
      gap: 8px;
    }}

    .venue-button {{
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      color: var(--ink);
      text-align: left;
      padding: 12px;
      cursor: pointer;
      display: grid;
      gap: 6px;
    }}

    .venue-button[aria-current="true"] {{
      border-color: var(--accent);
      box-shadow: inset 3px 0 0 var(--accent);
    }}

    .venue-name {{
      font-weight: 700;
      overflow-wrap: anywhere;
    }}

    .venue-meta {{
      color: var(--muted);
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      font-size: 13px;
    }}

    .detail {{
      display: grid;
      grid-template-columns: minmax(0, 1.1fr) minmax(300px, 0.9fr);
      gap: 22px;
      align-items: start;
    }}

    .hero {{
      min-height: 260px;
      border-bottom: 1px solid var(--line);
      background: #1f2933;
      position: relative;
      overflow: hidden;
    }}

    .hero img {{
      width: 100%;
      height: 340px;
      object-fit: cover;
      display: block;
      opacity: 0.92;
    }}

    .hero.empty {{
      display: grid;
      place-items: center;
      color: #eef2f3;
      background:
        linear-gradient(135deg, #243b53 0%, #506b5f 54%, #8a6f48 100%);
    }}

    .hero-title {{
      position: absolute;
      left: 26px;
      right: 26px;
      bottom: 22px;
      color: #fff;
      text-shadow: 0 2px 16px rgba(0, 0, 0, 0.45);
    }}

    .hero-title h2 {{
      margin: 0 0 8px;
      font-size: 38px;
      line-height: 1.05;
      letter-spacing: 0;
      overflow-wrap: anywhere;
    }}

    .hero-title p {{
      margin: 0;
      font-size: 16px;
    }}

    .section {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
      overflow: hidden;
    }}

    .section-body {{
      padding: 20px;
    }}

    .grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }}

    .fact {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      min-height: 76px;
    }}

    .fact span {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 6px;
    }}

    .fact strong {{
      overflow-wrap: anywhere;
    }}

    .side {{
      display: grid;
      gap: 14px;
    }}

    h3 {{
      font-size: 15px;
      margin: 0 0 12px;
      text-transform: uppercase;
      letter-spacing: 0;
      color: var(--muted);
    }}

    .chips {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}

    .chip {{
      display: inline-flex;
      align-items: center;
      min-height: 28px;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 4px 10px;
      background: #fafafa;
      color: var(--ink);
      font-size: 13px;
    }}

    .chip.warn {{
      border-color: #d6a15e;
      color: var(--warn);
      background: #fff8ed;
    }}

    .file-list,
    .source-list {{
      display: grid;
      gap: 8px;
      margin: 0;
      padding: 0;
      list-style: none;
    }}

    .file-list a,
    .source-list a {{
      display: grid;
      gap: 4px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      background: #fff;
      text-decoration: none;
    }}

    .file-list small,
    .source-list small {{
      color: var(--muted);
    }}

    .empty-text {{
      margin: 0;
      color: var(--muted);
    }}

    @media (max-width: 980px) {{
      .shell {{
        grid-template-columns: 1fr;
      }}

      aside {{
        position: static;
        height: auto;
      }}

      .detail {{
        grid-template-columns: 1fr;
      }}
    }}

    @media (max-width: 620px) {{
      main,
      aside {{
        padding: 16px;
      }}

      .stats,
      .grid {{
        grid-template-columns: 1fr;
      }}

      .hero img {{
        height: 280px;
      }}

      .hero-title h2 {{
        font-size: 29px;
      }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <aside>
      <div class="brand">
        <h1>TheatroDB</h1>
        <span class="db-pill">SQLite</span>
      </div>

      <div class="stats" id="stats"></div>

      <div class="controls">
        <input id="search" type="search" placeholder="Hledat město nebo prostor" autocomplete="off">
        <select id="countryFilter" aria-label="Země"></select>
        <select id="typeFilter" aria-label="Typ prostoru"></select>
      </div>

      <div class="venue-list" id="venueList"></div>
    </aside>

    <main>
      <div id="detail"></div>
    </main>
  </div>

  <script id="theatro-data" type="application/json">{data_json}</script>
  <script>
    const data = JSON.parse(document.getElementById("theatro-data").textContent);
    const assetPrefix = {json.dumps(asset_prefix)};
    const venues = data.venues;
    const state = {{
      selectedId: venues[0]?.id ?? null,
      search: "",
      country: "all",
      type: "all"
    }};

    const fmt = new Intl.NumberFormat("cs-CZ");

    const byId = (id) => venues.find((venue) => venue.id === id);
    const labelFor = (type) => data.type_labels[type] || type;

    function filteredVenues() {{
      const needle = state.search.trim().toLowerCase();
      return venues.filter((venue) => {{
        const haystack = [venue.city, venue.name, venue.country, venue.type_label].join(" ").toLowerCase();
        return (!needle || haystack.includes(needle))
          && (state.country === "all" || venue.country === state.country)
          && (state.type === "all" || venue.venue_type === state.type);
      }});
    }}

    function renderStats(list) {{
      const files = list.reduce((sum, venue) => sum + venue.source_file_count, 0);
      const photos = list.reduce((sum, venue) => sum + venue.photo_count, 0);
      document.getElementById("stats").innerHTML = `
        <div class="stat"><strong>${{fmt.format(list.length)}}</strong><span>prostorů</span></div>
        <div class="stat"><strong>${{fmt.format(files)}}</strong><span>souborů</span></div>
        <div class="stat"><strong>${{fmt.format(photos)}}</strong><span>fotek</span></div>
        <div class="stat"><strong>${{fmt.format(new Set(list.map((v) => v.city)).size)}}</strong><span>měst</span></div>
      `;
    }}

    function renderFilters() {{
      const countries = ["all", ...new Set(venues.map((venue) => venue.country))];
      const types = ["all", ...new Set(venues.map((venue) => venue.venue_type))];
      document.getElementById("countryFilter").innerHTML = countries.map((country) =>
        `<option value="${{country}}">${{country === "all" ? "Všechny země" : country}}</option>`
      ).join("");
      document.getElementById("typeFilter").innerHTML = types.map((type) =>
        `<option value="${{type}}">${{type === "all" ? "Všechny typy" : labelFor(type)}}</option>`
      ).join("");
    }}

    function renderList(list) {{
      const selectedVisible = list.some((venue) => venue.id === state.selectedId);
      if (!selectedVisible) {{
        state.selectedId = list[0]?.id ?? null;
      }}
      document.getElementById("venueList").innerHTML = list.map((venue) => `
        <button class="venue-button" data-id="${{venue.id}}" aria-current="${{venue.id === state.selectedId}}">
          <span class="venue-name">${{venue.city}} · ${{venue.name}}</span>
          <span class="venue-meta">
            <span>${{venue.country}}</span>
            <span>${{venue.type_label}}</span>
            <span>${{venue.source_file_count}} souborů</span>
          </span>
        </button>
      `).join("") || `<p class="empty-text">Nic nenalezeno.</p>`;
    }}

    function fileIcon(file) {{
      if (file.file_kind === "photo") return "Foto";
      if (file.file_kind === "document") return "Dokument";
      return "Soubor";
    }}

    function renderDetail() {{
      const venue = byId(state.selectedId);
      const detail = document.getElementById("detail");
      if (!venue) {{
        detail.innerHTML = `<section class="section"><div class="section-body"><p class="empty-text">Vyber prostor ze seznamu.</p></div></section>`;
        return;
      }}

      const files = venue.files.map((file) => `
        <li>
          <a href="${{assetPrefix}}${{encodeURI(file.path)}}" target="_blank">
            <strong>${{fileIcon(file)}} · ${{file.filename}}</strong>
            <small>${{file.extension.toUpperCase()}} · ${{file.path}}</small>
          </a>
        </li>
      `).join("");

      const sources = venue.web_sources.map((source) => `
        <li>
          <a href="${{source.url}}" target="_blank">
            <strong>${{source.title || source.url}}</strong>
            <small>${{source.source_type}} · ${{source.note || ""}}</small>
          </a>
        </li>
      `).join("");

      const hero = venue.hero_image
        ? `<div class="hero"><img src="${{assetPrefix}}${{encodeURI(venue.hero_image)}}" alt="${{venue.city}} - ${{venue.name}}"><div class="hero-title"><h2>${{venue.city}}</h2><p>${{venue.name}}</p></div></div>`
        : `<div class="hero empty"><div class="hero-title"><h2>${{venue.city}}</h2><p>${{venue.name}}</p></div></div>`;

      detail.innerHTML = `
        <div class="detail">
          <section class="section">
            ${{hero}}
            <div class="section-body">
              <div class="grid">
                <div class="fact"><span>Země</span><strong>${{venue.country}}</strong></div>
                <div class="fact"><span>Typ</span><strong>${{venue.type_label}}</strong></div>
                <div class="fact"><span>Stav</span><strong>${{venue.status}}</strong></div>
                <div class="fact"><span>Dokumenty</span><strong>${{venue.document_count}}</strong></div>
                <div class="fact"><span>Fotky</span><strong>${{venue.photo_count}}</strong></div>
                <div class="fact"><span>ID</span><strong>${{venue.id}}</strong></div>
              </div>
            </div>
          </section>

          <div class="side">
            <section class="section">
              <div class="section-body">
                <h3>Archiv</h3>
                <div class="chips">
                  <span class="chip">${{venue.source_folder}}</span>
                  ${{venue.status === "blacklisted" ? '<span class="chip warn">Blacklist</span>' : ""}}
                </div>
              </div>
            </section>

            <section class="section">
              <div class="section-body">
                <h3>{file_section_title}</h3>
                <ul class="file-list">${{files || '<li class="empty-text">{empty_file_text}</li>'}}</ul>
              </div>
            </section>

            <section class="section">
              <div class="section-body">
                <h3>Webové zdroje</h3>
                <ul class="source-list">${{sources || '<li class="empty-text">Bez webového zdroje.</li>'}}</ul>
              </div>
            </section>
          </div>
        </div>
      `;
    }}

    function render() {{
      const list = filteredVenues();
      renderStats(list);
      renderList(list);
      renderDetail();
    }}

    renderFilters();
    render();

    document.getElementById("search").addEventListener("input", (event) => {{
      state.search = event.target.value;
      render();
    }});

    document.getElementById("countryFilter").addEventListener("change", (event) => {{
      state.country = event.target.value;
      render();
    }});

    document.getElementById("typeFilter").addEventListener("change", (event) => {{
      state.type = event.target.value;
      render();
    }});

    document.getElementById("venueList").addEventListener("click", (event) => {{
      const button = event.target.closest("button[data-id]");
      if (!button) return;
      state.selectedId = Number(button.dataset.id);
      render();
    }});
  </script>
</body>
</html>
"""


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = build_data()
    ROOT_OUTPUT_PATH.write_text(html_template(public_data(data), "", public_mode=True), encoding="utf-8")
    OUTPUT_PATH.write_text(html_template(data, "../"), encoding="utf-8")
    print(f"Generated {ROOT_OUTPUT_PATH}")
    print(f"Generated {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
