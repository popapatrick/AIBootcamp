"""Extracție: text raport/apel -> Event (vezi extract.py)."""
from backend.extract.extract import CacheMiss, extract_event

__all__ = ["extract_event", "CacheMiss"]
