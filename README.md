# Information

`nilmtk-device` simulates a monitoring device installed in the home connected to the mains power supply. The device ID used is `1234`. Users must first sign up on https://nilmtk-service.firebaseapp.com/dashboard and register this device ID to receive push notifications.

To get push notifications about abnormalities in the fridge running times analysed in the REDD building 1 data run:

`python main.py`

- currently limited to a single report as multiple reports may be generated during analysis. This assumes the monitoring device has collected 1 week of data from the home and runs the disaggregation algorithm on this data.


To simulate this device in a real world setting and get notifications about the on/off states of appliances in the REDD building 1 data run:

`python simulate.py`

- currently set to simulate a monitoring device with a delay between measurements of `0.5` seconds. The on/off states are produced from analysing the REDD building 1 dataset directly, and not the predictions made by a disaggregation algorithm.

# Install 

```
git clone https://github.com/beautifwhale/nilmtk-device.git
cd nilmtk-device
conda env create -f environment.yml
```

# Build

`python convert.py`

Convert the data `data/REDD/low_freq` to `data/redd.h5`. This is sample mains
data. The monitoring device will record and generate this .h5 file data for disaggregation.

# Run

## `main.py`

Disaggregates the REDD building 1 data using George Harts algorithm. Analyses the running time of the predictions made for a fridge and reports any abnormalities in running time to the user using push notifications.

`python main.py`


### Options

`-u` update training model before disaggregation.


## `simulate.py`

`python simulate.py`




