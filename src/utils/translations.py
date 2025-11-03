"""
PingMonitor Pro - Traduzioni Italiano
Gestione centralizzata di tutte le stringhe dell'interfaccia
"""

# Traduzioni interfaccia principale
UI = {
    'app_title': 'PingMonitor Pro v2.3 - Monitoraggio Professionale Rete',
    'app_name': 'PingMonitor Pro',

    # Menu File
    'menu_file': '&File',
    'menu_import_devices': '&Importa Dispositivi da Config.json',
    'menu_export_config': '&Esporta Configurazione',
    'menu_exit': 'E&sci',

    # Menu View
    'menu_view': '&Vista',
    'menu_fullscreen': '&Schermo Intero',

    # Menu Tools
    'menu_tools': '&Strumenti',
    'menu_settings': '&Impostazioni',
    'menu_ssh_terminal': 'Terminale &SSH',

    # Menu Help
    'menu_help': '&Aiuto',
    'menu_about': '&Informazioni',

    # Toolbar
    'btn_start_monitoring': '▶ Avvia Monitoraggio',
    'btn_stop': '⏹ Stop',
    'btn_pause': '⏸ Pausa',
    'btn_resume': '▶ Riprendi',
    'btn_refresh': '🔄 Aggiorna',
    'btn_add_device': '➕ Aggiungi Dispositivo',
    'btn_ssh': '💻 Terminale SSH',

    # Tab names
    'tab_monitoring': '📊 Monitoraggio',
    'tab_logs': '📝 Log',
    'tab_devices': '🖥 Dispositivi',
    'tab_email_test': '📧 Test Email',
    'tab_settings': '⚙️ Impostazioni',

    # Status labels
    'lbl_total': 'Totale',
    'lbl_online': '🟢 Online',
    'lbl_offline': '🔴 Offline',
    'lbl_degraded': '🟡 Degradato',

    # Context menu
    'ctx_open_browser': '🌐 Apri nel Browser',
    'ctx_open_putty': '🖥 Apri in PuTTY',
    'ctx_open_ssh': '💻 Apri nel Terminale SSH',
    'ctx_force_reboot': '🔄 Forza Riavvio (SSH)',
    'ctx_force_check': '🔍 Forza Controllo Ora',
    'ctx_show_details': '📊 Mostra Dettagli',

    # System tray
    'tray_show': 'Mostra',
    'tray_exit': 'Esci',
    'tray_minimized': 'Applicazione minimizzata nella tray',
    'tray_already_running': 'PingMonitor Pro è già in esecuzione!',
    'tray_only_one_instance': 'Può essere eseguita solo una istanza alla volta.\\n\\nControlla la system tray.',

    # Status messages
    'status_ready': 'Pronto',
    'status_monitoring_active': '🟢 Monitoraggio Attivo',
    'status_monitoring_stopped': '🔴 Monitoraggio Fermato',
    'status_opening_browser': 'Apertura {} nel browser...',
    'status_opening_putty': 'Apertura PuTTY per {}...',
    'status_forcing_check': 'Forzando controllo per {}...',
    'status_auto_recovery': 'Auto-recupero avviato per {}',
    'status_settings_updated': 'Impostazioni aggiornate con successo!',

    # Dialog messages
    'dlg_error': 'Errore',
    'dlg_success': 'Successo',
    'dlg_warning': 'Avviso',
    'dlg_info': 'Informazione',
    'dlg_confirm': 'Conferma',

    'dlg_failed_browser': 'Impossibile aprire il browser:\\n{}',
    'dlg_putty_not_found': 'PuTTY non trovato',
    'dlg_putty_not_found_msg': 'PuTTY non è installato o non è nel PATH.\\n\\nInstallalo da: https://www.putty.org/',
    'dlg_confirm_reboot': 'Conferma Riavvio',
    'dlg_confirm_reboot_msg': 'Sei sicuro di voler riavviare {}?\\n\\nQuesta azione richiede SSH configurato.',
    'dlg_reboot_initiated': 'Riavvio Avviato',
    'dlg_reboot_initiated_msg': 'Comando di riavvio inviato a {}',
    'dlg_reboot_failed': 'Riavvio Fallito',
    'dlg_reboot_failed_msg': 'Impossibile riavviare {}:\\n{}',
    'dlg_device_details': 'Dettagli Dispositivo',
    'dlg_failed_start': 'Impossibile avviare il monitoraggio:\\n{}',
    'dlg_confirm_exit': 'Conferma Uscita',
    'dlg_confirm_exit_msg': 'Sei sicuro di voler uscire da PingMonitor Pro?',
    'dlg_confirm_exit_simple': 'Sei sicuro di voler uscire?',
    'dlg_devices_imported': 'Dispositivi Importati',
    'dlg_devices_imported_msg': 'Importati {} dispositivi da config.json',
    'dlg_import_failed': 'Importazione Fallita',
    'dlg_import_failed_msg': 'Impossibile importare i dispositivi:\\n{}',
    'dlg_settings_saved': 'Impostazioni salvate con successo!',
    'dlg_settings_restart': 'Alcune modifiche richiederanno il riavvio dell\\'applicazione.',
    'dlg_export_failed': 'Impossibile esportare la configurazione:\\n{}',

    # About dialog
    'about_title': 'Informazioni su PingMonitor Pro',
    'about_text': '''<h2>PingMonitor Pro v2.3</h2>
                     <p><b>Soluzione Professionale di Monitoraggio Rete</b></p>
                     <p>Sistema avanzato per il monitoraggio di CPUB PAI-PL<br>
                     (Passaggi a Livello Ferroviari)</p>
                     <p><b>Sviluppato da:</b> Fabrizio Cerchia</p>
                     <p><b>Anno:</b> 2025</p>
                     <p><b>Caratteristiche:</b></p>
                     <ul>
                     <li>Monitoraggio multi-protocollo (PING, HTTP, HTTPS, SSH, DNS)</li>
                     <li>Auto-recupero intelligente</li>
                     <li>Alert email automatici</li>
                     <li>Gestione centralizzata dispositivi</li>
                     <li>Interfaccia italiana professionale</li>
                     </ul>''',

    # Table headers
    'table_device': 'Dispositivo',
    'table_status': 'Stato',
    'table_ip': 'Indirizzo IP',
    'table_type': 'Tipo',
    'table_location': 'Posizione',
    'table_line': 'Linea',
    'table_doit': 'DOIT',
    'table_response_time': 'Tempo Risposta',
    'table_last_check': 'Ultimo Controllo',
    'table_uptime': 'Uptime %',

    # Device types (PAI-PL)
    'device_cpub': 'CPUB PAI-PL',
    'device_pl': 'Passaggio a Livello',
    'device_switch': 'Switch Rete',
    'device_server': 'Server',
    'device_unknown': 'Sconosciuto',
}

