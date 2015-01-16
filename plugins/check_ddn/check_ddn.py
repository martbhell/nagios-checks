#!/usr/bin/python
# Script to get useful monitoring info out of the API on a DDN SFA.
# To be used with nagios.
# As username / password is stored inside this file, make sure it's owned and readable as strictly as possible.
# API Reference Guide: http://ddntsr.com/u/sfaos-api_user_guide-9600325d.pdf
# Requires that Python26/27 and the corresponding DDN API Python Library Egg (and its dependencies, for example Twisted) to be installed. Ask DDN for download links of the eggs.
# Tested with SFA 1.5.3.0 and DDN_SFA_API-1.5.3.0.g_r12955-py2.6.egg
# Tested with SFA 2.2.1.3 and DDN_SFA_API-2.1.1.2.g_r18319-py2.6.egg
# Written by Johan Guldmyr @ CSC 2013-2014
# Version 0.1 Initial Release
# Version 0.2 Added additional checks to be run, attempt to determine where the errors are by checking controller, enclosures, ups and the unassigned pool.
# Version 0.3 Checking more places for errors.
# Version 0.4 Added exception handler to checking internal disks. Added checking RPs for pools for jobs.
# Version 0.5 Changed so that WARNING shows what the syschildhealth.str() is.
# Version 0.6 Added checking status of all the hosts (only if system state is WARNING / HEALTH_NON_CRITICAL).
# Version 0.7 Improve internaldiskcheck enclosure is now number 11 not 10. Also tested with SFAOS 2.1.1.2 and DDN_SFA_API-2.1.1.2.g_r18319-py2.6.egg
# Version 0.8 Improve several checks that gave exception when a controller is missing. Made this check require that one specifies two hostnames (each controller).
# Version 0.9 Added output when there are verify jobs running and also check hosts' status when system is critical.
# Version 0.10 Improve Presentation Health Checking. Added allhosts and allpresentations variables that has a list(?) of all the hosts/presentations in an SFA.
# Version 0.11 Changed wording from "a child is" to "a controller is". For HEALTH_NON_CRITICAL states of the controller.
# Version 0.12 Added check to check status of all the pools (also when they are non-critical) and print number of disks.
# Version 0.13 Temperature Sensor checking if going into HEALTH_NON_CRITICAL or CRITICAL. There are now several health checks in both non-critical and critical part. There's room for refactoring.
# Version 0.14 Also check the SESStatus of the sensor (this is what changes state if the temperature is too warm/cold).
# Version 0.15 Print more things about the sensor (location, current reading, warnings, failures, predictive failure)

from ddn.sfa.api import *
from ddn.sfa.core import *
#from ddn.sfa.status import *
import sys,os,socket

arglen=len(sys.argv)
arg0=str(sys.argv[0])
if ( arglen < 4) :
        print "Usage:"
        print arg0, "checkall hostname.or.ip.to.SFA hostname.or.ip.to.second.interface"
        exit(1)

arg1=str(sys.argv[1])
arg2=str(sys.argv[2])
arg3=str(sys.argv[3])

# Set username and password here. Host is grabbed from the 2nd argument sent to the script.
user="usernamehere"
password="passwordhere"
host="https://" + arg2

# Make sure the SFA is reachable before we continue.
unreachable = 0
ret = os.system("ping -q -c 1 -w 1 " + arg2 + ">/dev/null 2>&1")
ret1 = os.system("ping -q -c 1 -w 1 " + arg3 + ">/dev/null 2>&1")

if ret == 0:
         host="https://" + arg2
elif ret1 == 0:
         host="https://" + arg3
	 # So that we can give the message about arg2 being unreachable after HEALTH_CRITICAL
	 unreachable = 1 
# If both does not respond to ping then say that.
elif ret != 0 and ret1 != 0:
         print "CRITICAL:", arg2, "and", arg3, "are not pingable from", socket.gethostname()
         exit(2)
# If second host does not respond to ping
#if ret1 != 0:
#         print "CRITICAL:", arg3, "is not pingable from",
#         print socket.gethostname()
# If first host does not respond to ping
#if ret != 0:
#         print "CRITICAL:", arg2, "is not pingable from",
#         print socket.gethostname()

# host,user,password are the variables above.
APIConnect(host, auth=(user, password))

if "checkall" in arg1:
	# Start from top (the StorageSystem). 
	# One could go through all (or some of the) other subsystems to try to locate which child has an error.
	# HealthStates:
	# 0 == NA
	# 1 == OK
	# 2 == Non_Critical so exit(1) - Nagios Warning
	# 3 == Critical
	# 255 == Unknown
	sysname = SFAStorageSystem.get(Index=0).Name
	syshealth = SFAStorageSystem.get(Index=0).HealthState.str()
	syschildhealth = SFAStorageSystem.get(Index=0).ChildHealthState
	#syschildhealth = 2
	allhosts = SFAStack.get(Index=0).getHosts()
	allpresentations = SFAStack.get(Index=0).getPresentations()
	missingctrl = 0
	if syschildhealth == 1:
		print "OK:", syshealth, ":", sysname
		if unreachable != 0:
	 		print "Using", arg3, "because", arg2, "is unreachable from", socket.gethostname()
		APIDisconnect()
		exit(0)
	elif syschildhealth == 2:
