# Vintage Pricing Workflow – technische Spezifikation für Claude Code

## Ziel

Baue in n8n einen produktionsfähigen Workflow für das Vintage-Reselling:

1. Produktfoto(s) + optional bekannte Größe / Einkaufspreis entgegennehmen.
2. Produkt mit Gemini 3.8 Flash visuell und textuell klassifizieren.
3. Vintage Preis-Master NICHT vollständig an Gemini senden.
4. Kandidaten deterministisch aus dem kompakten `Pricing_Index` vorfiltern.
5. Nur die besten Kandidaten durch Gemini semantisch reranken lassen.
6. Preis mathematisch aus den akzeptierten Comparables berechnen.
7. Zustand nur anhand belegter Zustandsdaten korrigieren.
8. Listingpreis, Quick-Sale-Preis, maximalen Einkaufspreis, Confidence und Warenklasse ausgeben.
9. Jede Entscheidung vollständig in `Pricing_Log` protokollieren.

Der Preis darf niemals frei vom LLM erfunden werden.

---

## Infrastruktur / Datenquellen

### Google Sheet

**Vintage Preis-Master – KI & Analyse**

Spreadsheet ID:

`1m83ZNaSo22VqSHwZZjnarQIObShX4m_PhnZFS9YZns4`

URL:

https://docs.google.com/spreadsheets/d/1m83ZNaSo22VqSHwZZjnarQIObShX4m_PhnZFS9YZns4/edit

### Relevante Tabs

#### `Pricing_Index`

Primäre, kompakte Datenquelle für Pricing. Nicht `Daten` oder `Rohdaten` an das LLM schicken.

Spalten:

- Datensatz_ID
- Shop
- Recherche_Datum
- Status_Kategorie
- Preisart
- Produktname
- Marke
- Kleidungsstück
- Hauptkategorie
- Größe
- Größenart
- Bundweite_Inch
- Innenbein_Inch
- Farbe
- Ära
- Style_Merkmale
- Verein_Team
- Sport_Liga
- Motiv_Kategorie
- Zustand_Grade
- Mangel_Typ
- Mangel_Schwere
- Mangel_Ort
- Mangel_Beschreibung
- Zustand_Verifiziert
- Preis_EUR
- Vergleichspreis_EUR
- Datenqualität
- Match_Key_Streng
- Match_Key_Breit
- Quelle
- Produkt_URL
- Nachfrage_Signal

#### `Pricing_Config`

Alle Gewichte, Grenzwerte und Pricing-Parameter. Werte NICHT im Workflow hart codieren, sondern beim Start laden/cachen.

Wichtige Parameter u. a.:

- max_prefilter_candidates
- max_llm_comparables
- min_exact_matches
- min_strong_matches
- min_fallback_matches
- min_similarity_accept
- manual_review_confidence_below
- Gewichte für Produkttyp, Marke, Verein, Ära, Größe, Style, Farbe, Zustand, Aktualität
- Größen-Multiplikatoren
- recency_half_life_days
- IQR-Ausreißerparameter
- listing_markup
- quick_sale_discount
- target_gross_margin
- selling_fee_pct
- handling_cost_eur
- demand_normalization
- Warenklassen-Schwellenwerte
- condition_min_sample
- condition_min_confidence

#### `Zustandsdaten`

Evidenzbasierte Zustandsabschläge.

Spalten:

- Mangel_Typ
- Mangel_Schwere
- Produktgruppe
- Median_Abschlag_Prozent
- Stichprobe_N
- Quelle
- Confidence
- Stand_Datum
- Hinweis

WICHTIG: Wenn kein belastbarer Eintrag existiert, Abschlag NICHT schätzen. Stattdessen 0 % anwenden und `Manuelle_Pruefung=true` bzw. einen Grund ausgeben.

#### `Pricing_Log`

Jede Preisermittlung append-only protokollieren. Die vorhandenen Spalten verwenden.

#### `Mapping`

Normalisierung für Produkttypen und Vereine/Teams. Vor eigener Interpretation verwenden.

---

## Gemini

Verwende standardmäßig:

`gemini-3.8-flash`

Das Modell unterstützt Bildinput und Structured Outputs.

Gemini übernimmt:
- visuelle Produkterkennung
- semantische Attributerkennung
- Zustandserkennung aus Fotos
- semantisches Reranking bereits vorgefilterter Comparables

Gemini übernimmt NICHT:
- das Durchlesen aller ~30k Datensätze
- freie Preisfindung
- erfundene Zustandsabschläge
- endgültige Mathematik

Thinking standardmäßig niedrig oder mittel. Nur bei schwierigen/unklaren Produkten höher.

