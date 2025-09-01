#!/usr/bin/env python3
"""
Probepaket Finder WebApp
Eine moderne Web-Anwendung zur Suche nach verfügbaren Probepaketen
"""

from flask import Flask, render_template, request, jsonify
import os
import pandas as pd
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
from typing import List, Dict, Optional
import json
from datetime import datetime, timedelta
import base64

app = Flask(__name__)

class ProbepaketFinder:
    def __init__(self, spreadsheet_id: str):
        """Initialisiert den Probepaket Finder."""
        self.spreadsheet_id = spreadsheet_id
        self.service = self._authenticate_google_sheets()
        self.lager_data = None
        self.farben_data = None
        self.monday_data = None
        self.last_update = None
        
    def _authenticate_google_sheets(self):
        """Authentifiziert bei Google Sheets API."""
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
        creds = None
        
        print("🔍 DEBUG: Starte Google Sheets Authentifizierung...")
        print(f"🔍 DEBUG: Umgebungsvariable GOOGLE_CREDENTIALS_JSON vorhanden: {bool(os.getenv('GOOGLE_CREDENTIALS_JSON'))}")
        print(f"🔍 DEBUG: Lokale credentials.json vorhanden: {os.path.exists('credentials.json')}")
        print(f"🔍 DEBUG: Lokale token.pickle vorhanden: {os.path.exists('token.pickle')}")
        
        # Für Render: Credentials aus Umgebungsvariable laden
        if os.getenv('GOOGLE_CREDENTIALS_JSON'):
            try:
                print("🔍 DEBUG: Lade Credentials aus Umgebungsvariable...")
                credentials_string = os.getenv('GOOGLE_CREDENTIALS_JSON')
                print(f"🔍 DEBUG: Credentials String Länge: {len(credentials_string)}")
                print(f"🔍 DEBUG: Erste 100 Zeichen: {credentials_string[:100]}")
                print(f"🔍 DEBUG: Letzte 100 Zeichen: {credentials_string[-100:]}")
                
                credentials_json = json.loads(credentials_string)
                print(f"🔍 DEBUG: Credentials JSON geladen, Typ: {type(credentials_json)}")
                print(f"🔍 DEBUG: Credentials Keys: {list(credentials_json.keys()) if isinstance(credentials_json, dict) else 'Nicht ein Dictionary'}")
                
                creds = Credentials.from_authorized_user_info(credentials_json, SCOPES)
                print("🔍 DEBUG: Credentials erfolgreich aus Umgebungsvariable geladen")
            except Exception as e:
                print(f"❌ DEBUG: Fehler beim Laden der Credentials aus Umgebungsvariable: {e}")
                print(f"❌ DEBUG: Exception Typ: {type(e)}")
                print(f"❌ DEBUG: Credentials String (erste 200 Zeichen): {credentials_string[:200] if 'credentials_string' in locals() else 'Nicht verfügbar'}")
                import traceback
                print(f"❌ DEBUG: Traceback: {traceback.format_exc()}")
        
        # Fallback: Lokale Dateien (für Entwicklung)
        if not creds:
            print("🔍 DEBUG: Keine Credentials aus Umgebungsvariable, versuche lokale Dateien...")
            # Token aus vorheriger Sitzung laden
            if os.path.exists('token.pickle'):
                try:
                    with open('token.pickle', 'rb') as token:
                        creds = pickle.load(token)
                    print("🔍 DEBUG: Token aus token.pickle geladen")
                except Exception as e:
                    print(f"❌ DEBUG: Fehler beim Laden von token.pickle: {e}")
                    
            # Wenn keine gültigen Credentials vorhanden, neu authentifizieren
            if not creds or not creds.valid:
                print(f"🔍 DEBUG: Credentials gültig: {creds.valid if creds else 'Keine Credentials'}")
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                        print("🔍 DEBUG: Credentials erfolgreich aktualisiert")
                    except Exception as e:
                        print(f"❌ DEBUG: Fehler beim Aktualisieren der Credentials: {e}")
                else:
                    if os.path.exists('credentials.json'):
                        try:
                            flow = InstalledAppFlow.from_client_secrets_file(
                                'credentials.json', SCOPES)
                            creds = flow.run_local_server(port=0)
                            print("🔍 DEBUG: Neue Authentifizierung erfolgreich")
                        except Exception as e:
                            print(f"❌ DEBUG: Fehler bei neuer Authentifizierung: {e}")
                    else:
                        error_msg = "Keine Google API Credentials gefunden!"
                        print(f"❌ DEBUG: {error_msg}")
                        raise Exception(error_msg)
                    
                # Token für nächste Sitzung speichern
                if creds:
                    try:
                        with open('token.pickle', 'wb') as token:
                            pickle.dump(creds, token)
                        print("🔍 DEBUG: Token erfolgreich gespeichert")
                    except Exception as e:
                        print(f"❌ DEBUG: Fehler beim Speichern des Tokens: {e}")
        
        if not creds:
            error_msg = "Authentifizierung fehlgeschlagen - keine gültigen Credentials"
            print(f"❌ DEBUG: {error_msg}")
            raise Exception(error_msg)
            
        print("🔍 DEBUG: Erstelle Google Sheets Service...")
        try:
            service = build('sheets', 'v4', credentials=creds)
            print("✅ DEBUG: Google Sheets Service erfolgreich erstellt")
            return service
        except Exception as e:
            print(f"❌ DEBUG: Fehler beim Erstellen des Google Sheets Service: {e}")
            import traceback
            print(f"❌ DEBUG: Traceback: {traceback.format_exc()}")
            raise
    
    def load_data(self):
        """Lädt alle relevanten Daten aus den Google Sheets."""
        print("🔍 DEBUG: Starte Datenladevorgang...")
        print(f"🔍 DEBUG: Spreadsheet ID: {self.spreadsheet_id}")
        print(f"🔍 DEBUG: Service verfügbar: {self.service is not None}")
        
        # Daten aus Farben laden (enthält Produkte und deren Farben)
        try:
            print("🔍 DEBUG: Lade Farben Daten...")
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='Farben'
            ).execute()
            self.farben_data = result.get('values', [])
            print(f"✅ DEBUG: Farben Daten geladen: {len(self.farben_data)} Zeilen")
            if self.farben_data:
                print(f"🔍 DEBUG: Erste Farben Zeile: {self.farben_data[0] if self.farben_data else 'Leer'}")
        except Exception as e:
            print(f"❌ DEBUG: Fehler beim Laden von Farben: {e}")
            import traceback
            print(f"❌ DEBUG: Traceback: {traceback.format_exc()}")
            
        # Daten aus Monday laden (enthält Verfügbarkeitsstatus)
        try:
            print("🔍 DEBUG: Lade Monday Daten...")
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='monday'
            ).execute()
            self.monday_data = result.get('values', [])
            print(f"✅ DEBUG: Monday Daten geladen: {len(self.monday_data)} Zeilen")
            if self.monday_data:
                print(f"🔍 DEBUG: Erste Monday Zeile: {self.monday_data[0] if self.monday_data else 'Leer'}")
        except Exception as e:
            print(f"❌ DEBUG: Fehler beim Laden von Monday: {e}")
            import traceback
            print(f"❌ DEBUG: Traceback: {traceback.format_exc()}")
            
        # Daten aus Lager_neu laden (enthält tatsächliche Paket-Inhalte)
        try:
            print("🔍 DEBUG: Lade Lager_neu Daten...")
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='Lager_neu'
            ).execute()
            self.lager_data = result.get('values', [])
            print(f"✅ DEBUG: Lager_neu Daten geladen: {len(self.lager_data)} Zeilen")
            if self.lager_data:
                print(f"🔍 DEBUG: Erste Lager_neu Zeile: {self.lager_data[0] if self.lager_data else 'Leer'}")
        except Exception as e:
            print(f"❌ DEBUG: Fehler beim Laden von Lager_neu: {e}")
            import traceback
            print(f"❌ DEBUG: Traceback: {traceback.format_exc()}")
            
        self.last_update = datetime.now()
        print(f"🔍 DEBUG: Datenladevorgang abgeschlossen um {self.last_update}")
    
    def get_available_products(self) -> List[str]:
        """Gibt eine Liste aller verfügbaren Produkte zurück."""
        print("🔍 DEBUG: get_available_products aufgerufen")
        print(f"🔍 DEBUG: Farben Daten verfügbar: {self.farben_data is not None}")
        print(f"🔍 DEBUG: Farben Daten Länge: {len(self.farben_data) if self.farben_data else 0}")
        
        if not self.farben_data:
            print("❌ DEBUG: Keine Farben Daten verfügbar")
            return []
            
        products = []
        print("🔍 DEBUG: Durchlaufe Farben Daten...")
        for i, row in enumerate(self.farben_data):
            print(f"🔍 DEBUG: Zeile {i}: {row}")
            if row and len(row) > 0:
                product_name = row[0].strip()
                print(f"🔍 DEBUG: Produktname: '{product_name}'")
                # Nur echte Produktnamen hinzufügen (nicht Farben)
                if (product_name and 
                    product_name not in products and 
                    not any(color_word in product_name.lower() for color_word in 
                           ['blue', 'white', 'black', 'green', 'red', 'pink', 'orange', 'yellow', 'purple', 'grey', 'brown', 'apricot'])):
                    products.append(product_name)
                    print(f"✅ DEBUG: Produkt hinzugefügt: '{product_name}'")
                else:
                    print(f"⏭️ DEBUG: Produkt übersprungen: '{product_name}'")
        
        result = sorted(products)
        print(f"🔍 DEBUG: Finale Produktliste: {result}")
        return result
    
    def get_available_colors(self, product: str) -> List[str]:
        """Gibt eine Liste aller verfügbaren Farben für ein Produkt zurück."""
        if not self.farben_data:
            return ['Egal']
            
        colors = ['Egal']  # "Egal" immer als erste Option
        for i, row in enumerate(self.farben_data):
            if row and len(row) > 0 and row[0].strip() == product:
                # Die Farben stehen in der nächsten Zeile (i+1)
                if i + 1 < len(self.farben_data):
                    color_row = self.farben_data[i + 1]
                    for color in color_row:
                        if color and color.strip():
                            color_name = color.strip()
                            if color_name not in colors:
                                colors.append(color_name)
        
        return colors  # "Egal" ist bereits an Position 0
    
    def get_available_packages(self) -> List[Dict]:
        """Gibt eine Liste aller verfügbaren Probepakete zurück."""
        if not self.monday_data:
            return []
            
        available_packages = []
        
        # Durch alle Zeilen in Monday iterieren (ab Zeile 1, da Zeile 0 Header ist)
        for row in self.monday_data[1:]:
            if len(row) < 2:  # Mindestens Element und Status
                continue
                
            package_element = row[0] if len(row) > 0 else None
            status = row[2] if len(row) > 2 else None  # Status ist in Spalte 2
            
            # Nur Pakete mit Status "Im Lager" berücksichtigen
            if status and "Im Lager" in str(status):
                # Paketnummer aus Element extrahieren (z.B. "Probepaket 1017" -> "1017")
                package_number = None
                if package_element and "Probepaket" in package_element:
                    try:
                        package_number = package_element.split()[-1]
                    except:
                        package_number = package_element
                
                package_info = {
                    'nummer': package_number,
                    'element': package_element,
                    'status': status,
                    'lieferschein': row[3] if len(row) > 3 else None
                }
                
                available_packages.append(package_info)
        
        return available_packages
    
    def find_matching_packages(self, search_criteria: List[Dict], veredelung_required: List[str] = None) -> List[Dict]:
        """
        Findet Probepakete, die alle gewünschten Produkte in den gewünschten Farben enthalten.
        Verwendet die Lager_neu Tabelle für präzise Suche.
        
        Args:
            search_criteria: Liste von Dictionaries mit 'product' und 'color' Keys
            veredelung_required: Liste von gewünschten Veredelungen (Siebdruck, Stick, Digitaldruck)
        """
        if not self.lager_data or not self.monday_data or not search_criteria:
            return []
        
        # Alle Pakete sammeln, die mindestens ein Suchkriterium erfüllen
        all_matching_packages = {}
        
        # Paketnummern aus der ersten Zeile von Lager_neu extrahieren
        if len(self.lager_data) < 1:
            return []
        
        package_numbers = self.lager_data[0][2:]  # Ab Spalte 2 (nach "Nummer")
        
        # Für jedes Suchkriterium Pakete finden
        for criterion in search_criteria:
            gewünschtes_produkt = criterion.get('product', '').strip()
            gewünschte_farbe = criterion.get('color', '').strip()
            
            if not gewünschtes_produkt:
                continue
            
            # Durch alle Produktzeilen in Lager_neu iterieren
            current_product = None
            for row_idx, row in enumerate(self.lager_data[4:], start=4):  # Ab Zeile 4 (nach Header)
                if not row or len(row) < 2:
                    continue
                    
                product_name = row[0].strip()
                size = row[1].strip() if len(row) > 1 else ""
                
                # Wenn product_name nicht leer ist, ist es ein neues Produkt
                if product_name:
                    current_product = product_name
                
                # Prüfen ob das gewünschte Produkt in dieser Zeile steht
                if current_product == gewünschtes_produkt:
                    # Durch alle Paketspalten iterieren (ab Spalte 2)
                    for col_idx, color in enumerate(row[2:], start=2):
                        if col_idx - 2 < len(package_numbers):
                            package_number = package_numbers[col_idx - 2]
                            
                            # Prüfen ob die Farbe übereinstimmt
                            if color and color.strip():
                                package_color = color.strip()
                                
                                # Farbvergleich (case-insensitive und teilweise Übereinstimmung)
                                # Wenn "Egal" gewählt wurde, akzeptiere jede Farbe
                                if (gewünschte_farbe.lower() == 'egal' or
                                    gewünschte_farbe.lower() in package_color.lower() or 
                                    package_color.lower() in gewünschte_farbe.lower()):
                                    
                                    # Prüfen ob das Paket verfügbar ist (Status aus Monday)
                                    monday_info = self.get_monday_info(package_number)
                                    if monday_info and monday_info.get('status') == 'Im Lager':
                                        if package_number not in all_matching_packages:
                                            all_matching_packages[package_number] = {
                                                'nummer': package_number,
                                                'element': monday_info.get('element', f'Probepaket {package_number}'),
                                                'status': monday_info.get('status', 'Unbekannt'),
                                                'lieferschein': monday_info.get('lieferschein'),
                                                'produkte': []
                                            }
                                        
                                        # Produkt-Info hinzufügen
                                        product_info = {
                                            'produkt': current_product,
                                            'groesse': size,
                                            'farbe': package_color
                                        }
                                        all_matching_packages[package_number]['produkte'].append(product_info)
        
        # Nur Pakete zurückgeben, die ALLE spezifischen Suchkriterien erfüllen
        final_matching_packages = []
        for package_number, package_info in all_matching_packages.items():
            # Prüfe ob das Paket ALLE Suchkriterien erfüllt
            criteria_fulfilled = 0
            for criterion in search_criteria:
                gewünschtes_produkt = criterion.get('product', '').strip()
                gewünschte_farbe = criterion.get('color', '').strip()
                
                # Suche in den Produkten des Pakets nach dieser spezifischen Kombination
                found_match = False
                for produkt in package_info['produkte']:
                    if (produkt['produkt'] == gewünschtes_produkt and 
                        (gewünschte_farbe.lower() == 'egal' or
                         gewünschte_farbe.lower() in produkt['farbe'].lower() or 
                         produkt['farbe'].lower() in gewünschte_farbe.lower())):
                        found_match = True
                        break
                
                if found_match:
                    criteria_fulfilled += 1
            
            # Nur Pakete hinzufügen, die ALLE Suchkriterien erfüllen
            if criteria_fulfilled == len(search_criteria):
                # Prüfe Veredelungsanforderungen
                if veredelung_required:
                    package_veredelungen = self.get_veredelung_info(package_number)
                    # Prüfe ob alle gewünschten Veredelungen vorhanden sind
                    veredelung_match = all(veredelung in package_veredelungen for veredelung in veredelung_required)
                    if veredelung_match:
                        package_info['veredelungen'] = package_veredelungen
                        final_matching_packages.append(package_info)
                else:
                    # Keine Veredelungsanforderungen, füge Paket hinzu
                    package_info['veredelungen'] = self.get_veredelung_info(package_number)
                    final_matching_packages.append(package_info)
        
        return final_matching_packages
    
    def get_veredelung_info(self, package_number: str) -> List[str]:
        """Holt Veredelungsinformationen für ein Paket aus Lager_neu."""
        if not self.lager_data or len(self.lager_data) < 181:
            return []
        
        # Paketnummern aus der ersten Zeile extrahieren
        package_numbers = self.lager_data[0][2:]
        
        # Finde die Spalte für dieses Paket
        package_col_idx = None
        for i, pkg_num in enumerate(package_numbers):
            if pkg_num == package_number:
                package_col_idx = i + 2  # +2 weil die Paketnummern ab Spalte 2 stehen
                break
        
        if package_col_idx is None:
            return []
        
        veredelungen = []
        
        # Prüfe Siebdruck (Zeile 179)
        if len(self.lager_data) > 179 and len(self.lager_data[179]) > package_col_idx:
            if self.lager_data[179][package_col_idx] == '1':
                veredelungen.append('Siebdruck')
        
        # Prüfe Digitaldruck (Zeile 180) 
        if len(self.lager_data) > 180 and len(self.lager_data[180]) > package_col_idx:
            if self.lager_data[180][package_col_idx] == '1':
                veredelungen.append('Digitaldruck')
        
        # Prüfe Stick (Zeile 181)
        if len(self.lager_data) > 181 and len(self.lager_data[181]) > package_col_idx:
            if self.lager_data[181][package_col_idx] == '1':
                veredelungen.append('Stick')
        
        return veredelungen
    
    def get_monday_info(self, package_number: str) -> Optional[Dict]:
        """Holt Informationen über ein Paket aus der Monday Tabelle."""
        if not self.monday_data:
            return None
            
        for row in self.monday_data[1:]:  # Ab Zeile 1 (nach Header)
            if not row or len(row) < 1:
                continue
                
            element = row[0]
            if element and f"Probepaket {package_number}" in element:
                return {
                    'element': element,
                    'status': row[2] if len(row) > 2 else 'Unbekannt',
                    'lieferschein': row[3] if len(row) > 3 else None
                }
        
        return None

