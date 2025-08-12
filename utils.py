"""
Utility functions for NSIDC-0803 NetCDF generation
"""

import datetime as dt
import os
import subprocess
from pathlib import Path
from string import Template

import numpy as np
import pyproj
from netCDF4 import Dataset, date2num

INPUT_DIR = "/disks/sidads_staging/DATASETS/nsidc0740_AS2_nrt_nasateam_seaice_v1/"
OUTPUT_DIR = "/share/apps/nsidc0803/"
# OUTPUT_DIR = "/disks/sidads_staging/DATASETS/nsidc0803_daily_a2_seaice_conc/"


def get_grid_params():
    """Return grid parameters for both hemispheres"""
    north_crs = pyproj.CRS("EPSG:3411")
    south_crs = pyproj.CRS("EPSG:3412")

    north_cf = north_crs.to_cf()
    south_cf = south_crs.to_cf()

    north_cf.update(
        {
            "long_name": "NSIDC Sea Ice Polar Stereographic North",
            "GeoTransform": "-3850000 25000 0 5850000 0 -25000",
            "latitude_of_projection_origin": 90.0,
            "longitude_of_projection_origin": -45.0,
            "latitude_of_standard_parallel": north_cf.pop("standard_parallel"),
        }
    )

    south_cf.update(
        {
            "long_name": "NSIDC Sea Ice Polar Stereographic South",
            "GeoTransform": "-3950000 25000 0 4350000 0 -25000",
            "latitude_of_projection_origin": -90.0,
            "longitude_of_projection_origin": 0.0,
            "latitude_of_standard_parallel": south_cf.pop("standard_parallel"),
        }
    )

    return {
        "north": {
            "xdim": 304,
            "ydim": 448,
            "crs_attrs": north_cf,
            "geospatial_bounds_crs": "EPSG:3411",
            "geospatial_bounds": "POLYGON ((-3850000 5850000, 3750000 5850000,"
            "3750000 -5350000, -3850000 -5350000, -3850000 5850000))",
            "geospatial_lat_min": 30.980564,
            "geospatial_lat_max": 90.0,
        },
        "south": {
            "xdim": 316,
            "ydim": 332,
            "crs_attrs": south_cf,
            "geospatial_bounds_crs": "EPSG:3412",
            "geospatial_bounds": "POLYGON ((-3950000 4350000, 3950000 4350000,"
            "3950000 -3950000, -3950000 -3950000, -3950000 4350000))",
            "geospatial_lat_min": -90.0,
            "geospatial_lat_max": -39.23089,
        },
    }


def find_binary_file(binary_dir, date, hemisphere):
    """Find the binary file for a specific date and hemisphere"""
    ymd = date.strftime("%Y%m%d")
    hem_code = "n" if hemisphere == "north" else "s"

    filename = f"nt_{ymd}_as2_nrt_{hem_code}.bin"

    # Search in binary directory and subdirectories
    for root, dirs, files in os.walk(binary_dir):
        if filename in files:
            return Path(root) / filename

    return None


def get_output_filename(output_dir, date, hemisphere):
    """Create output NetCDF filename following NSIDC conventions"""
    ymd = date.strftime("%Y%m%d")
    hem_code = hemisphere[0].upper()  # N or S

    # Create date-based subdirectory
    date_dir = Path(output_dir) / date.strftime("%Y.%m.%d")
    date_dir.mkdir(parents=True, exist_ok=True)

    filename = f"NSIDC-0803_SEAICE_AMSR2_{hem_code}_{ymd}_v2.0.nc"
    return date_dir / filename


