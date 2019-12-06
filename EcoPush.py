""" EcoPush """
import pandas as pd
import json
import hart_85 as algo
import requests
from datetime import datetime
import os
import utils


class MonitoringSystem:

    def __init__(self, ecoPushConfig):
        self.deviceId = ecoPushConfig['deviceId'] or 1234
        self.appliance = ecoPushConfig['appliance'] or 'unknown'
        self.sumOnLoad = 0
        self.sumOnLoadToday = 0
        self.numberOfOnEntries = 0
        self.numberOfOnEntriesToday = 0
        self.previousLoad = 0
        self.isApplianceOn = False
        self.loadSpikeDetected = False
        self.ghostLoad = ecoPushConfig['ghostLoad'] or 50
        self.switchedOnCount = 0
        self.switchedOnCountToday = 0
        self.sumOnRunningTime = 0
        self.applianceRunningTimeStart = 0
        self.previousDate = None
        self.averageOnLoad = 0
        self.averageOnLoadToday = 0
        self.previousAverageOnLoad = 0
        self.outputMessage = ''

    def output(self, text):
        # print('EcoPush.py: {}'.format(text))
        print('{}'.format(text))

    def import_historical_data(self, currentLoad, timestamp):
        self.analyse_data(currentLoad=currentLoad, timestamp=timestamp, isHistoricalData=True)            

    def calculate_end_of_day_metrics(self, timestamp):

        currentDate = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d')

        if self.previousDate is None:
            self.previousDate = currentDate

        if currentDate != self.previousDate:

            if self.previousAverageOnLoad != 0:
                percentageChange = round(((self.averageOnLoadToday - self.previousAverageOnLoad) / self.previousAverageOnLoad) * 100, 2)
                
                self.output('{} was switched on {} times today'.format(self.appliance, self.switchedOnCountToday))

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
            self.switchedOnCountToday = 0

    def analyse_data(self, currentLoad, timestamp, isHistoricalData=False):
        
        self.calculate_end_of_day_metrics(timestamp)
        
        if not self.isApplianceOn and currentLoad > self.ghostLoad:
            self.isApplianceOn = True
            self.switchedOnCount += 1
            self.switchedOnCountToday += 1

            self.applianceRunningTimeStart = timestamp
            utc_dt = datetime.utcfromtimestamp(self.applianceRunningTimeStart)
            dateresult = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d')
            timeresult = datetime.utcfromtimestamp(timestamp).strftime('%H:%M:%S')

            if not isHistoricalData:
                # self.output("{} {} is on".format(utc_dt, self.appliance))
                # self.output("{},{},{},on".format(dateresult, timeresult, self.appliance))
                self.outputMessage = "{},{},{},ON,".format(dateresult, timeresult, self.appliance)

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

            dateresult = datetime.utcfromtimestamp(applianceRunningTimeEnd).strftime('%Y-%m-%d')
            timeresult = datetime.utcfromtimestamp(applianceRunningTimeEnd).strftime('%H:%M:%S')

            # if running time is 50% above the average
            if runningTime > (averageOnRunningTime * 2.0) and not isHistoricalData:                               
                  
                # self.output("{} {} is running for a long time. >>>> RUNNING TIME SPIKE <<<<".format(utc_dt, self.appliance))
                self.output("{},{},{},RUNNING TIME SPIKE".format(dateresult, timeresult, self.appliance))
                utils.send_report(self.deviceId, 'Your appliance {} has been running for longer than usual. You may have forgotten to turn if off.'.format(str(self.appliance).title()), reportType=utils.REPORT_TYPE_WARNING)

            if not isHistoricalData:
                # self.output("{} {} is off".format(utc_dt, self.appliance))
                self.outputMessage += "{},{},{},OFF,{}".format(dateresult, timeresult, self.appliance, runningTime)
                print(self.outputMessage)            
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
            if not self.loadSpikeDetected and currentLoad > (self.averageOnLoad * 10.0):
                self.loadSpikeDetected = True
                currentTime = datetime.utcfromtimestamp(timestamp)

                if not isHistoricalData:               
                    dateresult = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d')
                    timeresult = datetime.utcfromtimestamp(timestamp).strftime('%H:%M:%S')       
                    # self.output("{} {} power usage has spiked. >>>> LOAD SPIKE <<<<".format(utc_dt, self.appliance))
                    self.output("{},{},{},LOAD SPIKE".format(dateresult, timeresult, self.appliance))
                    utils.send_report(self.deviceId, 'Your appliance {} is using more power than usual. Please check that your appliance is working correctly. High power usage can indicate faulty appliances.'.format(str(self.appliance).title()), reportType=utils.REPORT_TYPE_WARNING)

        self.previousLoad = currentLoad
