# Information

`nilmtk-device` simulates a monitoring device installed in the home connected to the mains power supply. The device ID must be set in a `.env` file, e.g. `DEVICE_ID=1234`. Users must first sign up on https://nilmtk-service.firebaseapp.com and register this device ID to receive push notifications.

To get push notifications about abnormalities in unknown appliance running times analysed in the REDD building 1 data run:

`python main.py`

- This test assumes the monitoring device has collected 1 day of data from the home and runs the disaggregation algorithm on this data. The resulting predictions contains unknown appliances because of the unsupervised ML algorithm Hart85. Reports will reference appliances 0,1,2,etc.


To simulate this device in a real world setting using the REDD building 1 data run:

`python simulate.py`

- currently set to simulate a monitoring device with a delay between measurements of `0.5` seconds, this must be set in the `.env` file, e.g. `DELAY_IN_MEASUREMENT_FREQUENCY=0.5`.

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

## `main.py`

Disaggregates the REDD building 1 data using George Harts algorithm. Analyses the predictions made and reports any abnormalities to the user using push notifications.

`python main.py`


### Options

`-u` update training model before disaggregation.


## `simulate.py`

`python simulate.py`

Uses raw monitoring data for building 1 in the REDD dataset. Analyses this data and reports any abnormalities to the user using push notifications. Assumes disaggregation has be done on mains and individual appliance level metrics are available.


