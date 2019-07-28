# Install 

```
git clone https://github.com/beautifwhale/nilmtk-device.git
cd nilmtk-device
conda env create -f environment.yml
```

# Build

`python convert.py`

Convert the data `data/REDD/low_freq` to `data/redd.h5`. This is sample mains
data. The monitoring device will record and generate this .h5 file data for dissagregating.

# Run

`python main.py`

# Information

`nilmtk-device` runs on a monitoring device installed in the home connected to
the mains power supply.
