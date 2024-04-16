#!/usr/bin/env python3

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

@app.get("/files")
def get_files():
    return files.tolist()

@app.get("/vars")
def get_vars():
    nc = netCDF4.Dataset(files[0])
    return list(nc.variables.keys())

@app.get("/")
def get_var(file = files[0], variable = "depth", time = 0):
    assert file in files
    nc = netCDF4.Dataset(file)
    lng = nc["SCHISM_hgrid_node_x"][:]
    lat = nc["SCHISM_hgrid_node_y"][:]
    values = nc[variable][:]
    if len(values.shape) == 1:
        df = pd.DataFrame({"lat": lat, "lng": lng, variable: values})
    elif len(values.shape) == 3:
        values = values[time, :, :]
        dfs = []
        for depth_level in range(values.shape[-1]):
            values_at_depth = values[:, depth_level]
            df = pd.DataFrame({"lat": lat, "lng": lng, variable: values_at_depth, "depth": depth_level})
            dfs.append(df)
        df = pd.concat(dfs)
    return df.to_dict("records")