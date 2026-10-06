#!/usr/bin/env python3
"""Build the live root configuration files from airport source files."""

from pathlib import Path

from convert_geojson_to_txt import convert


ROOT = Path(__file__).resolve().parents[1]
AIRPORTS_DIR = ROOT / "Airports"


def airport_directories() -> list[Path]:
    directories = sorted(path for path in AIRPORTS_DIR.iterdir() if path.is_dir())
    if not directories:
        raise RuntimeError(f"No airport directories found in {AIRPORTS_DIR}")
    return directories


def require_sources(directories: list[Path], source_name: str) -> list[Path]:
    sources = [directory / source_name for directory in directories]
    missing = [source.relative_to(ROOT) for source in sources if not source.is_file()]
    if missing:
        missing_list = "\n".join(f"- {path}" for path in missing)
        raise FileNotFoundError(f"Missing airport source files:\n{missing_list}")
    return sources


def merge_airport_files(
    directories: list[Path], source_name: str, output_name: str
) -> None:
    """Merge one source file from every airport in ICAO order."""
    sources = require_sources(directories, source_name)
    chunks: list[str] = []

    for source in sources:
        content = source.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
        content = content.rstrip("\n")
        if not content:
            raise RuntimeError(f"Source file is empty: {source.relative_to(ROOT)}")
        chunks.append(content)

    output = ROOT / output_name
    with output.open("w", encoding="utf-8", newline="\n") as file:
        file.write("\n\n".join(chunks) + "\n")
    print(f"Merged {len(chunks)} airport files into {output.name}")


def main() -> None:
    directories = airport_directories()
    merge_airport_files(directories, "interval.txt", "sidInterval.txt")
    merge_airport_files(directories, "rate.txt", "rate.txt")

    taxi_area_sources = require_sources(directories, "TaxiAreas.geojson")
    convert(
        taxi_area_sources,
        ROOT / "taxizones.txt",
        validate_parent_icao=True,
    )


if __name__ == "__main__":
    main()
