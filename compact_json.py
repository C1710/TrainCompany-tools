import json
from typing import Generator, BinaryIO
from collections.abc import Callable
from os import PathLike
from pathlib import Path
import argparse

def clean_json(data: list[dict[str, object]] | Generator[dict[str, object], None, None], fields_to_remove: list[str], fields_to_clear: list[str] | None = None) -> Generator[dict[str, object], None, None]:
    for entry in data:
        for field_to_remove in fields_to_remove:
            if field_to_remove in entry:
                del entry[field_to_remove]
        if fields_to_clear:
            for field_to_clear in fields_to_clear:
                if field_to_clear in entry and type(entry[field_to_clear]) == str:
                    entry[field_to_clear] = ""
        yield entry


def clean_stations_data(data: list[dict[str, object]] | Generator[dict[str, object], None, None]) -> Generator[dict[str, object], None, None]:
    return clean_json(data, [
        "platformLength",
        "platforms",
        "network",
        "forRandomTasks",
        "inDefaultRectangle"
    ], [
        "name"
    ])


def clean_paths_data(data: list[dict[str, object]] | Generator[dict[str, object], None, None]) -> Generator[dict[str, object], None, None]:
    return clean_json(data, [
        "name",
        "group"
    ])


def process_json_file(in_file: BinaryIO, out_file: BinaryIO, cleaner: Callable[[list[dict[str, object], None, None]], Generator[dict[str, object], None, None]]):
    json_data = json.load(in_file)
    in_data = json_data["data"]
    cleared_data = cleaner(in_data)
    out_data = {
        "data": [entry for entry in cleared_data]
    }
    json.dump(out_data, out_file, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def test_gzip_size(in_file: PathLike) -> tuple[int, int]:
    import gzip
    with open(in_file, "rb") as in_data:
        data = in_data.read()
        gzipped = gzip.compress(data)
        return (len(data), len(gzipped))
    

# https://stackoverflow.com/a/1094933
def sizeof_fmt(num: int, suffix="B"):
    for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
        if num < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


def print_comparison(title: str, original_uncompressed: int, original_compressed: int, compact_uncompressed: int, compact_compressed: int):
    print("{}".format(title))
    print("    Original Uncompressed: {:>8s}      {:>5}%  " \
          "    Compact  Uncompressed: {:>8s}\n" \
          "    Original Compressed:   {:>8s}      {:>5}%  " \
          "    Compact  Compressed:   {:>8s}".format(
            sizeof_fmt(original_uncompressed), 
            "-{:2.1f}".format((1.0 - compact_uncompressed / original_uncompressed) * 100.0),
            sizeof_fmt(compact_uncompressed), 
            sizeof_fmt(original_compressed), 
            "-{:2.1f}".format((1.0 - compact_compressed / original_compressed) * 100.0),
            sizeof_fmt(compact_compressed)))


def process_stations_paths(stations_path: PathLike, paths_path: PathLike, suffix: str = "_min", overwrite: bool = False, test_gzip: bool = False):
    stations_path_out = Path(stations_path)
    stations_path_out = stations_path_out.with_stem(stations_path_out.stem + suffix)

    paths_path_out = Path(paths_path)
    paths_path_out = paths_path_out.with_stem(paths_path_out.stem + suffix)

    with open(stations_path, "rb") as in_stations, open(stations_path_out, "w" if overwrite else "x", encoding="utf-8", newline="\n") as out_stations:
        process_json_file(in_stations, out_stations, clean_stations_data)
    with open(paths_path, "rb") as in_paths, open(paths_path_out, "w" if overwrite else "x", encoding="utf-8", newline="\n") as out_paths:
        process_json_file(in_paths, out_paths, clean_paths_data)

    if test_gzip:
        o_stations_uncompressed, o_stations_compressed = test_gzip_size(stations_path)
        o_paths_uncompressed, o_paths_compressed = test_gzip_size(paths_path)

        stations_uncompressed, stations_compressed = test_gzip_size(stations_path_out)
        paths_uncompressed, paths_compressed = test_gzip_size(paths_path_out)

        print_comparison("Filesize of Station.json:", o_stations_uncompressed, o_stations_compressed, stations_uncompressed, stations_compressed)
        print()
        print_comparison("Filesize of Path.json:", o_paths_uncompressed, o_paths_compressed, paths_uncompressed, paths_compressed)

        print()
        # (27 characters label + 8 characters size) * 2 (original and compact) + 4 extra spaces in between
        print("-" * ((27 + 8) * 2 + 14))
        print()

        print_comparison("Total:",
                         o_stations_uncompressed + o_paths_uncompressed,
                         o_stations_compressed   + o_paths_compressed,
                         stations_uncompressed   + paths_uncompressed,
                         stations_compressed     + paths_compressed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="TrainCompany JSON compactor",
        description="Removes all optional fields from Stations and Paths that are not needed for routing, reducing their filesize."
    )
    parser.add_argument("-s", "--stations", default="Station.json")
    parser.add_argument("-p", "--paths", default="Path.json")
    parser.add_argument("--suffix", default="_min")
    parser.add_argument("-o", "--overwrite", action="store_true")
    parser.add_argument("--test-gzip", action="store_true")

    args = parser.parse_args()
    process_stations_paths(args.stations, args.paths, args.suffix, args.overwrite, args.test_gzip)