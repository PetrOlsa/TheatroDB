# TheatroDB - první třídění

Tahle složka je pracovní základ pro databázi divadelních a kulturních prostorů. Cíl první fáze je oddělit samotné prostory od dokumentů, fotek, kontaktů, technických údajů a uživatelských poznámek.

## Soubory

- `schema.sql` - návrh SQLite databáze.
- `theatrodb.sqlite` - vygenerovaná databáze po spuštění importu.
- `../tools/import_inventory.py` - import složek a souborů z archivu do databáze.
- `../tools/organize_archive.py` - přesun zdrojových složek do jednotné struktury podle databáze.
- `../incoming/new_venues` - příchozí složka pro nové nezařazené prostory.

## Hlavní členění

- `venues` - budovy/prostory: název, město, země, typ, stav, zdrojová složka.
- `performance_spaces` - jednotlivé sály/scény v rámci prostoru. Zatím se zakládá jedna hlavní scéna, později lze doplnit přední/zadní sál apod.
- `source_files` - všechny původní dokumenty a fotky z archivu.
- `technical_systems` - souhrny techniky podle oblastí: světla, zvuk, video, tahy, elektřina, rigging.
- `equipment_items` - konkrétní kusy vybavení: pulty, reflektory, stmívače, projektory, repro, mikrofony.
- `contacts` - kontaktní osoby, technici, produkce, organizace.
- `access_notes` - dojezd, vykládka, parkování, omezení.
- `user_notes` - volné poznámky z praxe, oddělené od ověřených údajů.
- `web_sources` - ověřené odkazy na oficiální weby a další zdroje.
- `extraction_tasks` - seznam úkolů, co je potřeba z dokumentů nebo webu doplnit.

## Typy prostorů

Z názvů složek se automaticky přiřazují tyto typy:

- `theatre` - divadlo
- `cultural_house` - kulturní dům / dům kultury / DK
- `sokol_hall` - sokolovna
- `cinema` - kino
- `concert_hall` - filharmonie / koncertní sál
- `outdoor_theatre` - venkovní nebo lesní divadlo
- `unknown` - zatím nerozpoznáno

## Stav prostoru

- `active` - běžný prostor.
- `blacklisted` - prostor označený ve složce jako blacklist.

## Další krok

Po inventáři je vhodné postupovat po dávkách:

1. Projít dokumenty a doplnit technické údaje.
2. Doplnit kontakty a odkazy z webu.
3. Vyplnit dojezd, parkování a vykládku.
4. Přidat uživatelské poznámky z praxe.
5. Vytvořit jednoduché vyhledávání nebo formulář nad SQLite databází.

## Doporučená struktura archivu

Nové prostory nahrávej do `incoming/new_venues`, každý prostor jako jednu složku. Import je potom založí v databázi a organizační skript je přesune do hlavního archivu.

Po organizaci jsou zdrojová data ukládána primárně podle země a města. Typ prostoru zůstává v databázi, ne v cestě:

```text
venues/
  CZ/
    mesto/
      prostor/
        source/
          documents/
          photos/
          other/
        notes/
        exports/
        README.md
  SK/
    mesto/
      prostor/
        ...
  _blacklisted/
    CZ/
      mesto/
        prostor/
          ...
```

Databáze drží aktuální cestu v `venues.source_folder`. Původní název složky po přesunu zůstává v `venues.original_source_folder`.
