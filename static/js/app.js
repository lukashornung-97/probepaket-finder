// Probepaket Finder JavaScript

class ProbepaketFinder {
    constructor() {
        this.products = [];
        this.colors = [];
        this.currentProduct = null;
        this.activeFields = 1; // Anzahl der aktiven Suchfelder
        this.maxFields = 4; // Maximale Anzahl der Suchfelder
        this.init();
    }

    async init() {
        await this.loadProducts();
        this.setupEventListeners();
        this.updateLastUpdateTime();
    }

    async loadProducts() {
        try {
            const response = await fetch('/api/products');
            const data = await response.json();
            
            if (data.success) {
                this.products = data.products;
                this.populateProductSelect();
                this.updateLastUpdateTime(data.last_update);
            } else {
                this.showToast('Fehler beim Laden der Produkte: ' + data.error, 'error');
            }
        } catch (error) {
            this.showToast('Fehler beim Laden der Produkte: ' + error.message, 'error');
        }
    }

    populateProductSelect() {
        // Alle Produkt-Selects befüllen
        for (let i = 1; i <= this.maxFields; i++) {
            const productSelect = document.getElementById(`productSelect${i}`);
            if (productSelect) {
                productSelect.innerHTML = '<option value="">Produkt auswählen...</option>';
                
                this.products.forEach(product => {
                    const option = document.createElement('option');
                    option.value = product;
                    option.textContent = product;
                    productSelect.appendChild(option);
                });
            }
        }
    }

    async loadColors(product, fieldNumber) {
        if (!product) {
            this.clearColorSelect(fieldNumber);
            return;
        }

        try {
            const response = await fetch(`/api/colors/${encodeURIComponent(product)}`);
            const data = await response.json();
            
            if (data.success) {
                this.populateColorSelect(fieldNumber, data.colors);
            } else {
                this.showToast('Fehler beim Laden der Farben: ' + data.error, 'error');
            }
        } catch (error) {
            this.showToast('Fehler beim Laden der Farben: ' + error.message, 'error');
        }
    }

    populateColorSelect(fieldNumber, colors) {
        const colorSelect = document.getElementById(`colorSelect${fieldNumber}`);
        if (colorSelect) {
            colorSelect.innerHTML = '<option value="">Farbe auswählen...</option>';
            
            colors.forEach(color => {
                const option = document.createElement('option');
                option.value = color;
                option.textContent = color;
                colorSelect.appendChild(option);
            });
            
            colorSelect.disabled = false;
        }
    }

    clearColorSelect(fieldNumber) {
        const colorSelect = document.getElementById(`colorSelect${fieldNumber}`);
        if (colorSelect) {
            colorSelect.innerHTML = '<option value="">Zuerst ein Produkt auswählen</option>';
            colorSelect.disabled = true;
        }
    }

