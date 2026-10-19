#!/usr/bin/env python3
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

if len(sys.argv) != 2:
    raise SystemExit("usage: test-import.py SOURCE.zip")

source = Path(sys.argv[1]).resolve()
with tempfile.TemporaryDirectory() as tmp:
    out = Path(tmp) / "catalog"
    subprocess.run([sys.executable, "scripts/import-bnetza.py", str(source), str(out), "--catalog-version", "test"], check=True)
    doc = json.loads((out / "questions.json").read_text(encoding="utf-8"))
    questions = doc["questions"]
    assert len(questions) == 1750
    classes = {"N": 0, "E": 0, "A": 0}
    media = set()
    for q in questions:
        assert q["correct_answer_ids"] == ["A"]
        assert q["id"].startswith("bnetza:")
        for topic in q["topics"]:
            if topic.startswith("Klasse "):
                classes[topic.removeprefix("Klasse ")] += 1
        for item in q["media"]:
            media.add(item["path"])
            assert (out / item["path"]).is_file()
    assert classes == {"N": 571, "E": 463, "A": 716}, classes
    assert len(media) == 687
    package = out.parent / "de.bnetza.amateurfunk.pruefungsfragen-test.zip"
    assert package.is_file()
    with zipfile.ZipFile(package) as archive:
        assert archive.namelist()[0] == "manifest.json"
print("BNetzA-Importtest erfolgreich")
