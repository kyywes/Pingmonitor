# 🔄 Sistema di Auto-Patching PingMonitor Pro v2.3

## Come Funziona

Il sistema di **Auto-Patching** rileva automaticamente le modifiche al codice sorgente e le applica senza dover ricompilare o reinstallare l'applicazione.

---

## 🚀 Metodi di Avvio

### 1. **START_PINGMONITOR.bat** ⭐ (RACCOMANDATO)
**Smart Launcher con Auto-Patching Automatico**

```bash
START_PINGMONITOR.bat
```

**Cosa fa:**
- ✅ Controlla automaticamente se ci sono modifiche al codice sorgente
- ✅ Se rileva modifiche → Avvia dal codice Python (applica patch)
- ✅ Se non rileva modifiche → Avvia dall'exe compilato (performance ottimali)
- ✅ Notifica l'utente quando vengono applicate patch

**Quando usarlo:**
- Uso quotidiano normale
- Quando vuoi avere sempre l'ultima versione del codice
- Dopo aver modificato file .py

---

### 2. **START_DIRECT.bat**
**Avvio Diretto dal Codice Sorgente (Sviluppo)**

```bash
START_DIRECT.bat
```

**Cosa fa:**
- ⚡ Avvia sempre direttamente dal codice Python
- ⚡ Non controlla modifiche (più veloce)
- ⚡ Utile per sviluppo e debug

**Quando usarlo:**
- Durante lo sviluppo
- Quando stai testando modifiche multiple
- Debug e troubleshooting

---

### 3. **smart_launcher.py**
**Launcher Python Avanzato**

```bash
python smart_launcher.py
```

**Cosa fa:**
- 🔧 Versione Python pura del launcher
- 🔧 Stessa logica di START_PINGMONITOR.bat
- 🔧 Multipiattaforma (Windows/Linux/macOS)

---

## 📊 Sistema di Versioning

### Come Rileva le Modifiche

Il sistema calcola un **hash MD5** di ogni file .py nella cartella `src/`:

```
src/
├── core/
│   ├── config_manager.py    → hash: abc123...
│   ├── logger.py             → hash: def456...
│   └── monitoring_engine.py  → hash: ghi789...
├── ui/
│   └── main_window_v2.py     → hash: jkl012...
└── ...
```

Gli hash vengono salvati in:
```
C:\Users\<username>\.pingmonitor\version.json
```

### Prima Esecuzione

```json
{
  "timestamp": "2025-11-03T22:00:00",
  "file_count": 38,
  "file_hashes": {
    "core/config_manager.py": "abc123...",
    "core/logger.py": "def456...",
    "ui/main_window_v2.py": "jkl012...",
    ...
  }
}
```

### Dopo una Modifica

**Scenario:** Modifichi `src/ui/main_window_v2.py`

1. **All'avvio**, il sistema:
   - Calcola hash di tutti i file
   - Confronta con version.json
   - Rileva che `main_window_v2.py` ha hash diverso

2. **Output nel log:**
   ```
   ======================================================================
   AUTO-PATCH: Checking for source code updates...
   ======================================================================
   [MODIFIED] ui/main_window_v2.py
   Found 1 changes in source code!
     - Modified: 1
     - New: 0
     - Deleted: 0
   🔄 AUTO-PATCH DETECTED!
   🔄 1 files have been modified
   🔄 Changes will be applied automatically
   ======================================================================
   ```

3. **Il launcher**:
   - Rileva la modifica
   - Avvia l'app dal codice Python invece dell'exe
   - **Le modifiche sono applicate immediatamente!**

---

## 🔧 File di Configurazione

### `version.json`
Posizione: `C:\Users\<username>\.pingmonitor\version.json`

**Contiene:**
- Timestamp dell'ultimo snapshot
- Numero di file monitorati
- Hash MD5 di ogni file sorgente

**Quando viene aggiornato:**
- Primo avvio dell'app
- Ogni volta che rileva modifiche

**Puoi eliminarlo** se vuoi forzare un nuovo snapshot:
```bash
del C:\Users\%USERNAME%\.pingmonitor\version.json
```

---

## 📝 Esempi Pratici

### Esempio 1: Modifica la Tabella Device

**Prima:**
```python
# src/ui/main_window_v2.py:530
self.monitoring_table.setColumnCount(9)
```

