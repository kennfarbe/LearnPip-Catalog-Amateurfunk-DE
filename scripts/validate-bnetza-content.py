#!/usr/bin/env python3
"""Inhaltliche Abnahme eines erzeugten BNetzA-LearnPip-Katalogs."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys
import zipfile

EXPECTED_QUESTIONS = 1750
EXPECTED_CLASSES = {"N": 571, "E": 463, "A": 716}
EXPECTED_MEDIA = 687


def fail(message: str) -> None:
    raise SystemExit("Katalogprüfung fehlgeschlagen: " + message)


def main() -> None:
    if len(sys.argv) != 2:
        fail("genau ein ZIP-Pfad ist erforderlich")

    with zipfile.ZipFile(Path(sys.argv[1])) as archive:
        names = set(archive.namelist())
        document = json.loads(archive.read("questions.json").decode("utf-8"))
        questions = document.get("questions")
        if not isinstance(questions, list) or len(questions) != EXPECTED_QUESTIONS:
            fail(f"erwartet {EXPECTED_QUESTIONS} Fragen")

        ids = [question.get("id") for question in questions]
        if len(set(ids)) != len(ids):
            fail("Fragen-IDs sind nicht eindeutig")

        classes = Counter()
        referenced_media = set()
        for question in questions:
            class_topics = [
                topic.removeprefix("Klasse ")
                for topic in question.get("topics", [])
                if isinstance(topic, str) and topic.startswith("Klasse ")
            ]
            if len(class_topics) != 1 or class_topics[0] not in EXPECTED_CLASSES:
                fail("ungültige Klassenzuordnung bei " + str(question.get("id")))
            classes[class_topics[0]] += 1

            answers = question.get("answers", [])
            answer_ids = {answer.get("id") for answer in answers if isinstance(answer, dict)}
            if answer_ids != {"A", "B", "C", "D"}:
                fail("Antwortsatz unvollständig bei " + str(question.get("id")))
            if question.get("correct_answer_ids") != ["A"]:
                fail("unerwartete Lösung bei " + str(question.get("id")))

            for media in question.get("media", []):
                path = media.get("path")
                if path not in names:
                    fail("fehlendes Medium " + str(path))
                referenced_media.add(path)

            block_media = set()
            for block in question.get("prompt_blocks", []):
                if block.get("kind") == "image":
                    block_media.add(block.get("path"))
            for answer in answers:
                for block in answer.get("blocks", []):
                    if block.get("kind") == "image":
                        block_media.add(block.get("path"))
            if not block_media.issubset(referenced_media):
                fail("Bildblock ohne Mediennachweis bei " + str(question.get("id")))

        if dict(classes) != EXPECTED_CLASSES:
            fail("Klassenverteilung stimmt nicht: " + repr(dict(classes)))
        if len(referenced_media) != EXPECTED_MEDIA:
            fail(f"erwartet {EXPECTED_MEDIA} referenzierte Medien")

        archive_media = {name for name in names if name.startswith("media/")}
        if archive_media != referenced_media:
            fail("Archiv enthält fehlende oder nicht referenzierte Medien")

    print(f"{EXPECTED_QUESTIONS} Fragen vollständig geprüft")
    print("Klassen: N=571, E=463, A=716")
    print(f"Referenzierte Medien: {EXPECTED_MEDIA}")


if __name__ == "__main__":
    main()
