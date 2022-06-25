# How to use
First, this repository needs to be the `tools` directory in `TrainCompany-Data`.
You can use the scripts from both this directory as well as the `TrainCompany-Data` directory, to which the script will change automatically.
In order to use the scripts, you will need to install the `requirements.txt`. Note that right now, a `matplotlib` installation would also be sufficient.

## Converting routes to station and route/path data
For this, you take the CSV with all stations covered by the route being marked as "Kundenhalt" (stop time >= 1, or 2 minutes) and open it with `python tools/convert_trasse.py trasse.csv`.
If no errors occur, it saves the following data:
- `Station.json`
  - _All attributes if available_
  - Note: If the location is not known, it will be inserted as `424242` and the script will tell you how to convert the coordinates (can be found e.g. through Google Maps).
  - If a station is already present (or one without a suffix, like `UE` instead of `UE P`), it will not be changed
- `Path.json`
  - `start`, `end`, `length`, `group`
  - The `maxSpeed`, `name` (optional) and `twistingFactor` need to be added manually

## Exporting the map to SVG
Here, you simply need to call `python plot.py`. It will then save the map to `map_plot.svg`, which you can open in Inkscape.

## Shifting all coordinates
You can also shift all coordinates to have another coordinate origin.
For this, you call `python shift_station_coordinates.py <x-offset> <y-offset>` with the offsets you want to add.

# License `bahnhoefe.csv`, `haltestellen.csv`, `strecken.MID`, and `bahnsteige.csv`:
> © 2016 Deutsche Bahn AG. Dieser Datensatz wird bereitgestellt unter der Lizenz Creative Commons Attribution 4.0 International (CC BY 4.0). 
Source:
- https://data.deutschebahn.com/dataset/data-stationsdaten.html
- https://data.deutschebahn.com/dataset/data-haltestellen.html
- https://data.deutschebahn.com/dataset/geo-strecke.html
- https://data.deutschebahn.com/dataset/data-bahnsteig.html