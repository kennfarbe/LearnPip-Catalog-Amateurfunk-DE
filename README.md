# LearnPip-Catalog-Amateurfunk-DE

Dieses Repository pflegt den deutschen Amateurfunk-Fragenkatalog als eigenständiges LearnPip-Katalogprodukt.

## Status

Die Repository- und Release-Infrastruktur ist vorbereitet. Offizielle Fragen der Bundesnetzagentur werden erst nach reproduzierbarem Import, Quellenprüfung und vollständigem Lizenznachweis veröffentlicht. Bis dahin gibt es bewusst kein Inhaltsrelease.

## Schnittstelle zu LearnPip

Katalog-Releases verwenden ausschließlich den öffentlichen LearnPip-Austauschvertrag `org.learnpip.catalog.zip` in einer von LearnPip unterstützten Schema-Version. Das Katalogprodukt besitzt eine eigene `catalog_version` und `source_revision`; beide sind unabhängig von der LearnPip-Anwendungsversion.

LearnPip selbst ist weder Build- noch Runtime-Abhängigkeit dieses Repositories. Ein veröffentlichtes ZIP kann lokal/offline importiert werden.

## Repository-Inhalte

- `catalog/`: Quelldaten und erzeugte Paketbestandteile, sobald fachlich freigegeben
- `scripts/`: katalogspezifische Import-/Validierungswerkzeuge
- `LICENSES.md`: Lizenzmatrix
- `NOTICE`: Hinweise zu Herkunft und Marken-/Behördenbezug
- `ATTRIBUTION`: Namensnennungen und Quellen
- `.github/workflows/validate.yml`: unabhängige CI und Release-Prüfung

## Veröffentlichung

Ein Release darf erst erstellt werden, wenn das Paket vollständig gegen den LearnPip-Vertrag validiert wurde. Release-Artefakte sind unveränderliche ZIP-Dateien; Änderungen erzeugen eine neue Katalogversion. Ein neues Katalogrelease erfordert kein LearnPip-Release.

Die technische Validierung beweist weder Rechte noch eine amtliche Zertifizierung. Fremdinhalte werden nicht durch die Softwarelizenz dieses Repositories umlizenziert.