---

## Eingabe-JSON

Der Workflow soll mindestens dieses Eingabeformat akzeptieren:

```json
{
  "request_id": "uuid",
  "images": ["<binary-or-url>"],
  "known_size": null,
  "purchase_price_eur": null,
  "source": "telegram|webhook|manual"
}
```

Mehrere Bilder desselben Produkts müssen gemeinsam analysiert werden.

---

## Structured Output – Produkterkennung

Gemini muss ausschließlich strukturiertes JSON liefern, etwa:

```json
{
  "brand": "Adidas",
  "garment_type": "Trainingsjacke",
  "main_category": "Jacken & Mäntel",
  "size": "M",
  "waist_inch": null,
  "inseam_inch": null,
  "color": ["Blau", "Rot"],
  "era": "00s/Y2K",
  "team": "FC Barcelona",
  "league": "Fußball",
  "motif_category": "Sport – Verein/Team",
  "style_features": ["3-Stripes", "embroidered crest"],
  "condition_grade": "B+",
  "defects": [
    {
      "type": "Fadenzieher",
      "severity": "leicht",
      "location": "rechter Ärmel",
      "confidence": 0.88
    }
  ],
  "identification_confidence": 0.91,
  "uncertainties": []
}
```

Keine Attribute erfinden. Unsicheres auf `null` bzw. `uncertainties` setzen.

Bekannte Nutzereingaben wie `known_size` haben Vorrang vor visueller Schätzung.

---

## Normalisierung

Nach Gemini:
1. Marke normalisieren.
2. Produkttyp gegen `Mapping` abgleichen.
3. Größe normalisieren.
4. Jeans W/L separat behandeln.
5. Verein/Team gegen Mapping-Aliase normalisieren.
6. Ära auf bestehende Master-Werte abbilden.
7. Farben normalisieren.
8. unbekannte Werte nicht erfinden.

---

## Kandidaten-Suche

### Grundprinzip

Die 29k+ Datensätze dürfen NICHT an Gemini geschickt werden.

Lade/cache `Pricing_Index` und filtere deterministisch.

Für Produktionsbetrieb bevorzugt:
- `Pricing_Index` regelmäßig in eine n8n Data Table / geeigneten lokalen Cache synchronisieren, sofern die vorhandene n8n-Version das sauber unterstützt.
- Preisabfragen dann gegen diesen Cache.
- Google Sheets bleibt Source of Truth.

Falls Data Tables nicht sinnvoll verfügbar sind, den Pricing_Index mit Google Sheets lesen und im Workflow effizient filtern. Nicht pro Anfrage mehrere vollständige Sheet-Reads durchführen.

### Ausschlüsse vor Scoring

- Preis_EUR fehlt oder <= 0 -> raus
- inkompatibler Produkttyp -> raus
- Digital/Service/Mystery/Gift Card nur mit exakt gleichem Zieltyp
- niedrige Datenqualität nur als Fallback
- bei Jeans W/L nicht mit S/M/L vermischen

### Match-Stufen

#### Tier A – Exact

Bevorzugt:
- Kleidungsstück exakt
- Marke exakt
- Verein exakt, wenn Zielprodukt Verein hat
- Größe exakt
- Ära exakt bzw. kompatibel

Wenn `min_exact_matches` erreicht wird: Tier A als Primärbasis nutzen.

#### Tier B – Strong

- Kleidungsstück exakt
- Marke exakt
- Verein exakt, falls vorhanden
- angrenzende Größe erlaubt
- Ära darf leicht erweitert werden

#### Tier C – Controlled fallback

- Kleidungsstück exakt
- Marke exakt
- Ära/Style möglichst ähnlich
- Team/Liga kontrolliert erweitern

#### Tier D – Market fallback

Nur wenn Datenbasis zu klein:
- identischer Produkttyp
- vergleichbare Marke / Liga / Motiv
- klar geringere Confidence

Maximal `max_prefilter_candidates` Kandidaten an Gemini übergeben.

---

## Deterministischer Similarity Score

Werte aus `Pricing_Config` laden.

Basis:

- Produkttyp
- Marke
- Verein/Team
- Ära
- Größe
- Style
- Farbe
- Zustand
- Aktualität

Wenn ein Merkmal beim Zielprodukt nicht anwendbar/erkannt ist, Gewichte der übrigen anwendbaren Merkmale auf 1 normieren. Fehlende Zielattribute dürfen nicht automatisch als Mismatch bestraft werden.

