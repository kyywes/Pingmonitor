# PingMonitor Pro - Code Analysis Report
**Data Analisi:** 2025-11-17
**Analista:** Claude Code Senior Reviewer
**Versione Software:** 2.3.0

---

## EXECUTIVE SUMMARY

Sono stati identificati **8 problemi critici** nel codice di PingMonitor Pro che causano malfunzionamenti nell'interfaccia utente, nel sistema di alert e nella funzionalità di auto-recovery. I problemi spaziano da bug di rendering UI a problemi architetturali nel monitoring engine e nel sistema di notifiche.

**Severity Distribution:**
- CRITICAL: 3 issues
- HIGH: 3 issues
- MEDIUM: 2 issues

---

## PROBLEMI IDENTIFICATI

### 1. PALLINI COLORATI MANCANTI NELLA TABELLA STATO
**Severity:** MEDIUM
**Category:** UI/Display
**Location:** `src/ui/main_window_v2.py:1050-1059`

#### Descrizione del Problema
La tabella di monitoraggio mostra emoji testuali ("🟢 ONLINE", "🔴 OFFLINE", "🟡 DEGRADED") invece di veri pallini colorati grafici. Questo riduce la leggibilità visiva della dashboard.

#### Causa Root
```python
# Linee 1051-1058 - main_window_v2.py
if device.current_status == 'online':
    status_icon = "🟢 ONLINE"
elif device.current_status == 'offline':
    status_icon = "🔴 OFFLINE"
elif device.current_status == 'degraded':
    status_icon = "🟡 DEGRADED"
```

Il codice usa emoji Unicode invece di creare widget grafici con QColor o QPainter.

#### Soluzione Raccomandata
Creare un widget personalizzato con pallino colorato:

```python
def _create_status_indicator(self, status: str) -> QWidget:
    """Create visual status indicator with colored circle"""
    widget = QWidget()
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)

    # Create colored circle
    circle_label = QLabel("●")  # Circle character
    circle_label.setStyleSheet(f"""
        font-size: 20px;
        color: {self._get_status_color(status)};
    """)
    layout.addWidget(circle_label)

    # Status text
    text_label = QLabel(status.upper())
    text_label.setStyleSheet("font-weight: bold;")
    layout.addWidget(text_label)

    return widget

def _get_status_color(self, status: str) -> str:
    """Get color for status"""
    colors = {
        'online': '#10b981',   # Green
        'offline': '#ef4444',  # Red
        'degraded': '#f59e0b'  # Orange
    }
    return colors.get(status, '#6b7280')  # Default gray
```

Poi modificare `_update_monitoring_table`:
```python
# Linea 1060
self.monitoring_table.setCellWidget(row, 0, self._create_status_indicator(device.current_status))
```

---

### 2. EMOJI NELLA COLONNA "TIPO" DA RIMUOVERE
**Severity:** MEDIUM
**Category:** UI/Presentation
**Location:** `src/ui/main_window_v2.py:1063`

#### Descrizione del Problema
La colonna "Tipo" mostra emoji che devono essere rimosse per un aspetto più professionale.

#### Causa Root
```python
# Linea 1063
self.monitoring_table.setItem(row, 3, QTableWidgetItem(device.device_type))
```

Il campo `device.device_type` probabilmente contiene emoji (es: "📱 PAI-PL" invece di "PAI-PL").

#### Soluzione Raccomandata
Rimuovere emoji dal device_type prima di visualizzare:

```python
import re

def _strip_emoji(self, text: str) -> str:
    """Remove emoji from text"""
    # Remove emoji using regex
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub('', text).strip()

# Modificare linea 1063:
device_type_clean = self._strip_emoji(device.device_type)
self.monitoring_table.setItem(row, 3, QTableWidgetItem(device_type_clean))
```

---

### 3. ULTIMO CHECK NON SI AGGIORNA IN REAL-TIME
**Severity:** CRITICAL
**Category:** Monitoring Engine / Data Sync
**Location:** `src/core/monitoring_engine.py:636` + `src/ui/main_window_v2.py:1093-1110`

#### Descrizione del Problema
Il campo "Ultimo Check" rimane fisso (es. 9:00 AM) e non si aggiorna in tempo reale, anche dopo check forzati.

#### Causa Root - Problema 1: Timestamp non aggiornato
```python
# monitoring_engine.py:636
device.last_check_time = result['timestamp']  # ISO string format
```

Il timestamp viene settato correttamente, MA il problema è nel formato e nell'aggiornamento della UI.