    setupEventListeners() {
        // Event Listeners für alle Produkt-Selects
        for (let i = 1; i <= this.maxFields; i++) {
            const productSelect = document.getElementById(`productSelect${i}`);
            if (productSelect) {
                productSelect.addEventListener('change', (e) => {
                    const selectedProduct = e.target.value;
                    const fieldNumber = i;
                    
                    if (selectedProduct) {
                        this.loadColors(selectedProduct, fieldNumber);
                    } else {
                        this.clearColorSelect(fieldNumber);
                    }
                });
            }
        }

        // Suchformular
        document.getElementById('searchForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.performSearch();
        });
    }

    async performSearch() {
        // Sammle alle Suchkriterien
        const searchCriteria = [];
        
        for (let i = 1; i <= this.activeFields; i++) {
            const productSelect = document.getElementById(`productSelect${i}`);
            const colorSelect = document.getElementById(`colorSelect${i}`);
            
            if (productSelect && colorSelect) {
                const product = productSelect.value;
                const color = colorSelect.value;
                
                if (product && color) {
                    searchCriteria.push({
                        product: product,
                        color: color
                    });
                }
            }
        }

        if (searchCriteria.length === 0) {
            this.showToast('Bitte wähle mindestens ein Produkt und eine Farbe aus.', 'warning');
            return;
        }

        // Sammle Veredelungsanforderungen
        const veredelungRequired = [];
        const veredelungCheckboxes = ['veredelungSiebdruck', 'veredelungDigitaldruck', 'veredelungStick'];
        
        veredelungCheckboxes.forEach(id => {
            const checkbox = document.getElementById(id);
            if (checkbox && checkbox.checked) {
                veredelungRequired.push(checkbox.value);
            }
        });

        this.showLoading(true);
        this.hideResults();

        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    search_criteria: searchCriteria,
                    veredelung_required: veredelungRequired
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.displayResults(data.packages, data.search_params);
            } else {
                this.showToast('Fehler bei der Suche: ' + data.error, 'error');
            }
        } catch (error) {
            this.showToast('Fehler bei der Suche: ' + error.message, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    displayResults(packages, searchParams) {
        const resultsSection = document.getElementById('resultsSection');
        const noResultsSection = document.getElementById('noResultsSection');
        const searchInfo = document.getElementById('searchInfo');
        const packagesList = document.getElementById('packagesList');

        // Suchinfo anzeigen
        const criteria = searchParams.search_criteria || [];
        const searchText = criteria.map(c => `${c.product} (${c.color})`).join(', ');
        
        searchInfo.innerHTML = `
            <i class="fas fa-info-circle me-2"></i>
            Suche nach: <strong>${searchText}</strong>
            <span class="float-end">${packages.length} Pakete gefunden</span>
        `;

        if (packages.length === 0) {
            resultsSection.style.display = 'none';
            noResultsSection.style.display = 'block';
            noResultsSection.classList.add('fade-in');
        } else {
            noResultsSection.style.display = 'none';
            resultsSection.style.display = 'block';
            resultsSection.classList.add('fade-in');

            // Pakete anzeigen
            packagesList.innerHTML = '';
            packages.forEach((pkg, index) => {
                const packageCard = this.createPackageCard(pkg, index);
                packagesList.appendChild(packageCard);
            });
        }
    }

    createPackageCard(pkg, index) {
        const card = document.createElement('div');
        card.className = 'package-card slide-in';
        card.style.animationDelay = `${index * 0.1}s`;

        const statusClass = this.getStatusClass(pkg.status);
        const statusText = this.getStatusText(pkg.status);

        // Produktliste anzeigen (für mehrere Produkte)
        let productList = '';
        if (pkg.produkte && pkg.produkte.length > 0) {
            productList = pkg.produkte.map(prod => 
                `${prod.produkt} (${prod.groesse}) - ${prod.farbe}`
            ).join('<br>');
        } else if (pkg.produkt && pkg.groesse && pkg.farbe) {
            productList = `${pkg.produkt} (${pkg.groesse}) - ${pkg.farbe}`;
        } else {
            productList = pkg.element || '';
        }

        card.innerHTML = `
            <div class="row align-items-center">
                <div class="col-md-3">
                    <div class="package-number">#${pkg.nummer || 'N/A'}</div>
                    <small class="text-muted">${pkg.element || ''}</small>
                </div>
                <div class="col-md-2">
                    <span class="package-status ${statusClass}">${statusText}</span>
                </div>
                <div class="col-md-4">
                    <small class="text-muted">
                        <i class="fas fa-box me-1"></i>
                        Enthaltene Produkte:
                    </small>
                    <br>
                    <small class="text-primary">${productList}</small>
                    ${pkg.veredelungen && pkg.veredelungen.length > 0 ? `
                        <br>
                        <small class="text-muted">
                            <i class="fas fa-magic me-1"></i>
                            Veredelungen:
                        </small>
                        <br>
                        <small class="text-success">
                            ${pkg.veredelungen.map(v => `<span class="badge bg-success me-1">${v}</span>`).join('')}
                        </small>
                    ` : ''}
                </div>
                <div class="col-md-3 text-end">
                    ${pkg.lieferschein ? `
                        <a href="${pkg.lieferschein}" target="_blank" class="btn btn-sm btn-outline-primary">
                            <i class="fas fa-file-pdf me-1"></i>
                            Lieferschein
                        </a>
                    ` : ''}
                </div>
            </div>
        `;

        return card;
    }

    getStatusClass(status) {
        if (!status) return 'status-unknown';
        
        const statusLower = status.toLowerCase();
        if (statusLower.includes('lager')) return 'status-available';
        if (statusLower.includes('reserviert')) return 'status-reserved';
        if (statusLower.includes('versendet') || statusLower.includes('gesendet')) return 'status-sent';
        
        return 'status-unknown';
    }

    getStatusText(status) {
        if (!status) return 'Unbekannt';
        
        const statusLower = status.toLowerCase();
        if (statusLower.includes('lager')) return 'Verfügbar';
        if (statusLower.includes('reserviert')) return 'Reserviert';
        if (statusLower.includes('versendet') || statusLower.includes('gesendet')) return 'Versendet';
        
        return status;
    }

    showLoading(show) {
        const loadingSection = document.getElementById('loadingSection');
        loadingSection.style.display = show ? 'block' : 'none';
    }

    hideResults() {
        document.getElementById('resultsSection').style.display = 'none';
        document.getElementById('noResultsSection').style.display = 'none';
    }

    async refreshData() {
        try {
            this.showToast('Daten werden aktualisiert...', 'info');
            
            const response = await fetch('/api/refresh');
            const data = await response.json();
            
            if (data.success) {
                this.showToast('Daten erfolgreich aktualisiert!', 'success');
                await this.loadProducts();
                this.updateLastUpdateTime(data.last_update);
            } else {
                this.showToast('Fehler beim Aktualisieren: ' + data.error, 'error');
            }
        } catch (error) {
            this.showToast('Fehler beim Aktualisieren: ' + error.message, 'error');
        }
    }

    updateLastUpdateTime(timestamp) {
        const lastUpdateElement = document.getElementById('lastUpdate');
        if (timestamp) {
            const date = new Date(timestamp);
            lastUpdateElement.textContent = date.toLocaleString('de-DE');
        } else {
            lastUpdateElement.textContent = 'Nie';
        }
    }

    showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        const toastBody = document.getElementById('toastBody');
        
        // Toast Header Icon basierend auf Typ
        const toastHeader = toast.querySelector('.toast-header i');
        toastHeader.className = this.getToastIcon(type);
        
        // Toast Body
        toastBody.textContent = message;
        
        // Toast anzeigen
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    }

    getToastIcon(type) {
        switch (type) {
            case 'success':
                return 'fas fa-check-circle text-success me-2';
            case 'error':
                return 'fas fa-exclamation-circle text-danger me-2';
            case 'warning':
                return 'fas fa-exclamation-triangle text-warning me-2';
            default:
                return 'fas fa-info-circle text-primary me-2';
        }
    }

    addSearchField() {
        if (this.activeFields < this.maxFields) {
            this.activeFields++;
            const fieldElement = document.querySelector(`[data-field="${this.activeFields}"]`);
            if (fieldElement) {
                fieldElement.style.display = 'block';
                fieldElement.classList.add('fade-in');
                
                // Produkt-Select befüllen
                const productSelect = document.getElementById(`productSelect${this.activeFields}`);
                if (productSelect) {
                    productSelect.innerHTML = '<option value="">Produkt auswählen...</option>';
                    this.products.forEach(product => {
                        const option = document.createElement('option');
                        option.value = product;
                        option.textContent = product;
                        productSelect.appendChild(option);
                    });
                }
                
                // Event Listener hinzufügen
                if (productSelect) {
                    productSelect.addEventListener('change', (e) => {
                        const selectedProduct = e.target.value;
                        const fieldNumber = this.activeFields;
                        
                        if (selectedProduct) {
                            this.loadColors(selectedProduct, fieldNumber);
                        } else {
                            this.clearColorSelect(fieldNumber);
                        }
                    });
                }
                
                // "Weitere Suche hinzufügen" Button verstecken wenn Maximum erreicht
                if (this.activeFields >= this.maxFields) {
                    const addBtn = document.getElementById('addFieldBtn');
                    if (addBtn) {
                        addBtn.style.display = 'none';
                    }
                }
            }
        }
    }

    removeSearchField(fieldNumber) {
        if (fieldNumber > 1 && fieldNumber <= this.activeFields) {
            // Feld verstecken
            const fieldElement = document.querySelector(`[data-field="${fieldNumber}"]`);
            if (fieldElement) {
                fieldElement.style.display = 'none';
                
                // Werte zurücksetzen
                const productSelect = document.getElementById(`productSelect${fieldNumber}`);
                const colorSelect = document.getElementById(`colorSelect${fieldNumber}`);
                
                if (productSelect) productSelect.value = '';
                if (colorSelect) {
                    colorSelect.value = '';
                    colorSelect.disabled = true;
                    colorSelect.innerHTML = '<option value="">Zuerst ein Produkt auswählen</option>';
                }
            }
            
            // Alle nachfolgenden Felder nach oben verschieben
            for (let i = fieldNumber + 1; i <= this.activeFields; i++) {
                const currentField = document.querySelector(`[data-field="${i}"]`);
                const prevField = document.querySelector(`[data-field="${i - 1}"]`);
                
                if (currentField && prevField) {
                    // Werte kopieren
                    const currentProduct = document.getElementById(`productSelect${i}`);
                    const currentColor = document.getElementById(`colorSelect${i}`);
                    const prevProduct = document.getElementById(`productSelect${i - 1}`);
                    const prevColor = document.getElementById(`colorSelect${i - 1}`);
                    
                    if (currentProduct && prevProduct) {
                        prevProduct.value = currentProduct.value;
                    }
                    if (currentColor && prevColor) {
                        prevColor.value = currentColor.value;
                        prevColor.disabled = currentColor.disabled;
                        prevColor.innerHTML = currentColor.innerHTML;
                    }
                    
                    // Aktuelles Feld zurücksetzen
                    if (currentProduct) currentProduct.value = '';
                    if (currentColor) {
                        currentColor.value = '';
                        currentColor.disabled = true;
                        currentColor.innerHTML = '<option value="">Zuerst ein Produkt auswählen</option>';
                    }
                }
            }
            
            // Letztes Feld verstecken
            const lastField = document.querySelector(`[data-field="${this.activeFields}"]`);
            if (lastField) {
                lastField.style.display = 'none';
            }
            
            this.activeFields--;
            
            // "Weitere Suche hinzufügen" Button wieder anzeigen
            const addBtn = document.getElementById('addFieldBtn');
            if (addBtn && this.activeFields < this.maxFields) {
                addBtn.style.display = 'inline-block';
            }
            
            // Delete-Button für Feld 1 verstecken
            const deleteBtn1 = document.querySelector('[onclick="removeSearchField(1)"]');
            if (deleteBtn1) {
                deleteBtn1.style.display = this.activeFields > 1 ? 'inline-block' : 'none';
            }
        }
    }
}

// Globale Funktionen
function refreshData() {
    if (window.probepaketFinder) {
        window.probepaketFinder.refreshData();
    }
}

function addSearchField() {
    if (window.probepaketFinder) {
        window.probepaketFinder.addSearchField();
    }
}

function removeSearchField(fieldNumber) {
    if (window.probepaketFinder) {
        window.probepaketFinder.removeSearchField(fieldNumber);
    }
}

// App initialisieren wenn DOM geladen ist
document.addEventListener('DOMContentLoaded', () => {
    window.probepaketFinder = new ProbepaketFinder();
});
