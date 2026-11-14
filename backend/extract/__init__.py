"""Extracție: text raport/apel -> Event (vezi extract.py)."""
from backend.extract.extract import CacheMiss, extract_event, extract_event_cu_metoda

__all__ = ["extract_event", "extract_event_cu_metoda", "CacheMiss"]