def create_cdl(template_file, output_path, date, hemisphere):
    """Create CDL file from template with substitutions"""
    grid_params = get_grid_params()
    params = grid_params[hemisphere]

    # Template substitutions
    substitutions = {
        "xdim": params["xdim"],
        "ydim": params["ydim"],
        "geospatial_bounds_crs": params["geospatial_bounds_crs"],
        "geospatial_bounds": params["geospatial_bounds"],
        "geospatial_lat_min": params["geospatial_lat_min"],
        "geospatial_lat_max": params["geospatial_lat_max"],
        "time_coverage_start": date.strftime("%Y-%m-%dT00:00:00Z"),
        "time_coverage_end": date.strftime("%Y-%m-%dT23:59:59Z"),
        "date_created": dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "date_modified": dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "software_version_id": "v2.0",
        "software_repository": "https://github.com/nsidc/nsidc0803",
    }

    # Read and substitute template
    with open(template_file, "r") as f:
        template = Template(f.read())

    cdl_content = template.safe_substitute(substitutions)

    # Write temporary CDL file
    temp_cdl = output_path.with_suffix(".cdl")
    with open(temp_cdl, "w") as f:
        f.write(cdl_content)

    return temp_cdl


def create_netcdf(cdl_path, nc_path):
    """Create NetCDF file from CDL using ncgen"""
    if nc_path.exists():
        nc_path.unlink()

    cmd = ["ncgen", "-k", "nc4", "-o", str(nc_path), str(cdl_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"ncgen failed: {result.stderr}")

    # Clean up temporary CDL
    cdl_path.unlink()

    return nc_path


def add_nc_coordinate_values(nc_path, date, hemisphere):
    """Add coordinate values to NetCDF file"""
    grid_params = get_grid_params()
    params = grid_params[hemisphere]
    crs_attrs = params["crs_attrs"]

    with Dataset(nc_path, "a") as ds:
        # Set time coordinate
        time_var = ds.variables["time"]
        file_time = date2num(date, units=time_var.units, calendar=time_var.calendar)
        time_var[0] = file_time

        # Set x coordinates (25km resolution)
        xdim = params["xdim"]
        geotransform = crs_attrs["GeoTransform"].split()
        x_origin = float(geotransform[0])
        x_pixel_size = float(geotransform[1])

        x_vals = np.linspace(
            x_origin + x_pixel_size / 2, x_origin + (xdim - 0.5) * x_pixel_size, xdim
        )
        ds.variables["x"][:] = x_vals

        # Set y coordinates (25km resolution)
        ydim = params["ydim"]
        y_origin = float(geotransform[3])
        y_pixel_size = float(geotransform[5])  # Negative for north-up

        y_vals = np.linspace(
            y_origin + y_pixel_size / 2, y_origin + (ydim - 0.5) * y_pixel_size, ydim
        )
        ds.variables["y"][:] = y_vals


def encode_binary_to_nc(nc_path, binary_path, hemisphere):
    """Add binary data to NetCDF file"""
    grid_params = get_grid_params()
    params = grid_params[hemisphere]

    # Read binary data
    with open(binary_path, "rb") as f:
        data = np.fromfile(f, dtype=np.uint8)

    # Skip 300-byte header (from binary analysis)
    grid_data = data[300:]

    # Validate grid size
    expected_size = params["xdim"] * params["ydim"]
    if len(grid_data) != expected_size:
        raise ValueError(
            f"Grid data size {len(grid_data)} doesn't match expected {expected_size}"
        )

    # Reshape to grid
    grid_array = grid_data.reshape(params["ydim"], params["xdim"])

    if hemisphere == "north":
        # Fill the pole hole
        kernel = np.zeros((448, 304), dtype=np.uint8)
        kernel[229, 150:158] = 1
        kernel[230:238, 149:159] = 1
        kernel[238, 150:158] = 1
        is_pole_hole = kernel == 1
        grid_array[is_pole_hole] = 251

    # scale the binary data
    scaled_data = grid_array * 0.004

    with Dataset(nc_path, "a") as ds:
        icecon = ds.variables["ICECON"]
        icecon[0, :, :] = scaled_data[:, :]
        crs_var = ds.variables["crs"]
        crs_attrs = params["crs_attrs"]

        for attr_name, attr_value in crs_attrs.items():
            crs_var.setncattr(attr_name, attr_value)
