#!/usr/bin/env python3
"""
NSIDC-0803 Daily NetCDF Generator
Modular approach following NSIDC patterns
"""

import datetime as dt
import os
import subprocess
from pathlib import Path
from string import Template

import click
import numpy as np
import yaml
from netCDF4 import Dataset, date2num


def load_config(config_file):
    """Load YAML configuration file"""
    with open(config_file, "r") as f:
        return yaml.safe_load(f)


def get_grid_params():
    """Return grid parameters for both hemispheres"""
    return {
        "north": {
            "xdim": 304,
            "ydim": 448,
            "crs_long_name": "NSIDC Sea Ice Polar Stereographic North",
            "straight_vertical_longitude_from_pole": -45.0,
            "longitude_of_projection_origin": -45.0,
            "latitude_of_projection_origin": 90.0,
            "latitude_of_standard_parallel": 70.0,
            "GeoTransform": "-3850000 25000 0 5850000 0 -25000 ",
            "geospatial_bounds_crs": "EPSG:3411",
            "geospatial_bounds": "POLYGON ((-3850000 5850000, 3750000 5850000,"
            "3750000 -5350000, -3850000 -5350000, -3850000 5850000))",
            "geospatial_lat_min": 30.980564,
            "geospatial_lat_max": 90.0,
            "crs_wkt": 'PROJCS["NSIDC Sea Ice Polar Stereographic North",'
            'GEOGCS["Hughes 1980",DATUM["Hughes_1980",'
            'SPHEROID["Hughes 1980",6378273,298.279411123064,'
            'AUTHORITY["EPSG","7058"]],AUTHORITY["EPSG",'
            '"1359"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG",'
            '"8901"]],UNIT["degree",0.0174532925199433,'
            'AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG",'
            '"10345"]],PROJECTION["Polar_Stereographic"],'
            'PARAMETER["latitude_of_origin",70],'
            'PARAMETER["central_meridian",-45],'
            'PARAMETER["false_easting",0],'
            'PARAMETER["false_northing",0],UNIT["metre",1,'
            'AUTHORITY["EPSG","9001"]],AUTHORITY["EPSG","3411"]]',
        },
        "south": {
            "xdim": 316,
            "ydim": 332,
            "crs_long_name": "NSIDC Sea Ice Polar Stereographic South",
            "straight_vertical_longitude_from_pole": 0.0,
            "longitude_of_projection_origin": 0.0,
            "latitude_of_projection_origin": -90.0,
            "latitude_of_standard_parallel": -70.0,
            "GeoTransform": "-3950000 25000 0 4350000 0 -25000 ",
            "geospatial_bounds_crs": "EPSG:3412",
            "geospatial_bounds": "POLYGON ((-3950000 4350000, 3950000 4350000,"
            "3950000 -3950000, -3950000 -3950000, -3950000 4350000))",
            "geospatial_lat_min": -90.0,
            "geospatial_lat_max": -39.23089,
            "crs_wkt": """PROJCS["NSIDC Sea Ice Polar Stereographic South",
            GEOGCS["Hughes 1980",DATUM["Hughes_1980",SPHEROID["Hughes 1980",
            6378273,298.279411123064,AUTHORITY["EPSG","7058"]],AUTHORITY["EPSG",
            "1359"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],
            UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG",
            "10345"]],PROJECTION["Polar_Stereographic"],PARAMETER["latitude_of_origin",
            -70],PARAMETER["central_meridian",0],PARAMETER["false_easting",0],
            PARAMETER["false_northing",0],UNIT["metre",1,
            AUTHORITY["EPSG","9001"]],AUTHORITY["EPSG","3412"]]""",
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

    filename = f"NSIDC0803_SIC_{hem_code}25km_{ymd}_v2.0.nc"
    return date_dir / filename


def create_cdl(template_file, output_path, date, hemisphere):
    """Create CDL file from template with substitutions"""
    grid_params = get_grid_params()
    params = grid_params[hemisphere]

    # Template substitutions
    substitutions = {
        "xdim": params["xdim"],
        "ydim": params["ydim"],
        "crs_long_name": params["crs_long_name"],
        # "longitude_of_origin": params["longitude_of_origin"],
        "longitude_of_projection_origin": params["longitude_of_projection_origin"],
        "straight_vertical_longitude_from_pole": params[
            "longitude_of_projection_origin"
        ],
        "latitude_of_projection_origin": params["latitude_of_projection_origin"],
        "latitude_of_standard_parallel": params["latitude_of_standard_parallel"],
        "GeoTransform": params["GeoTransform"],
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

    with Dataset(nc_path, "a") as ds:
        # Set time coordinate
        time_var = ds.variables["time"]
        file_time = date2num(date, units=time_var.units, calendar=time_var.calendar)
        time_var[0] = file_time

        # Set x coordinates (25km resolution)
        xdim = params["xdim"]
        geotransform = params["GeoTransform"].split()
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

        ds.variables["crs"].setncattr("crs_wkt", params["crs_wkt"])


class NetCDFGenerator:
    """Main NetCDF generator class following NSIDC patterns"""

    def __init__(self, binary_dir, output_dir, template_file):
        self.binary_dir = Path(binary_dir)
        self.output_dir = Path(output_dir)
        self.template_file = Path(template_file)

    def generate_ncfile(self, date, hemisphere):
        """
        Create netCDF4 file containing AMSR2 data for date/hemisphere
        Following the pattern from your NSIDC-0081 code
        """
        print(f"  Creating {date}: {hemisphere}")

        # Find binary file
        binary_file = find_binary_file(self.binary_dir, date, hemisphere)
        if not binary_file:
            print(f"No binary file found: {date} {hemisphere}")
            return False

        print(f"    Found binary: {binary_file}")

        # Create output filename
        output_file = get_output_filename(self.output_dir, date, hemisphere)

        try:
            # Create CDL from template
            print("    Creating CDL...")
            temp_cdl = create_cdl(self.template_file, output_file, date, hemisphere)

            # Generate NetCDF from CDL
            print("    Generating NetCDF...")
            create_netcdf(temp_cdl, output_file)

            # Add coordinate data
            print("    Adding coordinates...")
            add_nc_coordinate_values(output_file, date, hemisphere)

            # Add binary data
            print("    Adding ice concentration data...")
            encode_binary_to_nc(output_file, binary_file, hemisphere)

            print(f"    ✅ Created: {output_file}")
            return True

        except Exception as e:
            print(f"    ❌ Error: {e}")
            return False

    def generate_ncfiles(self, date, hemispheres=None):
        """
        Generate NetCDF4 files for this date
        Following the pattern from your NSIDC-0081 code
        """
        print(f"Processing date: {date}")

        if hemispheres is None:
            hemispheres = ["north", "south"]

        success_count = 0
        for hemisphere in hemispheres:
            if self.generate_ncfile(date, hemisphere):
                success_count += 1

        return success_count == len(hemispheres)

    def generate_netcdf_for_range(self, start_date, end_date, hemispheres=None):
        """
        Generate NetCDF files for a date range
        Following the pattern from your NSIDC-0081 code
        """
        day_delta = dt.timedelta(days=1)
        total_success = 0
        total_attempted = 0

        current_date = start_date
        while current_date <= end_date:
            if hemispheres is None:
                process_hemispheres = ["north", "south"]
            else:
                process_hemispheres = hemispheres

            total_attempted += len(process_hemispheres)
            if self.generate_ncfiles(current_date, process_hemispheres):
                total_success += len(process_hemispheres)

            current_date += day_delta

        return total_success, total_attempted


@click.command()
@click.option(
    "--binary-dir",
    "-b",
    required=True,
    type=click.Path(exists=True),
    help="Directory containing binary input files",
)
@click.option(
    "--output-dir",
    "-o",
    required=True,
    type=click.Path(),
    help="Directory for NetCDF output files",
)
@click.option(
    "--template",
    "-t",
    required=True,
    type=click.Path(exists=True),
    help="CDL template file",
)
@click.option(
    "--start-date",
    "-s",
    required=True,
    type=click.DateTime(formats=["%Y%m%d"]),
    help="Start date (YYYYMMDD)",
)
@click.option(
    "--end-date",
    "-e",
    type=click.DateTime(formats=["%Y%m%d"]),
    help="End date (YYYYMMDD), defaults to start-date",
)
@click.option(
    "--hemisphere",
    "-h",
    type=click.Choice(["north", "south", "both"]),
    default="both",
    help="Hemisphere to process",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def main(binary_dir, output_dir, template, start_date, end_date, hemisphere, verbose):
    """
    Generate NSIDC-0803 NetCDF files from AMSR2 binary data.

    Examples:

    \b
    # Process single date, both hemispheres
    python nsidc0803_generator.py -b /data/binary -o /data/output
        -t template.cdl -s 20240105

    \b
    # Process date range, northern hemisphere only
    python nsidc0803_generator.py -b /data/binary -o /data/output
        -t template.cdl -s 20240105 -e 20240110 -h north
    """

    if end_date is None:
        end_date = start_date

    if verbose:
        print(f"Binary directory: {binary_dir}")
        print(f"Output directory: {output_dir}")
        print(f"Template file: {template}")
        print(
            f"Date range: {start_date.strftime('%Y-%m-%d')}"
            f" to {end_date.strftime('%Y-%m-%d')}"
        )
        print(f"Hemisphere: {hemisphere}")
        print()

    # Initialize generator
    generator = NetCDFGenerator(binary_dir, output_dir, template)

    # Determine hemispheres to process
    if hemisphere == "both":
        hemispheres = ["north", "south"]
    else:
        hemispheres = [hemisphere]

    # Process date range
    total_success, total_attempted = generator.generate_netcdf_for_range(
        start_date, end_date, hemispheres
    )

    # Summary
    print()
    print(
        f"Processing complete: {total_success}/{total_attempted}"
        " files created successfully"
    )

    if total_success < total_attempted:
        exit(1)


if __name__ == "__main__":
    main()
