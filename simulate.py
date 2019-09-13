import utils
import time
from threading import Thread
from datetime import datetime


def check_on_off_states(payload, delaySeconds=0.0, numberOfWarmUpMeasurements=600):

    appliance = payload["appliance"]
    print("checking on/off states for", appliance)
    load = payload["load"]

    averageLoad = 0
    averageOnLoad = 0
    sumLoad = 0
    sumOnLoad = 0
    numberOfEntries = 0
    numberOfOnEntries = 0
    previousLoad = 0
    isApplianceOn = False
    loadSpikeDetected = False

    # ghost load is the power draw of an appliance when its plugged in
    # and on standby mode, we don't want to trigger an on state unless the
    # load draw is above the ghost load.
    ghostLoad = 40

    applianceRunningTimeStart = 0
    applianceRunningTimeEnd = 0

    switchedOnCount = 0
    sumOnRunningTime = 0

    # after the first numberOfWarmUpMeasurements use the average
    # to check appliance state on/off.
    for entry in load:

        currentLoad = entry["load"]

        numberOfEntries += 1
        sumLoad += currentLoad
        averageLoad = sumLoad / numberOfEntries

        # only check appliance state when the average load is calculated
        if numberOfEntries > numberOfWarmUpMeasurements:
            # measurement read frequency
            time.sleep(delaySeconds)

            # if currentLoad > averageLoad and not isApplianceOn and currentLoad > ghostLoad:
            if not isApplianceOn and currentLoad > ghostLoad:
                switchedOnCount += 1
                applianceRunningTimeStart = entry["timestamp"]
                utc_dt = datetime.utcfromtimestamp(applianceRunningTimeStart)

                print(
                    str(utc_dt)
                    + " "
                    + appliance
                    + " is on. Current load "
                    + str(currentLoad)
                    + " previous load "
                    + str(previousLoad)
                )
                isApplianceOn = True

                utils.send_report(1234, appliance.title() + ' is on.')

            # if currentLoad < averageLoad and isApplianceOn:
            if isApplianceOn and currentLoad < ghostLoad:
                isApplianceOn = False

                loadSpikeDetected = False
                applianceRunningTimeEnd = entry["timestamp"]
                utc_dt = datetime.utcfromtimestamp(applianceRunningTimeEnd)

                runningTime = applianceRunningTimeEnd - applianceRunningTimeStart
                print(
                    str(utc_dt)
                    + " "
                    + appliance
                    + " is off. Current load "
                    + str(currentLoad)
                    + " previous load "
                    + str(previousLoad)
                    + " running time:"
                    + str(runningTime)
                    + " seconds"
                )

                # running time measurement
                sumOnRunningTime += runningTime
                averageOnRunningTime = sumOnRunningTime / switchedOnCount

                # if running time is 50% above the average
                if runningTime > (averageOnRunningTime * 1.5):
                    message = (
                        ">>>> RUNNING TIME SPIKE >>>> "
                        + str(utc_dt)
                        + " "
                        + appliance
                        + " is on for 50% longer than average "
                        + str(averageOnRunningTime)
                    )
                    print(message)
                    utils.send_report(1234, 'Please check your {}, it has been running for longer than usual.'.format(appliance.title()), utils.REPORT_TYPE_WARNING)
                
                utils.send_report(1234, appliance.title() + ' is off.')


            # calculate the average on load and check if current load
            # is above the average
            if isApplianceOn:
                numberOfOnEntries += 1

                # load measurement
                sumOnLoad += currentLoad
                averageOnLoad = sumOnLoad / numberOfOnEntries

                # check for load spikes above the average load
                if not loadSpikeDetected and currentLoad > (averageOnLoad * 2.0):
                    loadSpikeDetected = True
                    applianceTimestamp = entry["timestamp"]
                    utc_dt = datetime.utcfromtimestamp(applianceTimestamp)
                    message = (
                        ">>>> LOAD SPIKE >>>> "
                        + str(utc_dt)
                        + " "
                        + appliance
                        + " load of "
                        + str(currentLoad)
                        + " is above average of "
                        + str(averageOnLoad)
                    )
                    print(message)
                    utils.send_report(1234, 'Please check your {}, it is using more power than usual.'.format(appliance.title()), utils.REPORT_TYPE_WARNING)

        previousLoad = currentLoad

    print(appliance + " average load " + str(averageLoad))


# get building data
building_data = utils.init(1)

# output appliances in building_data
print(building_data)


# delay between measurements
# dataset provides real world measurement frequency of 3 to 10 seconds
delaySeconds = 0.05
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
        target=check_on_off_states,
        args=(appliance_payload, delaySeconds, numberOfWarmUpMeasurements),
    )
    thread.start()
    threadList.append(thread)

for threadObject in threadList:
    thread.join()
    print("thread finished...exiting")
