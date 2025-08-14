# Grundlagen für die Nutzung der Tools
In dieser Anleitung geht es darum, die Tools zum Laufen zu bekommen.  
Je nachdem, was du bereits nutzt und wie gut du dich auskennst, kann die eine oder andere Methode für dich besser geeignet sein:

## Methode 1: Lokale Arbeit mit Git und VS Code
Bei dieser Methode laufen die Tools lokal auf deinem Rechner.

### Hinweise
- Wenn du dich mit der Kommandozeile eher unwohl fühlst oder deinen Rechner nicht mit fremder Software zumüllen möchtest, bietet sich Methode 2 eventuell besser an.
- Welcher Editor genutzt wird - sei es (wie hier beschrieben) Visual Studio Code, PyCharm, vim, emacs, Notepad mit oder ohne ++, ..., sollte im Großen und Ganzen keine Rolle spielen.
- Als Binary für Python nehme ich hier grundsätzlich `python` an und nicht `python3`. Don't @ me.
- Es empfiehlt sich an sich, alles in einer venv einzurichten, da weiß ich aber aus dem Kopf nicht, wie das geht.
- Der Konsistenz halber wird vieles in der Kommandozeile angegeben, was theoretisch auch über die GUI vieler Editoren geht.
- Grundsätzlich gehe ich hier davon aus, dass im Ordner `TrainCompany-Data` gearbeitet wird und die Tools sich im Unterordner `tools` befinden.

### Software-Voraussetzungen

Zunächst brauchst du die folgenden Anwendungen korrekt installiert - wie das für dein Betriebssystem geht, kann dir die Suchmaschine deines Vertrauens sagen:
- Git
- Visual Studio Code (oder ein anderer Editor) - Erweiterungen werden nicht zwingend benötigt.
- Python 3 (die aktuellen Tools laufen mit 3.13, ältere oder insbesondere neuere Versionen dürften auch funktionieren)

### Klonen der Repositories

_TL;DR für alle, die sich bereits mit Git usw. auskennen: Für TrainCompany-Tools werden auch **Submodules** benötigt._

Als nächstes musst du zwei Repositories mit Git klonen: Deinen **Fork** von `TrainCompany-Data` und `TrainCompany-Tools` (sofern du diese nicht modifizieren möchtest, brauchst du heirfür keinen Fork). Wo du diese platzierst, ist an sich nicht entscheidend, viele der Scripts gehen jedoch davon aus, dass die Tools sich in einem Unterordner `tools` innerhalb von `TrainCompany-Data` befinden.  
Um die beiden Repositories zu klonen, sollten die folgenden Befehle ausreichen:
```bash
git clone "https://github.com/<dein-benutzer>/TrainCompany-Data"
cd TrainCompany-Data
git clone --recurse-submodules --shallow-submodules "https://github.com/c1710/TrainCompany-Tools" tools
```

### Einrichten der Python-Bibliotheken
Die Tools benötigen teilweise zusätzliche Bibliotheken, die sich in der aktuellen Version auch über Pip installieren lassen sollten.  
Die Installation läuft über folgendes Kommando:
```
python -m pip install -r tools/requirements.txt
```
Es _kann_ sein, dass das für `pyproj` nicht funktioniert. In diesem Fall könnte https://pyproj4.github.io/pyproj/stable/installation.html weiterhelfen.  
Sollte alles funktioniert haben, sind die Tools ab jetzt vollständig einsatzbereit.

### Ausführen der Tools
Die Tools lassen sich jetzt mit folgendem Kommando starten:
```
python tools/<tool>.py
```


## Methode 2: Nutzung von GitHub Codespaces
Bei dieser Methode erfolgt die Arbeit vollständig im Browser auf Servern von GitHub/Microsoft.
### Hinweise
- Ich selbst habe damit bisher kaum gearbeitet, kann also nicht besonders viel sagen.
- Sollte der Fork noch älter sein und noch nicht den Ordner `.devcontainer` enthalten, wird es nicht funktionieren.
- Es gibt auch die Möglichkeit, mit Gitpod zu arbeiten, aber das wird wohl derzeit in der klassischen Version eingestellt. Zudem benötigt es eine zusätzliche Anmeldung. Als ich diese Methoden eingerichtet habe, waren GitHub Codespaces noch nicht für reguläre Nutzer freigeschaltet.
- Da mir ein paar Sachen noch nicht gefallen, kann es gut sein, dass in Kürze noch ein paar Änderungen stattfinden.

### Starten/Erstellen des Codespaces
Wenn du im Browser deinen Fork von `TrainCompany-Data` offen hast, kannst du oben auf die grüne Schaltfläche "Code" klicken. Dort gehst du auf den Reiter "Codespaces" und klickst auf das + (sofern du noch keinen erstellt hast - in dem Fall ist dein bestehender Codespace aufgelistet).  
Nach einer gewissen Wartezeit sollte in deinem Browser ein Visual Studio Code-Fenster mit deinem Repository auftauchen.

### Ausführen der Tools
Unten sollte ein Abschnitt sein, in dem sich  u.a. der Reiter "Terminal" befindet. Falls nicht, kann dieser geöffnet werden, indem du F1 drückst und dann "Terminal" eingibst.
Die Tools lassen sich hier ohne `python` und Angabe eines Ordners ausführen:
```
<tool>.py
```

### Aktualisieren des Containers
Die gesamte Umgebung ist in einem "Dev Container" ausgeführt, der durch die Konfiguration in `.devcontainer/devcontainer.json` und das darin verwendete Docker-Image definiert ist. Um die neuste Version der Umgebung zu erhalten, kannst du den Container aktualisieren.  
Das funktioniert, indem du mit F1 die Kommandoleiste (oder wie das heißt) öffnest und da "Rebuild Container" eingibst.


## Methode 3: Dev-Container in VS Code
Diese Methode ist ein Zwischending aus der lokalen Installation und der Nutzung von Codespaces: Anstatt, dass die Tools direkt auf deinem Rechner laufen, wird der Dev-Container, der auch in GitHub Codespaces verwendet wird, lokal gestartet.

### Voraussetzungen
Diese Methode habe ich selbst noch nicht getestet, im Prinzip sollten aber zwei Anwendungen ausreichen:
- Visual Studio Code
- Docker

### Einrichtung
Im GitHub-Repository zu `TrainCompany-Data` gibt es eine Schaltfläche "Remote - Containers | Open". Mit einem Klick darauf (und Bestätigung) öffnet sich die Umgebung in Visual Studio Code.  
**Achtung!** Damit wird _immer_ das Haupt-Repository geklont, deinen Fork musst du innerhalb von VS Code selbst auswählen.

### Ausführen der Tools
Genau wie in GitHub Codespaces reicht es, im eingebauten Terminal das Tool direkt auszuführen:
```
<tool>.py
```
