# LearnPip-Catalog-Amateurfunk-DE

Dieses Repository pflegt den deutschen Amateurfunk-Fragenkatalog als eigenständiges LearnPip-Katalogprodukt.

## Status

Der offizielle Fragenkatalog der Bundesnetzagentur, 3. Auflage März 2024, ist als reproduzierbare Importquelle verifiziert. Der Importer übernimmt 1.750 Fragen für die Klassen N, E und A sowie 687 referenzierte SVG-Abbildungen in den LearnPip-Austauschvertrag 1.0.0. Ein Inhaltsrelease wird erst nach erfolgreicher Paket- und Inhaltsvalidierung veröffentlicht.

## Schnittstelle zu LearnPip

Katalog-Releases verwenden ausschließlich den öffentlichen LearnPip-Austauschvertrag `org.learnpip.catalog.zip` in einer von LearnPip unterstützten Schema-Version. Das Katalogprodukt besitzt eine eigene `catalog_version` und `source_revision`; beide sind unabhängig von der LearnPip-Anwendungsversion.

LearnPip selbst ist weder Build- noch Runtime-Abhängigkeit dieses Repositories. Ein veröffentlichtes ZIP kann lokal/offline importiert werden.

## Repository-Inhalte

- `catalog/`: geprüftes, aus der freigegebenen Quelle erzeugtes Releasepaket
- `scripts/import-bnetza.py`: reproduzierbarer Import der freigegebenen BNetzA-Quelldatei\n- `scripts/validate-release.py`: Integritätsprüfung des LearnPip-Pakets\n- `scripts/validate-bnetza-content.py`: Vollständigkeitsprüfung für Fragen, Klassen, Lösungen und Medien
- `LICENSES.md`: Lizenzmatrix
- `NOTICE`: Hinweise zu Herkunft und Marken-/Behördenbezug
- `ATTRIBUTION`: Namensnennungen und Quellen
- `.github/workflows/validate.yml`: unabhängige CI und Release-Prüfung

## Veröffentlichung

Ein Release darf erst erstellt werden, wenn das Paket vollständig gegen den LearnPip-Vertrag validiert wurde. Release-Artefakte sind unveränderliche ZIP-Dateien; Änderungen erzeugen eine neue Katalogversion. Ein neues Katalogrelease erfordert kein LearnPip-Release.

Die technische Validierung beweist weder Rechte noch eine amtliche Zertifizierung. Fremdinhalte werden nicht durch die Softwarelizenz dieses Repositories umlizenziert.