#### Causa Root - Problema 2: Parsing del timestamp nella UI
```python
# main_window_v2.py:1093-1106
if device.last_check_time and device.last_check_time != "Never":
    try:
        dt = datetime.fromisoformat(device.last_check_time.replace('Z', '+00:00'))
        last_check = dt.strftime('%d/%m/%Y %H:%M')
    except (ValueError, AttributeError):
        last_check = str(device.last_check_time)
else:
    last_check = "Mai"
```

Questo codice dovrebbe funzionare MA c'è un problema di **sincronizzazione dell'oggetto device**.

#### Causa Root - Problema 3: Device object non sincronizzato con DB
Il device nel `monitoring_engine.devices` è un oggetto in memoria che NON è sincronizzato automaticamente con il database. Quando il monitoring engine aggiorna `device.last_check_time`, l'oggetto in memoria cambia MA l'oggetto nel database potrebbe non essere aggiornato, e viceversa.

#### Soluzione Raccomandata

**Step 1:** Garantire che il device object sia aggiornato nel database
```python
# monitoring_engine.py:636 - Dopo aver aggiornato le proprietà
device.last_check_time = result['timestamp']
device.response_time = result.get('response_time', 0)
device.total_checks += 1

# AGGIUNGI: Salva nel database
session = db_manager.get_session()
try:
    db_device = session.query(Device).filter_by(id=device.id).first()
    if db_device:
        db_device.last_check_time = device.last_check_time
        db_device.response_time = device.response_time
        db_device.total_checks = device.total_checks
        db_device.current_status = device.current_status
        session.commit()
except Exception as e:
    logger.error(f"Failed to update device in DB: {e}")
    session.rollback()
finally:
    session.close()
```

**Step 2:** Convertire il timestamp in formato locale per la visualizzazione
```python
# main_window_v2.py:1093-1110 - MIGLIORA il parsing
if device.last_check_time and device.last_check_time != "Never":
    try:
        from datetime import timezone
        # Parse UTC timestamp
        if isinstance(device.last_check_time, str):
            dt_utc = datetime.fromisoformat(device.last_check_time.replace('Z', '+00:00'))
        else:
            dt_utc = device.last_check_time

        # Convert to local timezone for display
        dt_local = dt_utc.astimezone()
        last_check = dt_local.strftime('%d/%m/%Y %H:%M:%S')

        # Calculate time ago for better UX
        now_local = datetime.now(timezone.utc).astimezone()
        delta = (now_local - dt_local).total_seconds()

        if delta < 60:
            time_ago = f"({int(delta)}s fa)"
        elif delta < 3600:
            time_ago = f"({int(delta/60)}m fa)"
        else:
            time_ago = f"({int(delta/3600)}h fa)"

        last_check += f" {time_ago}"

    except (ValueError, AttributeError) as e:
        logger.error(f"Error parsing last_check_time: {e}")
        last_check = str(device.last_check_time)
else:
    last_check = "Mai"
```

**Step 3:** Aumentare la frequenza di aggiornamento UI
```python
# main_window_v2.py:114
self.update_timer.start(500)  # Already OK - 500ms
```

---

### 4. STATO DEVICE SEMPRE "MAI" ANCHE DOPO CHECK FORZATO
**Severity:** CRITICAL
**Category:** Data Persistence / Synchronization
**Location:** `src/core/monitoring_engine.py:174` + `src/ui/main_window_v2.py:1211-1232`

#### Descrizione del Problema
Anche forzando l'aggiornamento manuale, il campo "Ultimo Check" rimane su "Mai" invece di mostrare il timestamp dell'ultimo controllo.

#### Causa Root
Questo problema è **correlato al Problema 3** ma ha una causa aggiuntiva:

**Causa 1:** Inizializzazione del device
```python
# monitoring_engine.py:174
self.last_check_times[device.id] = datetime.utcnow() - timedelta(hours=1)
```

