# Fix: Timestamp "Ultimo Check" aggiornato in real-time

## Problema Risolto

La colonna "Ultimo Check" nella tabella di monitoraggio rimaneva sempre "Mai" anche dopo aver eseguito check manuali o automatici.

## Causa Root

1. **Mancanza di persistenza nel database**: L'oggetto `device` in memoria veniva aggiornato con `last_check_time`, ma le modifiche NON venivano salvate nel database
2. **Colonne mancanti nel DB**: I campi `ping_status` e `web_status` non esistevano nella tabella `devices`, impedendo il salvataggio dello stato DEGRADED
3. **Parsing timestamp incompleto**: La UI non gestiva correttamente tutti i formati ISO8601

## Modifiche Applicate

### 1. Monitoring Engine (`src/core/monitoring_engine.py`)

#### a) Aggiunto metodo `_persist_device_updates()`

```python
def _persist_device_updates(self, device: Device):
    """
    Persist device updates to database for real-time UI synchronization

    Args:
        device: Device to persist
    """
    session = db_manager.get_session()
    try:
        # Get the device from database
        db_device = session.query(Device).filter_by(id=device.id).first()

        if db_device:
            # Update critical fields for UI display
            db_device.current_status = device.current_status
            db_device.last_check_time = device.last_check_time
            db_device.response_time = device.response_time
            db_device.total_checks = device.total_checks
            db_device.successful_checks = device.successful_checks
            db_device.failed_checks = device.failed_checks
            db_device.uptime_percentage = device.uptime_percentage

            # Persist ping/web status for DEGRADED detection
            if hasattr(device, 'ping_status'):
                db_device.ping_status = device.ping_status
            if hasattr(device, 'web_status'):
                db_device.web_status = device.web_status

            session.commit()
            logger.debug(f"Persisted device updates to DB: {device.name}")
        else:
            logger.warning(f"Device {device.id} not found in database")

    except Exception as e:
        logger.error(f"Failed to persist device updates for {device.name}: {e}")
        session.rollback()
    finally:
        session.close()
```

#### b) Chiamata a `_persist_device_updates()` dopo ogni check

Nel metodo `_process_check_result()`, dopo aver aggiornato le metriche del device:

```python
# Update device metrics
device.current_status = new_status
device.last_check_time = result['timestamp']
device.response_time = result.get('response_time', 0)
device.total_checks += 1

# CRITICAL FIX: Persist device updates to database for real-time UI sync
self._persist_device_updates(device)
```

### 2. Model Device (`src/models/device.py`)

Aggiunte nuove colonne per tracciare lo stato individuale di PING e WEB:

```python
# Individual check statuses (for DEGRADED detection)
ping_status = Column(String(20))  # success, failed, None
web_status = Column(String(20))   # success, failed, None
```

### 3. UI Main Window (`src/ui/main_window_v2.py`)

Migliorato il parsing del timestamp con gestione robusta di tutti i formati ISO8601:

```python
# Format last check time in Italian format (day/month/year hour:minute:second)
if device.last_check_time and device.last_check_time != "Never":
    try:
        # Parse ISO format timestamp with robust handling
        from datetime import datetime
        if isinstance(device.last_check_time, str):
            # Handle multiple ISO8601 formats:
            # - "2025-01-17T14:30:45.123456" (microseconds)
            # - "2025-01-17T14:30:45" (no microseconds)
            # - "2025-01-17 14:30:45" (space separator)
            # - "2025-01-17T14:30:45Z" (UTC indicator)
            # - "2025-01-17T14:30:45+00:00" (timezone)
            timestamp_str = device.last_check_time.replace('Z', '+00:00').replace(' ', 'T')
            dt = datetime.fromisoformat(timestamp_str)
        else:
            # Already a datetime object
            dt = device.last_check_time
        # Format in Italian: day/month/year hour:minute:second
        last_check = dt.strftime('%d/%m/%Y %H:%M:%S')
    except (ValueError, AttributeError, TypeError) as e:
        logger.warning(f"Failed to parse last_check_time for {device.name}: {e}")
        last_check = str(device.last_check_time) if device.last_check_time else "Mai"
else:
    last_check = "Mai"
```

### 4. Database Migration (`migrate_add_status_columns.py`)

Creato script di migrazione per aggiungere le nuove colonne al database esistente:

```python
# Add ping_status column
cursor.execute("""
    ALTER TABLE devices
    ADD COLUMN ping_status VARCHAR(20)
""")

# Add web_status column
cursor.execute("""
    ALTER TABLE devices
    ADD COLUMN web_status VARCHAR(20)
""")
```

## Come Applicare il Fix

### 1. Eseguire la migrazione del database

```bash
cd "C:\Users\Fabrizio.Cerchia\Desktop\PingMonitor Pro"
python migrate_add_status_columns.py
```

Output atteso:
```
================================================================================
DATABASE MIGRATION: Adding ping_status and web_status columns
================================================================================

Initializing database...
[OK] Database initialized

Database location: C:\Users\Fabrizio.Cerchia\.pingmonitor\pingmonitor.db

Connecting to database...
[OK] Connected

Adding ping_status column...
[OK] ping_status column added

Adding web_status column...
[OK] web_status column added

[OK] Migration committed successfully

================================================================================
MIGRATION SUCCESSFUL
================================================================================
```

### 2. Riavviare PingMonitor Pro

Chiudere completamente l'applicazione e riaprirla. Le modifiche verranno applicate automaticamente.

### 3. Verificare il funzionamento

1. Avviare il monitoraggio
2. Attendere il primo check automatico (o forzare un check con "Check Now")
3. Verificare che la colonna "Ultimo Check" si aggiorni con il timestamp corrente nel formato:
   ```
   17/11/2025 17:26:14
   ```

## Test di Verifica

È stato creato uno script di test automatico per verificare il corretto funzionamento:

```bash
python test_last_check_fix_ascii.py
```

### Risultato Atteso

```
[PASS] TEST PASSED: Timestamp is recent and properly formatted!
```

## Impatto delle Modifiche

✅ **Funzionalità Ripristinata**: Il timestamp "Ultimo Check" si aggiorna in real-time dopo ogni check

✅ **Persistenza Garantita**: Tutti gli aggiornamenti del device vengono salvati nel database

✅ **Formato Corretto**: Timestamp formattato in italiano (gg/mm/aaaa hh:mm:ss)

✅ **Stato DEGRADED Tracciato**: I campi ping_status e web_status permettono di identificare correttamente dispositivi in stato degradato

✅ **Compatibilità Mantenuta**: Le modifiche sono retrocompatibili con il database esistente tramite migration

## File Modificati

1. `src/core/monitoring_engine.py` - Aggiunto metodo di persistenza
2. `src/models/device.py` - Aggiunte colonne ping_status e web_status
3. `src/ui/main_window_v2.py` - Migliorato parsing timestamp
4. `migrate_add_status_columns.py` - Script di migrazione database (nuovo)
5. `test_last_check_fix_ascii.py` - Test automatico (nuovo)

## Data Fix

**Data**: 17 Novembre 2025
**Autore**: Claude Code Assistant
**Versione**: PingMonitor Pro v2.3
**Issue**: Timestamp "Ultimo Check" non aggiornato in real-time
**Status**: ✅ Risolto e Testato
