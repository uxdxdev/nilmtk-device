""" EcoPush """
import pandas as pd
import json
import hart_85 as algo
import requests
from datetime import datetime
import os
import utils


class MonitoringSystem:

    def __init__(self, deviceId, appliance):
        self.deviceId = deviceId
        self.appliance = appliance
        self.sumOnLoad = 0
        self.sumOnLoadToday = 0
        self.numberOfOnEntries = 0
        self.numberOfOnEntriesToday = 0
        self.previousLoad = 0
        self.isApplianceOn = False
        self.loadSpikeDetected = False
        self.ghostLoad = 40
        self.switchedOnCount = 0
        self.sumOnRunningTime = 0
        self.applianceRunningTimeStart = 0
        self.previousDate = None
        self.averageOnLoad = 0
        self.averageOnLoadToday = 0
        self.previousAverageOnLoad = 0

    def import_historical_data(self, currentLoad, timestamp):
        self.analyse_data(currentLoad=currentLoad, timestamp=timestamp, isHistoricalData=True)            

    def calculate_end_of_day_metrics(self, timestamp):

        currentDate = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d')

        if self.previousDate is None:
            self.previousDate = currentDate

        if currentDate != self.previousDate:

            if self.previousAverageOnLoad != 0:
                percentageChange = round(((self.averageOnLoadToday - self.previousAverageOnLoad) / self.previousAverageOnLoad) * 100, 2)
                
                summary = {
                    'deviceId': self.deviceId,
                    'date': currentDate,
                    'applianceId': self.appliance,
                    'averageLoad': self.averageOnLoadToday,
                    'change': percentageChange,
                    'timestamp': timestamp
                }
                utils.send_report_summary(summary)

            self.previousDate = currentDate
            self.previousAverageOnLoad = self.averageOnLoadToday
            self.sumOnLoadToday = 0
            self.numberOfOnEntriesToday = 0
            self.averageOnLoadToday = 0

    def analyse_data(self, currentLoad, timestamp, isHistoricalData=False):
        
        self.calculate_end_of_day_metrics(timestamp)
    
        if not self.isApplianceOn and currentLoad > self.ghostLoad:
            self.isApplianceOn = True
            self.switchedOnCount += 1

            self.applianceRunningTimeStart = timestamp
            utc_dt = datetime.utcfromtimestamp(self.applianceRunningTimeStart)

            if not isHistoricalData:
                print(
                    str(utc_dt)
                    + " "
                    + str(self.appliance)
                    + " is on. Current load "
                    + str(currentLoad)
                    + " previous load "
                    + str(self.previousLoad)
                )

                utils.send_report(self.deviceId, 'Appliance ' + str(
                    self.appliance).title() + ' is on.', appliance=str(self.appliance).title())

        # if currentLoad < averageLoad and isApplianceOn:
        if self.isApplianceOn and currentLoad < self.ghostLoad:            
            self.isApplianceOn = False
            self.loadSpikeDetected = False
            applianceRunningTimeEnd = timestamp
            utc_dt = datetime.utcfromtimestamp(applianceRunningTimeEnd)

            # running time measurement
            runningTime = applianceRunningTimeEnd - self.applianceRunningTimeStart
            self.sumOnRunningTime += runningTime
            averageOnRunningTime = self.sumOnRunningTime / self.switchedOnCount

            # if running time is 50% above the average
            if runningTime > (averageOnRunningTime * 1.5) and not isHistoricalData:               
                message = (
                    ">>>> RUNNING TIME SPIKE >>>> "
                    + str(utc_dt)
                    + " "
                    + str(self.appliance)
                    + " is on for 50% longer than average "
                    + str(averageOnRunningTime))
                print(message)
                utils.send_report(self.deviceId, 'Your appliance {} has been running for longer than usual. You may have forgotten to turn if off.'.format(
                    str(self.appliance).title()), reportType=utils.REPORT_TYPE_WARNING)

            if not isHistoricalData:
                message = (
                    str(utc_dt) 
                    + " "
                    + str(self.appliance)
                    + " is off. Current load "
                    + str(currentLoad)
                    + " previous load "
                    + str(self.previousLoad)
                    + " running time:"
                    + str(runningTime)
                    + " seconds")

                print(message)
                utils.send_report(self.deviceId, 'Appliance ' + str(self.appliance).title() + ' is off.')

        # calculate the average on load and check if current load
        # is above the average
        if self.isApplianceOn:
            self.numberOfOnEntries += 1
            self.numberOfOnEntriesToday += 1

            # load measurement
            self.sumOnLoad += currentLoad
            self.sumOnLoadToday += currentLoad

            self.averageOnLoad = self.sumOnLoad / self.numberOfOnEntries
            self.averageOnLoadToday = self.sumOnLoadToday / self.numberOfOnEntriesToday

            # check for load spikes above the average load
            if not self.loadSpikeDetected and currentLoad > (self.averageOnLoad * 2.0):
                self.loadSpikeDetected = True
                currentTime = datetime.utcfromtimestamp(timestamp)

                if not isHistoricalData:
                    message = (
                        ">>>> LOAD SPIKE >>>> "
                        + str(currentTime)
                        + " "
                        + str(self.appliance)
                        + " load of "
                        + str(currentLoad)
                        + " is above average of "
                        + str(self.averageOnLoad)
                    )
                    print(message)
                    utils.send_report(self.deviceId, 'Your appliance {} is using more power than usual. Please check that your appliance is working correctly. High power usage can indicate faulty appliances.'.format(
                        str(self.appliance).title()), reportType=utils.REPORT_TYPE_WARNING)

        self.previousLoad = currentLoad
