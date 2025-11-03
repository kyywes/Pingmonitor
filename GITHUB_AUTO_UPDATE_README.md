# 🌐 GitHub Auto-Update System

Sistema di aggiornamento automatico da repository GitHub per PingMonitor Pro.

---

## 🎯 Cosa Fa

Il sistema **GitHub Auto-Update** permette di:
- ✅ **Distribuire patch** a tutti i PC dove è installato PingMonitor
- ✅ **Controllo automatico** all'avvio dell'app (silenzioso)
- ✅ **Download automatico** delle modifiche dal tuo repository GitHub
- ✅ **Applicazione one-click** con backup automatico
- ✅ **Rollback** in caso di problemi
- ✅ **Restart automatico** dopo l'aggiornamento

---

## 🚀 Setup Iniziale

### Passo 1: Crea Repository GitHub

1. Vai su https://github.com/new
2. Crea un nuovo repository (es: `PingMonitorPro`)
3. Puoi renderlo:
   - **Pubblico** (tutti possono vedere)
   - **Privato** (solo tu con token)

### Passo 2: Carica il Codice Sorgente

```bash
cd C:\Users\fab\Desktop\PingMonitorPro_v2\PingMonitorPro_v2

# Inizializza git (se non già fatto)
git init

# Aggiungi remote
git remote add origin https://github.com/TUO_USERNAME/PingMonitorPro.git

# Aggiungi file
git add src/
git add requirements.txt
git add README.md

# Primo commit
git commit -m "Initial commit - PingMonitor Pro v2.3"

# Push
git push -u origin main
```

### Passo 3: Genera Personal Access Token (se repo privato)

1. Vai su https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Nome: `PingMonitor Auto-Update`
4. Scadenza: No expiration (o quella che preferisci)
5. Seleziona permessi:
   - ✅ `repo` (Full control of private repositories)
6. Click "Generate token"
7. **COPIA IL TOKEN** (non potrai più vederlo!)

### Passo 4: Configura GitHub Auto-Update

#### Metodo A: Script Automatico (RACCOMANDATO)

```bash
SETUP_GITHUB.bat
```

Segui il wizard interattivo.

#### Metodo B: Manuale

```bash
venv\Scripts\python.exe setup_github.py
```

**Inserisci:**
1. Repository URL: `https://github.com/TUO_USERNAME/PingMonitorPro.git`
2. Branch: `main` (o quello che usi)
3. Token: `ghp_xxxxxxxxxxxxx` (se privato)

---

## 📤 Come Pubblicare una Patch

### Su questo PC (Sviluppo)

Quando modifichi il codice:

```bash
cd C:\Users\fab\Desktop\PingMonitorPro_v2\PingMonitorPro_v2

# 1. Modifica file in src/
# (es: src/ui/main_window_v2.py)

# 2. Commit modifiche
git add src/
git commit -m "Fix: corretto bug nella tabella device"

# 3. Push su GitHub
git push
```

**Fatto!** 🎉 La patch è ora disponibile per tutti i PC.

---

## 📥 Come Si Aggiornano gli Altri PC

### Automaticamente (Senza Intervento)

**All'avvio di PingMonitor:**

1. ✅ L'app controlla GitHub in modo silenzioso
2. ✅ Se trova nuovi commit, mostra notifica
3. ✅ L'utente clicca "Installa Ora"
4. ✅ L'app scarica, applica patch e riavvia

**Nessuna azione richiesta all'utente!**

### Flusso Completo

```
PC Sviluppo (tuo)          GitHub              PC Produzione (cliente)
     │                       │                         │
     │ 1. Modifichi codice   │                         │
     │ 2. git push ────────> │                         │
     │                       │                         │
     │                       │ <──── 3. Avvia app      │
     │                       │ 4. Check updates ────>  │
     │                       │ <──── 5. Download       │
     │                       │                         │
     │                       │      6. Mostra popup ──>│
     │                       │      "Aggiornamento     │
     │                       │       disponibile"      │
     │                       │                         │
     │                       │ <──── 7. Click "Installa"
     │                       │ 8. Download src/ ────>  │
     │                       │                         │
     │                       │      9. Applica patch ──│
     │                       │      10. Backup ────────│
     │                       │      11. Copia file ────│
     │                       │      12. Restart app ───│
     │                       │                         │
     │                       │      ✅ AGGIORNATO!     │
```

---

## 🔧 Dettagli Tecnici

### File di Configurazione

**GitHub Config:** `C:\Users\<username>\.pingmonitor\github_config.json`

