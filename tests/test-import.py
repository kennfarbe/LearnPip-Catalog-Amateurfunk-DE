#!/usr/bin/env python3
"""End-to-end regression test for the pinned BNetzA source archive."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

SOURCE_SHA256 = "082fbf8de303d4ceafc57b9d5f15f211d08a2e24f3629b66c7e061abcb52bee4"
PACKAGE_ID = "de.bnetza.amateurfunk.pruefungsfragen"
CLASS_NAMES = {"1": "N", "2": "E", "3": "A"}
EXPECTED_CLASSES = {"N": 571, "E": 463, "A": 716}
EXPECTED_QUESTIONS = 1750
EXPECTED_MEDIA = 687
REPO_ROOT = Path(__file__).resolve().parents[1]
IMPORTER = REPO_ROOT / "scripts" / "import-bnetza.py"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def walk_sections(section: dict, parents: list[str]):
    path = parents + [section["title"]]
    for question in section.get("questions", []):
        yield path, question
    for child in section.get("sections", []):
        yield from walk_sections(child, path)


def build(source: Path, root: Path, version: str) -> tuple[Path, Path]:
    out = root / "catalog"
    subprocess.run(
        [
            sys.executable,
            str(IMPORTER),
            str(source),
            str(out),
            "--catalog-version",
            version,
        ],
        cwd=REPO_ROOT,
        check=True,
    )
    return out, root / f"{PACKAGE_ID}-{version}.zip"


def expected_blocks(text: str, picture: str | None) -> list[dict]:
    blocks = []
    if text.strip():
        blocks.append({"kind": "text", "text": text})
    if picture:
        blocks.append({"kind": "image", "path": f"media/{picture}.svg"})
    return blocks


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: test-import.py SOURCE.zip")

    source = Path(sys.argv[1]).resolve()
    assert source.is_file()
    assert digest(source) == SOURCE_SHA256

    with zipfile.ZipFile(source) as source_archive:
        source_document = json.loads(
            source_archive.read("fragenkatalog3b.json").decode("utf-8-sig")
        )
        expected = {}
        referenced_source_media = set()
        for top in source_document["sections"]:
            for section_path, source_question in walk_sections(top, []):
                number = source_question["number"]
                assert number not in expected
                expected[number] = (section_path, source_question)
                for key in (
                    "picture_question",
                    "picture_a",
                    "picture_b",
                    "picture_c",
                    "picture_d",
                ):
                    picture = source_question.get(key)
                    if picture:
                        referenced_source_media.add(picture)
                        assert source_archive.read(f"svgs/{picture}.svg")

        assert len(expected) == EXPECTED_QUESTIONS
        assert len(referenced_source_media) == EXPECTED_MEDIA

        with (
            tempfile.TemporaryDirectory() as first_tmp,
            tempfile.TemporaryDirectory() as second_tmp,
        ):
            out, package = build(source, Path(first_tmp), "test")
            _, second_package = build(source, Path(second_tmp), "test")
            assert package.is_file()
            assert second_package.is_file()
            assert digest(package) == digest(
                second_package
            ), "Katalog-ZIP ist nicht reproduzierbar"

            document = json.loads(
                (out / "questions.json").read_text(encoding="utf-8")
            )
            questions = document["questions"]
            assert len(questions) == EXPECTED_QUESTIONS
            generated = {
                question["id"].removeprefix("bnetza:").upper(): question
                for question in questions
            }
            assert set(generated) == set(expected)

            classes = Counter()
            generated_media = set()
            for number, (section_path, source_question) in expected.items():
                question = generated[number]
                class_name = CLASS_NAMES[source_question["class"]]
                classes[class_name] += 1

                prompt_text = source_question["question"]
                prompt_picture = source_question.get("picture_question")
                assert question["prompt"] == (
                    prompt_text if prompt_text.strip() else "[Bild]"
                )
                assert question["prompt_blocks"] == expected_blocks(
                    prompt_text, prompt_picture
                )
                assert question["correct_answer_ids"] == ["A"]
                assert question["selection_mode"] == "single"
                assert question["explanation"] == ""
                assert question["explanation_blocks"] == []
                assert f"Klasse {class_name}" in question["topics"]
                assert question["subject"] == section_path[0].removeprefix(
                    "Prüfungsfragen im Prüfungsteil: "
                )
                assert question["topic"] == section_path[-1]

                assert [answer["id"] for answer in question["answers"]] == [
                    "A",
                    "B",
                    "C",
                    "D",
                ]
                expected_media = set()
                if prompt_picture:
                    expected_media.add(f"media/{prompt_picture}.svg")
                for index, letter in enumerate("abcd"):
                    source_text = source_question[f"answer_{letter}"]
                    source_picture = source_question.get(f"picture_{letter}")
                    answer = question["answers"][index]
                    assert answer["text"] == (
                        source_text if source_text.strip() else "[Bild]"
                    )
                    assert answer["blocks"] == expected_blocks(
                        source_text, source_picture
                    )
                    if source_picture:
                        expected_media.add(f"media/{source_picture}.svg")

                actual_media = {item["path"] for item in question["media"]}
                assert actual_media == expected_media
                generated_media.update(actual_media)
                for media_path in actual_media:
                    picture = Path(media_path).stem
                    assert (out / media_path).read_bytes() == source_archive.read(
                        f"svgs/{picture}.svg"
                    )

            assert dict(classes) == EXPECTED_CLASSES
            assert len(generated_media) == EXPECTED_MEDIA

            with zipfile.ZipFile(package) as archive:
                assert archive.namelist()[0] == "manifest.json"
                manifest = json.loads(
                    archive.read("manifest.json").decode("utf-8")
                )
                assert manifest["catalog_version"] == "test"
                assert manifest["source_revision"] == "3. Auflage, März 2024"
                assert {
                    name
                    for name in archive.namelist()
                    if name.startswith("media/")
                } == generated_media

    print(
        "BNetzA-Importtest erfolgreich: Originaltexte, Antworten, SVGs "
        "und reproduzierbares ZIP geprüft"
    )


if __name__ == "__main__":
    main()
