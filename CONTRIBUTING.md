# Contributing to vIFF-CDM

Thank you for helping maintain the French vACC vIFF-CDM configuration.

Airport files are the source of truth for this repository. Please make changes
inside the relevant `Airports/<ICAO>/` directory and regenerate the live root
files before submitting your contribution.

## Requirements

- Python 3.9 or later
- No third-party Python packages are required

## Updating an Existing Airport

1. Edit the appropriate files under `Airports/<ICAO>/`.
2. Run the local build from the repository root:

   ```shell
   python scripts/build_live_files.py
   ```

3. Review the source and generated-file changes.
4. Commit the airport sources and regenerated live files together.

The following root files are generated and must not be edited directly:

- `rate.txt`
- `sidInterval.txt`
- `taxizones.txt`

## Adding an Airport

Create an uppercase ICAO directory under `Airports/` containing:

```text
Airports/<ICAO>/
├── capacity.txt
├── interval.txt
├── procedures.txt
├── rate.txt
└── TaxiAreas.geojson
```

Use an existing airport with similar operations as a formatting reference.
Also update `CDMconfig.xml` and the supported-airports section of `Readme.md`
when applicable.

## Taxi-Area GeoJSON

`TaxiAreas.geojson` must contain a GeoJSON `FeatureCollection`. Each feature
must:

- use the airport ICAO as its `icao` property;
- include a descriptive `label`;
- include a Boolean `taxiout` property;
- define a numeric taxi time for each applicable departure runway; and
- contain a polygon representing the associated airport area.

The feature `icao` must match the parent airport directory exactly. When
`taxiout` is `true`, the converter adds 10 minutes to each configured runway
value.

Example properties:

```json
{
  "icao": "LFXX",
  "label": "Terminal area",
  "taxiout": false,
  "09": 8,
  "27": 12
}
```

## Generated Outputs

The local build performs the same operations as the GitHub Actions workflow:

1. merges every `interval.txt` into `sidInterval.txt`;
2. merges every `rate.txt` into `rate.txt`; and
3. converts every `TaxiAreas.geojson` into `taxizones.txt`.

Airports are processed in alphabetical ICAO order. The build fails if a
required source file is missing or a taxi-area feature belongs to a different
airport.

After a contribution reaches `main`, the workflow rebuilds the outputs and
commits any necessary synchronization changes automatically.

## Pull-Request Checklist

- [ ] Airport source files contain only the intended changes.
- [ ] Every taxi-area feature uses the correct ICAO.
- [ ] `python scripts/build_live_files.py` completes successfully.
- [ ] Generated root files are included and have been reviewed.
- [ ] `CDMconfig.xml` and `Readme.md` are updated when adding an airport.
