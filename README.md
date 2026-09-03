# Vintage Background Remover

Lokales Windows-/Python-Tool zum automatischen Freistellen von Kleidungsstücken und anderen Produktfotos. Die Ausgabe wird als **PNG mit transparentem Hintergrund** gespeichert.

## Schnellstart: wirklich nur ein Ordner

1. Repository als ZIP herunterladen und entpacken.
2. `START_HIER.bat` doppelklicken.
3. Beim ersten Start werden Python-Umgebung, Pakete und das BiRefNet-Modell eingerichtet.
4. Danach Bilder in **`REIN_HIER`** legen.
5. Die freigestellten PNGs erscheinen automatisch in **`FREIGESTELLT`**.
6. Das schwarze Fenster offen lassen, solange der Sofort-Modus laufen soll.

Nach der Ersteinrichtung bleibt das KI-Modell im Watch-Mode geladen. Dadurch muss es nicht für jedes Bild neu gestartet werden.

## Welche Bildformate?

Das Programm entscheidet nach **Bildinhalt**, nicht nur nach Dateiendung. Alles, was Pillow bzw. `pillow-heif` lesen kann, wird verarbeitet. Typische Formate:

- JPG / JPEG / JFIF
- PNG
- WEBP
- BMP / DIB
- TIFF / TIF
- GIF (erster Frame)
- HEIC / HEIF
- AVIF, sofern vom lokalen HEIF-Backend unterstützt
- PPM / PGM / PBM / PNM
- ICO
- viele weitere von Pillow lesbare Rasterformate

Die Ausgabe ist unabhängig vom Eingabeformat immer PNG.

**Nicht gemeint mit „jedes Format“:** Vektorformate wie SVG, Office-Dateien, PDFs oder Kamera-RAW-Formate sind keine normalen Rasterfotos und werden nicht pauschal unterstützt. Für Reselling-Fotos sind die üblichen Handy-/Kameraformate abgedeckt, insbesondere HEIC von iPhones.

## Komfort-Dateien

- `START_HIER.bat` – richtet beim ersten Start alles ein und überwacht `REIN_HIER` dauerhaft.
- `ORDNER_EINMAL_VERARBEITEN.bat` – verarbeitet den aktuellen Inhalt einmal und beendet sich danach.
- `BILDER_HIER_DRAUFZIEHEN.bat` – Bilder per Drag & Drop auf die BAT-Datei ziehen.
- `INSTALLIEREN_ODER_REPARIEREN.bat` – setzt die lokale Python-Umgebung komplett neu auf.

## Ausgabe

Beispiel:

```text
REIN_HIER/
  nike_shirt.heic
  umbro_jacke.jpg

FREIGESTELLT/
  nike_shirt_freigestellt.png
  umbro_jacke_freigestellt.png
```

Der Hintergrund ist standardmäßig transparent. Das sichtbare Produkt wird automatisch zugeschnitten und bekommt einen kleinen transparenten Rand.

## CLI

```powershell
python background_remover.py foto.jpg output.png
python background_remover.py REIN_HIER FREIGESTELLT --recursive
python background_remover.py REIN_HIER FREIGESTELLT --watch --recursive
python background_remover.py REIN_HIER FREIGESTELLT --canvas 1600 --margin 0.06
python background_remover.py foto.jpg output.png --json
```

## Modell und lokale Verarbeitung

Standard ist `birefnet-general` über `rembg`. Das Bild wird lokal auf dem Rechner verarbeitet. Beim ersten Start wird das Modell heruntergeladen und danach lokal gecacht.

## CPU / GPU

Standardmäßig wird die CPU-Version aus `requirements.txt` installiert. Für NVIDIA/CUDA gibt es zusätzlich `requirements-gpu.txt`.

## Für spätere n8n-Integration

Das Python-Script ist absichtlich nicht an n8n gekoppelt. Claude Code kann später entweder die CLI mit `--json` aufrufen oder das Modul direkt einbinden. Exit-Code `0` bedeutet Erfolg.

## Lizenzhinweis

Der Wrapper-Code in diesem Repository steht unter MIT-Lizenz. Externe Python-Pakete und Modellgewichte haben jeweils eigene Lizenzen; vor kommerziellem Einsatz die Bedingungen des verwendeten Modells prüfen.