# Traduzioni Email
EMAIL = {
    'subject_alert': 'PingMonitor Pro - Allerta Dispositivo',
    'subject_test': 'PingMonitor Pro - Email di Test',
    'subject_alert_critical': '[CRITICO] PingMonitor Pro - Intervento Richiesto',

    'header_alert': 'ALLERTA DISPOSITIVO',
    'header_test': '✅ Test Email Riuscito',
    'header_critical': 'ALLERTA CRITICA',

    'status_offline': '🔴 Dispositivo OFFLINE',
    'status_online': '🟢 Dispositivo ONLINE',
    'status_degraded': '🟡 Servizio DEGRADATO',

    'device_info': 'Informazioni Dispositivo',
    'device_name': 'Nome Dispositivo',
    'device_ip': 'Indirizzo IP',
    'device_location': 'Posizione',
    'device_line': 'Linea Ferroviaria',
    'device_status': 'Stato',

    'recovery_info': 'Tentativo Auto-Recupero',
    'recovery_action': 'Azione di Recupero',
    'recovery_reboot': 'Riavvio SSH eseguito',
    'recovery_time': 'Ora Riavvio',
    'recovery_wait': 'Tempo di Attesa',
    'recovery_result': 'Risultato',
    'recovery_success': '✅ Dispositivo recuperato dopo riavvio',
    'recovery_failed': '❌ Dispositivo ancora OFFLINE dopo recupero',

    'action_required': '⚡ Azione Richiesta',
    'action_required_text': 'Questo dispositivo necessita di intervento manuale:',
    'action_steps': [
        'Connettersi via SSH per investigare',
        'Verificare log di sistema e servizi',
        'Eseguire diagnostica manuale',
        'Riavviare servizi o dispositivo'
    ],

    'test_email_text': 'Questa è una email di test da <strong>PingMonitor Pro v2.3</strong>.',
    'test_email_text2': 'Se hai ricevuto questa email, il sistema di allerta email è configurato correttamente.',
    'test_details': 'Dettagli Test',
    'test_time': 'Ora',
    'test_type': 'Tipo',
    'test_type_simple': 'Test Semplice',
    'test_status': 'Stato',
    'test_status_working': '✅ Funzionante',

    'footer': 'PingMonitor Pro v2.3 - Monitoraggio Professionale Rete PAI-PL',
    'footer_author': 'by Fabrizio Cerchia',

    'btn_web_interface': '🌐 Apri Interfaccia Web',
    'btn_ssh_connect': '💻 Connetti SSH',
}