# Globale Instanz des Finders
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID', "191RsU9uDyRQDIM4UITTY2F8KxalA9uGP497pdWKoRvA")
finder = None

def get_finder():
    """Singleton Pattern für den Finder."""
    global finder
    print(f"🔍 DEBUG: get_finder aufgerufen, finder ist None: {finder is None}")
    if finder is None:
        print(f"🔍 DEBUG: Erstelle neuen ProbepaketFinder mit Spreadsheet ID: {SPREADSHEET_ID}")
        try:
            finder = ProbepaketFinder(SPREADSHEET_ID)
            print("🔍 DEBUG: ProbepaketFinder erfolgreich erstellt")
            print("🔍 DEBUG: Starte load_data...")
            finder.load_data()
            print("🔍 DEBUG: load_data abgeschlossen")
        except Exception as e:
            print(f"❌ DEBUG: Fehler beim Erstellen des Finders: {e}")
            import traceback
            print(f"❌ DEBUG: Traceback: {traceback.format_exc()}")
            raise
    else:
        print("🔍 DEBUG: Verwende existierenden Finder")
    return finder

@app.route('/')
def index():
    """Hauptseite der WebApp."""
    return render_template('index.html')

@app.route('/debug')
def debug():
    """Debug-Seite um Logs anzuzeigen."""
    debug_info = []
    
    # Umgebungsvariablen prüfen
    debug_info.append(f"🔍 GOOGLE_CREDENTIALS_JSON vorhanden: {bool(os.getenv('GOOGLE_CREDENTIALS_JSON'))}")
    debug_info.append(f"🔍 SPREADSHEET_ID: {os.getenv('SPREADSHEET_ID', 'Nicht gesetzt')}")
    
    # Erweiterte Credentials Debug-Informationen
    if os.getenv('GOOGLE_CREDENTIALS_JSON'):
        try:
            credentials_string = os.getenv('GOOGLE_CREDENTIALS_JSON')
            debug_info.append(f"🔍 Credentials Länge: {len(credentials_string)} Zeichen")
            debug_info.append(f"🔍 Erste 100 Zeichen: {credentials_string[:100]}")
            debug_info.append(f"🔍 Letzte 100 Zeichen: {credentials_string[-100:]}")
            debug_info.append(f"🔍 Enthält 'type': {'\"type\"' in credentials_string}")
            debug_info.append(f"🔍 Enthält 'private_key': {'\"private_key\"' in credentials_string}")
            debug_info.append(f"🔍 Enthält 'client_email': {'\"client_email\"' in credentials_string}")
        except Exception as e:
            debug_info.append(f"❌ Fehler beim Analysieren der Credentials: {str(e)}")
    
    # Versuche Finder zu erstellen
    try:
        finder = get_finder()
        debug_info.append(f"✅ Finder erfolgreich erstellt")
        debug_info.append(f"🔍 Farben Daten: {len(finder.farben_data) if finder.farben_data else 0} Zeilen")
        debug_info.append(f"🔍 Monday Daten: {len(finder.monday_data) if finder.monday_data else 0} Zeilen")
        debug_info.append(f"🔍 Lager_neu Daten: {len(finder.lager_data) if finder.lager_data else 0} Zeilen")
        
        # Teste Produkte laden
        products = finder.get_available_products()
        debug_info.append(f"✅ Produkte geladen: {len(products)}")
        debug_info.append(f"🔍 Produkte: {products}")
        
    except Exception as e:
        debug_info.append(f"❌ Fehler beim Erstellen des Finders: {str(e)}")
        import traceback
        debug_info.append(f"❌ Traceback: {traceback.format_exc()}")
    
    # HTML für Debug-Seite
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Debug - Probepaket Finder</title>
        <style>
            body {{ font-family: monospace; margin: 20px; background: #f5f5f5; }}
            .debug-item {{ background: white; margin: 10px 0; padding: 10px; border-radius: 5px; border-left: 4px solid #007bff; }}
            .error {{ border-left-color: #dc3545; }}
            .success {{ border-left-color: #28a745; }}
            .info {{ border-left-color: #17a2b8; }}
            h1 {{ color: #333; }}
            .refresh {{ background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }}
        </style>
    </head>
    <body>
        <h1>🔍 Probepaket Finder Debug</h1>
        <button class="refresh" onclick="location.reload()">🔄 Aktualisieren</button>
        <div style="margin-top: 20px;">
    """
    
    for item in debug_info:
        if "❌" in item:
            html += f'<div class="debug-item error">{item}</div>'
        elif "✅" in item:
            html += f'<div class="debug-item success">{item}</div>'
        else:
            html += f'<div class="debug-item info">{item}</div>'
    
    html += """
        </div>
        <div style="margin-top: 30px;">
            <a href="/" style="color: #007bff;">← Zurück zur Hauptseite</a>
        </div>
    </body>
    </html>
    """
    
    return html

@app.route('/api/products')
def get_products():
    """API Endpoint für verfügbare Produkte."""
    try:
        print("🔍 DEBUG: /api/products aufgerufen")
        finder = get_finder()
        print(f"🔍 DEBUG: Finder erstellt: {finder is not None}")
        print(f"🔍 DEBUG: Farben Daten verfügbar: {finder.farben_data is not None}")
        print(f"🔍 DEBUG: Farben Daten Länge: {len(finder.farben_data) if finder.farben_data else 0}")
        
        products = finder.get_available_products()
        print(f"🔍 DEBUG: Produkte gefunden: {len(products)}")
        print(f"🔍 DEBUG: Produkte: {products}")
        
        return jsonify({
            'success': True,
            'products': products,
            'last_update': finder.last_update.isoformat() if finder.last_update else None
        })
    except Exception as e:
        print(f"❌ DEBUG: Fehler in /api/products: {e}")
        import traceback
        print(f"❌ DEBUG: Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/colors/<product>')
def get_colors(product):
    """API Endpoint für verfügbare Farben eines Produkts."""
    try:
        finder = get_finder()
        colors = finder.get_available_colors(product)
        return jsonify({
            'success': True,
            'colors': colors
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/search', methods=['POST'])
def search_packages():
    """API Endpoint für die Paketsuche."""
    try:
        data = request.get_json()
        
        # Unterstütze sowohl alte (einzelne) als auch neue (mehrere) Suchkriterien
        if 'search_criteria' in data:
            # Neue Format: Liste von Suchkriterien
            search_criteria = data.get('search_criteria', [])
        else:
            # Alte Format: Einzelne Produkt/Farbe für Rückwärtskompatibilität
            product = data.get('product', '')
            color = data.get('color', '')
            if product and color:
                search_criteria = [{'product': product, 'color': color}]
            else:
                search_criteria = []
        
        # Veredelungsanforderungen extrahieren
        veredelung_required = data.get('veredelung_required', [])
        
        finder = get_finder()
        packages = finder.find_matching_packages(search_criteria, veredelung_required)
        
        return jsonify({
            'success': True,
            'packages': packages,
            'search_params': {
                'search_criteria': search_criteria
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/refresh')
def refresh_data():
    """API Endpoint zum Aktualisieren der Daten."""
    try:
        global finder
        finder = ProbepaketFinder(SPREADSHEET_ID)
        finder.load_data()
        
        return jsonify({
            'success': True,
            'message': 'Daten erfolgreich aktualisiert',
            'last_update': finder.last_update.isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)
