# T2024 Vending Machine Controller

Software di controllo e diagnostica per distributori automatici serie **T2024** (ESP32-based).

Il software interagisce con l'hardware tramite API REST HTTP e shell di debug `/debug` per azionamento motori (PWM), bobine/solenoidi di espulsione, lettura sensori infrarossi vassoio (ADC) e manipolazione della memoria EEPROM.

---

## 📁 Struttura del Progetto

```
programma_macchinette/
├── t2024.py          # Script controller principale (CLI)
├── mock_server.py    # Server simulatore per test locali senza hardware
├── requirements.txt  # Dipendenze Python
├── .gitignore        # File ignorati da Git
└── README.md         # Documentazione
```

---

## 🚀 Requisiti e Installazione

1. Assicurati di avere Python 3 installato.
2. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🛠️ Utilizzo

### Modalità Reale (Hardware T2024 su rete 10.4.2.120)

```bash
# Mostra la lista prodotti, slot, prezzi e giacenze
python3 t2024.py list

# Eroga un prodotto casuale
python3 t2024.py random

# Eroga un prodotto da uno slot specifico (es. C2)
python3 t2024.py dispense C2

# Modifica prezzo (ID prodotto, centesimi)
python3 t2024.py price 1 60

# Modifica tutti i prezzi a 1 centesimo
python3 t2024.py all_price 1

# Aggiunge credito virtuale (in centesimi, es. 100 = 1.00 €)
python3 t2024.py credit 100

# Diagnostica (Firmware, temperatura, checksum memoria)
python3 t2024.py check

# Cancella tutti i log diagnostici
python3 t2024.py clean
```

---

### 🧪 Test in Locale con Simulatore (Mock Server)

Per testare il funzionamento dei comandi su qualsiasi computer senza avere la macchinetta fisica:

1. **Avvia il server di simulazione:**
   ```bash
   python3 mock_server.py
   ```
   *(Il server rimarrà in ascolto su `http://localhost:8080`)*

2. **In un altro terminale, invia i comandi impostando `T2024_HOST`:**
   ```bash
   export T2024_HOST="http://localhost:8080"

   python3 t2024.py list
   python3 t2024.py random
   python3 t2024.py check
   python3 t2024.py dispense D0
   ```

---

## 🔌 Hardware Spec (T2024)

- **GPIO 18:** Motor PWM (avanzamento spirale)
- **GPIO 19:** Direzione motore (1 = CW / 0 = CCW)
- **GPIO 20–29:** Solenoidi espulsione (colonne 0–9)
- **GPIO 30–89:** Sensori IR caduta prodotto nel vassoio
- **EEPROM:** Tabella 60 prodotti con offset ID, stock, prezzo e stato attivo
