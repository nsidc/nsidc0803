<p align="center">
  <img alt="NSIDC logo" src="https://nsidc.org/themes/custom/nsidc/logo.svg" width="150" />
</p>

# NSIDC-0803 D

This repository enables users to generate daily NetCDF files from AMSR2 binary sea ice concentration data for the NSIDC-0803 dataset. The tool creates CF-compliant NetCDF files with proper metadata and coordinate reference system information using pyproj for authoritative CRS definitions.

## Level of Support

* This repository is not actively supported by NSIDC but we welcome issue submissions and
  pull requests in order to foster community contribution.

See the [LICENSE](LICENSE) for details on permissions and warranties. Please contact
nsidc@nsidc.org for more information.

## Requirements

* Python 3.8+
* conda or mamba

All Python dependencies are managed via the included `environment.yml` file.

## Installation

```bash
# Create conda environment
conda env create -f environment.yml

# Activate environment
conda activate nsidc0803
```

## Usage

The main script processes binary AMSR2 files and generates CF-compliant NetCDF files with proper metadata following the approved NSIDC-0803 specification.

### Basic Usage

```bash
# Process yesterday's data with all defaults
python nsidc0803_generator.py

# Process specific date
python nsidc0803_generator.py -s 2024-01-05

# Process date range
python nsidc0803_generator.py -s 2024-01-05 -e 2024-01-10

# Process only northern hemisphere
python nsidc0803_generator.py -s 2024-01-05 -h north
```

### Command Line Options

- `-b, --binary-dir`: Directory containing binary input files (default: `/disks/sidads_staging/DATASETS/nsidc0740_AS2_nrt_nasateam_seaice_v1/`)
- `-o, --output-dir`: Directory for NetCDF output files (default: `/share/apps/nsidc0803/`)
- `-t, --template`: CDL template file (default: `nsidc0803_template.cdl`)
- `-s, --start-date`: Start date YYYY-MM-DD or YYYYMMDD (default: yesterday)
- `-e, --end-date`: End date YYYY-MM-DD or YYYYMMDD (default: same as start-date)
- `-h, --hemisphere`: north/south/both (default: both)
- `-v, --verbose`: Verbose output

### Date Format Support

The tool accepts dates in two formats:
- `YYYY-MM-DD` (e.g., `2024-01-05`)
- `YYYYMMDD` (e.g., `20240105`)

### Examples

```bash
# Process yesterday's data (simplest usage)
python nsidc0803_generator.py

# Process specific date with dashes
python nsidc0803_generator.py -s 2024-01-05 -e 2024-01-05

# Process date range, northern hemisphere only
python nsidc0803_generator.py -s 2024-01-05 -e 2024-01-10 -h north

# Custom directories and template
python nsidc0803_generator.py \
  -b /custom/binary/path \
  -o /custom/output/path \
  -t custom_template.cdl \
  -s 2024-01-05

# Verbose output for debugging
python nsidc0803_generator.py -v
```

## File Structure

### Input Files Expected
- `nt_YYYYMMDD_as2_nrt_n.bin` (Northern Hemisphere)
- `nt_YYYYMMDD_as2_nrt_s.bin` (Southern Hemisphere)

### Output Files Generated
- `NSIDC0803_SIC_N25km_YYYYMMDD_v2.0.nc` (Northern Hemisphere)
- `NSIDC0803_SIC_S25km_YYYYMMDD_v2.0.nc` (Southern Hemisphere)

### Output Directory Structure
Files are organized in date-based subdirectories:
```
output_dir/
├── 2024.01.05/
│   ├── NSIDC0803_SIC_N25km_20240105_v2.0.nc
│   └── NSIDC0803_SIC_S25km_20240105_v2.0.nc
├── 2024.01.06/
│   ├── NSIDC0803_SIC_N25km_20240106_v2.0.nc
│   └── NSIDC0803_SIC_S25km_20240106_v2.0.nc
└── ...
```

## Configuration

Default paths are defined in `utils.py` and can be modified:

```python
INPUT_DIR = "/disks/sidads_staging/DATASETS/nsidc0740_AS2_nrt_nasateam_seaice_v1/"
OUTPUT_DIR = "/share/apps/nsidc0803/"
```

## Development

The codebase is organized into:

- `nsidc0803_generator.py`: Main CLI interface and orchestration
- `utils.py`: Core utility functions for file processing
- `nsidc0803_template.cdl`: NetCDF template with metadata

## Troubleshooting

### Common Issues

**Missing binary files:**
```
No binary file found: 2024-01-05 north
```
- Check that binary files exist in the specified directory
- Verify file naming convention: `nt_YYYYMMDD_as2_nrt_[n|s].bin`

**ncgen errors:**
```
ncgen failed: syntax error
```
- Ensure `ncgen` is installed and available in PATH
- Check CDL template syntax

**Import errors:**
- Verify conda environment is activated
- Check that all dependencies are installed: `conda env update -f environment.yml`

### Verbose Mode

Use `-v` flag for detailed processing information:
```bash
python nsidc0803_generator.py -v
```

## Credit

This content was developed by the National Snow and Ice Data Center with funding from multiple sources.
