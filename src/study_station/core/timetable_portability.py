"""Timetable Portability Service for Study Station.

Provides robust import and export capabilities:
1. Export to JSON (matching official timetable schema with metadata).
2. Export to RFC 4180 CSV (with UTF-8 BOM for seamless Excel/Sheets compatibility).
3. Import from JSON with schema validation and descriptive error reporting.
4. Import from CSV with automatic delimiter detection (comma/semicolon) and French/English header support.
5. Import from University PDF schedule grids via pypdf with OCR-like text structure analysis.
6. Collision detection for overlapping time slots and duplicate prevention.
"""

from __future__ import annotations
import csv
from datetime import datetime
import json
from pathlib import Path
import re
from typing import Sequence
import unicodedata

from study_station.core.models import (
    AcademicSession,
    DAY_INDEX_MAP,
    Subject,
    TimeSlot,
    normalize_time_str,
)

# Standard Day Code Map (French + English variants)
DAY_NAME_MAP: dict[str, str] = {
    # French
    "lun": "Lun",
    "lundi": "Lun",
    "mar": "Mar",
    "mardi": "Mar",
    "mer": "Mer",
    "mercredi": "Mer",
    "jeu": "Jeu",
    "jeudi": "Jeu",
    "ven": "Ven",
    "vendredi": "Ven",
    "sam": "Sam",
    "samedi": "Sam",
    "dim": "Dim",
    "dimanche": "Dim",
    # English
    "mon": "Lun",
    "monday": "Lun",
    "tue": "Mar",
    "tuesday": "Mar",
    "wed": "Mer",
    "wednesday": "Mer",
    "thu": "Jeu",
    "thursday": "Jeu",
    "fri": "Ven",
    "friday": "Ven",
    "sat": "Sam",
    "saturday": "Sam",
    "sun": "Dim",
    "sunday": "Dim",
}

STANDARD_SLOTS = [
    ("08:00", "09:30"),
    ("09:40", "11:10"),
    ("11:15", "12:45"),
    ("13:30", "15:00"),
    ("15:10", "16:40"),
]


def normalize_day(day_str: str) -> str:
    """Normalize any day representation to standard 3-letter capital title (e.g. 'Lun')."""
    cleaned = day_str.strip().lower()
    return DAY_NAME_MAP.get(cleaned, day_str.strip().capitalize()[:3])


def clean_time(time_str: str) -> str:
    """Normalize hours/minutes to standard HH:MM (e.g. '8:00' -> '08:00', '8h30' -> '08:30')."""
    s = time_str.strip().lower().replace("h", ":")
    if ":" in s:
        parts = s.split(":")
        h = int(parts[0]) if parts[0].isdigit() else 0
        m = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        return f"{h:02d}:{m:02d}"
    elif s.isdigit():
        return f"{int(s):02d}:00"
    return time_str.strip()


def export_sessions_to_json(
    sessions: Sequence[AcademicSession],
    target_file: Path | str,
    metadata: dict | None = None,
) -> None:
    """Export academic sessions to structured JSON matching the timetable schema."""
    target_path = Path(target_file)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    sorted_sessions = sorted(sessions, key=lambda s: (s.day_index, s.time_slot.start))

    export_data = {
        "greeting": "Study Station Timetable Export",
        "metadata": metadata or {
            "exportedAt": datetime.now().isoformat(),
            "totalSessions": len(sorted_sessions),
            "format": "StudyStation-v1.0",
        },
        "sessions": [
            {
                "day": s.day,
                "timeSlot": {
                    "start": s.time_slot.start,
                    "end": s.time_slot.end,
                },
                "subject": {
                    "name": s.subject.name,
                    "core": s.subject.core,
                },
                "location": s.location or "",
            }
            for s in sorted_sessions
        ],
    }

    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)


