#!/usr/bin/env python3
"""Fail-closed release gate for a LearnPip catalog ZIP."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import zipfile

REQUIRED = {"manifest.json", "questions.json", "LICENSES.md", "NOTICE", "ATTRIBUTION"}
FORMAT_ID = "org.learnpip.catalog.zip"
SCHEMA_VERSION = "1.0.0"


def fail(message: str) -> None:
    raise SystemExit("Release abgelehnt: " + message)


def main() -> None:
    if len(sys.argv) != 2:
        fail("genau ein ZIP-Pfad ist erforderlich")
    path = Path(sys.argv[1])
    if not path.is_file():
        fail("Paket fehlt")
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            if not names or names[0] != "manifest.json":
                fail("manifest.json muss erster ZIP-Eintrag sein")
            if len(names) != len(set(names)):
                fail("doppelte ZIP-Pfade")
            missing = REQUIRED - set(names)
            if missing:
                fail("Pflichtdateien fehlen: " + ", ".join(sorted(missing)))
            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
            questions = json.loads(archive.read("questions.json").decode("utf-8"))
            if manifest.get("format_id") != FORMAT_ID:
                fail("unbekanntes format_id")
            if manifest.get("schema_version") != SCHEMA_VERSION:
                fail("Release-Workflow unterstützt derzeit nur Schema 1.0.0")
            if not isinstance(questions.get("questions"), list) or not questions["questions"]:
                fail("Fragenliste ist leer")
            declared = manifest.get("files")
            if not isinstance(declared, list):
                fail("manifest.files fehlt")
            records = {item.get("path"): item for item in declared if isinstance(item, dict)}
            expected = set(names) - {"manifest.json"}
            if set(records) != expected:
                fail("manifest.files entspricht nicht dem Archivinhalt")
            for name in sorted(expected):
                data = archive.read(name)
                record = records[name]
                if record.get("size") != len(data):
                    fail("falsche Dateigröße für " + name)
                digest = hashlib.sha256(data).hexdigest()
                if record.get("sha256") != digest:
                    fail("falscher SHA-256 für " + name)
    except (OSError, zipfile.BadZipFile, UnicodeError, json.JSONDecodeError) as error:
        fail(str(error))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    print("LearnPip-Katalogrelease geprüft")
    print("Format: " + FORMAT_ID)
    print("Schema: " + SCHEMA_VERSION)
    print("Paket: " + path.name)
    print("SHA-256: " + digest)


if __name__ == "__main__":
    main()