#		print "WARNING: a controller is", syschildhealth.str(), ":", sysname
		if unreachable != 0:
	 		print "Using", arg3, "because", arg2, "is unreachable from", socket.gethostname()

		## An initiators go CRITICAL if their path is down.
		# This causes the system to go into HEALTH_NON_CRITICAL
		for host in allhosts:
			hosthealth = host.HealthState
			if hosthealth != 1:
				print "Host", host.Name, "is", host.HealthState.str()

		## Check states of pools

                # Find pools
                # If there is a missing ctrl, we're missing two RPs
                missingrp = 0
                raidprocessors = 4
                if missingctrl == 1:
                        missingrp = missingctrl * 2
                        raidprocessors = raidprocessors - missingrp

                for i in range(0,raidprocessors):
                        lepool = SFARAIDProcessor.get(Index=i).getStoragePools()
                        #lepool is a list of all pools in this RP
			# i is the SFAStoragePool class
                        for i in lepool:
                                try:
                                        poolstate = i.PoolState
					if poolstate != 0:
						print i.Name, "is in status", i.PoolState.str(), "and it has", i.NumDisks, "disks assigned."
                                except Exception as e:
                                        # print "Error", e
                                        continue

                ## Enclosures
                numberofenclosures = 12
                if missingctrl != 0:
                        numberofenclosures = numberofenclosures - missingctrl
                for i in range(0,numberofenclosures):
                        enclchildhealth = SFAEnclosure.get(Index=i).ChildHealthState
                        enclname = SFAEnclosure.get(Index=i).ElementName
			# Also check all temperature sensors in each enclosure.
                        lesensors = SFAEnclosure.get(Index=i).getTemperatureSensors()
                        #lesensors is a list of all temperature sensors in this enclosure
                        for sensor in lesensors:
                                try:
                                        sensorhealth = sensor.HealthState
                                        sesstatus = sensor.SESStatus
					sensorlocation = sensor.Location
					sensorcurrentreading = sensor.CurrentReading
					sensortempfailure = sensor.TemperatureFailure
					sensortempwarning = sensor.TemperatureWarning
					sensorpredictfailure = sensor.PredictFailure
                                        if sensorhealth != 1:
                                                print sensor.ElementName, "in", sensorlocation, "is in status", sensorhealth.str(), "SESStatus:", sesstatus.str(), "Current Reading:", sensorcurrentreading, "tempfailure:", sensortempfailure, "tempwarning:", sensortempwarning, "predict failure:", sensorpredictfailure
                                except Exception as e:
                                        # print "Error", e
                                        continue


		APIDisconnect()
		exit(1)
	else:
		print "CRITICAL:", syschildhealth.str(), ":", sysname
		print "A child of StorageSystem is critical."
		# unreachable is set to 1 if ping to arg2 fails.
		if unreachable != 0:
	 		print "CRITICAL: Using", arg3, "because", arg2, "is unreachable from", socket.gethostname()