def export_sessions_to_csv(
    sessions: Sequence[AcademicSession],
    target_file: Path | str,
) -> None:
    """Export sessions to RFC 4180 CSV with UTF-8 BOM for Excel/Sheets compatibility."""
    target_path = Path(target_file)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    sorted_sessions = sorted(sessions, key=lambda s: (s.day_index, s.time_slot.start))

    with open(target_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Day", "Start", "End", "Subject", "Core", "Location"])
        for s in sorted_sessions:
            writer.writerow([
                s.day,
                s.time_slot.start,
                s.time_slot.end,
                s.subject.name,
                s.subject.core,
                s.location or "",
            ])


def import_sessions_from_json(source: Path | str) -> tuple[list[AcademicSession], list[str]]:
    """Parse sessions from a JSON file or raw JSON string.
    
    Returns (sessions, warnings).
    """
    warnings: list[str] = []
    sessions: list[AcademicSession] = []

    try:
        source_path = Path(source)
        if source_path.exists() and source_path.is_file():
            with open(source_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = json.loads(str(source))
    except Exception as e:
        return [], [f"Failed to parse JSON content: {e}"]

    raw_list = data.get("sessions") if isinstance(data, dict) else (data if isinstance(data, list) else None)
    if not isinstance(raw_list, list):
        return [], ["Invalid format: JSON does not contain a 'sessions' list."]

    for idx, item in enumerate(raw_list, start=1):
        if not isinstance(item, dict):
            warnings.append(f"Row {idx}: Skipped non-dictionary session entry.")
            continue

        day_raw = item.get("day", "")
        day = normalize_day(day_raw)
        if day not in DAY_INDEX_MAP:
            warnings.append(f"Row {idx}: Unknown day '{day_raw}'.")
            continue

        time_data = item.get("timeSlot") or item.get("time_slot") or {}
        start = clean_time(time_data.get("start", ""))
        end = clean_time(time_data.get("end", ""))
        if not start or not end:
            warnings.append(f"Row {idx}: Missing start or end time.")
            continue

        subj_data = item.get("subject", {})
        if isinstance(subj_data, dict):
            subj_name = subj_data.get("name", "").strip()
            core = subj_data.get("core", "COURS").strip().upper()
        else:
            subj_name = str(subj_data).strip()
            core = str(item.get("core", "COURS")).strip().upper()

        if not subj_name:
            warnings.append(f"Row {idx}: Missing subject name.")
            continue

        location = str(item.get("location", "")).strip()

        sessions.append(
            AcademicSession(
                day=day,
                time_slot=TimeSlot(start=start, end=end),
                subject=Subject(name=subj_name, core=core),
                location=location,
            )
        )

    return sessions, warnings


def import_sessions_from_csv(source: Path | str) -> tuple[list[AcademicSession], list[str]]:
    """Parse sessions from a CSV file or raw string with delimiter sniffing.
    
    Returns (sessions, warnings).
    """
    warnings: list[str] = []
    sessions: list[AcademicSession] = []

    content = ""
    source_path = Path(source)
    if source_path.exists() and source_path.is_file():
        with open(source_path, "r", encoding="utf-8-sig", errors="replace") as f:
            content = f.read()
    else:
        content = str(source)

    if not content.strip():
        return [], ["CSV file is empty."]

    # Sniff delimiter (comma or semicolon)
    first_line = content.splitlines()[0]
    delimiter = ";" if first_line.count(";") > first_line.count(",") else ","

    reader = csv.reader(content.splitlines(), delimiter=delimiter)
    try:
        header = next(reader)
    except StopIteration:
        return [], ["CSV file is empty."]

    # Header index mapping
    col_map: dict[str, int] = {}
    for idx, col in enumerate(header):
        c = col.strip().lower()
        if c in ("day", "jour", "weekday"):
            col_map["day"] = idx
        elif c in ("start", "start_time", "debut", "début", "heure debut"):
            col_map["start"] = idx
        elif c in ("end", "end_time", "fin", "heure fin"):
            col_map["end"] = idx
        elif c in ("subject", "matiere", "matière", "course", "cours"):
            col_map["subject"] = idx
        elif c in ("core", "type", "format"):
            col_map["core"] = idx
        elif c in ("location", "salle", "lab", "room"):
            col_map["location"] = idx

    # Fallback to positional columns if headers are standard Day, Start, End, Subject...
    if "day" not in col_map and len(header) >= 4:
        col_map = {"day": 0, "start": 1, "end": 2, "subject": 3, "core": 4, "location": 5}

    if "day" not in col_map or "start" not in col_map or "end" not in col_map or "subject" not in col_map:
        return [], ["CSV missing required columns (Day, Start, End, Subject)."]

    for row_idx, row in enumerate(reader, start=2):
        if not row or not any(row):
            continue

        try:
            day_raw = row[col_map["day"]]
            start_raw = row[col_map["start"]]
            end_raw = row[col_map["end"]]
            subj_raw = row[col_map["subject"]]
            core_raw = row[col_map["core"]] if "core" in col_map and col_map["core"] < len(row) else "COURS"
            loc_raw = row[col_map["location"]] if "location" in col_map and col_map["location"] < len(row) else ""

            day = normalize_day(day_raw)
            if day not in DAY_INDEX_MAP:
                warnings.append(f"Row {row_idx}: Unknown day '{day_raw}'.")
                continue

            start = clean_time(start_raw)
            end = clean_time(end_raw)
            subj = subj_raw.strip()
            if not subj:
                warnings.append(f"Row {row_idx}: Empty subject name.")
                continue

            sessions.append(
                AcademicSession(
                    day=day,
                    time_slot=TimeSlot(start=start, end=end),
                    subject=Subject(name=subj, core=core_raw.strip().upper() or "COURS"),
                    location=loc_raw.strip(),
                )
            )
        except Exception as e:
            warnings.append(f"Row {row_idx}: Error parsing row: {e}")

    return sessions, warnings


def import_sessions_from_pdf(source: Path | str) -> tuple[list[AcademicSession], list[str]]:
    """Extract timetable sessions from a university schedule PDF grid.
    
    Returns (sessions, warnings).
    """
    warnings: list[str] = []
    sessions: list[AcademicSession] = []

    pdf_path = Path(source)
    if not pdf_path.exists():
        return [], [f"PDF file not found: {pdf_path}"]

    try:
        import pypdf
    except ImportError:
        return [], ["pypdf is not installed. Please install pypdf to parse PDF files."]

    try:
        reader = pypdf.PdfReader(str(pdf_path))
        if not reader.pages:
            return [], ["PDF contains no pages."]

        raw_text = reader.pages[0].extract_text()
        norm_text = unicodedata.normalize("NFKD", raw_text)
        # Normalize ligatures and spacing
        norm_text = (
            norm_text.replace("\ufb01", "fi")
            .replace("\ufb02", "fl")
            .replace("V en", "Ven")
            .replace(",h", "")
            .replace("/◦•", "")
            .replace("/•◦", "")
        )
    except Exception as e:
        return [], [f"Failed to read PDF file: {e}"]

    # University schedule pattern parser:
    # Matches day blocks: Lun, Mar, Mer, Jeu, Ven, Sam
    day_blocks = re.split(r"\n(?=(?:Lun|Mar|Mer|Jeu|Ven|Sam)\b)", norm_text)

    # Core types to recognize
    core_pattern = re.compile(r"\b(TP|Cours|TD|CI)\b", re.IGNORECASE)

    for block in day_blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue

        first_word = lines[0].split()[0] if lines[0].split() else ""
        day = normalize_day(first_word)
        if day not in DAY_INDEX_MAP:
            continue

        # Re-join remaining block lines to extract class blocks
        day_content = " ".join(lines)
        # Remove day prefix
        day_content = re.sub(r"^(?:Lun|Mar|Mer|Jeu|Ven|Sam)\b", "", day_content, flags=re.IGNORECASE).strip()

        # Split on format markers (TP, Cours, TD, CI)
        segments = re.split(r"(?=\b(?:TP|Cours|TD|CI)\b)", day_content, flags=re.IGNORECASE)

        day_sessions: list[tuple[str, str, str]] = []  # (core, subject, location)
        for seg in segments:
            seg = seg.strip(" ,.\n\t")
            if not seg:
                continue

            match = core_pattern.match(seg)
            if not match:
                continue

            core = match.group(1).upper()
            body = seg[match.end() :].strip(" ,.\n\t")

            # Split on commas to extract subject, teacher, and room
            parts = [p.strip() for p in body.split(",") if p.strip()]
            if not parts:
                continue

            subj_raw = parts[0]
            # Clean unwanted artifacts and student group references
            subj_clean = re.sub(r"\bT-LSI\b.*", "", subj_raw, flags=re.IGNORECASE).strip()
            if not subj_clean and len(parts) > 1:
                subj_clean = parts[1]

            # Room/location is typically the last element (e.g. Lab 20, SC 3, S 1)
            location = ""
            for p in reversed(parts):
                if re.search(r"\b(Lab|SC|Salle|S|Amphi)\b", p, re.IGNORECASE):
                    location = p
                    break

            if subj_clean:
                day_sessions.append((core, subj_clean, location))

        # Assign sessions to standard university time slots in order
        for idx, (c, s_name, loc) in enumerate(day_sessions):
            if idx < len(STANDARD_SLOTS):
                slot_start, slot_end = STANDARD_SLOTS[idx]
            else:
                slot_start, slot_end = ("16:50", "18:20")

            sessions.append(
                AcademicSession(
                    day=day,
                    time_slot=TimeSlot(start=slot_start, end=slot_end),
                    subject=Subject(name=s_name, core=c),
                    location=loc,
                )
            )

    if not sessions:
        warnings.append("No class sessions could be identified in the PDF.")

    return sessions, warnings


def detect_collisions(sessions: Sequence[AcademicSession]) -> list[tuple[AcademicSession, AcademicSession]]:
    """Detect time overlaps between sessions scheduled on the same weekday."""
    collisions: list[tuple[AcademicSession, AcademicSession]] = []
    by_day: dict[str, list[AcademicSession]] = {}

    for s in sessions:
        by_day.setdefault(s.day.upper(), []).append(s)

    for day, day_sessions in by_day.items():
        for i in range(len(day_sessions)):
            for j in range(i + 1, len(day_sessions)):
                s1 = day_sessions[i]
                s2 = day_sessions[j]
                # Check overlap: start_1 < end_2 and start_2 < end_1
                if s1.time_slot.start < s2.time_slot.end and s2.time_slot.start < s1.time_slot.end:
                    collisions.append((s1, s2))

    return collisions


def merge_sessions(
    existing: Sequence[AcademicSession],
    incoming: Sequence[AcademicSession],
    replace: bool = False,
) -> tuple[list[AcademicSession], int, int]:
    """Merge incoming sessions with existing ones.
    
    Returns (final_sessions, added_count, duplicate_count).
    """
    if replace:
        return list(incoming), len(incoming), 0

    combined = list(existing)
    added = 0
    duplicates = 0

    # Build unique identity set for existing
    existing_identities = {
        (s.day.upper(), s.time_slot.start, s.time_slot.end, s.subject.name.strip().lower())
        for s in existing
    }

    for s in incoming:
        ident = (s.day.upper(), s.time_slot.start, s.time_slot.end, s.subject.name.strip().lower())
        if ident in existing_identities:
            duplicates += 1
        else:
            combined.append(s)
            existing_identities.add(ident)
            added += 1

    combined.sort(key=lambda s: (s.day_index, s.time_slot.start))
    return combined, added, duplicates
