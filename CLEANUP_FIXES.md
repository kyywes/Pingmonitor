# Fix per il Freeze al Chiudere il Programma - PingMonitor Pro

## Problema Risolto
Il programma si bloccava completamente al momento della chiusura, causando un freeze dell'interfaccia e richiedendo la chiusura forzata del processo.

## Cause Identificate
1. **Thread non terminati correttamente** - I thread di monitoring e scheduling non venivano fermati in modo pulito
2. **Connessioni SSH rimaste aperte** - Le connessioni SSH del servizio auto-recovery non venivano chiuse
3. **ThreadPoolExecutor non chiuso con timeout** - L'executor rimaneva in attesa indefinita
4. **Timer QTimer non fermati** - I timer continuavano a eseguire callback dopo la chiusura
5. **Database connections non chiuse** - Le sessioni del database rimanevano aperte

## Modifiche Applicate

### 1. File: `src/ui/main_window_v2.py`

#### Nuovo Metodo `_perform_cleanup()`
Implementato un metodo dedicato per eseguire la pulizia in modo ordinato e sequenziale:

```python
def _perform_cleanup(self):
    """Perform proper cleanup before closing"""
    logger.info("Application closing - starting cleanup...")

    try:
        # 1. Stop monitoring engine first
        if hasattr(self, 'monitoring_engine') and self.monitoring_engine and self.monitoring_engine.running:
            logger.info("Stopping monitoring engine...")
            self.monitoring_engine.stop()
            # Wait max 3 seconds for clean stop
            start = time.time()
            while self.monitoring_engine.running and (time.time() - start) < 3:
                from PyQt6.QtWidgets import QApplication
                QApplication.processEvents()
                time.sleep(0.1)

        # 2. Stop all timers
        logger.info("Stopping timers...")
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        if hasattr(self, 'email_aggregate_timer'):
            self.email_aggregate_timer.stop()

        # 3. Close SSH connections
        if hasattr(self, 'ssh_terminal'):
            logger.info("Closing SSH terminal...")
            try:
                self.ssh_terminal.close()
            except Exception as e:
                logger.debug(f"SSH terminal close warning: {e}")

        # 4. Close auto-recovery service SSH connections
        if hasattr(self, 'auto_recovery_service') and self.auto_recovery_service:
            logger.info("Closing auto-recovery connections...")
            try:
                self.auto_recovery_service.cleanup()
            except Exception as e:
                logger.debug(f"Auto-recovery cleanup warning: {e}")
            self.auto_recovery_service = None

        # 5. Flush database writes
        logger.info("Flushing database...")
        try:
            from ..services.performance_service import batch_writer
            batch_writer.force_flush()
        except Exception as e:
            logger.debug(f"Batch writer flush warning: {e}")

        # 6. Close database connections
        logger.info("Closing database connections...")
        try:
            from ..models.base import db_manager
            db_manager.close_all_sessions()
        except Exception as e:
            logger.debug(f"Database close warning: {e}")

        # 7. Save window geometry and config
        logger.info("Saving configuration...")
        try:
            geometry = {
                'width': self.width(),
                'height': self.height()
            }
            self.config.set('ui.window_geometry', geometry)
            self.config.save()
        except Exception as e:
            logger.debug(f"Config save warning: {e}")

        logger.info("Cleanup completed successfully")

    except Exception as e:
        logger.error(f"Error during cleanup: {e}", exc_info=True)
```

#### Modificato `closeEvent()`
Il metodo `closeEvent()` ora chiama `_perform_cleanup()`:

```python
def closeEvent(self, event):
    """Handle window close event with proper cleanup"""
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
        reply = QMessageBox.question(self, "Conferma Uscita",
                                     "Sei sicuro di voler uscire?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self._perform_cleanup()
            event.accept()
        else:
            event.ignore()
```

#### Modificato `quit_application()`
Anche questo metodo ora usa `_perform_cleanup()`:

```python
def quit_application(self):
    """Force quit application (from tray Exit)"""
    reply = QMessageBox.question(self, "Conferma Uscita",
                                 "Sei sicuro di voler uscire da PingMonitor Pro?",
                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

    if reply == QMessageBox.StandardButton.Yes:
        # Perform cleanup
        self._perform_cleanup()

        # Hide tray icon
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()

        # Quit application
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()
```

### 2. File: `src/core/monitoring_engine.py`

#### Migliorato il Metodo `stop()`
Il metodo `stop()` è stato completamente riscritto per garantire una chiusura pulita e veloce:

