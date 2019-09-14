import os
import sys
import utils
import urllib.request
from threading import Thread
from dotenv import load_dotenv
load_dotenv()

DELAY_IN_MEASUREMENT_FREQUENCY = os.getenv("DELAY_IN_MEASUREMENT_FREQUENCY")

# to update the model pass -u as an argument when running main.py
flag_update = False
if len(sys.argv) > 1 and sys.argv[1] == '-u':
    print('Model will be updated')
    flag_update = True

# set the timeframe for the building data
start = '2011-04-25'
end = '2011-04-26'

# train algorithm on building number;
traning_building_number = 1
ground_truth_data = utils.init(traning_building_number, start, end)

# apply disaggregation to building number;
application_building_number = 2
building_data = utils.init(application_building_number, start, end)

# get mains readings from training building
mains = building_data.mains()

# download model from remote server
url = 'https://drive.google.com/uc?authuser=0&id=1xkpI7QQ4jZ1wQJauI0Kn65Q2OeUzL32l&export=download'

# don't use the default model URL, update the model and get new URL
if flag_update:
    # update model and get URL
    url = utils.update_model(ground_truth_data)

# download latest model to models/
print('Model URL', url)
model_path = 'models/latest_model.pickle'
urllib.request.urlretrieve(url, model_path)

# use model during disaggregation
predictions = utils.disaggregate(mains, model_path)

applianceList = [0, 1, 2]
threadList = []
for appliance in applianceList:
    appliance_payload = utils.get_payload_for_unknown_appliance(
        predictions, appliance)

    thread = Thread(
        target=utils.check_on_off_states,
        args=(appliance_payload, DELAY_IN_MEASUREMENT_FREQUENCY),
    )
    thread.start()
    threadList.append(thread)

for threadObject in threadList:
    thread.join()
    print("thread finished...exiting")
