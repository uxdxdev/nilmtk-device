import sys
import utils
import urllib.request
from threading import Thread
from dotenv import load_dotenv
load_dotenv()

# to update the model pass -u as an argument when running main.py
flag_update = False
if len(sys.argv) > 1 and sys.argv[1] == '-u':
    print('Model will be updated')
    flag_update = True

# train algorithm on building number;
traning_building_number = 1
ground_truth = utils.init(traning_building_number)

# apply disaggregation to building number;
building_data = utils.init(1)

# get mains readings from training building
mains = building_data.mains()

# download model from remote server
url = 'https://drive.google.com/uc?authuser=0&id=1xkpI7QQ4jZ1wQJauI0Kn65Q2OeUzL32l&export=download'

# don't use the default model URL, update the model and get new URL
if flag_update:
    # update model and get URL
    url = utils.update_model(traning_building_number)

# download latest model to models/
print('Model URL', url)
model_path = 'models/latest_model.pickle'
urllib.request.urlretrieve(url, model_path)

# use model during disaggregation
predictions = utils.disaggregate(mains, model_path)

# delay between measurements
# dataset provides real world measurement frequency of 3 to 10 seconds
delaySeconds = 0.05
# number of measurements to calculate average
# delaySeconds is not used during average calculation to speed this step up
# 20 measurements @ ~3 seconds each is ~1 minute of real time.
# 1200 measurements @ ~3 seconds each is ~1 hour of real time.
# 28800 measurements @ ~3 seconds each is ~24 hours of real time.
numberOfWarmUpMeasurements = 1200

applianceList = [0, 1, 2]
threadList = []
for appliance in applianceList:
    appliance_payload = utils.get_payload_for_unknown_appliance(
        predictions, appliance)

    thread = Thread(
        target=utils.check_on_off_states,
        args=(appliance_payload, delaySeconds, numberOfWarmUpMeasurements),
    )
    thread.start()
    threadList.append(thread)

for threadObject in threadList:
    thread.join()
    print("thread finished...exiting")
