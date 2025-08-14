# Erstellen einer neuen Aufgabe
_Wie in allen Anleitungen gehe ich hier davon aus, dass die Tools bereits korrekt installiert sind (siehe [Basis.md](./Basis.md)). Für die Ausführung eines Tools verwende ich grundsätzlich die Syntax `python tools/<tool>.py`. Solltest du in einem GitHub Codespace arbeiten, verkürzt sich das zu `<tool>.py`._

In dieser Anleitung geht es darum, eine neue Aufgabe zum Spiel mithilfe des Tools `create_tasks.py` hinzuzufügen.

## Die Zuggattung
Jede Aufgabe braucht zunächst eine Zuggattung. Diese bestimmt, was für Züge im Spiel am besten abschneiden, was für Güter/Fahrgäste befördert werden und, wie die Standardbeschreibungen aussehen. Die folgende Tabelle gibt einen Überblick über die mit `create_tasks.py` verfügbaren Gattungen:
| Gattung                                                       	| `ID`                                      	| Ausschreibung/Direktvergabe 	| Beladungen                     	| Gruppe                  	| Nutzt SFS 	|
|---------------------------------------------------------------	|-------------------------------------------	|-----------------------------	|--------------------------------	|-------------------------	|-----------	|
| S-Bahn, Regionalbahn                                          	| `S`, `RB`                                 	| Ausschreibung               	| Fahrgäste                      	| 3 - S-Bahn              	| Ja        	|
| Regionalexpress, TER, Interregio-Express                      	| `RE`, `TER`, `IRE`                        	| Ausschreibung               	| Fahrgäste                      	| 2 - Regional            	| Ja        	|
| Intercity, Interregio, Ouigo Train Classique, Ouigo, Eurocity 	| `IC`, `IR`, `OTC`, `OGV`, `EC`            	| Ausschreibung               	| Fahrgäste                      	| 1 - Intercity           	| Ja        	|
| ICE, ICE-Sprinter, TGV, Frecciarossa, Eurocity-Express        	| `ICE`, `ICE-Sprinter`, `TGV`, `FR`, `ECE` 	| Ausschreibung               	| Fahrgäste                      	| 0 - Hochgeschwindigkeit 	| Ja        	|
| Nightjet                                                      	| `NJ`                                      	| Ausschreibung               	| Fahrgäste, Betten              	| 1 - Intercity           	| Ja        	|
| Amtrak                                                        	| `AT`                                      	| Ausschreibung               	| Fahrgäste, Betten, Speisewagen 	| 1 - Intercity           	| Ja        	|

Aktuell werden von dem Tool noch keine Direktvergaben generiert.  
Die Zuggattung ist das erste Argument, das `create_task.py` mitgegeben wird:
```bash
python tools/create_tasks.py RE
```

## Die Haltepunkte
Eine Fahrt, die nirgends hält, ergibt wenig Sinn (außer für Streckensammler vielleicht. Aber auch die müssen irgendwo zusteigen). Hierfür verwendest du das Argument `--stations`, gefolgt von den IDs der Haltestellen (`"ril100"` in der `Station.json`). Ein einfaches Beispiel:
```bash
python tools/create_tasks.py RE --stations EHM ESOT ELPP EPD HA HWBD HWAR FKW
```
Das funktioniert soweit einfach für Haltestellen in Deutschland, bzw. solche, die einen echten RIL100-Code haben. Es gibt aber auch viele Haltestellen im Ausland, auf die das nicht zutrifft. Nehmen wir bspw. ein Teilstück der Ligne de la Côte Bleue von Miramas nach L'Estaque:
| Haltestelle  	| `ril100` 	|
|--------------	|----------	|
| Miramas      	| `XFMI`   	|
| Istres       	| `🇫🇷ISR`   |
| Port-de-Bouc 	| `🇫🇷PDB`   |
| Martigues    	| `XFMAG`  	|

