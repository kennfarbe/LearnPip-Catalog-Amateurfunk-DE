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
LICENSE_ID = "DL-DE-BY-2.0"
SOURCE_SHA256 = "082fbf8de303d4ceafc57b9d5f15f211d08a2e24f3629b66c7e061abcb52bee4"\nATTRIBUTION = (
    "Prüfungsfragen zum Erwerb von Amateurfunkprüfungsbescheinigungen, "
    "Bundesnetzagentur, 3. Auflage, März 2024, "
    "(www.bundesnetzagentur.de/amateurfunk), Datenlizenz Deutschland – "
    "Namensnennung – Version 2.0 (www.govdata.de/dl-de/by-2-0)"
)
CLASS_NAMES = {"1": "N", "2": "E", "3": "A"}
PICTURE_FIELDS = {
    "picture_question": None,
    "picture_a": "A",
    "picture_b": "B",
    "picture_c": "C",
    "picture_d": "D",
}


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


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_zip", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--catalog-version", required=True)
    args = parser.parse_args()

    out = args.output_dir
    if out.exists():
        shutil.rmtree(out)
    (out / "media").mkdir(parents=True)

    with zipfile.ZipFile(args.source_zip) as source:
        raw = source.read("fragenkatalog3b.json")
        catalog = json.loads(raw.decode("utf-8"))
        metadata = catalog["metadata"]
        if metadata.get("edition") != SOURCE_REVISION:
            raise SystemExit("Unerwartete BNetzA-Ausgabe: " + str(metadata.get("edition")))
        if metadata.get("valid_from") != "2024-06-24":
            raise SystemExit("Unerwarteter Gültigkeitsbeginn")
        if metadata.get("license") != "DL-DE->BY-2.0":
            raise SystemExit("Unerwartete Quellenlizenz")

        questions = []
        copied_media: set[str] = set()
        seen_ids: set[str] = set()

        for top in catalog["sections"]:
            for section_path, source_question in walk_sections(top, []):
                number = source_question["number"]
                if number in seen_ids:
                    raise SystemExit("Doppelte Fragenummer: " + number)
                seen_ids.add(number)
                class_name = CLASS_NAMES.get(source_question["class"])
                if class_name is None:
                    raise SystemExit("Unbekannte Klasse bei " + number)

                prompt_blocks = [text_block(source_question["question"])]
                media = []
                q_picture = source_question.get("picture_question")
                if q_picture:
                    media_path = f"media/{q_picture}.svg"
                    source_path = f"svgs/{q_picture}.svg"
                    data = source.read(source_path)
                    (out / media_path).write_bytes(data)
                    copied_media.add(media_path)
                    prompt_blocks.append(image_block(media_path))
                    media.append({
                        "path": media_path,
                        "alt": f"Abbildung zur Prüfungsfrage {number}",
                        "license": license_info(),
                        "provenance": provenance(),
                    })

                answers = []
                for letter in "abcd":
                    answer_id = letter.upper()
                    answer_text = source_question[f"answer_{letter}"]
                    blocks = [text_block(answer_text)]
                    picture = source_question.get(f"picture_{letter}")
                    if picture:
                        media_path = f"media/{picture}.svg"
                        source_path = f"svgs/{picture}.svg"
                        data = source.read(source_path)
                        (out / media_path).write_bytes(data)
                        copied_media.add(media_path)
                        blocks.append(image_block(media_path))
                        media.append({
                            "path": media_path,
                            "alt": f"Abbildung zu Antwort {answer_id} der Prüfungsfrage {number}",
                            "license": license_info(),
                            "provenance": provenance(),
                        })
                    answers.append({"id": answer_id, "text": answer_text, "blocks": blocks})

                subject = section_path[0].replace("Prüfungsfragen im Prüfungsteil: ", "")
                topic = section_path[-1]
                topics = []
                for item in [f"Klasse {class_name}", *section_path]:
                    if item not in topics:
                        topics.append(item[:128])

                questions.append({
                    "id": f"bnetza:{number.lower()}",
                    "language": "de-DE",
                    "prompt": source_question["question"],
                    "answers": answers,
                    "correct_answer_ids": ["A"],
                    "explanation": "",
                    "topics": topics,
                    "difficulty": "unknown",
                    "license": license_info(),
                    "provenance": provenance(),
                    "media": media,
                    "subject": subject[:120],
                    "topic": topic[:120],
                    "question_version": SOURCE_REVISION,
                    "selection_mode": "single",
                    "prompt_blocks": prompt_blocks,
                    "explanation_blocks": [],
                    "source_note": f"Originalfrage {number}; Amateurfunkklasse {class_name}",
                })

        if len(questions) != 1750:
            raise SystemExit(f"Erwartet 1750 Fragen, gefunden {len(questions)}")
        if len(copied_media) != 687:
            raise SystemExit(f"Erwartet 687 referenzierte SVGs, gefunden {len(copied_media)}")

    questions_doc = {"questions": questions}
    (out / "questions.json").write_text(
        json.dumps(questions_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    for name in ("LICENSES.md", "NOTICE", "ATTRIBUTION"):
        shutil.copyfile(Path(name), out / name)

    files = []
    for path in sorted(p for p in out.rglob("*") if p.is_file()):
        rel = path.relative_to(out).as_posix()
        if rel == "manifest.json":
            continue
        data = path.read_bytes()
        record = {"path": rel, "sha256": sha256(data), "size": len(data)}
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
        "description": "Offizielle Prüfungsfragen der Bundesnetzagentur für die Amateurfunkklassen N, E und A.",
        "language": "de-DE",
        "publisher": "LearnPip-Catalog-Amateurfunk-DE",
        "created_at": "2024-03-20T00:00:00Z",
        "license": license_info(),
        "files": files,
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    package = out.parent / f"{PACKAGE_ID}-{args.catalog_version}.zip"
    with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as target:
        target.write(out / "manifest.json", "manifest.json")
        for path in sorted(p for p in out.rglob("*") if p.is_file() and p.name != "manifest.json"):
            target.write(path, path.relative_to(out).as_posix())
    print(package)


if __name__ == "__main__":
    main()
