#!/usr/bin/env python3
"""
NSIDC-0803 Utility functions
Following NSIDC patterns for modular code organization
"""

import datetime as dt
import yaml
from pathlib import Path


def days_ago(n):
    """Return date n days ago (utility function like nsidc0081.util)"""
    return dt.datetime.now() - dt.timedelta(days=n)


def load_config(config_file):
    """Load YAML configuration file (like nsidc0081.util.load_config)"""
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)


def get_hemisphere_params():
    """Return hemisphere-specific parameters"""
    return {
        'north': {
            'xdim': 304,
            'ydim': 448,
            'hemisphere_code': 'n',
            'hemisphere_name': 'Northern Hemisphere',
            'crs_long_name': 'NSIDC Sea Ice Polar Stereographic North',
            'longitude_of_origin': -45.0,
            'latitude_of_standard_parallel': 70.0,
            'GeoTransform': '-3850000 25000 0 5850000 0 -25000',
            'geospatial_bounds_crs': 'EPSG:3411',
            'geospatial_bounds': 'POLYGON ((-3850000 5850000, 3750000 5850000, 3750000 -5350000, -3850000 -5350000, -3850000 5850000))',
            'geospatial_lat_min': 30.980564,
            'geospatial_lat_max': 90.0,
            'crs_wkt': '''PROJCS["NSIDC Sea Ice Polar Stereographic North",GEOGCS["Unspecified datum based upon the Hughes 1980 ellipsoid",DATUM["Not_specified_based_on_Hughes_1980_ellipsoid",SPHEROID["Hughes 1980",6378273,298.279411123064,AUTHORITY["EPSG","7058"]],AUTHORITY["EPSG","6054"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4054"]],PROJECTION["Polar_Stereographic"],PARAMETER["latitude_of_origin",70],PARAMETER["central_meridian",-45],PARAMETER["scale_factor",1],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AUTHORITY["EPSG","3411"]]'''
        },
        'south': {
            'xdim': 316,
            'ydim': 332,
            'hemisphere_code': 's',
            'hemisphere_name': 'Southern Hemisphere',
            'crs_long_name': 'NSIDC Sea Ice Polar Stereographic South',
            'longitude_of_origin': 0.0,
            'latitude_of_standard_parallel': -70.0,
            'GeoTransform': '-3950000 25000 0 4350000 0 -25000',
            'geospatial_bounds_crs': 'EPSG:3412',
            'geospatial_bounds': 'POLYGON ((-3950000 4350000, 3950000 4350000, 3950000 -3950000, -3950000 -3950000, -3950000 4350000))',
            'geospatial_lat_min': -90.0,
            'geospatial_lat_max': -39.23089,
            'crs_wkt': '''PROJCS["NSIDC Sea Ice Polar Stereographic South",GEOGCS["Unspecified datum based upon the Hughes 1980 ellipsoid",DATUM["Not_specified_based_on_Hughes_1980_ellipsoid",SPHEROID["Hughes 1980",6378273,298.279411123064,AUTHORITY["EPSG","7058"]],AUTHORITY["EPSG","6054"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4054"]],PROJECTION["Polar_Stereographic"],PARAMETER["latitude_of_origin",-70],PARAMETER["central_meridian",0],PARAMETER["scale_factor",1],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AUTHORITY["EPSG","3412"]]'''
        }
    }


def get_filename_template():
    """Return filename templates for binary and NetCDF files"""
    return {
        'binary': {
            'pattern': 'nt_{ymd}_as2_nrt_{hem}.bin',
            'description': 'AMSR2 binary sea ice concentration files'
        },
        'netcdf': {
            'pattern': 'NSIDC0803_SIC_{hem_upper}25km_{ymd}_v2.0.nc',
            'description': 'NSIDC-0803 NetCDF sea ice concentration files'
        }
    }


def get_processing_params():
    """Return processing parameters"""
    return {
        'header_size': 300,  # bytes
        'resolution': 25,    # km
        'product_version': 'v2.0',
        'software_repository': 'https://github.com/nsidc/nsidc0803',
        'institution': 'National Snow and Ice Data Center',
        'platform': 'GCOM-W1 > Global Change Observation Mission 1st-Water',
        'instrument': 'AMSR2 > Advanced Microwave Scanning Radiometer 2'
    }


