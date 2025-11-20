# Fix Alert Email - Intervallo Modificato da 24 ore a 6 ore

## Problema Risolto
Gli alert aggregati erano configurati per essere inviati ogni 24 ore invece di ogni 6 ore come richiesto.

## File Modificati

### 1. `src/ui/main_window_v2.py`

#### Modifica Timer (Linea 119)
**Prima:**
```python
self.email_aggregate_timer.start(86400000)  # 24 hours = 86400000 ms (daily report)
```

**Dopo:**
```python
self.email_aggregate_timer.start(21600000)  # 6 hours = 21600000 ms (6 ore × 60 min × 60 sec × 1000 ms)
```

**Calcolo:**
- 6 ore × 60 minuti = 360 minuti
- 360 minuti × 60 secondi = 21,600 secondi
- 21,600 secondi × 1,000 millisecondi = 21,600,000 ms

#### Aggiunto Logging Inizializzazione (Linee 122-135)
Aggiunto logging dettagliato all'avvio per confermare che:
- Timer è attivo
- Intervallo è corretto (6 ore)
- Destinatari sono configurati
- Server SMTP è configurato

```python
# Log timer initialization
if self.email_config and self.email_config.get('smtp_server'):
    recipients = self.aggregated_email_service._get_recipients()
    logger.info("=" * 80)
    logger.info("AGGREGATED EMAIL SERVICE INITIALIZED")
    logger.info(f"Timer interval: 6 hours (21,600,000 ms)")
    logger.info(f"Next report scheduled in: 6 hours")
    logger.info(f"Recipients: {recipients}")
    logger.info(f"SMTP Server: {self.email_config.get('smtp_server')} : {self.email_config.get('smtp_port')}")
    logger.info("=" * 80)
else:
    logger.warning("=" * 80)
    logger.warning("EMAIL CONFIG MISSING - Aggregated email reports DISABLED")
    logger.warning("Configure email settings in the Settings tab to enable reports")
    logger.warning("=" * 80)
```

#### Migliorato Logging Invio Email (Funzione `_send_aggregated_email`, Linee 1653-1684)
Aggiunto logging dettagliato per ogni invio schedulato:
- Data e ora del trigger
- Presenza di risultati da inviare
- Esito dell'invio (successo/fallimento)
- Messaggio di stato

### 2. `src/services/aggregated_email_service.py`

#### Aggiornato Subject Email (Linea 100)
**Prima:**
```python
msg['Subject'] = f"PingMonitor Pro - Report Giornaliero Dispositivi PAI-PL ({datetime.now().strftime('%d/%m/%Y')})"
```

**Dopo:**
```python
msg['Subject'] = f"PingMonitor Pro - Report Dispositivi PAI-PL ({datetime.now().strftime('%d/%m/%Y %H:%M')})"
```
- Rimosso "Giornaliero" (non è più accurato)
- Aggiunto orario nell'oggetto per identificare il report

#### Aggiornato Corpo Email HTML (Linee 210-215)
**Prima:**
```html
<div class="summary">
    <p><strong>Data Report:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
    <p><strong>Dispositivi Recuperati (ultime 24 ore):</strong> ...</p>
    <p><strong>Tentativi Recupero Falliti (ultime 24 ore):</strong> ...</p>
</div>
```

**Dopo:**
```html
<div class="summary">
    <p><strong>Data Report:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
    <p><strong>Frequenza Report:</strong> Ogni 6 ore (automatico)</p>
    <p><strong>Dispositivi Recuperati (ultime 6 ore):</strong> ...</p>
    <p><strong>Tentativi Recupero Falliti (ultime 6 ore):</strong> ...</p>
</div>
```
- Aggiunto indicatore di frequenza report
- Cambiato timeframe da "24 ore" a "6 ore"

#### Aggiunto Logging Dettagliato (Linea 86)
```python
logger.info(f"send_aggregated_email called - force={force}, pending_recoveries={len(self.pending_recoveries)}, pending_failures={len(self.pending_failures)}")
logger.info(f"Email recipients: {recipients}")
```

## Test Effettuati

### Test 1: Calcolo Timer
✓ Verificato che 6 ore = 21,600,000 millisecondi
✓ Verificato che il timer QTimer accetta questo valore

### Test 2: Inizializzazione Servizio Email
✓ Servizio si inizializza correttamente
✓ Destinatari predefiniti sono presenti:
  - fabrizio.cerchia@eredimercuri.com
  - assistenza.paipl@eredimercuri.com

### Test 3: Logging
✓ Logging all'avvio mostra configurazione corretta
✓ Logging ad ogni trigger del timer
✓ Logging per invii email (successi e fallimenti)

## Comportamento Atteso

### All'Avvio
Nei log apparirà:
```
================================================================================
AGGREGATED EMAIL SERVICE INITIALIZED
Timer interval: 6 hours (21,600,000 ms)
Next report scheduled in: 6 hours
Recipients: ['fabrizio.cerchia@eredimercuri.com', 'assistenza.paipl@eredimercuri.com']
SMTP Server: smtp.gmail.com : 587
================================================================================
```

### Ogni 6 Ore (Automatico)
Il timer triggera automaticamente la funzione `_send_aggregated_email` che:
1. Verifica se ci sono risultati da inviare (recuperi o fallimenti)
2. Se SÌ: invia email con:
   - Dispositivi recuperati nelle ultime 6 ore
   - Dispositivi che hanno fallito recovery nelle ultime 6 ore
   - Stato ATTUALE di TUTTI i dispositivi (offline, degraded, online)
3. Se NO: salta l'invio e logga "No pending recovery results to send"

### Con Pulsante "Check Now"
Forza un controllo immediato e invia SEMPRE un'email di report (anche senza pending results).

## Note Importanti

1. **Timer Permanente**: Il timer continua a girare anche se non ci sono dispositivi con problemi
2. **Email Condizionale**: L'email viene inviata solo se ci sono:
   - Recuperi riusciti nelle ultime 6 ore, OPPURE
   - Fallimenti nelle ultime 6 ore, OPPURE
   - Uso del pulsante "Check Now" (force=True)
3. **Stato Real-Time**: Ogni email include SEMPRE lo stato attuale di tutti i dispositivi
4. **Destinatari Fissi**: I destinatari predefiniti sono sempre inclusi
5. **Logging Completo**: Ogni operazione è loggata per debugging

## Verifica Funzionamento

Per verificare che il fix funzioni:

1. **Avvia l'applicazione** e controlla i log all'avvio
2. **Cerca nei log**: "AGGREGATED EMAIL SERVICE INITIALIZED"
3. **Verifica**: Timer interval deve essere "6 hours (21,600,000 ms)"
4. **Aspetta 6 ore** OPPURE usa il pulsante "Check Now"
5. **Controlla email** ai destinatari configurati
6. **Verifica subject**: Deve includere data e ora
7. **Verifica corpo**: Deve dire "Frequenza Report: Ogni 6 ore (automatico)"

## Rollback (se necessario)

Se serve tornare a 24 ore:
1. In `main_window_v2.py` linea 119: cambia `21600000` → `86400000`
2. In `aggregated_email_service.py` linea 212: cambia "Ogni 6 ore" → "Ogni 24 ore"
3. In `aggregated_email_service.py` linee 213-214: cambia "ultime 6 ore" → "ultime 24 ore"

## Data Fix
17/11/2025 - 18:20
