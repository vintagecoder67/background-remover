# CLAUDE.md

## Projektkontext

Dieses Repository gehört zum Vintage-Reselling-Workflow.

Für den n8n-Pricing-Workflow ist die verbindliche Spezifikation:

`docs/VINTAGE_PRICING_WORKFLOW_SPEC.md`

Lies diese Datei vollständig, bevor du den Workflow planst oder änderst.

## n8n

Nutze die bereits konfigurierte n8n-MCP-Integration (czlonkowski/n8n-mcp), um aktuelle Node-Dokumentation zu lesen, den bestehenden n8n-Stand zu prüfen, den Workflow zu bauen und zu validieren.

Wichtig:
- zuerst n8n-MCP-Dokumentation und vorhandene Workflows prüfen
- keine Node-Parameter erfinden
- alle wichtigen Parameter explizit konfigurieren
- Node-Konfigurationen minimal und vollständig validieren
- anschließend gesamten Workflow validieren und testen
- vorhandene Credentials verwenden, Secrets nie in Git committen
- Preislogik aus der Spezifikation nicht durch freie LLM-Schätzung ersetzen

## Google Sheet

Source of Truth:
`Vintage Preis-Master – KI & Analyse`

Spreadsheet ID:
`1m83ZNaSo22VqSHwZZjnarQIObShX4m_PhnZFS9YZns4`

Für automatische Preisfindung primär die Tabs verwenden:
- `Pricing_Index`
- `Pricing_Config`
- `Zustandsdaten`
- `Pricing_Log`
- `Mapping`

Nicht die komplette Master-Tabelle an Gemini senden.

## Gemini

Standardmodell laut Spezifikation:
`gemini-3.8-flash`

Gemini erkennt und rerankt. Die endgültige Preisberechnung ist deterministisch.
