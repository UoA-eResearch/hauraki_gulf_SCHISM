#!/usr/bin/env python3

from fastapi import FastAPI, Response
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import pandas as pd
import netCDF4
from glob import glob

files = sorted(glob("../pvol/outputs/**/schout_*.nc", recursive=True))

app = FastAPI(root_path="/API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/vars")
def get_vars():
    nc = netCDF4.Dataset(files[0])
    safe_dict = {}
    for key, value in nc.variables.items():
        safe_subdict = {}
        for k, v in value.__dict__.items():
            if type(v) == np.int32:
                v = int(v)
            elif type(v) == np.float32:
                v = float(v)
            safe_subdict[k] = v
        safe_dict[key] = safe_subdict
    return safe_dict

@app.get("/")
def get_var(timestamp:str = "1994-02-01 01:00:00", variable:str = "depth", format:str = "json", limit:float = 100):
    timestamp = pd.to_datetime(timestamp)
    hour = timestamp.hour
    file = f"../pvol/outputs/{timestamp.year}/{timestamp.month:02d}/schout_{timestamp.day}.nc"
    print(f"Loading {file}")
    assert file in files
    nc = netCDF4.Dataset(file)
    lng = nc["SCHISM_hgrid_node_x"][:]
    lat = nc["SCHISM_hgrid_node_y"][:]
    values = nc[variable][:]
    if len(values.shape) == 1:
        df = pd.DataFrame({"lat": lat, "lng": lng, variable: values})
    elif len(values.shape) == 3:
        values = values[hour, :, :]
        dfs = []
        for depth_level in range(values.shape[-1]):
            values_at_depth = values[:, depth_level]
            df = pd.DataFrame({"lat": lat, "lng": lng, variable: values_at_depth, "depth": depth_level})
            dfs.append(df)
        df = pd.concat(dfs).dropna()
    print(df)
    df = df.head(int(limit))
    if format == "json":
      return df.to_dict("records")
    elif format == "csv":
      csv = df.to_csv(index=False)
      return PlainTextResponse(csv)