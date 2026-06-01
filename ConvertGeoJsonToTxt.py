#!/usr/bin/env python3
"""
Convert GeoJSON features -> taxizones.txt (one line per runway)

Output header + lines:
AIRPORT:RUNWAY:BOTTOM_LEFT_LAT:BOTTOM_LEFT_LON:TOP_LEFT_LAT:TOP_LEFT_LON:TOP_RIGHT_LAT:TOP_RIGHT_LON:BOTTOM_RIGHT_LAT:BOTTOM_RIGHT_LON:TAXITIME
"""
import json, argparse
from typing import List, Tuple, Dict, Any

def flatten_ring(coords) -> List[Tuple[float,float]]:
    pts = []
    def walk(o):
        if isinstance(o, (int,float)):
            return
        if isinstance(o, list):
            if len(o) >= 2 and isinstance(o[0], (int,float)) and isinstance(o[1], (int,float)):
                pts.append((float(o[0]), float(o[1])))
                return
            for it in o:
                walk(it)
    walk(coords)
    return pts

def bbox_corners(points: List[Tuple[float,float]]):
    xs = [p[0] for p in points]; ys = [p[1] for p in points]
    minx, maxx = min(xs), max(xs); miny, maxy = min(ys), max(ys)
    # GeoJSON coords are (lon,lat) -> x=lon, y=lat
    return {"TL":(minx,maxy),"TR":(maxx,maxy),"BR":(maxx,miny),"BL":(minx,miny)}

def closest_point_to(target:Tuple[float,float], points:List[Tuple[float,float]]):
    best=None; bd=None
    for p in points:
        d=(p[0]-target[0])**2+(p[1]-target[1])**2
        if bd is None or d<bd:
            bd=d; best=p
    return best

def pick_corners(points:List[Tuple[float,float]]):
    if not points: return None
    corners=bbox_corners(points)
    pts=points.copy()
    sel={}
    for name in ("TL","TR","BR","BL"):
        if not pts:
            sel[name]=corners[name]; continue
        c=corners[name]; p=closest_point_to(c, pts)
        sel[name]=p if p is not None else c
        if p in pts: pts.remove(p)
    return sel

def process_feature(feat:Dict[str,Any], taxiout_add:int):
    geom = feat.get("geometry",{}); props = feat.get("properties",{})
    coords = geom.get("coordinates"); gtype = geom.get("type","")
    if coords is None: return []
    pts=[]
    if gtype=="Polygon":
        if isinstance(coords,list) and coords: pts = flatten_ring(coords[0])
    elif gtype=="MultiPolygon":
        if isinstance(coords,list):
            for poly in coords:
                if poly and isinstance(poly,list):
                    pts = flatten_ring(poly[0])
                    if len(pts)>=3: break
    else:
        pts = flatten_ring(coords)
    if not pts: return []
    sel = pick_corners(pts)
    if not sel: return []
    # gather numeric properties (exclude metadata)
    out_lines=[]
    icao = props.get("icao","").strip()
    taxiout = bool(props.get("taxiout", False))
    for k,v in props.items():
        if k in ("icao","label","taxiout"): continue
        if isinstance(v,(int,float)):
            val = float(v) + (taxiout_add if taxiout else 0)
            taxitime = int(val) if float(val).is_integer() else val
            # sel values are (lon,lat) -> convert to lat,lon as required
            BL_lon,BL_lat = sel["BL"]; TL_lon,TL_lat = sel["TL"]
            TR_lon,TR_lat = sel["TR"]; BR_lon,BR_lat = sel["BR"]
            line = f"{icao}:{k}:{BL_lat:.6f}:{BL_lon:.6f}:{TL_lat:.6f}:{TL_lon:.6f}:{TR_lat:.6f}:{TR_lon:.6f}:{BR_lat:.6f}:{BR_lon:.6f}:{taxitime}"
            out_lines.append(line)
    return out_lines

def convert(inpath,outpath,taxiout_add=10):
    with open(inpath,"r",encoding="utf-8") as f: gj=json.load(f)
    features = gj.get("features",[])
    lines = []
    # header
    header = "AIRPORT:RUNWAY:BOTTOM_LEFT_LAT:BOTTOM_LEFT_LON:TOP_LEFT_LAT:TOP_LEFT_LON:TOP_RIGHT_LAT:TOP_RIGHT_LON:BOTTOM_RIGHT_LAT:BOTTOM_RIGHT_LON:TAXITIME"
    lines.append("# " + header)
    for feat in features:
        feat_lines = process_feature(feat,taxiout_add)
        # If this feature produced one or more runway lines, add a comment identifying the airport and label
        if feat_lines:
            props = feat.get("properties", {})
            icao = str(props.get("icao", "") or "").strip()
            label = str(props.get("label", "") or "").strip()
            if icao or label:
                comment = f"# {icao} - {label}" if icao and label else (f"# {icao}" if icao else f"# {label}")
                lines.append(comment)
            lines.extend(feat_lines)
    with open(outpath,"w",encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Wrote {len(lines)-1} runway lines to {outpath}")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("-i","--input", default="TaxiAreas.geojson")
    p.add_argument("-o","--output", default="taxizones.txt")
    p.add_argument("--taxiout-add", type=int, default=10, help="minutes to add when taxiout=true")
    args=p.parse_args()
    convert(args.input, args.output, args.taxiout_add)

if __name__=="__main__":
    main()