# Traduzioni Settings
SETTINGS = {
    'title': 'Impostazioni',
    'tab_general': 'Generale',
    'tab_monitoring': 'Monitoraggio',
    'tab_email': 'Email',
    'tab_advanced': 'Avanzate',

    'lbl_check_interval': 'Intervallo Controllo (secondi)',
    'lbl_timeout': 'Timeout (secondi)',
    'lbl_retry_count': 'Numero Tentativi',
    'lbl_concurrent_checks': 'Controlli Simultanei',

    'lbl_smtp_server': 'Server SMTP',
    'lbl_smtp_port': 'Porta SMTP',
    'lbl_smtp_username': 'Nome Utente',
    'lbl_smtp_password': 'Password',
    'lbl_from_email': 'Email Mittente',
    'lbl_alert_email': 'Email Destinatari',
    'lbl_alert_email_hint': '(separati da virgola)',

    'btn_save': 'Salva',
    'btn_cancel': 'Annulla',
    'btn_test_email': 'Invia Email di Test',
    'btn_reset_defaults': 'Ripristina Predefiniti',
}

# Traduzioni Devices
DEVICES = {
    'title': 'Gestione Dispositivi',
    'btn_add': 'Aggiungi',
    'btn_edit': 'Modifica',
    'btn_delete': 'Elimina',
    'btn_enable': 'Abilita',
    'btn_disable': 'Disabilita',
    'btn_import': 'Importa da Excel',
    'btn_export': 'Esporta',

    'dlg_add_device': 'Aggiungi Dispositivo',
    'dlg_edit_device': 'Modifica Dispositivo',
    'dlg_delete_device': 'Elimina Dispositivo',
    'dlg_delete_confirm': 'Sei sicuro di voler eliminare {}?',

    'lbl_name': 'Nome',
    'lbl_ip': 'Indirizzo IP',
    'lbl_type': 'Tipo',
    'lbl_location': 'Posizione',
    'lbl_line': 'Linea Ferroviaria',
    'lbl_doit': 'DOIT',
    'lbl_km': 'Kilometraggio',
    'lbl_enabled': 'Abilitato',

    'placeholder_name': 'es. PL km 161+672',
    'placeholder_ip': 'es. 192.168.2.1',
    'placeholder_location': 'es. PGPL km 161+672',
    'placeholder_line': 'es. NAPOLI C.LE - FOGGIA',
}

# Traduzioni Logs
LOGS = {
    'title': 'Visualizzatore Log',
    'btn_refresh': 'Aggiorna',
    'btn_clear': 'Pulisci',
    'btn_export': 'Esporta',
    'btn_auto_refresh': 'Auto-Aggiornamento',

    'filter_all': 'Tutti',
    'filter_info': 'Info',
    'filter_warning': 'Avvisi',
    'filter_error': 'Errori',

    'lbl_filter': 'Filtro Livello:',
    'lbl_lines': 'righe',
    'lbl_last_refresh': 'Ultimo aggiornamento:',
}

def get(key, default=''):
    """Get translation by key (supports nested keys like 'EMAIL.subject_alert')"""
    if '.' in key:
        section, subkey = key.split('.', 1)
        section_dict = globals().get(section, {})
        return section_dict.get(subkey, default)
    return UI.get(key, default)
