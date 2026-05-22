# Incoming

Sem nahrávej nové prostory, které ještě nejsou zařazené v databázi.

## Kam dávat nové prostory

Každý nový prostor vlož jako samostatnou složku do:

```text
incoming/new_venues/
```

Doporučený název složky:

```text
Město - Název prostoru
```

Příklady:

```text
incoming/new_venues/Praha - Divadlo Example/
incoming/new_venues/Žilina, Dom kultúry Example/
incoming/new_venues/DK Example !BLACKLIST!/
```

Do složky můžeš rovnou nahrát PDF, DOCX, Pages, RTF, fotky a další podklady. Nemusíš je ručně třídit podle dokumentů a fotek, to udělá organizační skript.

## Jak se nové prostory zařadí

1. `tools/import_inventory.py` načte složky z `incoming/new_venues` do databáze.
2. `tools/organize_archive.py --apply` je přesune do výsledného archivu:

```text
venues/CZ/mesto/prostor/
venues/SK/mesto/prostor/
venues/_blacklisted/CZ/mesto/prostor/
```

Uvnitř prostoru se soubory uloží do:

```text
source/documents/
source/photos/
source/other/
notes/
exports/
```

Typ prostoru zůstává v databázi, cesta je záměrně podle země a města.