def validate_hemisphere(hemisphere):
    """Validate hemisphere parameter"""
    valid_hemispheres = ['north', 'south', 'n', 's']
    if hemisphere.lower() not in valid_hemispheres:
        raise ValueError(f"Invalid hemisphere: {hemisphere}. Must be one of {valid_hemispheres}")
    
    # Normalize to full name
    if hemisphere.lower() in ['n', 'north']:
        return 'north'
    else:
        return 'south'


def format_date_for_filename(date):
    """Format date for use in filenames (YYYYMMDD)"""
    return date.strftime('%Y%m%d')


def format_date_for_iso(date):
    """Format date for ISO 8601 strings"""
    return date.strftime('%Y-%m-%dT%H:%M:%SZ')


def get_date_range(start_date, end_date):
    """Generate list of dates between start and end (inclusive)"""
    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current)
        current += dt.timedelta(days=1)
    return dates


class FileNameGenerator:
    """Generate consistent filenames following NSIDC conventions"""
    
    def __init__(self):
        self.templates = get_filename_template()
        self.processing_params = get_processing_params()
    
    def get_binary_filename(self, date, hemisphere):
        """Generate binary input filename"""
        hemisphere = validate_hemisphere(hemisphere)
        hem_params = get_hemisphere_params()[hemisphere]
        
        return self.templates['binary']['pattern'].format(
            ymd=format_date_for_filename(date),
            hem=hem_params['hemisphere_code']
        )
    
    def get_netcdf_filename(self, date, hemisphere):
        """Generate NetCDF output filename"""
        hemisphere = validate_hemisphere(hemisphere)
        hem_params = get_hemisphere_params()[hemisphere]
        
        return self.templates['netcdf']['pattern'].format(
            ymd=format_date_for_filename(date),
            hem_upper=hem_params['hemisphere_code'].upper()
        )
    
    def get_output_directory(self, base_dir, date):
        """Generate output directory path with date subdirectory"""
        date_subdir = date.strftime('%Y.%m.%d')
        return Path(base_dir) / date_subdir


def create_substitution_dict(date, hemisphere):
    """Create template substitution dictionary for CDL processing"""
    hemisphere = validate_hemisphere(hemisphere)
    hem_params = get_hemisphere_params()[hemisphere]
    proc_params = get_processing_params()
    
    now = dt.datetime.now()
    
    substitutions = {
        # Grid parameters
        'xdim': hem_params['xdim'],
        'ydim': hem_params['ydim'],
        
        # CRS parameters
        'crs_long_name': hem_params['crs_long_name'],
        'longitude_of_origin': hem_params['longitude_of_origin'],
        'latitude_of_standard_parallel': hem_params['latitude_of_standard_parallel'],
        'GeoTransform': hem_params['GeoTransform'],
        'crs_wkt': hem_params['crs_wkt'],
        
        # Geospatial parameters
        'geospatial_bounds_crs': hem_params['geospatial_bounds_crs'],
        'geospatial_bounds': hem_params['geospatial_bounds'],
        'geospatial_lat_min': hem_params['geospatial_lat_min'],
        'geospatial_lat_max': hem_params['geospatial_lat_max'],
        
        # Time parameters
        'time_coverage_start': date.strftime('%Y-%m-%dT00:00:00Z'),
        'time_coverage_end': date.strftime('%Y-%m-%dT23:59:59Z'),
        'date_created': format_date_for_iso(now),
        'date_modified': format_date_for_iso(now),
        
        # Processing parameters
        'software_version_id': proc_params['product_version'],
        'software_repository': proc_params['software_repository']
    }
    
    return substitutions


if __name__ == "__main__":
    # Test the utility functions
    print("NSIDC-0803 Utilities Test")
    print("=" * 30)
    
    # Test date functions
    today = dt.datetime.now()
    print(f"Today: {today}")
    print(f"5 days ago: {days_ago(5)}")
    print(f"Date for filename: {format_date_for_filename(today)}")
    
    # Test hemisphere validation
    print(f"Validate 'n': {validate_hemisphere('n')}")
    print(f"Validate 'south': {validate_hemisphere('south')}")
    
    # Test filename generation
    fn_gen = FileNameGenerator()
    print(f"Binary filename: {fn_gen.get_binary_filename(today, 'north')}")
    print(f"NetCDF filename: {fn_gen.get_netcdf_filename(today, 'south')}")
    
    # Test substitution dictionary
    subs = create_substitution_dict(today, 'north')
    print(f"Substitution keys: {list(subs.keys())}")