Größe:
- exakt = size_weight_exact
- 1 Stufe daneben = size_weight_adjacent
- 2 Stufen daneben = size_weight_two_steps
- weiter entfernt stark abwerten
- Jeans W/L separat als Distanz behandeln

Aktualitätsgewicht:

`recency_weight = 0.5 ^ (age_days / recency_half_life_days)`

Datenqualität:
- High / Mittel / Low anhand Pricing_Config gewichten.

Unter `min_similarity_accept`: Kandidat verwerfen.

---

## Gemini Reranking

Gemini erhält NUR:
- erkanntes Zielprodukt
- relevante Pricing_Config-Werte
- maximal `max_prefilter_candidates` kompakte Kandidaten

Pro Kandidat nur benötigte Felder schicken:
- Datensatz_ID
- Marke
- Kleidungsstück
- Größe / W/L
- Ära
- Farbe
- Style
- Verein
- Liga
- Zustand (falls vorhanden)
- Preis
- Datum
- Datenqualität
- Status/Preisart

Gemini gibt strukturiert zurück:

```json
{
  "accepted": [
    {
      "id": "PM-000123",
      "tier": "exact",
      "semantic_similarity": 0.94,
      "reason": "gleiche Marke, Barcelona, 00s, Track Jacket, Größe M"
    }
  ],
  "rejected": [
    {
      "id": "PM-000999",
      "reason": "Hoodie statt Trainingsjacke"
    }
  ]
}
```

Maximal `max_llm_comparables` akzeptieren.

LLM darf hier keinen Endpreis setzen.

---

## Preisberechnung

### 1. Gesamtgewicht pro Comparable

Empfehlung:

`weight = deterministic_similarity * semantic_similarity * recency_weight * data_quality_weight`

Größenkomponente nicht doppelt anwenden, wenn sie bereits vollständig im deterministic_similarity steckt.

### 2. Ausreißer

Ab `outlier_min_n`:
- Q1 / Q3
- IQR
- Werte außerhalb Q1 - multiplier*IQR bzw. Q3 + multiplier*IQR markieren
- Primärwert zusätzlich ohne Ausreißer berechnen

### 3. Basispreis

Primär:

`weighted_median(Preis_EUR, weight)`

Nicht einfacher Durchschnitt.

### 4. Zustandsabschlag

Suche `Zustandsdaten` nach:
- Mangel_Typ
- Mangel_Schwere
- kompatibler Produktgruppe

Automatisch nur anwenden, wenn:
- Stichprobe_N >= condition_min_sample
- Confidence >= condition_min_confidence

Sonst:
- 0 % automatische Korrektur
- `Manuelle_Pruefung=true`
- Grund im Ergebnis dokumentieren

Mehrere belegte Mängel nicht naiv addieren; kombinierten Abschlag deckeln bzw. später empirisch modellieren.

### 5. Marktwert

`market_value = base_price * (1 - condition_discount)`

Demand standardmäßig NICHT zusätzlich auf den Preis aufschlagen, da Nachfrage bereits in Marktpreisen enthalten sein kann. `demand_price_adjustment` steht deshalb standardmäßig auf 0.

### 6. Listingpreis

`listing = market_value * (1 + listing_markup)`

Anschließend nach `price_rounding_rule` kommerziell runden (z. B. x9,90).

### 7. Quick Sale

`quick_sale = market_value * (1 - quick_sale_discount)`

danach runden.

### 8. Maximaler Einkaufspreis

`max_buy = market_value * (1 - selling_fee_pct) * (1 - target_gross_margin) - handling_cost_eur`

Nie unter 0.

---

## Nachfrage / Warenklasse

Die Rohquote `Nicht verfügbar / Gesamt` darf NICHT blind shopübergreifend verglichen werden, da Shop-Snapshots unterschiedliche Statusverteilungen haben.

Verwende `demand_normalization = within_shop_percentile`:

1. Demand-Proxy innerhalb jedes Shops / geeigneten Clusters berechnen.
2. In Perzentil oder normalisierten Score umwandeln.
3. Wenn mehrere Shops vorhanden: robust aggregieren (Median bevorzugt).
4. Bei weniger als `min_shops_for_demand` Confidence abwerten.

Warenklassen anhand `Pricing_Config`:
- S
- A
- B
- C
- D

Die Schwellenwerte sind initial konfigurierbar und kein Naturgesetz.

Warenklasse dient für Sortierung/Priorisierung, nicht als Beweis für einen bestimmten Verkaufspreis.

---

## Ergebnis-JSON