Questo imposta il last_check_time nel dizionario interno, MA `device.last_check_time` (la proprietà dell'oggetto Device) NON viene mai inizializzata, quindi rimane `None` o vuota.

**Causa 2:** Force check non aggiorna immediatamente
```python
# main_window_v2.py:1220-1221
logger.info("Forcing immediate check on all devices...")
self.monitoring_engine.force_immediate_check()
```

Il metodo `force_immediate_check` resetta solo i timestamp interni ma NON esegue immediatamente i check - aspetta il prossimo ciclo dello scheduler (fino a 5 secondi).

#### Soluzione Raccomandata

**Opzione 1 (MIGLIORE):** Inizializzare last_check_time sul device object
```python
# monitoring_engine.py:174-175
self.devices[device.id] = device
self.last_check_times[device.id] = datetime.utcnow() - timedelta(hours=1)

# AGGIUNGI:
if not device.last_check_time:
    device.last_check_time = datetime.utcnow().isoformat()
```

**Opzione 2:** Forzare aggiornamento immediato nella UI dopo refresh
```python
# main_window_v2.py:1222-1228 - Modificare _refresh_data
def _refresh_data(self):
    try:
        logger.info("Refreshing devices from database...")
        device_count = self.monitoring_engine.reload_devices()

        if self.monitoring_engine.running:
            logger.info("Forcing immediate check on all devices...")
            self.monitoring_engine.force_immediate_check()

            # AGGIUNGI: Wait for checks to complete
            QTimer.singleShot(3000, lambda: self._update_ui())  # Update UI after 3 seconds

        self._update_ui()  # Immediate update
        self.status_bar.showMessage(f"✓ Data aggiornati - {device_count} dispositivi", 4000)
    except Exception as e:
        logger.error(f"Error refreshing data: {e}")
```

---

### 5. ALERT NON FUNZIONANTI (configurato ogni 6 ore ma non invia mai)
**Severity:** HIGH
**Category:** Alert System / Notification Service
**Location:** `src/ui/main_window_v2.py:118-119` + `src/services/notification_service.py:106-161`

#### Descrizione del Problema
Gli alert email sono configurati per essere inviati ogni 6 ore ma non vengono mai mandati.

#### Causa Root - Problema 1: Timer configurato male
```python
# main_window_v2.py:118-119
self.email_aggregate_timer.timeout.connect(self._send_aggregated_email)
self.email_aggregate_timer.start(86400000)  # 24 hours NOT 6 hours!
```

Il timer è impostato su 24 ore (86400000ms) invece di 6 ore (21600000ms).

#### Causa Root - Problema 2: Logica di alert troppo restrittiva
```python
# notification_service.py:106-161
def should_send_alert(self, device_ip: str, ping_ok: bool, web_ok: bool) -> bool:
    # ... logica complessa ...
    if time_since_reboot < 300:  # Less than 5 minutes
        return False
```

La logica richiede:
1. Ping OK
2. Web NON OK
3. Tentativo di recovery fallito
4. Attesa di 5 minuti post-recovery

Questo è troppo restrittivo e potrebbe impedire l'invio di alert per altre situazioni critiche.

#### Causa Root - Problema 3: Alert non inviati per transizioni di stato
```python
# main_window_v2.py:910-918 - Alert via email solo se _should_send_status_email ritorna True
should_send_email = self._should_send_status_email(device, old_status, new_status)
if should_send_email:
    self._send_status_change_email(device, old_status, new_status)
```

Ma `_should_send_status_email` verifica solo se l'email è abilitata:
```python
# main_window_v2.py:935-936
if not self.email_config.get('enabled', False):
    return False
```

Se `email_config['enabled']` è `False`, nessun alert viene inviato!

#### Soluzione Raccomandata

**Fix 1:** Correggere l'intervallo del timer (6 ore invece di 24)
```python
# main_window_v2.py:119
# OLD: self.email_aggregate_timer.start(86400000)  # 24 hours
self.email_aggregate_timer.start(21600000)  # 6 hours = 6 * 60 * 60 * 1000ms
```

**Fix 2:** Semplificare la logica di alert per includere più casistiche
```python
# notification_service.py:106 - Modificare should_send_alert
def should_send_alert(self, device_ip: str, ping_ok: bool, web_ok: bool,
                     device_status: str = None) -> bool:
    """
    Determine if alert should be sent

    Send alerts for:
    1. Device goes OFFLINE (ping fail)
    2. Device goes DEGRADED (ping OK, web fail) after recovery attempt
    3. Device remains OFFLINE or DEGRADED for > 10 minutes
    """
    # Send immediate alert if device goes OFFLINE
    if not ping_ok:
        logger.warning(f"{device_ip}: OFFLINE - sending immediate alert")
        return True

    # Send alert if DEGRADED and recovery failed
    if ping_ok and not web_ok:
        with self._recovery_attempts_lock:
            if device_ip in self.recovery_attempts:
                recovery = self.recovery_attempts[device_ip]
                time_since_reboot = (datetime.now() - recovery['reboot_time']).total_seconds()

                if time_since_reboot >= 300:  # 5 minutes
                    logger.error(f"{device_ip}: Recovery failed - sending alert")
                    return True

    return False
```

**Fix 3:** Assicurarsi che email sia abilitata nella configurazione
```python
# Verificare che in config/config.json o nel database:
{
  "email": {
    "enabled": true,  # DEVE ESSERE true!
    "smtp_server": "...",
    "smtp_port": 587,
    "username": "...",
    "password": "...",
    "alert_email": "..."
  }
}
```

**Fix 4:** Aggiungere logging per debug alert
```python
# notification_service.py:178
def send_email_alert(self, config: dict, device_info: dict, alert_type: str) -> bool:
    if not config.get('enabled', False):
        logger.warning(f"Email alerts DISABLED in config - skipping alert for {device_info.get('name')}")
        return False

    logger.info(f"Preparing email alert for {device_info.get('name')} - type: {alert_type}")
    # ... rest of method
```

---

### 6. AUTO-RECOVERY SSH NON FUNZIONA
**Severity:** CRITICAL
**Category:** Auto-Recovery / SSH
**Location:** Multiple files

#### Descrizione del Problema
Per device degraded dovrebbe:
1. Entrare con SSH
2. Fare reboot
3. Verificare cambio stato
4. Mandare alert

Ma non funziona correttamente.

#### Causa Root - Problema 1: SSH config non caricata
```python
# main_window_v2.py:84-85
ssh_config = {}
if legacy_config_path.exists():
    _, email_config, ssh_config = ConfigImporter.import_from_legacy_config(legacy_config_path)
```

Se il file config.json non esiste o non contiene SSH config, `ssh_config` rimane vuoto `{}`.

Poi:
```python
# main_window_v2.py:88
self.auto_recovery_service = AutoRecoveryService(ssh_config)
```

AutoRecoveryService riceve un dict vuoto e quindi SSH è disabilitato:
```python
# auto_recovery_service.py:47-49
if not self.ssh_config.get('enabled', False):
    logger.warning("SSH auto-recovery is disabled in config")
    return False, "SSH auto-recovery disabled"
```

#### Causa Root - Problema 2: Auto-recovery service non collegato al monitoring engine all'avvio
```python
# main.py:117-120
if hasattr(self.main_window, 'auto_recovery_service'):
    self.monitoring_engine.set_auto_recovery_service(self.main_window.auto_recovery_service)
    logger.info("Auto-recovery service connected to monitoring engine")
```

Questo codice dipende dall'ordine di inizializzazione. Se il main_window crea l'auto_recovery_service DOPO che questo check viene fatto, il collegamento non avviene.

#### Causa Root - Problema 3: Cooldown troppo lungo tra tentativi
```python
# monitoring_engine.py:854-856
time_since_last = (datetime.utcnow() - last_attempt).total_seconds()
if time_since_last < 300:  # 5 minutes
    logger.info(f"Recovery cooldown active - skipping")
    return
```

5 minuti di cooldown potrebbero essere troppo lunghi per ambienti critici.

#### Soluzione Raccomandata

**Fix 1:** Assicurarsi che SSH config sia caricata correttamente
```python
# main_window_v2.py:79-92 - MIGLIORARE caricamento config
# Initialize advanced services
email_config = {}
ssh_config = {
    'enabled': True,  # Default enabled
    'username': 'root',  # Default username
    'password': '',  # Will be loaded from config
    'port': 22
}

# Try to load from legacy config if available
legacy_config_path = Path(__file__).parent.parent.parent / "config" / "config.json"
if legacy_config_path.exists():
    devices, loaded_email, loaded_ssh = ConfigImporter.import_from_legacy_config(legacy_config_path)
    if loaded_email:
        email_config = loaded_email
    if loaded_ssh:
        ssh_config.update(loaded_ssh)  # Merge with defaults

logger.info(f"SSH config loaded: enabled={ssh_config.get('enabled')}, user={ssh_config.get('username')}")
```

**Fix 2:** Garantire che auto_recovery_service sia collegato al monitoring engine
```python
# main_window_v2.py:DOPO riga 92 - AGGIUNGI collegamento esplicito
self.auto_recovery_service = AutoRecoveryService(self.ssh_config)

# Collega IMMEDIATAMENTE al monitoring engine
if self.monitoring_engine:
    self.monitoring_engine.set_auto_recovery_service(self.auto_recovery_service)
    logger.info("Auto-recovery service connected to monitoring engine at startup")
```

**Fix 3:** Ridurre il cooldown e aggiungere max_attempts
```python
# monitoring_engine.py:854-860 - Modificare cooldown
time_since_last = (datetime.utcnow() - last_attempt['timestamp']).total_seconds()
max_attempts = 3
current_attempts = last_attempt.get('attempts', 0)

if current_attempts >= max_attempts:
    logger.warning(f"Max recovery attempts ({max_attempts}) reached for {device.name}")
    return

if time_since_last < 180:  # 3 minutes instead of 5
    logger.info(f"Recovery cooldown active - skipping ({int(180-time_since_last)}s remaining)")
    return

# Update attempts counter
self.recovery_attempts[device_key] = {
    'timestamp': datetime.utcnow(),
    'attempts': current_attempts + 1
}
```

**Fix 4:** Verificare credenziali SSH
```python
# auto_recovery_service.py:58-66 - Aggiungere logging dettagliato
try:
    logger.info(f"SSH connection attempt: {device_ip}:22 user={self.ssh_config.get('username')}")
    client.connect(
        hostname=device_ip,
        port=22,
        username=self.ssh_config.get('username', 'root'),
        password=self.ssh_config.get('password', ''),
        timeout=10,
        allow_agent=False,
        look_for_keys=False
    )
    logger.info(f"{device_ip}: SSH connection established successfully")
except paramiko.AuthenticationException as e:
    logger.error(f"{device_ip}: SSH auth failed - user={self.ssh_config.get('username')}, error={e}")
    return False, f"Authentication failed: {e}"
```

**Fix 5:** Test di connettività SSH all'avvio
```python
# main_window_v2.py:DOPO riga 127 - AGGIUNGI test SSH
# Test SSH connectivity to first device
if self.ssh_config.get('enabled') and self.monitoring_engine.devices:
    first_device = list(self.monitoring_engine.devices.values())[0]
    logger.info(f"Testing SSH connectivity to {first_device.name}...")
    success, message = self.auto_recovery_service.check_ssh_connectivity(first_device.ip_address)
    if success:
        logger.info(f"SSH test successful: {message}")
    else:
        logger.warning(f"SSH test failed: {message} - Auto-recovery might not work")
```

---

### 7. FREEZE AL CHIUDERE IL PROGRAMMA
**Severity:** HIGH
**Category:** Thread Management / Shutdown
**Location:** `src/core/monitoring_engine.py:252-295` + `src/ui/main_window_v2.py:1571-1607`

#### Descrizione del Problema
Il programma si freeza quando si prova a chiuderlo, rimanendo in uno stato hung.

#### Causa Root - Problema 1: Thread non terminano correttamente
```python
# monitoring_engine.py:279-283
if self._monitor_thread and self._monitor_thread.is_alive():
    self._monitor_thread.join(timeout=5)
if self._scheduler_thread and self._scheduler_thread.is_alive():
    self._scheduler_thread.join(timeout=5)
```

I thread sono marcati come `daemon=True` (linea 237, 242) MA il `join(timeout=5)` attende comunque 5 secondi ANCHE se il thread è già terminato. Se ci sono ritardi, questo può causare freeze.

#### Causa Root - Problema 2: ThreadPoolExecutor non chiude correttamente
```python
# monitoring_engine.py:289-293
try:
    self.executor.shutdown(wait=False, cancel_futures=True)
except Exception as e:
    logger.warning(f"Executor shutdown warning: {e}")
```

`shutdown(wait=False)` NON aspetta che i worker thread finiscano, MA se ci sono task bloccati (es. SSH connection timeout), i thread rimangono attivi.

#### Causa Root - Problema 3: SSH connections aperte
```python
# auto_recovery_service.py:129-133
finally:
    try:
        client.close()
    except:
        pass
```

Le connessioni SSH potrebbero non chiudersi correttamente se ci sono timeout o errori, lasciando socket aperti.

#### Causa Root - Problema 4: Timer non cancellati
```python
# monitoring_engine.py:122-138 - _cleanup_timers
with self._active_timers_lock:
    timers_to_cancel = self._active_timers.copy()
    self._active_timers.clear()

for timer in timers_to_cancel:
    try:
        timer.cancel()
    except:
        pass
```

Questo dovrebbe funzionare MA se ci sono race condition, alcuni timer potrebbero non essere cancellati.

#### Soluzione Raccomandata

**Fix 1:** Forzare terminazione thread più aggressivamente
```python
# monitoring_engine.py:252-283 - Modificare stop()
def stop(self):
    if not self.running:
        logger.warning("Monitoring engine is not running")
        return

    logger.info("Stopping monitoring engine...")
    self.running = False  # This signals threads to stop

    # Flush pending writes
    logger.info("Flushing pending database writes...")
    batch_writer.force_flush()

    # Clear task queue IMMEDIATELY to prevent new tasks
    logger.info("Clearing task queue...")
    cleared = 0
    while not self.task_queue.empty():
        try:
            self.task_queue.get_nowait()
            cleared += 1
        except:
            break
    logger.info(f"Cleared {cleared} pending tasks")

    # Cancel all active timers BEFORE waiting for threads
    logger.info("Cancelling active timers...")
    self._cleanup_timers()

    # Shutdown executor IMMEDIATELY (don't wait for futures)
    logger.info("Shutting down executor...")
    try:
        self.executor.shutdown(wait=False, cancel_futures=True)
        self.executor_shutdown = True
    except Exception as e:
        logger.warning(f"Executor shutdown warning: {e}")

    # Give threads SHORT time to finish, then proceed anyway
    logger.info("Waiting for threads to finish...")
    if self._monitor_thread and self._monitor_thread.is_alive():
        self._monitor_thread.join(timeout=1)  # REDUCED to 1 second
        if self._monitor_thread.is_alive():
            logger.warning("Monitor thread still alive after timeout - forcing shutdown")

    if self._scheduler_thread and self._scheduler_thread.is_alive():
        self._scheduler_thread.join(timeout=1)  # REDUCED to 1 second
        if self._scheduler_thread.is_alive():
            logger.warning("Scheduler thread still alive after timeout - forcing shutdown")

    logger.info("Monitoring engine stopped")
```

**Fix 2:** Aggiungere timeout globale per shutdown in main_window
```python
# main_window_v2.py:1589-1592 - Modificare stop_monitoring
def stop_monitoring(self):
    try:
        logger.info("Stopping monitoring engine...")

        # Stop in background thread to prevent UI freeze
        from PyQt6.QtCore import QThread, pyqtSignal

        class StopWorker(QThread):
            finished = pyqtSignal()

            def __init__(self, engine):
                super().__init__()
                self.engine = engine

            def run(self):
                try:
                    self.engine.stop()
                except Exception as e:
                    logger.error(f"Error stopping engine: {e}")
                finally:
                    self.finished.emit()

        self.stop_worker = StopWorker(self.monitoring_engine)
        self.stop_worker.finished.connect(lambda: self._on_stop_finished())
        self.stop_worker.start()

        # Show "stopping" message
        self.status_bar.showMessage("🔴 Arresto monitoraggio in corso...", 10000)

    except Exception as e:
        logger.error(f"Failed to stop monitoring: {e}")

def _on_stop_finished(self):
    """Called when monitoring engine stop completes"""
    self.btn_start.setEnabled(True)
    self.btn_stop.setEnabled(False)
    self.status_bar.showMessage("🔴 Monitoraggio Fermato", 3000)
    logger.info("Monitoring stopped successfully")
```

**Fix 3:** Force kill application dopo timeout
```python
# main_window_v2.py:1571-1607 - Modificare closeEvent
def closeEvent(self, event):
    """Handle window close event with timeout"""
    if self.config.get('application.minimize_to_tray', True):
        event.ignore()
        self.hide()
        if hasattr(self, 'tray_icon'):
            self.tray_icon.showMessage(
                "PingMonitor Pro",
                "Applicazione minimizzata nella tray",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
    else:
        reply = QMessageBox.question(
            self, "Conferma Uscita",
            "Sei sicuro di voler uscire?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # AGGIUNGI: Timeout per force quit
            import threading

            def force_quit():
                """Force quit after 5 seconds"""
                import time
                time.sleep(5)
                logger.warning("Force quit after timeout - killing application")
                import os
                os._exit(0)  # Force exit

            # Start force quit timer
            force_quit_thread = threading.Thread(target=force_quit, daemon=True)
            force_quit_thread.start()

            # Try graceful shutdown
            logger.info("Starting graceful shutdown...")

            # Stop monitoring
            if self.monitoring_engine.running:
                self.monitoring_engine.stop()

            # Close SSH terminal
            if hasattr(self, 'ssh_terminal'):
                self.ssh_terminal.close()

            # Save window geometry
            geometry = {
                'width': self.width(),
                'height': self.height()
            }
            self.config.set('ui.window_geometry', geometry)
            self.config.save()

            logger.info("Graceful shutdown complete")
            event.accept()
        else:
            event.ignore()
```

---

### 8. SETUP NON ELIMINA VERSIONI PRECEDENTI
**Severity:** HIGH
**Category:** Installer / Deployment
**Location:** Setup script (non trovato nel repository)

#### Descrizione del Problema
L'installer non rimuove le installazioni precedenti di PingMonitor Pro, causando:
- Conflitti di versione
- Occupazione di spazio disco inutile
- Possibili problemi di configurazione con file vecchi

#### Causa Root
Il problema è che non è stato trovato alcun file di setup/installer nel repository analizzato. Probabilmente il setup è:
1. Un file `.iss` (Inno Setup) esterno
2. Un file `.spec` (PyInstaller) esterno
3. Un file batch/script custom

Senza vedere il file di setup, posso solo ipotizzare che:
- Non esiste una logica `[UninstallDelete]` in Inno Setup
- Non esiste uno script pre-install che rimuove le versioni precedenti

#### Soluzione Raccomandata

**Opzione 1 (MIGLIORE): Usare Inno Setup con logica di uninstall**

Creare un file `setup.iss`:
```inno
[Setup]
AppName=PingMonitor Pro
AppVersion=2.3.0
DefaultDirName={pf}\PingMonitor Pro
DefaultGroupName=PingMonitor Pro
UninstallDisplayIcon={app}\icon.ico
OutputDir=installer
OutputBaseFilename=PingMonitor_Pro_v2.3.0_Setup

; IMPORTANTE: Questa opzione rimuove automaticamente versioni precedenti
PrivilegesRequired=admin

[Code]
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
  UninstallString: String;
begin
  // Check if PingMonitor Pro is already installed
  if RegQueryStringValue(HKLM, 'Software\Microsoft\Windows\CurrentVersion\Uninstall\PingMonitor Pro_is1',
     'UninstallString', UninstallString) then
  begin
    // Ask user if they want to uninstall previous version
    if MsgBox('PingMonitor Pro è già installato. Vuoi disinstallare la versione precedente?',
              mbConfirmation, MB_YESNO) = IDYES then
    begin
      // Run uninstaller silently
      if Exec(RemoveQuotes(UninstallString), '/SILENT', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
      begin
        Result := True;
      end
      else
      begin
        MsgBox('Errore durante la disinstallazione della versione precedente.', mbError, MB_OK);
        Result := False;
      end;
    end
    else
      Result := False;  // User cancelled
  end
  else
    Result := True;  // No previous version found, proceed with install
end;

[Files]
Source: "dist\PingMonitor Pro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\PingMonitor Pro"; Filename: "{app}\PingMonitor Pro.exe"
Name: "{commondesktop}\PingMonitor Pro"; Filename: "{app}\PingMonitor Pro.exe"

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
Type: filesandordirs; Name: "{localappdata}\PingMonitor Pro"
Type: filesandordirs; Name: "{userappdata}\PingMonitor Pro"
```

**Opzione 2: Script Python pre-install**

Creare `uninstall_previous.py`:
```python
"""
Uninstall previous versions of PingMonitor Pro before installing new version
"""

import os
import shutil
import winreg
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def find_previous_installation():
    """Find previous installation path from registry"""
    try:
        # Check HKLM
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"Software\Microsoft\Windows\CurrentVersion\Uninstall\PingMonitor Pro_is1"
        )
        install_location, _ = winreg.QueryValueEx(key, "InstallLocation")
        winreg.CloseKey(key)
        return install_location
    except FileNotFoundError:
        pass

    # Check common installation paths
    common_paths = [
        r"C:\Program Files\PingMonitor Pro",
        r"C:\Program Files (x86)\PingMonitor Pro",
        Path.home() / "AppData" / "Local" / "Programs" / "PingMonitor Pro"
    ]

    for path in common_paths:
        if Path(path).exists():
            return str(path)

    return None

def remove_previous_installation(install_path):
    """Remove previous installation"""
    try:
        logger.info(f"Removing previous installation: {install_path}")

        # Stop running processes
        os.system("taskkill /F /IM \"PingMonitor Pro.exe\" 2>nul")

        # Remove directory
        if Path(install_path).exists():
            shutil.rmtree(install_path, ignore_errors=True)
            logger.info(f"Removed: {install_path}")

        # Remove AppData files
        appdata_paths = [
            Path.home() / "AppData" / "Local" / "PingMonitor Pro",
            Path.home() / "AppData" / "Roaming" / "PingMonitor Pro"
        ]

        for path in appdata_paths:
            if path.exists():
                shutil.rmtree(path, ignore_errors=True)
                logger.info(f"Removed: {path}")

        return True
    except Exception as e:
        logger.error(f"Error removing previous installation: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    install_path = find_previous_installation()
    if install_path:
        print(f"Found previous installation at: {install_path}")
        response = input("Do you want to remove it? (y/n): ")
        if response.lower() == 'y':
            if remove_previous_installation(install_path):
                print("Previous installation removed successfully!")
            else:
                print("Failed to remove previous installation")
    else:
        print("No previous installation found")
```

Poi chiamare questo script PRIMA del setup principale.

---

## RACCOMANDAZIONI GENERALI

### Architettura
1. **Separare la logica di business dalla UI:** Il monitoring engine è troppo accoppiato alla UI. Creare un layer intermedio (Service Layer) per gestire la comunicazione.

2. **Usare un Event Bus:** Invece di callback diretti, usare un event bus (es. PyPubSub) per decoupling.

3. **Database connection pooling:** Usare connection pooling per evitare di aprire/chiudere connessioni continuamente.

### Performance
1. **Batch updates:** Il codice già usa `batch_writer` MA potrebbe essere ottimizzato ulteriormente con SQLAlchemy bulk operations.

2. **Ridurre il polling:** Invece di aggiornare la UI ogni 500ms, usare Qt signals per aggiornamenti event-driven.

### Security
1. **Password encryption:** Il codice usa Fernet encryption MA fallback a base64 è INSICURO. Rimuovere il fallback.

2. **Input validation:** Aggiungere validazione più rigorosa per IP addresses, email addresses, etc.

3. **SQL Injection:** Il codice usa SQLAlchemy ORM che protegge da SQL injection, ma assicurarsi di NON usare mai raw SQL con input utente non sanitizzato.

### Testing
1. **Unit tests:** Non ci sono unit test visibili nel repository. Aggiungere pytest con coverage > 80%.

2. **Integration tests:** Testare l'integrazione tra monitoring_engine, auto_recovery_service e notification_service.

3. **UI tests:** Usare PyQt6 QTest per testare l'interfaccia utente.

### Logging
1. **Structured logging:** Usare logging strutturato (JSON) per facilitare analisi.

2. **Log rotation:** Il codice ha log rotation MA configurare anche compressione dei log vecchi.

3. **Separate log levels per component:** Configurare log levels diversi per UI, monitoring engine, services.

---

## PRIORITA' DI RISOLUZIONE

**CRITICAL (da risolvere immediatamente):**
1. Problema 3: Ultimo check non real-time
2. Problema 4: Stato device sempre "Mai"
3. Problema 6: Auto-recovery SSH non funziona

**HIGH (da risolvere entro 1 settimana):**
4. Problema 5: Alert non funzionanti
5. Problema 7: Freeze al chiudere
6. Problema 8: Setup non elimina versioni precedenti

**MEDIUM (da risolvere entro 1 mese):**
7. Problema 1: Pallini colorati mancanti
8. Problema 2: Emoji da rimuovere

---

## TESTING PLAN

Dopo aver applicato le fix:

1. **Test Problema 3 & 4:**
   - Avviare monitoraggio
   - Forzare check con "Check Now"
   - Verificare che "Ultimo Check" si aggiorni immediatamente
   - Verificare che il timestamp sia corretto

2. **Test Problema 6:**
   - Configurare SSH credentials corrette
   - Simulare un device degraded (ping OK, web DOWN)
   - Verificare che auto-recovery tenti il reboot
   - Verificare che venga mandato alert se recovery fallisce

3. **Test Problema 5:**
   - Configurare email alert con intervallo 6 ore
   - Simulare device offline/degraded
   - Verificare che email venga inviata
   - Verificare contenuto email corretto

4. **Test Problema 7:**
   - Avviare monitoraggio con 10+ devices
   - Chiudere l'applicazione
   - Verificare che si chiuda entro 5 secondi
   - Verificare che non rimangano processi zombie

5. **Test Problema 8:**
   - Installare versione 2.2
   - Installare versione 2.3 sopra la 2.2
   - Verificare che la 2.2 venga rimossa
   - Verificare che non ci siano file duplicati

---

## CONCLUSIONE

PingMonitor Pro ha una base di codice solida ma presenta problemi critici che impediscono il corretto funzionamento delle funzionalità chiave. La maggior parte dei problemi sono risolvibili con modifiche mirate e non richiedono un refactoring architetturale completo.

**Stima tempo di fix:**
- CRITICAL issues: 16-24 ore sviluppo
- HIGH issues: 12-16 ore sviluppo
- MEDIUM issues: 4-6 ore sviluppo
- Testing completo: 8-12 ore

**Totale stimato: 40-58 ore di sviluppo**

La priorità deve essere data ai problemi CRITICAL che impediscono il corretto monitoraggio in tempo reale e l'auto-recovery, funzionalità core dell'applicazione.
