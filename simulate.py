import utils
from threading import Thread
from dotenv import load_dotenv
load_dotenv()

# get building data
building_data = utils.init(1)

# output appliances in building_data
print(building_data)


# delay between measurements
# dataset provides real world measurement frequency of 3 to 10 seconds
delaySeconds = 0.0
# number of measurements to calculate average
# delaySeconds is not used during average calculation to speed this step up
# 20 measurements @ ~3 seconds each is ~1 minute of real time.
# 1200 measurements @ ~3 seconds each is ~1 hour of real time.
# 28800 measurements @ ~3 seconds each is ~24 hours of real time.
numberOfWarmUpMeasurements = 1200


applianceList = ["fridge", "dish washer", "microwave", "light"]
threadList = []
for appliance in applianceList:
    appliance_payload = utils.get_payload_for_appliance(
        building_data, appliance)

    thread = Thread(
        target=utils.check_on_off_states,
        args=(appliance_payload, delaySeconds, numberOfWarmUpMeasurements),
    )
    thread.start()
    threadList.append(thread)

for threadObject in threadList:
    thread.join()
    print("thread finished...exiting")