```json
{
  "request_id": "...",
  "identified_product": {...},
  "pricing": {
    "base_price_eur": 59.40,
    "condition_discount_pct": 0.04,
    "market_value_eur": 57.02,
    "listing_price_eur": 62.90,
    "quick_sale_eur": 52.90,
    "max_buy_eur": 28.50
  },
  "evidence": {
    "candidate_count": 43,
    "accepted_comparables": 12,
    "exact_matches": 4,
    "strong_matches": 6,
    "fallback_matches": 2,
    "comparable_ids": ["PM-...", "PM-..."]
  },
  "confidence": 0.89,
  "ware_class": "A",
  "manual_review": false,
  "reasons": [
    "Adidas",
    "00s/Y2K",
    "FC Barcelona",
    "Trainingsjacke",
    "4 Exact Matches"
  ]
}
```

---

## Pricing_Log

Nach jeder erfolgreichen oder manuellen Preisermittlung append-only in `Pricing_Log` schreiben.

Auch Fehlerfälle loggen:
- keine Comparables
- schlechte Confidence
- unklarer Produkttyp
- widersprüchliche Bilder
- Zustandsabschlag ohne Evidenz

Keine bestehenden Log-Zeilen überschreiben.

---

## Externe Web-Recherche

Nur Fallback, wenn:
- weniger als `web_search_min_comparables`
ODER
- Confidence < `web_search_confidence_below`

Externe Preise separat kennzeichnen. Nicht still mit Master-Daten vermischen.

---

## n8n-Architektur

Baue möglichst modular, z. B.:

1. Trigger (Webhook / Telegram)
2. Input validieren
3. Bild(er) vorbereiten
4. Gemini Product Extraction
5. JSON Schema Validation
6. Normalisierung
7. Pricing_Config laden
8. Pricing_Index / Cache abfragen
9. Deterministic Prefilter + Score
10. Branch: genug Kandidaten?
11. Gemini Comparable Reranking
12. Weighted Median + Outlier Logic
13. Zustandsdaten Lookup
14. Final Pricing
15. Demand / Warenklasse
16. Pricing_Log Append
17. Antwort ausgeben
18. Error Handler

Die genaue Node-Auswahl anhand der aktuell installierten n8n-Version mit n8n-MCP ermitteln.

---

## n8n-MCP Arbeitsweise

Verwende die vorhandene n8n-MCP-Integration.

Repository:
https://github.com/czlonkowski/n8n-mcp

Vor dem Bau:
1. `tools_documentation()`
2. Templates und passende Nodes suchen.
3. Node-Dokumentation lesen.
4. Alle Node-Konfigurationen explizit setzen.
5. Minimal validieren.
6. Full/runtime validieren.
7. Workflow bauen.
8. Gesamten Workflow validieren.
9. Testlauf mit mehreren Testfällen.
10. Fehler reparieren und erneut validieren.

Keine nicht existierenden Node-Parameter erfinden.

Die bestehende n8n-Verbindung / Credentials verwenden. Keine API-Schlüssel oder Secrets in Workflow-Code, GitHub-Dateien oder Logs schreiben.

---

## Testfälle

Mindestens:

### Test 1
Adidas FC Barcelona 00s Trainingsjacke, M, guter Zustand.

Erwartung:
- Team = Barcelona
- Football/Sport-Matches priorisiert
- Trainingsjacke nicht mit Hoodie vermischen

### Test 2
Levi's Jeans W32/L32.

Erwartung:
- W/L-Logik
- keine S/M/L-Vergleiche

### Test 3
Nike Basic Sweater ohne Team.

Erwartung:
- Team-Gewicht aus Score herausnormalisieren
- keine Strafe für fehlendes Team

### Test 4
Teil mit leichtem Loch, aber keine belastbaren Zustandsdaten.

Erwartung:
- Mangel erkennen
- keinen erfundenen Abschlag anwenden
- manuelle Prüfung markieren

### Test 5
Seltenes Produkt mit <3 Comparables.

Erwartung:
- kontrollierter Fallback
- niedrigere Confidence
- ggf. externe Recherche

---

## Abnahmekriterien

Der Workflow ist erst fertig, wenn:

- kein Request die gesamten ~30k Datensätze an Gemini schickt
- Pricing_Config statt harter Konstanten verwendet wird
- Ergebnis reproduzierbar ist
- Preis mathematisch berechnet wird
- Comparables nachvollziehbar geloggt sind
- Zustandsabschläge nicht erfunden werden
- Jeansgrößen korrekt behandelt werden
- Vereins-/Sportprodukte korrekt berücksichtigt werden
- niedrige Confidence zuverlässig manuelle Prüfung auslöst
- n8n-Workflow vollständig validiert ist
- mindestens die oben genannten Testfälle erfolgreich laufen
