#!/usr/bin/env python3
"""Reproduzierbarer Import des offiziellen BNetzA-Amateurfunk-Fragenkatalogs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

PACKAGE_ID = "de.bnetza.amateurfunk.pruefungsfragen"
SOURCE_URL = "https://www.bundesnetzagentur.de/Amateurfunk"
SOURCE_REVISION = "3. Auflage, März 2024"
SOURCE_VALID_FROM = "2024-06-24"
SOURCE_LICENSE = "DL-DE->BY-2.0"
LICENSE_ID = "DL-DE-BY-2.0"
SOURCE_SHA256 = "082fbf8de303d4ceafc57b9d5f15f211d08a2e24f3629b66c7e061abcb52bee4"
ATTRIBUTION = (
    "Prüfungsfragen zum Erwerb von Amateurfunkprüfungsbescheinigungen, "
    "Bundesnetzagentur, 3. Auflage, März 2024, "
    "(www.bundesnetzagentur.de/amateurfunk), Datenlizenz Deutschland – "
    "Namensnennung – Version 2.0 (www.govdata.de/dl-de/by-2-0)"
)
CLASS_NAMES = {"1": "N", "2": "E", "3": "A"}
EXPECTED_QUESTIONS = 1750
EXPECTED_MEDIA = 687
FIXED_ZIP_TIME = (2024, 3, 20, 0, 0, 0)
REPO_ROOT = Path(__file__).resolve().parents[1]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def license_info() -> dict:
    return {
        "id": LICENSE_ID,
        "license_url": "https://www.govdata.de/dl-de/by-2-0",
        "holder": "Bundesnetzagentur",
        "attribution": ATTRIBUTION,
    }


def provenance() -> dict:
    return {
        "kind": "verbatim",
        "source_url": SOURCE_URL,
        "source_revision": SOURCE_REVISION,
    }


def text_block(text: str) -> dict:
    return {"kind": "text", "text": text}


def image_block(path: str) -> dict:
    return {"kind": "image", "path": path}


def walk_sections(section: dict, parents: list[str]):
    path = parents + [section["title"]]
    for question in section.get("questions", []):
        yield path, question
    for child in section.get("sections", []):
        yield from walk_sections(child, path)


def add_media(
    source: zipfile.ZipFile,
    output_dir: Path,
    question_media: dict[str, dict],
    copied_media: dict[str, str],
    picture_id: str,
    alt: str,
) -> str:
    source_path = f"svgs/{picture_id}.svg"
    media_path = f"media/{picture_id}.svg"
    try:
        data = source.read(source_path)
    except KeyError as error:
        raise SystemExit(f"Referenziertes BNetzA-Medium fehlt: {source_path}") from error

    digest = sha256_bytes(data)
    previous = copied_media.get(media_path)
    if previous is not None and previous != digest:
        raise SystemExit(f"Widersprüchliche Mediendaten für {media_path}")
    if previous is None:
        (output_dir / media_path).write_bytes(data)
        copied_media[media_path] = digest

    question_media.setdefault(
        media_path,
        {
            "path": media_path,
            "alt": alt,
            "license": license_info(),
            "provenance": provenance(),
        },
    )
    return media_path


def write_json(path: Path, document: dict) -> None:
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    return info


def write_deterministic_zip(package: Path, output_dir: Path) -> None:
    files = [output_dir / "manifest.json"]
    files.extend(
        sorted(
            path
            for path in output_dir.rglob("*")
            if path.is_file() and path.name != "manifest.json"
        )
    )
    with zipfile.ZipFile(
        package, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as target:
        for path in files:
            name = path.relative_to(output_dir).as_posix()
            target.writestr(
                zip_info(name),
                path.read_bytes(),
                compress_type=zipfile.ZIP_DEFLATED,
                compresslevel=9,
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_zip", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--catalog-version", required=True)
    args = parser.parse_args()

    source_zip = args.source_zip.resolve()
    if not source_zip.is_file():
        raise SystemExit(f"BNetzA-Quelldatei fehlt: {source_zip}")
    actual_source_hash = sha256_file(source_zip)
    if actual_source_hash != SOURCE_SHA256:
        raise SystemExit(
            "Unerwartete BNetzA-Quelldatei: SHA-256 "
            f"{actual_source_hash}; erwartet {SOURCE_SHA256}"
        )

    out = args.output_dir.resolve()
    if out == REPO_ROOT.resolve() or out == source_zip.parent:
        raise SystemExit("Unsicheres Ausgabeverzeichnis")
    if out.exists():
        shutil.rmtree(out)
    (out / "media").mkdir(parents=True)

    try:
        source = zipfile.ZipFile(source_zip)
    except zipfile.BadZipFile as error:
        raise SystemExit("BNetzA-Quelldatei ist kein gültiges ZIP") from error

    with source:
        source_names = source.namelist()
        if len(source_names) != len(set(source_names)):
            raise SystemExit("BNetzA-Quelldatei enthält doppelte ZIP-Pfade")
        try:
            raw = source.read("fragenkatalog3b.json")
        except KeyError as error:
            raise SystemExit(
                "fragenkatalog3b.json fehlt in der BNetzA-Quelldatei"
            ) from error
        try:
            catalog = json.loads(raw.decode("utf-8-sig"))
        except (UnicodeError, json.JSONDecodeError) as error:
            raise SystemExit(
                "BNetzA-Fragenkatalog ist kein gültiges UTF-8-JSON"
            ) from error

        metadata = catalog.get("metadata")
        if not isinstance(metadata, dict):
            raise SystemExit("BNetzA-Metadaten fehlen")
        if metadata.get("edition") != SOURCE_REVISION:
            raise SystemExit(
                "Unerwartete BNetzA-Ausgabe: " + str(metadata.get("edition"))
            )
        if metadata.get("valid_from") != SOURCE_VALID_FROM:
            raise SystemExit(
                "Unerwarteter Gültigkeitsbeginn: " + str(metadata.get("valid_from"))
            )
        if metadata.get("license") != SOURCE_LICENSE:
            raise SystemExit(
                "Unerwartete Quellenlizenz: " + str(metadata.get("license"))
            )

        sections = catalog.get("sections")
        if not isinstance(sections, list) or not sections:
            raise SystemExit("BNetzA-Katalog enthält keine Abschnitte")

        questions: list[dict] = []
        copied_media: dict[str, str] = {}
        seen_numbers: set[str] = set()

        for top in sections:
            for section_path, source_question in walk_sections(top, []):
                number = source_question.get("number")
                if not isinstance(number, str) or not number:
                    raise SystemExit("Frage ohne gültige Prüfungsnummer")
                if number in seen_numbers:
                    raise SystemExit("Doppelte Fragenummer: " + number)
                seen_numbers.add(number)

                source_class = source_question.get("class")
                class_name = CLASS_NAMES.get(source_class)
                if class_name is None:
                    raise SystemExit("Unbekannte Klasse bei " + number)

                prompt_text = source_question.get("question")
                if not isinstance(prompt_text, str):
                    raise SystemExit(f"Ungültiges Feld question bei {number}")

                question_media: dict[str, dict] = {}
                prompt_blocks = [text_block(prompt_text)] if prompt_text.strip() else []
                q_picture = source_question.get("picture_question")
                if q_picture:
                    media_path = add_media(
                        source,
                        out,
                        question_media,
                        copied_media,
                        q_picture,
                        f"Abbildung zur Prüfungsfrage {number}",
                    )
                    prompt_blocks.append(image_block(media_path))
                if not prompt_blocks:
                    raise SystemExit(f"Frage ohne Text und Bild: {number}")
                prompt_summary = prompt_text if prompt_text.strip() else "[Bild]"

                answers = []
                for letter in "abcd":
                    answer_id = letter.upper()
                    answer_text = source_question.get(f"answer_{letter}")
                    if not isinstance(answer_text, str):
                        raise SystemExit(
                            f"Ungültiges Feld answer_{letter} bei {number}"
                        )
                    blocks = [text_block(answer_text)] if answer_text.strip() else []
                    picture = source_question.get(f"picture_{letter}")
                    if picture:
                        media_path = add_media(
                            source,
                            out,
                            question_media,
                            copied_media,
                            picture,
                            f"Abbildung zu Antwort {answer_id} der Prüfungsfrage {number}",
                        )
                        blocks.append(image_block(media_path))
                    if not blocks:
                        raise SystemExit(
                            f"Antwort {answer_id} ohne Text und Bild bei {number}"
                        )
                    answer_summary = answer_text if answer_text.strip() else "[Bild]"
                    answers.append(
                        {"id": answer_id, "text": answer_summary, "blocks": blocks}
                    )

                if not section_path:
                    raise SystemExit("Frage ohne Abschnitt: " + number)
                subject = section_path[0].removeprefix(
                    "Prüfungsfragen im Prüfungsteil: "
                )
                topic = section_path[-1]
                if not (1 <= len(subject) <= 120):
                    raise SystemExit("Ungültige Fachbezeichnung bei " + number)
                if not (1 <= len(topic) <= 120):
                    raise SystemExit("Ungültige Themenbezeichnung bei " + number)

                topics: list[str] = []
                for item in [f"Klasse {class_name}", *section_path]:
                    if (
                        not isinstance(item, str)
                        or not item.strip()
                        or len(item) > 128
                    ):
                        raise SystemExit("Ungültiger Themenpfad bei " + number)
                    if item not in topics:
                        topics.append(item)

                questions.append(
                    {
                        "id": f"bnetza:{number.lower()}",
                        "language": "de-DE",
                        "prompt": prompt_summary,
                        "answers": answers,
                        "correct_answer_ids": ["A"],
                        "explanation": "",
                        "topics": topics,
                        "difficulty": "unknown",
                        "license": license_info(),
                        "provenance": provenance(),
                        "media": list(question_media.values()),
                        "subject": subject,
                        "topic": topic,
                        "question_version": SOURCE_REVISION,
                        "selection_mode": "single",
                        "prompt_blocks": prompt_blocks,
                        "explanation_blocks": [],
                        "source_note": (
                            f"Originalfrage {number}; Amateurfunkklasse {class_name}"
                        ),
                    }
                )

        if len(questions) != EXPECTED_QUESTIONS:
            raise SystemExit(
                f"Erwartet {EXPECTED_QUESTIONS} Fragen, gefunden {len(questions)}"
            )
        if len(copied_media) != EXPECTED_MEDIA:
            raise SystemExit(
                f"Erwartet {EXPECTED_MEDIA} referenzierte SVGs, "
                f"gefunden {len(copied_media)}"
            )

    write_json(out / "questions.json", {"questions": questions})
    for name in ("LICENSES.md", "NOTICE", "ATTRIBUTION"):
        source_doc = REPO_ROOT / name
        if not source_doc.is_file():
            raise SystemExit(f"Repository-Dokument fehlt: {name}")
        shutil.copyfile(source_doc, out / name)

    files = []
    for path in sorted(path for path in out.rglob("*") if path.is_file()):
        rel = path.relative_to(out).as_posix()
        if rel == "manifest.json":
            continue
        data = path.read_bytes()
        record = {"path": rel, "sha256": sha256_bytes(data), "size": len(data)}
        if rel.endswith(".svg"):
            record["media_type"] = "image/svg+xml"
        files.append(record)

    manifest = {
        "format_id": "org.learnpip.catalog.zip",
        "schema_version": "1.0.0",
        "package_id": PACKAGE_ID,
        "catalog_version": args.catalog_version,
        "source_revision": SOURCE_REVISION,
        "title": "Amateurfunk-Prüfungsfragen Deutschland",
        "description": (
            "Offizielle Prüfungsfragen der Bundesnetzagentur für die "
            "Amateurfunkklassen N, E und A."
        ),
        "language": "de-DE",
        "publisher": "LearnPip-Catalog-Amateurfunk-DE",
        "created_at": "2024-03-20T00:00:00Z",
        "license": license_info(),
        "files": files,
    }
    write_json(out / "manifest.json", manifest)

    package = out.parent / f"{PACKAGE_ID}-{args.catalog_version}.zip"
    write_deterministic_zip(package, out)
    print(package)


if __name__ == "__main__":
    main()
