# Probepaket Finder - Render Deployment

## 🚀 Deployment auf Render

### 1. Google API Credentials vorbereiten

1. **Google Cloud Console** öffnen: https://console.cloud.google.com/
2. **Neues Projekt erstellen** oder bestehendes auswählen
3. **Google Sheets API aktivieren**:
   - APIs & Services → Library
   - "Google Sheets API" suchen und aktivieren
4. **Credentials erstellen**:
   - APIs & Services → Credentials
   - "Create Credentials" → "Service Account"
   - Name: `probepaket-finder`
   - Role: `Editor` oder `Viewer`
   - JSON-Datei herunterladen

### 2. Service Account Berechtigung

1. **Google Sheets öffnen**: https://docs.google.com/spreadsheets/d/191RsU9uDyRQDIM4UITTY2F8KxalA9uGP497pdWKoRvA
2. **"Teilen" klicken**
3. **Service Account E-Mail hinzufügen** (aus der JSON-Datei: `client_email`)
4. **Berechtigung**: "Leseberechtigt"

### 3. Render Setup

1. **Render Dashboard** öffnen: https://dashboard.render.com/
2. **"New +" → "Web Service"**
3. **Git Repository verbinden**
4. **Konfiguration**:
   - **Name**: `probepaket-finder`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`

### 4. Umgebungsvariablen setzen

In Render Dashboard → Environment:

```
GOOGLE_CREDENTIALS_JSON = {"type":"service_account","project_id":"...","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"...","client_id":"...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"..."}

SPREADSHEET_ID = 191RsU9uDyRQDIM4UITTY2F8KxalA9uGP497pdWKoRvA
```

**Wichtig**: Die gesamte JSON-Datei als eine Zeile einfügen!

### 5. Deployment

1. **"Create Web Service" klicken**
2. **Warten** bis Build und Deployment abgeschlossen sind
3. **URL testen**: https://probepaket-finder.onrender.com

## 🔧 Lokale Entwicklung

```bash
# Repository klonen
git clone <your-repo-url>
cd probepaket

# Virtual Environment erstellen
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate     # Windows

# Dependencies installieren
pip install -r requirements.txt

# Google API Credentials einrichten
# credentials.json in den Projektordner kopieren

# App starten
python app.py
```

## 📁 Projektstruktur

```
probepaket/
├── app.py                 # Hauptanwendung
├── requirements.txt       # Python Dependencies
├── render.yaml           # Render Konfiguration
├── Procfile              # Heroku/Render Start Command
├── .gitignore            # Git Ignore Regeln
├── templates/
│   └── index.html        # Frontend Template
├── static/
│   ├── css/
│   │   └── style.css     # Styling
│   └── js/
│       └── app.js        # Frontend JavaScript
└── README_DEPLOYMENT.md  # Diese Datei
```

## 🐛 Troubleshooting

### Build Fehler
- **Python Version**: Render verwendet Python 3.11.0
- **Dependencies**: Alle in `requirements.txt` aufgelistet

### Runtime Fehler
- **Google API**: Service Account Berechtigung prüfen
- **Umgebungsvariablen**: JSON korrekt formatiert?
- **Logs**: In Render Dashboard → Logs prüfen

### Performance
- **Free Tier**: 750 Stunden/Monat
- **Sleep Mode**: Nach 15 Min Inaktivität
- **Cold Start**: Erste Anfrage kann langsam sein

## 🔒 Sicherheit

- ✅ **Keine Credentials im Code**
- ✅ **Umgebungsvariablen für sensible Daten**
- ✅ **Service Account mit minimalen Berechtigungen**
- ✅ **HTTPS automatisch aktiviert**

## 📞 Support

Bei Problemen:
1. **Render Logs** prüfen
2. **Google API Quotas** überprüfen
3. **Service Account Berechtigung** testen
4. **Lokale Entwicklung** zum Debuggen nutzen