```json
{
  "repo_url": "https://github.com/tuousername/PingMonitorPro.git",
  "branch": "main",
  "token": "ghp_xxxxx...",
  "configured_at": "2025-11-03T22:30:00"
}
```

**GitHub State:** `C:\Users\<username>\.pingmonitor\github_state.json`

```json
{
  "last_commit_hash": "a1b2c3d4...",
  "last_update": "2025-11-03T23:00:00",
  "backup_path": "C:\\Users\\fab\\.pingmonitor\\backups\\backup_20251103_230000",
  "copied_files": 38
}
```

### Directory Backup

**Path:** `C:\Users\<username>\.pingmonitor\backups\`

Contiene gli ultimi 5 backup automatici di `src/`.

**Rollback manuale:**
```bash
# Vedi backup disponibili
dir C:\Users\%USERNAME%\.pingmonitor\backups

# Ripristina manualmente (esempio)
xcopy /E /I /Y C:\Users\%USERNAME%\.pingmonitor\backups\backup_20251103_230000\* src\
```

### Come Funziona il Check

1. **Clone Shallow:** Scarica solo l'ultimo commit (veloce)
2. **Hash Comparison:** Confronta hash commit remoto vs locale
3. **Se diversi:** Mostra notifica update disponibile
4. **Download:** Clone in directory temporanea
5. **Backup:** Crea backup `src/` corrente
6. **Apply:** Copia file da temp a `src/`
7. **Cleanup:** Elimina temp directory
8. **Restart:** Riavvia app per applicare modifiche

---

## 🎨 UI dell'Utente

### Popup Aggiornamento

```
┌───────────────────────────────────────┐
│  🌐 Aggiornamento Disponibile        │
├───────────────────────────────────────┤
│                                       │
│  È disponibile un aggiornamento       │
│  da GitHub!                           │
│                                       │
│  Commit: a1b2c3d4                     │
│  Messaggio: Fix bug tabella device    │
│                                       │
│  Vuoi scaricare e installare          │
│  l'aggiornamento ora?                 │
│                                       │
│  L'applicazione verrà riavviata       │
│  dopo l'aggiornamento.                │
│                                       │
│  [  Installa Ora  ] [ Più Tardi ]    │
└───────────────────────────────────────┘
```

### Progress Dialog

```
┌───────────────────────────────────────┐
│  Aggiornamento GitHub                │
├───────────────────────────────────────┤
│                                       │
│  Download e applicazione              │
│  aggiornamento in corso...            │
│                                       │
│  ████████████████████░░░  80%        │
│                                       │
└───────────────────────────────────────┘
```

### Success Dialog

```
┌───────────────────────────────────────┐
│  ✅ Aggiornamento Completato         │
├───────────────────────────────────────┤
│                                       │
│  Aggiornamento installato             │
│  con successo!                        │
│                                       │
│  Successfully applied 38 file updates │
│                                       │
│  L'applicazione verrà riavviata       │
│  per applicare le modifiche.          │
│                                       │
│  [            OK            ]         │
└───────────────────────────────────────┘
```

---

## 🧪 Testing

### Test 1: Controllo Funzionamento

```bash
# 1. Configura GitHub
SETUP_GITHUB.bat

# 2. Inserisci dati repository

# 3. Test connessione
# (lo script ti chiederà se vuoi testare)
```

### Test 2: Simulare Aggiornamento

```bash
# Su PC sviluppo:
# 1. Modifica un file
echo "# Test update" >> src/test_update.txt

# 2. Commit
git add src/test_update.txt
git commit -m "Test: file di test per update"

# 3. Push
git push

# Su altro PC:
# 1. Avvia PingMonitor
START_PINGMONITOR.bat

# 2. Dovresti vedere popup aggiornamento
# 3. Click "Installa Ora"
# 4. L'app scarica, applica e riavvia
```

### Test 3: Rollback

```bash
# Se qualcosa va storto durante update:
venv\Scripts\python.exe -c "from src.utils.github_updater import GitHubUpdater; updater = GitHubUpdater(); updater.rollback()"
```

---

## 📋 Troubleshooting

### Problema: "Git not found"

**Causa:** Git non installato

**Soluzione:**
```bash
# Scarica e installa Git
https://git-scm.com/download/win

# Riavvia terminale
# Verifica installazione
git --version
```

---

### Problema: "Authentication failed"

**Causa:** Token errato o scaduto

**Soluzione:**
```bash
# 1. Genera nuovo token su GitHub
https://github.com/settings/tokens

