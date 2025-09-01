# 🎯 Probepaket Finder WebApp

Eine moderne Web-Anwendung zur Suche nach verfügbaren Probepaketen basierend auf Kundenwünschen (Produkt und Farbe).

## ✨ Features

- **Moderne Web-Oberfläche** mit Bootstrap 5 und Font Awesome Icons
- **Dropdown-Listen** für einfache Produkt- und Farbauswahl
- **Echtzeit-Suche** mit AJAX-API
- **Responsive Design** für alle Geräte
- **Google Sheets Integration** für Live-Daten
- **Automatische Datenaktualisierung**
- **Lieferschein-Downloads** direkt aus der App

## 🚀 Installation & Setup

### 1. Google Cloud Console Setup
1. Gehe zu [Google Cloud Console](https://console.cloud.google.com/)
2. Erstelle ein neues Projekt oder wähle ein bestehendes aus
3. Aktiviere die **Google Sheets API**:
   - Gehe zu "APIs & Services" → "Library"
   - Suche nach "Google Sheets API"
   - Klicke "Enable"

### 2. Credentials erstellen
1. Gehe zu "APIs & Services" → "Credentials"
2. Klicke "Create Credentials" → "OAuth client ID"
3. Wähle "Desktop application" als Application type
4. Gib einen Namen ein (z.B. "Probepaket Finder")
5. Klicke "Create"

### 3. credentials.json herunterladen
1. Nach der Erstellung wird eine JSON-Datei heruntergeladen
2. **Wichtig**: Benenne diese Datei in `credentials.json` um
3. Platziere sie in deinem Projektordner

### 4. Dependencies installieren
```bash
pip3 install -r requirements.txt
pip3 install flask
```

### 5. WebApp starten
```bash
python3 app.py
```

Die WebApp ist dann unter `http://localhost:5001` erreichbar.

## 📁 Projektstruktur

```
probepaket/
├── app.py                 # Flask Backend
├── templates/
│   └── index.html        # Hauptseite
├── static/
│   ├── css/
│   │   └── style.css     # Custom CSS
│   └── js/
│       └── app.js        # Frontend JavaScript
├── credentials.json      # Google API Credentials
├── token.pickle         # Authentifizierungstoken
├── requirements.txt     # Python Dependencies
└── README.md           # Diese Datei
```

## 🔧 API Endpoints

- `GET /` - Hauptseite
- `GET /api/products` - Verfügbare Produkte
- `GET /api/colors/<product>` - Farben für ein Produkt
- `POST /api/search` - Probepakete suchen
- `GET /api/refresh` - Daten aktualisieren

## 📊 Datenquellen

Die App verwendet drei Google Sheets Tabellenblätter:

1. **Farben** - Produktnamen und deren verfügbare Farben
2. **monday** - Verfügbarkeitsstatus der Probepakete
3. **Lager_neu** - Detaillierte Paket-Inhalte (für zukünftige Erweiterungen)

## 🎨 Verfügbare Produkte

- Bio Hoodie
- Bio Premium Hoodie
- Bio Premium Polo
- Bio Premium Shirt
- Bio Premium Sweater
- Bio Shirt
- Classic Hoodie
- Classic Shirt
- Premium Polo

## 🔍 Verwendung

1. **Produkt auswählen**: Wähle aus der Dropdown-Liste das gewünschte Produkt
2. **Farbe auswählen**: Nach der Produktauswahl werden die verfügbaren Farben geladen
3. **Suchen**: Klicke auf "Probepakete suchen"
4. **Ergebnisse**: Alle verfügbaren Probepakete werden angezeigt
5. **Lieferschein**: Klicke auf "Lieferschein" um das PDF herunterzuladen

## 🚀 Deployment

### Lokaler Server
```bash
python3 app.py
```

### Produktions-Server
Für den Produktionseinsatz empfehle ich:
- **Heroku** - Einfaches Deployment
- **Railway** - Moderne Alternative
- **DigitalOcean App Platform** - Für größere Anwendungen

## 🔒 Sicherheit

- Die `credentials.json` sollte niemals in Version Control committet werden
- Verwende Umgebungsvariablen für sensible Daten
- Implementiere Rate Limiting für Produktionsumgebungen

## 🐛 Troubleshooting

### Port bereits belegt
```bash
# Ändere den Port in app.py
app.run(debug=True, host='0.0.0.0', port=5002)
```

### Google API Fehler
1. Überprüfe, ob die Google Sheets API aktiviert ist
2. Stelle sicher, dass `credentials.json` korrekt ist
3. Lösche `token.pickle` und authentifiziere neu

### Keine Daten geladen
1. Überprüfe die Google Sheets ID in `app.py`
2. Stelle sicher, dass die Tabellenblätter "Farben" und "monday" existieren
3. Überprüfe die Berechtigungen der Google Sheets

## 📝 Changelog

### v1.0.0
- ✅ Moderne Web-Oberfläche
- ✅ Google Sheets Integration
- ✅ Produkt- und Farbauswahl
- ✅ Probepaket-Suche
- ✅ Lieferschein-Downloads
- ✅ Responsive Design

## 🤝 Support

Bei Fragen oder Problemen:
1. Überprüfe die Troubleshooting-Sektion
2. Schaue in die Logs der WebApp
3. Teste die API-Endpoints direkt

## 📄 Lizenz

Dieses Projekt ist für den internen Gebrauch von Gradu Print bestimmt.
