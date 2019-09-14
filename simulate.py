import os
import utils
from threading import Thread
from dotenv import load_dotenv
load_dotenv()


# delay between measurements
# dataset provides real world measurement frequency of 3 to 10 seconds
DELAY_IN_MEASUREMENT_FREQUENCY = os.getenv("DELAY_IN_MEASUREMENT_FREQUENCY")

# set the timeframe for analysis
# full timeframe for REDD data start='2011-04-18 09:22:09-04:00', end='2011-05-24 15:57:02-04:00'
start = '2011-04-20'
end = '2011-04-24'

# get building data
building_number = 1
building_data = utils.init(building_number, start, end)

# output appliances in building_data
print(building_data)

applianceList = ["fridge", "dish washer", "microwave", "light"]
threadList = []
for appliance in applianceList:
    appliance_payload = utils.get_payload_for_appliance(
        building_data, appliance)

    thread = Thread(
        target=utils.check_on_off_states,
        args=(appliance_payload, DELAY_IN_MEASUREMENT_FREQUENCY),
    )
    thread.start()
    threadList.append(thread)

for threadObject in threadList:
    thread.join()
    print("thread finished...exiting")