# 2. Riconfigura
SETUP_GITHUB.bat
```

---

### Problema: "Failed to clone repository"

**Causa:** URL repository errato

**Soluzione:**
```bash
# Verifica URL corretto
# Su GitHub, vai al tuo repository
# Click "Code" → Copia URL

# Esempio corretto:
https://github.com/tuousername/PingMonitorPro.git

# Riconfigura con URL corretto
SETUP_GITHUB.bat
```

---

### Problema: "Update failed - rollback needed"

**Causa:** Errore durante applicazione patch

**Soluzione automatica:**
- Il sistema esegue rollback automatico
- Torna alla versione precedente

**Soluzione manuale:**
```bash
# Vedi backup disponibili
dir C:\Users\%USERNAME%\.pingmonitor\backups

# Copia backup più recente
xcopy /E /I /Y C:\Users\%USERNAME%\.pingmonitor\backups\backup_XXXXXXXXX_XXXXXX\* src\
```

---

## 🔒 Sicurezza

### Token Storage

**⚠️ IMPORTANTE:**
- Il token è salvato in `github_config.json`
- Attualmente **NON** criptato (TODO: criptare)
- File path: `C:\Users\<username>\.pingmonitor\github_config.json`

**Per proteggere:**
```bash
# Imposta permessi file (solo tuo utente)
icacls C:\Users\%USERNAME%\.pingmonitor\github_config.json /inheritance:r /grant:r "%USERNAME%:F"
```

### Repository Privato vs Pubblico

**Pubblico:**
- ✅ Nessun token necessario
- ❌ Tutti possono vedere il codice

**Privato:**
- ✅ Solo tu vedi il codice
- ⚠️ Richiede token (rischio se compromesso)

**Raccomandazione:** Usa repository **pubblico** se non ci sono segreti nel codice.

---

## 📊 Monitoraggio

### Log GitHub Updates

**Path:** `C:\Users\<username>\.pingmonitor\logs\`

**Cerca:**
```
🔍 GITHUB AUTO-UPDATE: Checking for updates...
🆕 NEW UPDATES AVAILABLE!
📦 APPLYING GITHUB UPDATES...
✅ UPDATES APPLIED SUCCESSFULLY!
```

### Stato Ultimo Update

```bash
venv\Scripts\python.exe -c "from src.utils.github_updater import GitHubUpdater; print(GitHubUpdater().get_update_info())"
```

Output:
```python
{
  'configured': True,
  'repo_url': 'https://github.com/tuousername/PingMonitorPro.git',
  'branch': 'main',
  'last_update': '2025-11-03T23:00:00',
  'last_commit': 'a1b2c3d4',
  'configured_at': '2025-11-03T22:30:00'
}
```

---

## 🎓 Best Practices

### 1. Commit Message Chiari

```bash
# ❌ Cattivo
git commit -m "fix"

# ✅ Buono
git commit -m "Fix: corretto errore tabella device (colonna mancante)"
```

### 2. Test Prima di Push

```bash
# Testa localmente prima di pubblicare
START_DIRECT.bat

# Verifica funzionamento
# Solo dopo: git push
```

### 3. Changelog

Mantieni un file `CHANGELOG.md`:

```markdown
# Changelog

## [2.3.1] - 2025-11-03
### Fixed
- Corretto bug nella tabella device
- Rimosso menu SSH ridondante

### Added
- Sistema auto-update da GitHub
```

### 4. Tag Versioni

```bash
# Tagga versioni importanti
git tag -a v2.3.1 -m "Version 2.3.1 - GitHub Auto-Update"
git push --tags
```

---

## 🌟 Vantaggi

1. **✅ Zero Distribuzione Manuale**
   - Pubblichi una volta su GitHub
   - Tutti i PC si aggiornano automaticamente

2. **✅ Controllo Versione**
   - Storico completo modifiche
   - Rollback facile a qualsiasi versione

3. **✅ Sicurezza**
   - Backup automatici
   - Rollback in caso errori

4. **✅ Trasparenza**
   - Utenti vedono cosa cambia
   - Commit message chiari

5. **✅ Scalabilità**
   - 1 PC o 1000 PC: stesso processo
   - Nessun server di distribuzione necessario

---

## 📞 Supporto

**Autore:** Fabrizio Cerchia
**Sistema:** GitHub Auto-Update v1.0

**File Path:**
- Updater: `src/utils/github_updater.py`
- Config: `C:\Users\<username>\.pingmonitor\github_config.json`
- Backups: `C:\Users\<username>\.pingmonitor\backups\`

---

**🎉 Aggiornamenti distribuiti facilmente con GitHub!**
