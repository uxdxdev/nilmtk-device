# Information

`nilmtk-device` simulates a monitoring device installed in the home connected to the mains power supply.

To simulate this device in a real world setting using the REDD dataset run:

`python simulate.py <device-id>`

- currently set to simulate a monitoring device with a delay between measurements of `0.02` seconds, this must be set in the `.env` file, e.g. `DELAY_IN_MEASUREMENT_FREQUENCY_REALTIME_SAMPLING=0.02`.

# Install 

```
git clone https://github.com/beautifwhale/nilmtk-device.git
cd nilmtk-device
conda env create -f environment.yml
```

# Build

`python convert.py`

Convert the data `data/REDD/low_freq` to `data/redd.h5`. This is sample mains data. The monitoring device will record and generate this .h5 file data for disaggregation.

# Run

## `simulate.py`

`python simulate.py <device-id>`

### Options

`id` The device ID used to register the device to a user. See https://nilmtk-service.firebaseapp.com.

Uses raw monitoring data for building 1 in the REDD dataset. Analyses this data and reports any abnormalities to the user using push notifications. Assumes disaggregation has be done on mains and individual appliance level metrics are available.


