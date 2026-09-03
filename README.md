# Vintage Background Remover

Lokales Windows-/Python-Tool zum automatischen Freistellen von Kleidungsstücken und anderen Produktfotos. Die Ausgabe wird als **PNG mit transparentem Hintergrund** gespeichert.

## Python-Version

Das Projekt ist jetzt auf **Python 3.14.x** ausgelegt und wird im GitHub-Workflow auch mit Python 3.14 getestet. **Python 3.14.7 ist passend.**

Der Starter bevorzugt automatisch `py -3.14`. Falls der Windows-Python-Launcher nicht vorhanden ist, wird auf `python` zurückgegriffen, sofern dahinter Python 3.14 läuft.

Wichtig: Die veröffentlichte Paket-Metadaten von `rembg 2.0.83` erlauben Python 3.14 (`>=3.11,<4.0`). Die README des Upstream-Projekts zeigt teilweise noch die ältere Grenze `<3.14`; maßgeblich für pip ist die aktuelle Paket-Metadaten.

## Schnellstart

1. Repository als ZIP herunterladen und entpacken.
2. **Python 3.14.x** installieren. Python 3.14.7 ist in Ordnung.
3. Beim Python-Installer nach Möglichkeit den Python Launcher und `Add python.exe to PATH` aktivieren.
4. `START_HIER.bat` doppelklicken.
5. Beim ersten Start werden `.venv`, Pakete und das BiRefNet-Modell eingerichtet.
6. Danach Bilder in **`REIN_HIER`** legen.
7. Die freigestellten PNGs erscheinen automatisch in **`FREIGESTELLT`**.
8. Das schwarze Fenster offen lassen, solange der Sofort-Modus laufen soll.

Wenn bereits eine alte `.venv` mit Python 3.11/3.12/3.13 existiert, erkennt `START_HIER.bat` das und baut die virtuelle Umgebung automatisch neu mit Python 3.14 auf.

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

- `START_HIER.bat` – richtet Python-3.14-Umgebung beim ersten Start ein und überwacht `REIN_HIER` dauerhaft.
- `ORDNER_EINMAL_VERARBEITEN.bat` – verarbeitet den aktuellen Inhalt einmal und beendet sich danach.
- `BILDER_HIER_DRAUFZIEHEN.bat` – Bilder per Drag & Drop auf die BAT-Datei ziehen.
- `INSTALLIEREN_ODER_REPARIEREN.bat` – setzt die lokale Python-3.14-Umgebung komplett neu auf.

## Ausgabe

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

## Abhängigkeiten

CPU-Standard:

- `rembg[cpu]==2.0.83`
- `onnxruntime==1.29.0`
- `watchdog`
- `pillow-heif`

`onnxruntime 1.29.0` wird explizit verwendet, damit ein moderner Python-3.14-kompatibler ONNX-Runtime-Build installiert wird.

Für NVIDIA/CUDA existiert zusätzlich `requirements-gpu.txt` mit `onnxruntime-gpu==1.29.0`. Dafür müssen NVIDIA-Treiber/CUDA/cuDNN zur verwendeten Runtime passen.

## Modell und lokale Verarbeitung

Standard ist `birefnet-general` über `rembg`. Das Bild wird lokal auf dem Rechner verarbeitet. Beim ersten Start wird das Modell heruntergeladen und danach lokal gecacht.

## GitHub ZIP-Build

Der Workflow unter `.github/workflows/package.yml` richtet Python 3.14 ein, installiert die Abhängigkeiten, kompiliert/importiert das Script testweise und erzeugt erst danach die Windows-ZIP. Dadurch fällt eine kaputte Python-3.14-Abhängigkeit bereits beim Build auf.

## Für spätere n8n-Integration

Das Python-Script ist absichtlich nicht an n8n gekoppelt. Claude Code kann später entweder die CLI mit `--json` aufrufen oder das Modul direkt einbinden. Exit-Code `0` bedeutet Erfolg.

## Lizenzhinweis

Der Wrapper-Code in diesem Repository steht unter MIT-Lizenz. Externe Python-Pakete und Modellgewichte haben jeweils eigene Lizenzen; vor kommerziellem Einsatz die Bedingungen des verwendeten Modells prüfen.
