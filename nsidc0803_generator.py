#!/usr/bin/env python3
"""
NSIDC-0803 Daily NetCDF Generator
Modular approach following NSIDC patterns
"""

import datetime as dt
from pathlib import Path

import click
import yaml

from utils import (
    INPUT_DIR,
    OUTPUT_DIR,
    add_nc_coordinate_values,
    create_cdl,
    create_netcdf,
    encode_binary_to_nc,
    find_binary_file,
    get_output_filename,
)


def load_config(config_file):
    """Load YAML configuration file"""
    with open(config_file, "r") as f:
        return yaml.safe_load(f)


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
    default=INPUT_DIR,
    type=click.Path(exists=True),
    help="Directory containing binary input files",
)
@click.option(
    "--output-dir",
    "-o",
    required=True,
    default=OUTPUT_DIR,
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
