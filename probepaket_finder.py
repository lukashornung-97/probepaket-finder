#!/usr/bin/env python3
"""
Probepaket Finder - Ein Programm zur Suche nach verfügbaren Probepaketen
basierend auf Kundenwünschen (Produkt und Farbe).

Verwendet Google Sheets API für:
- Lager_neu: Inhalt der Probepakete
- Farben: Textilien und Farben
- Monday: Verfügbarkeitsstatus
"""

import os
import pandas as pd
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
from typing import List, Dict, Optional
import json

class ProbepaketFinder:
    def __init__(self, spreadsheet_id: str):
        """
        Initialisiert den Probepaket Finder.
        
        Args:
            spreadsheet_id: Die ID der Google Sheets Tabelle
        """
        self.spreadsheet_id = spreadsheet_id
        self.service = self._authenticate_google_sheets()
        self.lager_data = None
        self.farben_data = None
        self.monday_data = None
        
    def _authenticate_google_sheets(self):
        """Authentifiziert bei Google Sheets API."""
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
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
                
            # Token für nächste Sitzung speichern
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
                
        return build('sheets', 'v4', credentials=creds)
    
    def load_data(self):
        """Lädt alle relevanten Daten aus den Google Sheets."""
        print("Lade Daten aus Google Sheets...")
        
        # Daten aus Lager_neu laden
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='Lager_neu'
            ).execute()
            self.lager_data = pd.DataFrame(result.get('values', []))
            if not self.lager_data.empty:
                self.lager_data.columns = self.lager_data.iloc[0]
                self.lager_data = self.lager_data.iloc[1:]
            print(f"✓ Lager_neu Daten geladen: {len(self.lager_data)} Zeilen")
        except Exception as e:
            print(f"✗ Fehler beim Laden von Lager_neu: {e}")
            
        # Daten aus Farben laden
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='Farben'
            ).execute()
            self.farben_data = pd.DataFrame(result.get('values', []))
            if not self.farben_data.empty:
                self.farben_data.columns = self.farben_data.iloc[0]
                self.farben_data = self.farben_data.iloc[1:]
            print(f"✓ Farben Daten geladen: {len(self.farben_data)} Zeilen")
        except Exception as e:
            print(f"✗ Fehler beim Laden von Farben: {e}")
            
        # Daten aus Monday laden
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='Monday'
            ).execute()
            self.monday_data = pd.DataFrame(result.get('values', []))
            if not self.monday_data.empty:
                self.monday_data.columns = self.monday_data.iloc[0]
                self.monday_data = self.monday_data.iloc[1:]
            print(f"✓ Monday Daten geladen: {len(self.monday_data)} Zeilen")
        except Exception as e:
            print(f"✗ Fehler beim Laden von Monday: {e}")
    
    def get_available_packages(self) -> List[Dict]:
        """
        Gibt eine Liste aller verfügbaren Probepakete zurück.
        
        Returns:
            Liste von Dictionaries mit Probepaket-Informationen
        """
        if self.monday_data is None:
            print("Monday Daten nicht geladen!")
            return []
            
        available_packages = []
        
        # Durch alle Zeilen in Monday iterieren
        for idx, row in self.monday_data.iterrows():
            if len(row) < 2:  # Mindestens Nummer und Status
                continue
                
            package_number = row.iloc[0] if len(row) > 0 else None
            status = row.iloc[1] if len(row) > 1 else None
            
            # Nur Pakete mit Status "Im Lager" berücksichtigen
            if status and "Im Lager" in str(status):
                package_info = {
                    'nummer': package_number,
                    'status': status,
                    'produkte': {}
                }
                
                # Produkte und Farben aus der Zeile extrahieren
                for col_idx, value in enumerate(row.iloc[2:], start=2):
                    if pd.notna(value) and str(value).strip():
                        # Spaltenname aus Header ermitteln
                        if col_idx < len(self.monday_data.columns):
                            product_name = self.monday_data.columns[col_idx]
                            package_info['produkte'][product_name] = str(value).strip()
                
                available_packages.append(package_info)
        
        return available_packages
    
    def find_matching_packages(self, gewünschtes_produkt: str, gewünschte_farbe: str) -> List[Dict]:
        """
        Findet Probepakete, die das gewünschte Produkt in der gewünschten Farbe enthalten.
        
        Args:
            gewünschtes_produkt: Name des gewünschten Produkts
            gewünschte_farbe: Gewünschte Farbe
            
        Returns:
            Liste der passenden Probepakete
        """
        available_packages = self.get_available_packages()
        matching_packages = []
        
        for package in available_packages:
            # Prüfen ob das gewünschte Produkt im Paket enthalten ist
            if gewünschtes_produkt in package['produkte']:
                package_color = package['produkte'][gewünschtes_produkt]
                
                # Farbvergleich (case-insensitive)
                if (gewünschte_farbe.lower() in package_color.lower() or 
                    package_color.lower() in gewünschte_farbe.lower()):
                    matching_packages.append(package)
        
        return matching_packages
    
    def get_available_products(self) -> List[str]:
        """Gibt eine Liste aller verfügbaren Produkte zurück."""
        if self.farben_data is None:
            return []
            
        products = []
        for idx, row in self.farben_data.iterrows():
            if len(row) > 0 and pd.notna(row.iloc[0]):
                products.append(str(row.iloc[0]).strip())
        
        return sorted(list(set(products)))
    
    def get_available_colors(self, product: str) -> List[str]:
        """Gibt eine Liste aller verfügbaren Farben für ein Produkt zurück."""
        if self.farben_data is None:
            return []
            
        colors = []
        for idx, row in self.farben_data.iterrows():
            if len(row) > 0 and str(row.iloc[0]).strip() == product:
                # Alle Farben in der Zeile sammeln
                for col_idx, value in enumerate(row.iloc[1:], start=1):
                    if pd.notna(value) and str(value).strip():
                        colors.append(str(value).strip())
        
        return sorted(list(set(colors)))
    
    def display_package_details(self, package: Dict):
        """Zeigt Details eines Probepakets an."""
        print(f"\n📦 Probepaket #{package['nummer']}")
        print(f"   Status: {package['status']}")
        print("   Enthaltene Produkte:")
        for product, color in package['produkte'].items():
            print(f"   • {product}: {color}")
    
    def interactive_search(self):
        """Interaktive Suche nach Probepaketen."""
        print("\n" + "="*50)
        print("🎯 PROBEPAKET FINDER")
        print("="*50)
        
        # Verfügbare Produkte anzeigen
        available_products = self.get_available_products()
        if not available_products:
            print("❌ Keine Produktdaten verfügbar!")
            return
            
        print(f"\n📋 Verfügbare Produkte ({len(available_products)}):")
        for i, product in enumerate(available_products, 1):
            print(f"   {i}. {product}")
        
        # Produktauswahl
        while True:
            try:
                choice = input(f"\n🔍 Wählen Sie ein Produkt (1-{len(available_products)}) oder geben Sie den Namen ein: ").strip()
                
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(available_products):
                        selected_product = available_products[idx]
                        break
                    else:
                        print("❌ Ungültige Nummer!")
                else:
                    # Direkte Eingabe des Produktnamens
                    if choice in available_products:
                        selected_product = choice
                        break
                    else:
                        print("❌ Produkt nicht gefunden!")
            except ValueError:
                print("❌ Ungültige Eingabe!")
        
        print(f"\n✅ Ausgewähltes Produkt: {selected_product}")
        
        # Verfügbare Farben für das Produkt anzeigen
        available_colors = self.get_available_colors(selected_product)
        if not available_colors:
            print("❌ Keine Farbdaten für dieses Produkt verfügbar!")
            return
            
        print(f"\n🎨 Verfügbare Farben für '{selected_product}' ({len(available_colors)}):")
        for i, color in enumerate(available_colors, 1):
            print(f"   {i}. {color}")
        
        # Farbauswahl
        while True:
            try:
                choice = input(f"\n🎨 Wählen Sie eine Farbe (1-{len(available_colors)}) oder geben Sie den Namen ein: ").strip()
                
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(available_colors):
                        selected_color = available_colors[idx]
                        break
                    else:
                        print("❌ Ungültige Nummer!")
                else:
                    # Direkte Eingabe der Farbe
                    if choice in available_colors:
                        selected_color = choice
                        break
                    else:
                        print("❌ Farbe nicht gefunden!")
            except ValueError:
                print("❌ Ungültige Eingabe!")
        
        print(f"\n✅ Ausgewählte Farbe: {selected_color}")
        
        # Suche nach passenden Probepaketen
        print(f"\n🔍 Suche nach Probepaketen mit '{selected_product}' in '{selected_color}'...")
        matching_packages = self.find_matching_packages(selected_product, selected_color)
        
        if matching_packages:
            print(f"\n✅ {len(matching_packages)} passende Probepakete gefunden:")
            for package in matching_packages:
                self.display_package_details(package)
        else:
            print(f"\n❌ Keine passenden Probepakete gefunden!")
            print("💡 Tipp: Versuchen Sie eine ähnliche Farbe oder ein ähnliches Produkt.")

def main():
    """Hauptfunktion des Programms."""
    # Google Sheets ID aus der URL
    SPREADSHEET_ID = "191RsU9uDyRQDIM4UITTY2F8KxalA9uGP497pdWKoRvA"
    
    try:
        # Probepaket Finder initialisieren
        finder = ProbepaketFinder(SPREADSHEET_ID)
        
        # Daten laden
        finder.load_data()
        
        # Interaktive Suche starten
        while True:
            finder.interactive_search()
            
            # Weiter suchen?
            choice = input("\n🔄 Möchten Sie eine weitere Suche durchführen? (j/n): ").strip().lower()
            if choice not in ['j', 'ja', 'y', 'yes']:
                break
        
        print("\n👋 Vielen Dank für die Nutzung des Probepaket Finders!")
        
    except FileNotFoundError:
        print("❌ Fehler: 'credentials.json' nicht gefunden!")
        print("📝 Bitte stellen Sie sicher, dass die Google Sheets API Credentials vorhanden sind.")
        print("🔗 Anleitung: https://developers.google.com/sheets/api/quickstart/python")
        
    except Exception as e:
        print(f"❌ Ein Fehler ist aufgetreten: {e}")

if __name__ == "__main__":
    main()
