#!/usr/bin/env python3
"""Convert one or more airport GeoJSON files into taxizones.txt."""

import argparse
import json
from pathlib import Path
from typing import Any, Iterable


HEADER = (
    "AIRPORT:RUNWAY:BOTTOM_LEFT_LAT:BOTTOM_LEFT_LON:TOP_LEFT_LAT:TOP_LEFT_LON:"
    "TOP_RIGHT_LAT:TOP_RIGHT_LON:BOTTOM_RIGHT_LAT:BOTTOM_RIGHT_LON:TAXITIME"
)


def flatten_ring(coords: Any) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []

    def walk(value: Any) -> None:
        if isinstance(value, (int, float)):
            return
        if isinstance(value, list):
            if (
                len(value) >= 2
                and isinstance(value[0], (int, float))
                and isinstance(value[1], (int, float))
            ):
                points.append((float(value[0]), float(value[1])))
                return
            for item in value:
                walk(item)

    walk(coords)
    return points


def bbox_corners(points: list[tuple[float, float]]) -> dict[str, tuple[float, float]]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    return {
        "TL": (min_x, max_y),
        "TR": (max_x, max_y),
        "BR": (max_x, min_y),
        "BL": (min_x, min_y),
    }


def closest_point_to(
    target: tuple[float, float], points: list[tuple[float, float]]
) -> tuple[float, float]:
    return min(
        points,
        key=lambda point: (point[0] - target[0]) ** 2
        + (point[1] - target[1]) ** 2,
    )


def pick_corners(
    points: list[tuple[float, float]],
) -> dict[str, tuple[float, float]] | None:
    if not points:
        return None

    corners = bbox_corners(points)
    remaining = points.copy()
    selected: dict[str, tuple[float, float]] = {}
    for name in ("TL", "TR", "BR", "BL"):
        if not remaining:
            selected[name] = corners[name]
            continue
        point = closest_point_to(corners[name], remaining)
        selected[name] = point
        remaining.remove(point)
    return selected


def process_feature(feature: dict[str, Any], taxiout_add: int) -> list[str]:
    geometry = feature.get("geometry", {})
    properties = feature.get("properties", {})
    coordinates = geometry.get("coordinates")
    geometry_type = geometry.get("type", "")
    if coordinates is None:
        return []

    points: list[tuple[float, float]] = []
    if geometry_type == "Polygon":
        if isinstance(coordinates, list) and coordinates:
            points = flatten_ring(coordinates[0])
    elif geometry_type == "MultiPolygon":
        if isinstance(coordinates, list):
            for polygon in coordinates:
                if polygon and isinstance(polygon, list):
                    points = flatten_ring(polygon[0])
                    if len(points) >= 3:
                        break
    else:
        points = flatten_ring(coordinates)

    selected = pick_corners(points)
    if not selected:
        return []

    icao = str(properties.get("icao", "") or "").strip()
    taxiout = bool(properties.get("taxiout", False))
    output_lines: list[str] = []

    for runway, value in properties.items():
        if runway in ("icao", "label", "taxiout") or not isinstance(
            value, (int, float)
        ):
            continue

        adjusted_value = float(value) + (taxiout_add if taxiout else 0)
        taxi_time = (
            int(adjusted_value) if adjusted_value.is_integer() else adjusted_value
        )

        bottom_left_lon, bottom_left_lat = selected["BL"]
        top_left_lon, top_left_lat = selected["TL"]
        top_right_lon, top_right_lat = selected["TR"]
        bottom_right_lon, bottom_right_lat = selected["BR"]
        output_lines.append(
            f"{icao}:{runway}:"
            f"{bottom_left_lat:.6f}:{bottom_left_lon:.6f}:"
            f"{top_left_lat:.6f}:{top_left_lon:.6f}:"
            f"{top_right_lat:.6f}:{top_right_lon:.6f}:"
            f"{bottom_right_lat:.6f}:{bottom_right_lon:.6f}:{taxi_time}"
        )

    return output_lines


def convert(
    input_paths: Iterable[Path],
    output_path: Path,
    taxiout_add: int = 10,
    validate_parent_icao: bool = False,
) -> None:
    lines = [f"# {HEADER}"]
    source_count = 0

    for input_path in input_paths:
        source_count += 1
        with input_path.open("r", encoding="utf-8-sig") as file:
            geojson = json.load(file)

        if geojson.get("type") != "FeatureCollection":
            raise ValueError(f"Expected a FeatureCollection in {input_path}")
        features = geojson.get("features")
        if not isinstance(features, list):
            raise ValueError(f"Expected a features array in {input_path}")

        expected_icao = input_path.parent.name if validate_parent_icao else None
        for feature_index, feature in enumerate(features, start=1):
            properties = feature.get("properties", {})
            icao = str(properties.get("icao", "") or "").strip()
            if expected_icao and icao != expected_icao:
                raise ValueError(
                    f"Feature {feature_index} in {input_path} has ICAO {icao!r}; "
                    f"expected {expected_icao!r}"
                )

            feature_lines = process_feature(feature, taxiout_add)
            if not feature_lines:
                continue

            label = str(properties.get("label", "") or "").strip()
            if icao or label:
                comment = (
                    f"# {icao} - {label}"
                    if icao and label
                    else (f"# {icao}" if icao else f"# {label}")
                )
                lines.append(comment)
            lines.extend(feature_lines)

    with output_path.open("w", encoding="utf-8", newline="\n") as file:
        file.write("\n".join(lines) + "\n")

    runway_line_count = sum(
        1 for line in lines if line and not line.startswith("#")
    )
    print(
        f"Converted {source_count} GeoJSON files into {output_path.name} "
        f"({runway_line_count} runway lines)"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("-o", "--output", type=Path, default=Path("taxizones.txt"))
    parser.add_argument(
        "--taxiout-add",
        type=int,
        default=10,
        help="minutes to add when taxiout=true",
    )
    parser.add_argument(
        "--validate-parent-icao",
        action="store_true",
        help="require every feature ICAO to match its parent directory",
    )
    args = parser.parse_args()
    convert(
        args.inputs,
        args.output,
        args.taxiout_add,
        args.validate_parent_icao,
    )


if __name__ == "__main__":
    main()
