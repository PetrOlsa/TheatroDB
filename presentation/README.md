# TheatroDB Presentation

Statická HTML prezentace databáze. Soubor `index.html` je generovaný z SQLite databáze a obsahuje vložená data, takže jde otevřít přímo v prohlížeči.

Generátor vytváří dvě verze:

- `../index.html` - root stránka pro GitHub Pages.
- `index.html` - lokální kopie v této složce.

Po změnách v databázi obnov prezentaci příkazem:

```bash
python3 tools/generate_presentation.py
```
