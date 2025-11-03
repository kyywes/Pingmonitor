# ⚡ GitHub Auto-Update - Guida Rapida

## 🚀 Setup in 5 Minuti

### 1. Crea Repository GitHub

```bash
https://github.com/new
Nome: PingMonitorPro
Tipo: Pubblico (o Privato se preferisci)
```

### 2. Carica Codice

```bash
cd C:\Users\fab\Desktop\PingMonitorPro_v2\PingMonitorPro_v2

git init
git remote add origin https://github.com/TUO_USERNAME/PingMonitorPro.git
git add src/ requirements.txt README.md
git commit -m "Initial commit"
git push -u origin main
```

### 3. Genera Token (solo se repo privato)

```bash
https://github.com/settings/tokens
→ Generate new token (classic)
→ Seleziona: repo ✓
→ Copia token: ghp_xxxxxxxxxxxxx
```

### 4. Configura PingMonitor

```bash
SETUP_GITHUB.bat
```

Inserisci:
- URL: `https://github.com/TUO_USERNAME/PingMonitorPro.git`
- Branch: `main`
- Token: `ghp_xxxxx` (se privato)

### 5. Fatto! ✅

---

## 📤 Pubblica Modifiche

```bash
# 1. Modifica codice
notepad src/ui/main_window_v2.py

# 2. Commit
git add src/
git commit -m "Fix: bug xyz"

# 3. Push
git push
```

**Tutti i PC riceveranno l'aggiornamento al prossimo avvio!**

---

## 📥 Installa su Nuovo PC

### Opzione A: Setup Completo

```bash
# 1. Installa PingMonitor normalmente
PingMonitorPro_v2.3_Setup.exe

# 2. Configura GitHub
SETUP_GITHUB.bat

# 3. Avvia
START_PINGMONITOR.bat
```

### Opzione B: Solo Codice

```bash
# 1. Clone repository
git clone https://github.com/TUO_USERNAME/PingMonitorPro.git
cd PingMonitorPro

# 2. Setup Python
python -m venv venv
venv\Scripts\pip install -r requirements.txt

# 3. Configura GitHub
SETUP_GITHUB.bat

# 4. Avvia
START_DIRECT.bat
```

---

## 🎯 Workflow Completo

```
TUO PC (Dev)             GitHub              PC CLIENTE
    │                      │                     │
    │ git push ──────────> │                     │
    │                      │                     │
    │                      │ <─── Avvio app      │
    │                      │                     │
    │                      │      Popup ──────>  │
    │                      │   "Aggiornamento    │
    │                      │    disponibile"     │
    │                      │                     │
    │                      │ <─── Click "Installa"
    │                      │                     │
    │                      │      Download ────> │
    │                      │      Applica ─────> │
    │                      │      Restart ─────> │
    │                      │                     │
    │                      │      ✅ FATTO!     │
```

---

## 🔧 Comandi Utili

### Verifica Stato

```bash
git status
git log --oneline -5
```

### Rollback Locale

```bash
git reset --hard HEAD~1
git push --force
```

### Info Update

```bash
venv\Scripts\python.exe -c "from src.utils.github_updater import GitHubUpdater; print(GitHubUpdater().get_update_info())"
```

---

## 📞 Help

**Problema:** Git not found
**Fix:** Installa Git da https://git-scm.com

**Problema:** Authentication failed
**Fix:** Rigenera token su GitHub → SETUP_GITHUB.bat

**Problema:** Update failed
**Fix:** L'app fa rollback automatico

---

## 📋 Checklist

- [ ] Repository GitHub creato
- [ ] Codice caricato (`git push`)
- [ ] Token generato (se privato)
- [ ] GitHub configurato (`SETUP_GITHUB.bat`)
- [ ] Test aggiornamento funzionante
- [ ] Tutti i PC configurati

---

**🎉 Pronto per distribuire aggiornamenti automatici!**
