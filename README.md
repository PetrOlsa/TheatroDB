# TheatroDB

Webová prezentace databáze divadelních a kulturních prostorů.

## Online prezentace

GitHub Pages používá root soubor:

```text
index.html
```

Online verze odkazuje jen na soubory, které jsou nahrané v tomto repozitáři (podle `git ls-files`). Ostatní fotografie a technické dokumenty zůstávají pouze v lokální pracovní databázi a archivu a na webu se u prostoru jen spočítají.

Data v HTML jsou generovaná ze SQLite databáze:

```bash
python3 tools/generate_presentation.py
```

## Mapa a polohy prostorů

Souřadnice prostorů se udržují v `database/venue_locations.csv` (jeden řádek na prostor podle `slug`). Sloupec `precision` říká, jak přesná poloha je: `exact` (ověřená budova), `approx` (odhad podle adresy) nebo `city` (střed obce). Po úpravě CSV načti polohy do databáze a přegeneruj web:

```bash
python3 tools/import_locations.py
python3 tools/generate_presentation.py
```

Mapa používá knihovnu Leaflet uloženou v `assets/leaflet/` a mapové podklady OpenStreetMap (bez API klíče).

## Struktura

- `index.html` - online prezentace pro GitHub Pages.
- `presentation/` - lokální kopie prezentace a poznámky.
- `venues/` - zdrojové soubory prostorů podle země a města.
- `database/` - SQLite databáze a schéma.
- `tools/` - import, organizace archivu, import poloh a generování HTML.
- `assets/leaflet/` - knihovna Leaflet pro mapu.
- `incoming/new_venues/` - příchozí složka pro nové nezařazené prostory.