#		print "Check DDN CLI for more details."
#		print "For example: show job"

		### Check underlying components for non-1 childhealthstates:
		## Controllers themselves.
		try: 
			ctrl0health = SFAController.get(Index=0).HealthState
			if ctrl0health != 1:
				print "Problem with Ctrl 0"
		except APIException:
			print "APIException with ctrl1health, ctrl1 missing?"
			missingctrl += 1
		try: 
			ctrl1health = SFAController.get(Index=1).HealthState
			if ctrl1health != 1:
				print "Problem with Ctrl 1"
		except APIException:
			print "APIException with ctrl1health, ctrl1 missing?"
			missingctrl += 1
		## Children of controllers.
		ctrl0childhealth = SFAController.get(Index=0).ChildHealthState
		if ctrl0childhealth != 1:
			print "Problem with child of Ctrl 0"
		try:
			ctrl1childhealth = SFAController.get(Index=1).ChildHealthState
			if ctrl1childhealth != 1:
				print "Problem with child of Ctrl 1"
		except APIException:
			print "APIexception with ctrl1childhealth, ctrl1 missing?"

		## Enclosures
		numberofenclosures = 12
		if missingctrl != 0:
			numberofenclosures = numberofenclosures - missingctrl
		for i in range(0,numberofenclosures):
			enclchildhealth = SFAEnclosure.get(Index=i).ChildHealthState
			enclname = SFAEnclosure.get(Index=i).ElementName
			lesensors = SFAEnclosure.get(Index=i).getTemperatureSensors()
                        #lesensors is a list of all temperature sensors in this enclosure
			for sensor in lesensors:
				try:
                                        sensorhealth = sensor.HealthState
                                        sesstatus = sensor.SESStatus
                                        sensorlocation = sensor.Location
                                        sensorcurrentreading = sensor.CurrentReading
                                        sensortempfailure = sensor.TemperatureFailure
                                        sensortempwarning = sensor.TemperatureWarning
                                        sensorpredictfailure = sensor.PredictFailure
                                        if sensorhealth != 1:
                                                print sensor.ElementName, "in", sensorlocation, "is in status", sensorhealth.str(), "SESStatus:", sesstatus.str(), "Current Reading:", sensorcurrentreading, "tempfailure:", sensortempfailure, "tempwarning:", sensortempwarning, "predict failure:", sensorpredictfailure

				except Exception as e:
					# print "Error", e
					continue

			if enclchildhealth != 1:
				print "Problem in", enclname
		## UPS
		upschildhealth = SFAUPS.get(Index=1, EnclosureIndex=0).ChildHealthState
		if upschildhealth != 1:
			print "Problem with UPS"

		## Unassigned Pool (where failed disks go)
	        unassnumdisks = SFAUnassignedPool.get(Index=0).NumDisks
        	unasschildhealth = SFAUnassignedPool.get(Index=0).ChildHealthState
	        if unasschildhealth != 1:
			if unassnumdisks == 1:
       				print "There is", unassnumdisks, "unassigned disk."
			elif unassnumdisks > 1:
       				print "There are", unassnumdisks, "unassigned disks."

		## Internal disks
		for i in range(1,4):
#			print i
			try:
				intdisks = SFAInternalDiskDrive.get(Index=i, EnclosureIndex=0).HealthState
			except APIException:
				#Error hopefully that disk is not found, setting it to 1
				print "APIException with intdisks"
				intdisks = 1
			try:
				intencl11disks = SFAInternalDiskDrive.get(Index=i, EnclosureIndex=11).HealthState
			except APIException:
				print "APIException with intencl11disks"
				intencl11disks = 1
			if intdisks != 1:
				print "Problem with an internal disk in ctrl enclosure 0"
			if intencl11disks != 1:
				print "Problem with an internal disk in ctrl enclosure 11"

		## Pools and Jobs
		# Iterate over all raid processors and get a list of pools in each.
		# Iterate over all pools and getActiveJob().type.
	
		verjobs = 0
		otherjobs = 0
		# Find pools

		# If there is a missing ctrl, we're missing two RPs
		missingrp = 0
		raidprocessors = 4
		if missingctrl == 1:
			missingrp = missingctrl * 2
			raidprocessors = raidprocessors - missingrp
		
		for i in range(0,raidprocessors):
			lepool = SFARAIDProcessor.get(Index=i).getStoragePools()
			#lepool is a list of all pools in this RP
			for i in lepool:
				try:
					ajob = i.getActiveJob().Type
					# ajob gets the activejob on a pool
					# 9 == verify job
					if ajob == 9:
						verjobs = verjobs + 1
					else:
						otherjobs = otherjobs + 1
				except Exception as e:
					# Exception catcher probably not needed with getActiveJob
					# Was needed with getJobOID that was empty/unassigned if no job existed.
					# print "Error", e
					continue

		# This part is identical/copy-paste to what is when ctrl is non-critical. Should be factorized..
                                try:
                                        poolstate = i.PoolState
                                        if poolstate != 0:
                                                print i.Name, "is in status", i.PoolState.str(), "and it has", i.NumDisks, "disks assigned."
                                except Exception as e:
                                        # print "Error", e
                                        continue
		## End of iteration through raid processors looking for pools.

		totjobs = verjobs + otherjobs

		if totjobs > 0:
			if otherjobs > 0 and verjobs > 0:
				print "There are", otherjobs, "non-verify and", verjobs, "verify jobs running."
			if otherjobs > 0 and verjobs == 0:
				print "There are", otherjobs, "non-verify jobs running."
			if otherjobs == 0 and verjobs > 0:
				print "There are", verjobs, "verify jobs running."

		## Hosts in critical? (same check under WARNING / HEALTH_NON_CRITICAL)
                for host in allhosts:
                        hosthealth = host.HealthState
                        if hosthealth != 1:
                                print "Host", host.Name, "is", host.HealthState.str()

		# Disconnect.
		APIDisconnect()
		exit(2)

else:
	APIDisconnect()
        print "Usage:"
        print arg0, "checkall hostname.or.ip.to.SFA hostname.or.ip.to.second.interface"
	exit(3)

APIDisconnect()

exit()
