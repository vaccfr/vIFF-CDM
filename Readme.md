# vIFF-CDM Config

## CDM Airports

**LFPG**, **LFPO**, **LFMN**, **LFBO**, **LFLL**, **LFML**, 

## File Description

### CDMconfig.xml
This files is used to configure the EuroScope CDM plugin

### ctot.txt
This files is used to associate CTOT to CID during slotted events

### rate.txt
This files is used to configure CDM airports rate based on runway config

### sidInterval.txt
This files is used to configure CDM airports minimum SID interval time (currently setup to enforce 2 mins between same SID departures)

### taxizones.txt
This files is used to configure CDM airports taxi time based on gate

## Updating the live files

The files in each `Airports/<ICAO>/` directory are the source files.
Each taxi-area feature must have an `icao` property matching its airport
directory. The build stops with an error if an airport source file is missing
or a taxi-area feature is stored under the wrong airport.
After each push to `main`, the **Build live configuration files** workflow:

1. merges every `Airports/<ICAO>/interval.txt` into `sidInterval.txt`;
2. merges every `Airports/<ICAO>/rate.txt` into `rate.txt`;
3. converts every `Airports/<ICAO>/TaxiAreas.geojson` into `taxizones.txt`; and
4. commits changed live files back to `main`.

Airport directories are merged in alphabetical ICAO order. To rebuild the live
files locally, run the following command from the repository root. The three
root output files are generated and should not be edited directly.

```shell
python scripts/build_live_files.py
```
