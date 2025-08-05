<p align="center">
  <img alt="NSIDC logo" src="https://nsidc.org/themes/custom/nsidc/logo.svg" width="150" />
</p>


# NSIDC 0803

This repository enables users to generate daily NetCDF files from AMSR2 binary sea ice concentration data for the NSIDC-0803 dataset.


## Level of Support

* This repository is not actively supported by NSIDC but we welcome issue submissions and
  pull requests in order to foster community contribution.

See the [LICENSE](LICENSE) for details on permissions and warranties. Please contact
nsidc@nsidc.org for more information.


## Requirements

* Python
* conda

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

```bash
# Process single date (both hemispheres)
python nsidc0803_generator.py \
  -b /path/to/binary/files \
  -o /path/to/output \
  -t nsidc0803_template.cdl \
  -s 20250104
```
NOTE: this will be improved to use click

```
- `-b, --binary-dir`: Directory containing binary input files (required)
- `-o, --output-dir`: Directory for NetCDF output files (required)  
- `-t, --template`: CDL template file (required)
- `-s, --start-date`: Start date YYYYMMDD (required)
- `-e, --end-date`: End date YYYYMMDD (optional, defaults to start-date)
- `-h, --hemisphere`: north/south/both (default: both)
- `-v, --verbose`: Verbose output
```

**Input files expected:**
- `nt_YYYYMMDD_as2_nrt_n.bin` (Northern Hemisphere)
- `nt_YYYYMMDD_as2_nrt_s.bin` (Southern Hemisphere)

**Output files generated:**
- `NSIDC0803_SIC_N25km_YYYYMMDD_v2.0.nc` (Northern Hemisphere)
- `NSIDC0803_SIC_S25km_YYYYMMDD_v2.0.nc` (Southern Hemisphere)

Files are organized in date-based subdirectories: `YYYY.MM.DD/`

## Troubleshooting

{troubleshooting}


## Credit

This content was developed by the National Snow and Ice Data Center with funding from
multiple sources.
