#!/usr/bin/env python3
"""
Test-Script um die Google Sheets Verbindung zu testen
und die verfügbaren Tabellenblätter zu finden.
"""

import os
import pandas as pd
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

def test_sheets_connection():
    """Testet die Verbindung zu Google Sheets und zeigt verfügbare Tabellenblätter."""
    
    # Google Sheets ID aus der URL
    SPREADSHEET_ID = "191RsU9uDyRQDIM4UITTY2F8KxalA9uGP497pdWKoRvA"
    
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    creds = None
    
    # Token aus vorheriger Sitzung laden
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            
    # Wenn keine gültigen Credentials vorhanden, neu authentifizieren
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("❌ Fehler: 'credentials.json' nicht gefunden!")
                print("📝 Bitte laden Sie die credentials.json Datei herunter und platzieren Sie sie hier.")
                return False
                
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Token für nächste Sitzung speichern
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    try:
        # Google Sheets Service erstellen
        service = build('sheets', 'v4', credentials=creds)
        
        # Verfügbare Tabellenblätter abrufen
        print("🔍 Lade verfügbare Tabellenblätter...")
        spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        sheets = spreadsheet.get('sheets', [])
        
        print(f"\n📋 Verfügbare Tabellenblätter ({len(sheets)}):")
        for i, sheet in enumerate(sheets, 1):
            sheet_name = sheet['properties']['title']
            print(f"   {i}. {sheet_name}")
        
        # Teste jeden Tabellenblatt
        print(f"\n🧪 Teste Datenzugriff auf Tabellenblätter...")
        
        for sheet in sheets:
            sheet_name = sheet['properties']['title']
            try:
                result = service.spreadsheets().values().get(
                    spreadsheetId=SPREADSHEET_ID,
                    range=f'{sheet_name}!A1:Z10'  # Erste 10 Zeilen und Spalten
                ).execute()
                
                values = result.get('values', [])
                if values:
                    print(f"   ✅ {sheet_name}: {len(values)} Zeilen gefunden")
                    # Zeige erste Zeile (Header)
                    if len(values) > 0:
                        print(f"      Header: {values[0][:5]}...")  # Erste 5 Spalten
                else:
                    print(f"   ⚠️  {sheet_name}: Keine Daten gefunden")
                    
            except Exception as e:
                print(f"   ❌ {sheet_name}: Fehler beim Laden - {e}")
        
        print(f"\n✅ Verbindung zu Google Sheets erfolgreich!")
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei der Verbindung: {e}")
        return False

if __name__ == "__main__":
    print("🎯 Google Sheets Verbindungstest")
    print("=" * 40)
    test_sheets_connection()
