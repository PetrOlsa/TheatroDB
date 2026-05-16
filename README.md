# TheatroDB

Webová prezentace databáze divadelních a kulturních prostorů.

## Online prezentace

GitHub Pages používá root soubor:

```text
index.html
```

Online verze nepublikuje lokální fotografie a technické dokumenty. Ty zůstávají pouze v lokální pracovní databázi a archivu.

Data v HTML jsou generovaná ze SQLite databáze:

```bash
python3 tools/generate_presentation.py
```

## Struktura

- `index.html` - online prezentace pro GitHub Pages.
- `presentation/` - lokální kopie prezentace a poznámky.
- `venues/` - zdrojové soubory prostorů podle země a města.
- `database/` - SQLite databáze a schéma.
- `tools/` - import, organizace archivu a generování HTML.
- `incoming/new_venues/` - příchozí složka pro nové nezařazené prostory.