**Modifichi in:**
```python
# src/ui/main_window_v2.py:530
self.monitoring_table.setColumnCount(10)  # Aggiunta colonna
```

**Salvi il file** → Chiudi l'app → Lanci `START_PINGMONITOR.bat`

**Output:**
```
AUTO-PATCH: Checking for source code updates...
[MODIFIED] ui/main_window_v2.py
Found 1 changes in source code!
🔄 AUTO-PATCH DETECTED!
📦 UPDATES DETECTED - APPLYING PATCH
Avvio in modalità AUTO-PATCH dal codice Python...
```

✅ **La modifica è applicata senza reinstallare!**

---

### Esempio 2: Nessuna Modifica

**Lanci l'app normalmente**

**Output:**
```
AUTO-PATCH: Checking for source code updates...
No source code changes detected
No updates found - using compiled exe for better performance
🚀 LAUNCHING FROM COMPILED EXE
```

✅ **Usa l'exe per performance ottimali**

---

## 🎯 Vantaggi del Sistema

1. **✅ Zero Ricompilazione**
   - Non devi mai rifare il build
   - Non serve reinstallare

2. **✅ Modifiche Immediate**
   - Modifichi il codice
   - Riavvii l'app
   - Le modifiche sono applicate

3. **✅ Performance Ottimali**
   - Se non ci sono modifiche → Usa exe (veloce)
   - Se ci sono modifiche → Usa codice (aggiornato)

4. **✅ Tracciabilità**
   - Sai sempre quando sono state applicate modifiche
   - Log dettagliati di ogni modifica rilevata

5. **✅ Sicurezza**
   - Ogni file è verificato tramite hash
   - Nessuna modifica passa inosservata

---

## 🔍 Diagnostica

### Verifica Stato Versioning

**Controlla il file version.json:**
```bash
type C:\Users\%USERNAME%\.pingmonitor\version.json
```

**Dovresti vedere:**
```json
{
  "timestamp": "2025-11-03T22:14:31.123456",
  "file_count": 38,
  "file_hashes": {
    ...
  }
}
```

### Forza Nuovo Snapshot

**Elimina version.json:**
```bash
del C:\Users\%USERNAME%\.pingmonitor\version.json
START_PINGMONITOR.bat
```

L'app creerà un nuovo snapshot baseline.

---

## 📋 Troubleshooting

### Problema: "Version check failed"

**Causa:** Errore nel calcolo degli hash

**Soluzione:**
```bash
del C:\Users\%USERNAME%\.pingmonitor\version.json
START_DIRECT.bat
```

---

### Problema: "Le modifiche non vengono applicate"

**Verifica:**
1. Hai salvato il file modificato?
2. Stai usando `START_PINGMONITOR.bat`?
3. Il file version.json esiste?

**Soluzione:**
```bash
# Forza rilevamento modifiche
del C:\Users\%USERNAME%\.pingmonitor\version.json
START_PINGMONITOR.bat
```

---

### Problema: "L'app è lenta"

**Causa:** Stai usando codice Python invece dell'exe

**Verifica:**
- Se non hai fatto modifiche, usa l'exe
- Elimina version.json per resettare

**Soluzione:**
```bash
del C:\Users\%USERNAME%\.pingmonitor\version.json
START_PINGMONITOR.bat
```

L'app userà l'exe se non rileva modifiche.

---

## 🎓 Best Practices

1. **✅ Usa START_PINGMONITOR.bat per uso normale**
   - Gestisce automaticamente tutto
   - Ottima performance

2. **✅ Usa START_DIRECT.bat durante sviluppo**
   - Più veloce per test rapidi
   - Non controlla modifiche

3. **✅ Tieni version.json**
   - Non eliminarlo se non necessario
   - Ottimizza i controlli

4. **✅ Monitora i log**
   - Controlla C:\Users\<username>\.pingmonitor\logs\
   - Verifica quando vengono applicate patch

---

## 📞 Supporto

**Autore:** Fabrizio Cerchia
**Versione:** 2.3.0
**Sistema:** Auto-Patching con Version Checker MD5

**Log Path:** `C:\Users\<username>\.pingmonitor\logs\`
**Config Path:** `C:\Users\<username>\.pingmonitor\version.json`

---

**🎉 Buon monitoraggio con auto-patching automatico!**