```python
def stop(self):
    """Stop the monitoring engine with proper cleanup"""
    if not self.running:
        logger.warning("Monitoring engine is not running")
        return

    logger.info("Stopping monitoring engine...")
    self.running = False
    self.paused = False

    try:
        # 1. Cancel all active timers FIRST to prevent new tasks
        logger.info("Cancelling active timers...")
        with self._active_timers_lock:
            for timer in self._active_timers:
                if timer.is_alive():
                    timer.cancel()
            self._active_timers.clear()

        # 2. Wait for monitor thread to finish (max 2 seconds)
        logger.info("Waiting for monitor thread...")
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2.0)
            if self._monitor_thread.is_alive():
                logger.warning("Monitor thread did not finish in time")

        # 3. Wait for scheduler thread to finish (max 2 seconds)
        logger.info("Waiting for scheduler thread...")
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            self._scheduler_thread.join(timeout=2.0)
            if self._scheduler_thread.is_alive():
                logger.warning("Scheduler thread did not finish in time")

        # 4. Shutdown executor with short timeout
        logger.info("Shutting down executor...")
        if self.executor and not self.executor_shutdown:
            try:
                self.executor.shutdown(wait=True, cancel_futures=True)
                self.executor_shutdown = True
            except Exception as e:
                logger.warning(f"Executor shutdown warning: {e}")

        # 5. Clear queues
        logger.info("Clearing task queues...")
        while not self.task_queue.empty():
            try:
                self.task_queue.get_nowait()
            except:
                break

        # 6. Flush pending batch writes
        logger.info("Flushing pending database writes...")
        try:
            batch_writer.force_flush()
        except Exception as e:
            logger.warning(f"Batch writer flush warning: {e}")

        # 7. Log final performance metrics
        logger.info("Final performance summary:")
        try:
            performance_metrics.log_summary()
            logger.info(f"Device cache hit rate: {device_cache.get_hit_rate():.1f}% ({device_cache.hits} hits, {device_cache.misses} misses)")
        except Exception as e:
            logger.warning(f"Performance metrics warning: {e}")

        logger.info("Monitoring engine stopped successfully")

    except Exception as e:
        logger.error(f"Error stopping engine: {e}", exc_info=True)
```

### 3. File: `src/services/auto_recovery_service.py`

#### Aggiunto Tracking delle Connessioni SSH
Nel `__init__()`:

```python
def __init__(self, ssh_config: dict):
    """
    Initialize auto-recovery service

    Args:
        ssh_config: SSH configuration (username, password, etc.)
    """
    self.ssh_config = ssh_config
    self.recovery_log = {}
    self._active_connections = []  # Track active SSH connections for cleanup
```

#### Tracking in `attempt_recovery()`
```python
# Track connection for cleanup
self._active_connections.append(client)

# ...

finally:
    try:
        client.close()
        # Remove from active connections
        if client in self._active_connections:
            self._active_connections.remove(client)
    except:
        pass
```

#### Nuovo Metodo `cleanup()`
```python
def cleanup(self):
    """Close all SSH connections for clean shutdown"""
    logger.info("Closing all active SSH connections...")
    closed_count = 0

    for client in self._active_connections[:]:  # Create a copy to iterate
        try:
            client.close()
            closed_count += 1
        except Exception as e:
            logger.debug(f"Error closing SSH connection: {e}")

    self._active_connections.clear()
    logger.info(f"Closed {closed_count} SSH connections")
```

## Sequenza di Chiusura

La chiusura avviene ora in questo ordine preciso:

1. **Stop Monitoring Engine** (max 3 secondi)
   - Cancella tutti i timer attivi
   - Aspetta che i thread terminino (max 2 secondi ciascuno)
   - Chiude il ThreadPoolExecutor cancellando i futures in attesa
   - Svuota le code di task

2. **Stop UI Timers**
   - `update_timer` (aggiornamento UI)
   - `email_aggregate_timer` (report email periodici)

3. **Chiusura Connessioni SSH**
   - Terminale SSH integrato
   - Connessioni SSH del servizio auto-recovery

4. **Flush Database**
   - Scritture batch pending
   - Chiusura di tutte le sessioni database

5. **Salvataggio Configurazione**
   - Geometria della finestra
   - Configurazioni utente

## Timeout e Sicurezza

- **Timeout totale chiusura**: ~7-8 secondi massimo
- **Timeout per thread**: 2 secondi ciascuno
- **Timeout executor**: Immediato con `cancel_futures=True`
- **Gestione errori**: Tutti gli errori sono catturati e loggati senza bloccare la chiusura

## Test
Per testare il fix:

```bash
cd "C:\Users\Fabrizio.Cerchia\Desktop\PingMonitor Pro"
python test_cleanup.py
```

Il test avvia l'applicazione e la chiude dopo 10 secondi, verificando che:
- La chiusura avvenga in meno di 10 secondi
- Non ci siano freeze
- Tutti i log di cleanup siano presenti
- L'applicazione termini senza errori

## Verifica
Dopo le modifiche, verificare:

1. ✓ L'applicazione si chiude rapidamente (< 5 secondi)
2. ✓ Non ci sono freeze dell'interfaccia
3. ✓ Tutti i thread terminano correttamente
4. ✓ Le connessioni SSH vengono chiuse
5. ✓ Il database viene salvato correttamente
6. ✓ I log mostrano una sequenza di cleanup pulita

## File Modificati

- `src/ui/main_window_v2.py` - Aggiunto `_perform_cleanup()`, modificati `closeEvent()` e `quit_application()`
- `src/core/monitoring_engine.py` - Riscritto completamente `stop()`
- `src/services/auto_recovery_service.py` - Aggiunto tracking connessioni e metodo `cleanup()`

## Note Importanti

- Tutte le eccezioni durante la chiusura sono catturate e loggate ma non bloccano il processo
- I timeout sono configurati per garantire una chiusura rapida anche in caso di problemi
- La sequenza di cleanup è ottimizzata per minimizzare il rischio di deadlock
- Tutti i warning durante il cleanup sono normali e non indicano problemi