Emoji-Flaggen einzugeben ist oft nicht gerade einfach. Alternativ kannst du statt der Flagge auch den entsprechenden [Ländercode](https://de.wikipedia.org/wiki/ISO-3166-1-Kodierliste) mit einem Doppelpunkt verwenden. Das Script übersetzt es automatisch:
| Haltestelle  	| `ril100` 	|
|--------------	|----------	|
| Miramas      	| `XFMI`   	|
| Istres       	| `FR:ISR`  |
| Port-de-Bouc 	| `FR:PDB`  |
| Martigues    	| `XFMAG`  	|

Wenn du nun viele Haltestellen in einem Land angibst, gibt es noch ein Hilfsmittel, das zu verkürzen. Wenn du an einer Position _nur_ den Ländercode angibst, wird dieser für die folgenden Haltestellen als Standard übernommen. Ein Doppelpunkt alleine setzt das für die folgenden Haltepunkte wieder zurück auf nichts (bzw. Deutschland).  
Die folgenden Kommandos/Argumente sind identisch:
```bash
python tools/create_tasks.py RE --stations FR: XFMI ISR PDB XFMAG  
python tools/create_tasks.py RE --stations XFMI FR:ISR FR:PDB XFMAG  
python tools/create_tasks.py RE --stations XFMI 🇫🇷ISR 🇫🇷PDB XFMAG
```
Ein etwas komplexeres Beispiel für einen Zug durch den Eurotunnel von Glasgow nach Düsseldorf:
```bash
python tools/create_tasks.py EC --stations GB: GLC EDB YRK XKAI XFFE FR:STO XBB : KM KD
```
Wie in dem Beispiel zu sehen ist, haben richtige RIL100-Codes und Länder-Präfixe für einen einzelnen Haltepunkt grundsätzlich Vorrang.

Du kannst das Argument `--stations` auch mehrmals verwenden, um mehrere Varianten einer Linie gleichzeitig zu erstellen.

## Weitere Einstellungen für die automatischen Beschreibungen
Im Großen und Ganzen reicht es bereits aus, die Zuggattung und die Haltestellen anzugeben. Dadurch wird der Eintrag für die Aufgabe generiert mit einem passenden Standardtext. Diese Standardtexte lassen sich bereits bei der Generierung etwas anpassen:
| Eigenschaft  	| Argument    	| Beschreibung                               	| Beispiel            	|
|--------------	|-------------	|--------------------------------------------	|---------------------	|
| Liniennummer 	| `--number`  	| Eine festgelegte Liniennummer              	| `--number 11`       	|
| Linienname   	| `--name`    	| Eine Bezeichnung für eine Linie            	| `Rhein-Hellweg-Express` 	|
| Artikel      	| `--article` 	| Ein bestimmter Artikel für den Liniennamen 	| `--article der`     	|

Ansonsten kannst du aber auch leicht in der `TaskModel.json` direkt die Beschreibungen anpassen.

## Die `pathSuggestion`
Wenn du dir die Ausgabe des Skripts ansiehst, taucht in der `TaskModel.json` ein Feld namens `pathSuggestion` auf, das einige zusätzliche Haltestellen beinhaltet. Diese Auflistung hilft dem Spiel, dir von Anfang an eine gute Strecke anzugeben und enthält alle Wegpunkte, bei denen eine Verzweigung besteht. Derzeit ist die Berechnung dieser `pathSuggestion` der aufwendigste Teil des Skripts (ich plane derzeit, hierfür ein optionales, deutlich schnelleres Modul einzuführen).


## Weitere Einstellungen für die `pathSuggestion` (optional)
Du kannst dem Skript auch noch ein paar weitere Optionen mitgeben, die in manchen Fällen Sinn ergeben:
| Eigenschaft                     	| Argument              	| Beschreibung                                                                                                                                                                 	| Beispiel               	|
|---------------------------------	|-----------------------	|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------	|------------------------	|
| Schnellfahrstrecken vermeiden   	| `--avoid-sfs`         	| Die `pathSuggestion` versucht, Schnellfahrstrecken zu vermeiden. Ist eine SFS unvermeidbar, wird diese dennoch genommen.                                                              	| /                      	|
| Nur elektrifizierte Strecken    	| `--electrified`       	| Die `pathSuggestion` leitet nur über elektrifizierte Strecken. Wirft einen Fehler, wenn keine elektrifizierte Strecke existiert.                                             	| /                      	|
| Ausstattungen vermeiden         	| `--avoid-equipment`   	| Die `pathSuggestion` erlaubt keine Strecken, die die angegebene(n) Ausstattung(en) (siehe `TrainEquipment.json`) benötigen.                                                  	| `avoid-equipments KRM` 	|
| Keine `pathSuggestion` ausgeben 	| `--no_add_suggestion` 	| Die `pathSuggestion` wird zwar generiert, aber verworfen, bevor die Datei geschrieben wird (nicht empfohlen).                                                                	| /                      	|
| Vollen Pfad ausgeben            	| `--full-path`         	| Die `pathSuggestion` enthält normal nur die Haltestellen selbst sowie Punkte im Netz, an denen sich Strecken verzweigen. Hiermit werden _alle_ passierten Punkte ausgegeben. 	| /                      	|


## Vollständiges Beispiel
Nehmen wir an, wir wollen eine fiktiven Regionalbahn (`RB`) erstellen, der London Soest verbindet. Der Einfachheit halber nehmen wir hier weniger Halte als es für einen Regionalzug normal wäre:

|Haltepunkt|`ril100`|
|----------|--------|
|London|`XKLP`|
|Ebbsfleet International|`XKEI`|
|Ashford International|`XKAI`|
|Calais-Fréthun|`XFFE`|
|Armentières|`🇫🇷ARM`|
|Lille|`XFLIE`|
|Gent-Sint-Pieters|`XBGP`|
|Aalst|`XBAAS`|
|Bruxelles Midi|`XBB`|
|Liège|`XBLIG`|
|Aachen Hbf|`KA`|
|Mönchengladbach Hbf|`KM`|
|Düsseldorf Hbf|`KD`|
|Essen Hbf|`EE`|
|Dortmund Hbf|`EDO`|
|Hammhauptbahnhof|`EHM`|
|Welver|`EWVE`|
|Soest|`ESOT`|

Das können wir mit dem Argument `--stations` zusammenfassen:  
`--stations XKLP XKEI XKAI FR:ARM XFLIE XBGP XBAAS XBB XBLIG KA KM KD EE EDO EHM EWVE ESOT`

Regionalzüge fahren im Regelfall nicht unbedingt über Schnellfahrstrecken, deshalb verwenden wir zusätzlich das Argument `--avoid-sfs`.  
Wir geben der Linie noch einen schmissigen Namen: _Die Thames-Börde-Bahn_ (RB 83). Diesen übergeben wir mit den Argumenten `--article die --name "Thames-Börde-Bahn" --number 83`.

Mit allen Kommandozeilenargumenten sieht das Kommando nun so aus:
```bash
python tools/create_tasks.py RB --article die --name "Thames-Börde-Bahn" --number 83 --avoid-sfs --stations XKLP XKEI XKAI FR:ARM XFLIE XBGP XBAAS XBB XBLIG KA KM KD EE EDO EHM EWVE ESOT
```

Nach einer gewissen Wartezeit enthält die Datei `TaskModel.json` nun an einer zufälligen Stelle (um Git Merge-Konflikte zu vermeiden) nun den folgenden Eintrag:
```json
{
    "name": "Thames-Börde-Bahn von %s nach %s",
    "descriptions": [
        "Bringe die Regionalbahn der Linie 83 von %s nach %s.",
        "Bring die Fahrgäste in der RB 83 pünktlich nach %2$s.",
        "Fahre die RB störungsfrei nach %2$s.",
        "Bring die Thames-Börde-Bahn von %s nach %s.",
        "Bringe die Regionalbahn pünktlich über die SFS von %s nach %s"
    ],
    "stations": [ "XKLP", "XKEI", "XKAI", "🇫🇷ARM", "XFLIE", "XBGP", "XBAAS", "XBB", "XBLIG", "KA", "KM", "KD", "EE", "EDO", "EHM", "EWVE", "ESOT" ],
    "neededCapacity": [
        { "name": "passengers" }
    ],
    "group": 1,
    "service": 3,
    "pathSuggestion": [ "XKLP", "XKEI", "XKAI", "XFFE", "XFHZ", "🇫🇷ARM", "XFLIE", "XBGP", "XBAAS", "XBB", "XBLIG", "XBHE", "KA", "KM", "KN", "KD", "EDG", "EE", "EDO", "EHM", "EWVE", "ESOT" ]
}
```

Diesen Eintrag kannst du nun nach Belieben anpassen und bspw. Sätze ergänzen (siehe dazu die README-Datei von `TrainCompany-Data`).  
Das einzige, was jetzt noch fehlt, ist, dass jemand einen Flirt 2 umrüstet, dass der auch durch Belgien, Frankreich, den Eurotunnel und über die High Speed One im UK fahren kann. 