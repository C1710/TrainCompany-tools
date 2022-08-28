# TrainCompany-Tools
Das hier sind einige Kommandozeilen-Tools rund um [TrainCompany](https://github.com/marhei/TrainCompany-Data).

Um diese Tools zu benutzen, muss zunächst das Repository inklusive Submodulen in ein `tools`-Verzeichnis im geklonten `TrainCompany-Data`-Repository geklont werden.
Das kann (im entsprechenden Verzeichnis) mit dem folgenden Kommando durchgeführt werden:
```
git clone --recurse-submodules https://github.com/c1710/TrainCompany-tools tools
```

Desweiteren wird eine funktionierende Python 3.9-Installation benötigt (andere Versionen könnten allerdings auch funktionieren).
Die genutzten Bibliotheken können mit Pip installiert werden:
```
python -m pip install -r requirements.txt
```
**Hinweis:** Es könnte auch sein, dass es `python3` heißt.
Außerdem kann es (z.B. bei Macs mit M1-Prozessor) sein, dass `pyproj` nicht in der aktuellen Version vorkompiliert verfügbar ist.
In dem Fall kann es helfen, in der `requirements.txt`, die Zeile `pyproj~=3.3.0` durch `pyproj==3.3.0` zu ersetzen.
Ist alles installiert, sollten die Tools nutzbar sein.
In den Beispielen nehmen wird an, dass sie aus dem `Traincompany-Data`-Verzeichnis ausgeführt werden.

## Die verfügbaren Tools
Um Informationen zu bekommen, was an Optionen verfügbar ist, kann die `-h`-Option genutzt werden.
Die wichtigsten Tools werden unten noch weiter erläutert.
- `cleanup.py`: Entfernt Annotationen (lange Haltestellennamen) aus `Path.json`.
- `convert_coordinates`: Konvertiert die angegebenen Geo-Koordinaten in das Format von TrainCompany, inklusive Projektion.
- `create_tasks.py`: Erstellt eine neue Ausschreibung.
- `export_station_list.py`: Exportiert alle Haltestellen eines Landes in eine Datei.
- `fix_positions.py`: _Nicht mehr unterstützt_
- `import_stations.py`: Fügt neue Haltestellen zu `Station.json` hinzu.
- `import_trassenfinder.py`: Importiert einen CSV-Export von trassenfinder.de, bzw. vergleichbare Dateien.
- `plot.py`: Rendert die aktuelle Karte in `map_plot.svg`.
- `project_coordinates.py`: Transformiert alle Koordinaten in die ausgewählte Projektion (nur welche, die noch nicht projiziert sind).
- `shift_station_coordinates.py`: _Sollte i.d.R. nicht (mehr) erforderlich sein._
- `update_path_suggestions.py`: _Bitte nicht nutzen - damit werden alle `pathSuggestions` überschrieben._
- `validate_files.py`: Prüft die Daten auf mögliche Probleme.
- `import_brouter.py`: Importiert einen GPX+Wegpunkte-Export aus https://brouter.de/brouter-web.

## Haltestellen-Auflistungen
In die Tools `import_stations.py` und `create_tasks.py` müssen viele Haltestellen-Codes (RIL100, usw.) eingegeben werden.
Um das insbesondere im Ausland zu vereinfachen, gibt es ein paar Komfortfunktionen:
- Anstatt einer Flagge (bspw. `🇫🇷LDO`), kann auch ein mit Doppelpunkt abgetrennter ISO-Code angegeben werden, z.B. `FR:LDO`.
- Es kann auch ein "Standard"-Land für die nachfolgenden Codes festgelegt werden, indem der Doppelpunkt-Code einzeln gegeben wird.
  Bspw. ist `FR: LOI LDO ...` äquivalent zu `FR:LOI FR:LDO`.
- Wird explizit ein Land in einem Code eingegeben, wird das "Standard"-Land dafür ignoriert.
 `XFBRT` würde weiterhin funktionieren, auch wenn z.B. `IT` derzeit das ausgewählte Land ist.
- Nur ein Doppelpunkt setzt das "Standard"-Land zurück auf Deutschland/gar nichts.
- Werden komplette UIC-Codes eingegeben, werden die in das Format Flagge + UIC-Code, aber ohne Länderpräfix umgewandelt.

Ein längeres Beispiel:
```
FR: XFCZ XFAI CSK AEB XFEI XFSAC XFJMA IT: 8300205 XITU
```

Das `import_stations`-Tool unterstützt es auch, zwei Codes für die Ausführung als äquivalent zu kennzeichen.
Bspw. gibt es in der Stationsliste zwei Einträge für den Hbf von Orléans:
```tsv
Orleans	XFOL
Orléans Centre	🇫🇷ORL - 🇫🇷54300 - 8754300
```
Die Daten beider Haltestellen können nun zusammengefasst werden, indem `XFOL=FR:ORL` angegeben wird.

## Die Tools
### `create_tasks.py`
Hiermit kannst du einfach neue Ausschreibungen mit Standard-Aufgabentexten und (vermutlich interessanter) `pathSuggestion`s hinzufügen.
Du kannst mehrere verschiedene Streckenverläufe angeben, indem du die `--stations`-Option mehrfach nutzt.
Das Format der Optionen ist relativ einfach:
Als Erstes kommt die Zuggattung. Dafür stehen ein paar zur Auswahl.
Derzeit lassen sich keine eigenen definieren. Verwende daher ggf. eine ähnliche Zuggattung und ändere den Text manuell.
Dann kann ggf. noch ein Produktname und Artikel hinzugefügt werden (bspw. `--name Traverso --article der`).
Dann können eine oder mehr `--stations`-Listen angegeben werden mit den angefahrenen Haltepunkten.
Beispiel:
```sh
python tools/create_tasks.py TER --stations XFR XFLAM XFSBC FR: MXR LDI LDO XFBRT
```

### `export_station_list.py`
Hiermit lässt sich eine Liste der den Tools bekannten Haltestellen für ein Land exportieren.
Als Argument muss schlicht ein ISO-Code eines Landes angegeben werden (etwa `DE`, `FR`, `CH`, usw.).
Dabei wird eine Datei `stations_FR.tsv` (z.B.) generiert.
Es werden darin die Stationen mit den zugehörigen Codes angegeben.
Dabei kann es vorkommen, dass manche Haltestellen aus verschiedenen Datensätzen nicht richtig als zusammenhängend erkannt wird.
Beispiel:
```
Orleans	XFOL
Orléans Centre	🇫🇷ORL - 🇫🇷54300 - 8754300
```

Daher ist es empfehlenswert, nach Variationen des Namens zu suchen oder Platzhalter zu lassen.
Bspw. VS Code unterstützt es auch, mit regulären Ausdrücken zu suchen (da z.B. mit `.*` als Symbol markiert).
Da kann bspw. `.` eingesetzt werden, was einem beliebigen Zeichen entspricht.
Dadurch können z.B. sowohl Leerzeichen, als auch Bindestriche gefunden werden oder `e` und `é`, usw.

Wenn es mehrere Einträge gibt, können die in `import_stations` temporär als zusammengehörig markiert werden (s.o.).

### `import_stations.py`
Das ist wohl eines der wichtigsten Tools, mit dem neue Stationen importiert werden können.
Grundsätzlich wird es genutzt mit der `--stations`-Option und einer Leerzeichen-getrennte Liste von Stations-Codes.

Zusätzlich gibt es aber noch zwei weitere Optionen:
- `--trassenfinder` erstellt eine CSV-Datei, die sich später wie ein Trassenfinder-Export importieren lässt.
  Da müssen dann nur noch die Entfernungen vom Startpunkt angegeben werden.
- `--gpx` erstellt eine GPX-Datei, die bspw. auf brouter.de als Route importiert werden kann. Damit lassen sich dann die Halte/Entfernungen leichter finden.

#### Importierte Daten
- Haltestellenname
- Code/RIL100
- (Falls verfügbar) Koordinaten
- (Falls verfügbar) Bahnsteigdaten
- Die Gruppe - wird aus den verfügbaren Informationen abgeleitet.

Insbesondere Bahnsteigdaten und Gruppe können auch fehlerhaft sein und sollten auf Plausiblität überprüft werden.

### `import_trassenfinder.py`
Hiermit können CSV-Exporte aus trassenfinder.de importiert werden (oder ähnliche Dateien). Es wird alle Haltepunkte, die
mit `"Kundenhalt"` markiert sind, bzw. im Trassenfinder mit einer Haltezeit >0 angegeben sind. Um die Strecken leichter
zu identifizieren, gibt es die `--annotate`-Option. Dadurch werden in den Eintrag in `Path.json` auch die vollen
Haltestellennamen hinzugefügt. Die sollten aber später wieder über `cleanup.py` gelöscht werden, weil sie die Daten noch
größer/unübersichtlicher machen würden. Ansonsten werden die Tests fehlschlagen.

#### Importierte Daten

- Angefahrene Haltestellen-Codes
- Segment/Streckenlänge
- Länderzulassungen
- (Falls Streckennummer angegeben und Daten vorhanden) Elektrifizierung, Streckengruppe (Haupt-/Nebenbahn, SFS)
- `twistingFactor` der Strecke

Insbesondere Höchstgeschwindigkeit wird _nicht_ importiert.

### `import_brouter.py`

Hiermit lässt sich ein GPX-Export (mit Wegpunkten aktiviert) aus brouter.de (oder vergleichbar) importieren. Dafür
müssen alle angefahrenen Haltestellen als Wegpunkte markiert sein (also durch Klicken). Das Tool gleicht dann die
Wegpunkte mit bekannten Haltestellen ab und erstellt ggf. neue (erkennbar an den Flagge + O + Zahlen-Codes).

### Importierte Daten

- Haltestellen
	- Code
	- Name
	- Standort
	- Art (kann falsch liegen, bitte kontrollieren)
	- Falls in den Daten vorhanden, Bahnsteiginformationen
- Strecken
	- Wegpunkte
	- Falls `--annotate` angegeben ist, auch die langen Namen der Wegpunkte
	  (müssen später mit `cleanup.py` wieder entfernt werden)
	- Segmentlängen
	- `twistingFactor`
	- Länderzulassungen (müssen ggf. manuell bei `TrainEquipment.json` hinzugefügt werden)
	  Bei Grenzen kann/muss ggf. eine der beiden Zulassungen entfernt werden

Es werden _keine_ Höxhstgeschwindigkeiten und Informationen zu Streckenart und Elektrifizierung hinzugefügt. Hierzu
bitte bspw. bei OpenRailwayMap nachsehen.

### `plot.py`

Ein einfaches Tool ohne Optionen (auch ohne `-h`), das die aktuelle Haltestellen/Strecken-Karte erstellt - `map_plot.py`
. Die kann in Inkscape oder vielleicht auch einem Webbrowser geöffnet werden und dient als Hilfe um z.B. fehlerhafte
Koordinaten zu finden oder Haltestellen zu entklumpen.

### `validate_files.py`

Prüft die Datensätze auf Probleme, wie zu lange Streckenabschnitte, Haltestellen ohne Anschluss ans Netz usw. Manche
Probleme bringen mehr oder weniger "Punkte". Ist eine bestimmte Schwelle (derzeit standardmäßig 700) überschritten,
schlägt es fehl. Meist liegt das an einzelnen großen Problemen, etwa noch vorhandenen langen Namen. Steigt dieser
Punktestand nur leicht gegenüber der existierenden Version an, wird das wahrscheinlich okay sein, auch wenn der
Punktestand dann so gerade über den Schwellwert kommt.

## Wie eine neue (internationale) Strecke hinzugefügt werden kann

Hier gehen wir ein Beispiel durch, wie eine neue Strecke außerhalb Deutschlands ins Spiel importiert werden kann.

[Noch nicht fertig]

### 1. Strecke zusammenstellen

Auf https://brouter.de/brouter-web/ (oder auch https://brouter.m11n.de) wird die Strecke erstellt. Dazu sollte oben
links "Eisenbahn" ausgewählt werden. Dann können die Stationen (erkennbar an den blauen Quadraten bei den Strecken)
nacheinander ausgewählt werden. Es ist (derzeit) wichtig, dass alle zu berücksichtigenden Zwischenstops ausgewählt
werden. Es ist auch möglich (wenn die Abstände zwischen den Stationen zu groß sind), Punkte auf der Strecke auszuwählen,
die nah an einem Ort sind.

### 2. Strecke exportieren

Ist das alles fertig, kann die Strecke exportiert werden. Wichtig ist, beim Export als Format `GPX` zu wählen und die
Wegpunkte mit zu exportieren.

### 3. Import

Der Import erfolgt nun über das `import_brouter`-Tool. Das benötigt die Datei als Eingabe-Parameter. Sollen zusätzlich
Orte als "Stationen" genutzt werden, wird der `--towns`-Parameter benötigt. Bei längeren Strecken empfiehlt es sich,
den `--tolerance`-Parameter zu erhöhen, etwa auf `0.08` oder `0.1`. Das sorgt dafür, dass die Strecke, für die via
Overpass nach relevanten Segmenten gesucht wird, etwas stärker vereinfacht wird. Genauer beschreibt `--tolerance` die
maximale Abweichung von der Strecke in km.

Der Import wird nun eine Weile dauern, auch bei einer schnellen Internetverbindung oder einer kurzen Strecke können das
einige Sekunden sein (weil es immer ein bisschen wartet, um eine Überlastung der Server zu verhindern). Es kann dabei
vorkommen, dass einzelne Halte nicht gefunden/ignoriert werden. Das ist meistens nicht schlimm, kann aber zu längeren
Streckensegmenten führen. U.u. fehlt auch schlicht der `--towns`-Parameter.

### 4. Korrekturen

Wenn nun alles erfolgreich importiert ist, kann es trotzdem noch Fehler o.Ä. geben:

- Es kann sein, dass manche Stationen nicht richtig erkannt worden sind und daher `O1234567`-Codes haben, obwohl es
  bessere gibt. Das sollte in `Station` und `Path` angepasst werden.
- Durch den gleichen Fehler kann es sein, dass manche Haltestellen doppelt (mit anderen Codes) vorhanden sind.
- Die `group` der Haltestellen stimmt oftmals nicht. Die sollten daher komplett überprüft werden (etwa, indem brouter.de
  noch daneben geöffnet ist)
- Ist keine Höchstgeschwindigkeit für einen Streckenabschnitt bekannt, wird `-1` eingesetzt. Darüber hinaus kann es
  vorkommen, dass die Höchstgeschwindigket falsch ist. Sie sollte daher kurz auf Plausibilität überprüft werden.
- Der `twistingFactor` kann bei größeren Kurven schon mal sehr hoch werden. Werte >0.4 sollten verringert werden.

# Lizenzen der Datensätze

Vgl. `data/README.md`