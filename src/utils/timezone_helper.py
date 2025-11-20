"""
PingMonitor Pro - Timezone Helper
Gestisce la conversione dei timestamp da UTC a timezone locale (CET/CEST)
"""

from datetime import datetime, timezone
import pytz
import logging

logger = logging.getLogger(__name__)

# Timezone Italia (CET/CEST con cambio automatico ora legale)
ITALY_TZ = pytz.timezone('Europe/Rome')


def get_local_now():
    """
    Ottiene l'ora corrente in timezone locale italiano

    Returns:
        datetime: Ora corrente in timezone CET/CEST
    """
    return datetime.now(ITALY_TZ)


def utc_to_local(utc_dt):
    """
    Converte un datetime UTC in timezone locale italiano

    Args:
        utc_dt: datetime object in UTC (naive o aware)

    Returns:
        datetime: datetime in timezone CET/CEST
    """
    if utc_dt is None:
        return None

    # Se il datetime è naive (senza timezone), assumiamo che sia UTC
    if utc_dt.tzinfo is None:
        utc_dt = pytz.UTC.localize(utc_dt)

    # Converte a timezone italiano
    return utc_dt.astimezone(ITALY_TZ)


def local_to_utc(local_dt):
    """
    Converte un datetime locale in UTC

    Args:
        local_dt: datetime object in timezone locale

    Returns:
        datetime: datetime in UTC
    """
    if local_dt is None:
        return None

    # Se il datetime è naive, assumiamo che sia già in timezone locale
    if local_dt.tzinfo is None:
        local_dt = ITALY_TZ.localize(local_dt)

    # Converte a UTC
    return local_dt.astimezone(pytz.UTC)


def format_local_time(dt, format_str='%d/%m/%Y %H:%M:%S'):
    """
    Formatta un datetime in timezone locale

    Args:
        dt: datetime object (UTC o naive)
        format_str: formato stringa (default: dd/mm/yyyy HH:MM:SS)

    Returns:
        str: timestamp formattato in timezone locale
    """
    if dt is None:
        return 'N/A'

    # Se è una stringa ISO, convertiamo prima
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except:
            return dt

    # Converte a timezone locale
    local_dt = utc_to_local(dt)

    return local_dt.strftime(format_str)


def parse_iso_to_local(iso_string):
    """
    Parse una stringa ISO 8601 e converte in timezone locale

    Args:
        iso_string: stringa ISO 8601

    Returns:
        datetime: datetime in timezone locale
    """
    if not iso_string:
        return None

    try:
        # Parse ISO string
        dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        # Converte a locale
        return utc_to_local(dt)
    except Exception as e:
        logger.error(f"Errore parsing ISO string '{iso_string}': {e}")
        return None
