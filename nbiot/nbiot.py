'''
  Sixfab_RPi_NBIoT_Library 
  -
  Library for Sixfab RPi NBIoT Shield.
  -
  Created by Yasin Kaya (selengalp), September 19, 2018.
'''

import time
import serial
import RPi.GPIO as GPIO
from Adafruit_ADS1x15 import ADS1015
from .SDL_Pi_HDC1000 import *
from .MMA8452Q import MMA8452Q

# Peripheral Pin Definations
USER_BUTTON = 21
USER_LED = 20
RESET = 16
RELAY = 26
OPTO1 = 12
OPTO2 = 5
VDD_EXT = 6
LUX_CHANNEL = 0

SCRAMBLE_ON = "TRUE"
SCRAMBLE_OFF = "FALSE"

AUTO_ON = "TRUE"
AUTO_OFF = "FALSE"

# global variables
TIMEOUT = 3 # seconds
ser = serial.Serial()

###########################################
### Private Methods #######################
###########################################

# function for printing debug message 
def debug_print(message):
	print(message)

# function for getting time as miliseconds
def millis():
	return int(time.time())

# function for delay as miliseconds
def delay(ms):
	time.sleep(float(ms/1000.0))

###########################################
### NB IoT Shield Class ################
###########################################	
class NBIoT:
	board = "" # Shield name (NB IoT or NB IoT App.)
	ip_address = "" # ip address       
	domain_name = "" # domain name   
	port_number = "" # port number 
	timeout = TIMEOUT # default timeout for function and methods on this library.
	
	SCRAMBLE_ON = "0"
	SCRAMBLE_OFF = "1"
	
	def __init__(self, serial_port="/dev/ttyS0", serial_baudrate=115200, board="Sixfab NB IoT Shield"):
		
		self.board = board
    	
		ser.port = serial_port
		ser.baudrate = serial_baudrate
		ser.parity=serial.PARITY_NONE
		ser.stopbits=serial.STOPBITS_ONE
		ser.bytesize=serial.EIGHTBITS
		
		GPIO.setmode(GPIO.BCM)
		GPIO.setwarnings(False)
		GPIO.setup(BC95_ENABLE, GPIO.OUT)
			
		debug_print(self.board + " Class initialized!")
 
	def enable(self):
		GPIO.output(BC95_ENABLE,1)
		debug_print("BC95 module enabled!")

	# power down BC95 module and all peripherals from voltage regulator 
	def disable(self):
		GPIO.output(BC95_ENABLE,0)
		debug_print("BC95 module disabled!")
		
	# send at comamand to module
	def sendATCommOnce(self, command):
		if (ser.isOpen() == False):
			ser.open()		
		compose = ""
		compose = "\r\n" + str(command) + "\r\n"
		ser.reset_input_buffer()
		ser.write(compose.encode())
		debug_print(compose)

	# function for sending at command to BC95_AT.
	def sendATComm(self, command, desired_response):
		
		self.sendATCommOnce(command)
		
		timer = millis()
		while 1:
			if( millis() - timer > self.timeout): 
				self.sendATCommOnce(command)
				timer = millis()
			
			response =""
			while(ser.inWaiting()):
				response += ser.read(ser.inWaiting()).decode('utf-8')
			if(response.find(desired_response) != -1):
				debug_print(response)
				ser.close()
				break

	# function for saving conf. and reset BC95_AT module
	def resetModule(self):
		self.saveConfigurations()
		delay(200)
		self.disable()
		delay(200)
		self.enable()

	# Function for save configurations tShield be done in current session. 
	def saveConfigurations(self):
		self.sendATComm("AT&W","OK\r\n")

	# Function for getting IMEI number
	def getIMEI(self):
		return self.sendATComm("AT+CGSN","OK\r\n")


	# Function for getting firmware info
	def getFirmwareInfo(self):
		return self.sendATComm("AT+CGMR","OK\r\n")

	# Function for getting hardware info
	def getHardwareInfo(self):
		return self.sendATComm("AT+CGMM","OK\r\n")

	# Function for setting autoconnect feature configuration 
	def setAutoConnectConf(self, autoconnect):
		compose = "AT+QCFG=AUTOCONNECT,"
		compose += autoconnect

		self.sendATComm(compose,"OK\r\n")

	# Function for setting scramble feature configuration 
	def setScrambleConf(self, scramble):
		compose = "AT+QCFG=CR_0354_0338_SCRAMBLING,"
		compose += scramble

		self.sendATComm(compose,"OK\r\n")

	# function for getting self.ip_address
	def getIPAddress(self):
		return self.ip_address

	# function for setting self.ip_address
	def setIPAddress(self, ip):
		self.ip_address = ip

	# function for getting self.domain_name
	def getDomainName(self):
		return self.domain_name

	# function for setting domain name
	def setDomainName(self, domain):
		self.domain_name = domain

	# function for getting port
	def getPort(self):
		return self.port_number

	# function for setting port
	def setPort(self, port):
		self.port_number = port

	# get timout in ms
	def getTimeout(self):
		return self.timeout

	# set timeout in ms    
	def setTimeout(self, new_timeout):
		self.timeout = new_timeout


	#******************************************************************************************
	#*** Network Service Functions ************************************************************
	#****************************************************************************************** 

	# 
	def getSignalQuality(self):
		return self.sendATComm("AT+CSQ","OK\r\n")

	# connect to base station of operator
	def connectToOperator(self):
		debug_print("Trying to connect base station of operator...")
		self.sendATComm("AT+CGATT=1","OK\r\n")
		delay(500)
		self.sendATComm("AT+CGATT?","+CGATT:1\r\n")

		self.getSignalQuality()


	#******************************************************************************************
	#*** UDP Protocols Functions ********************************************************
	#******************************************************************************************
	
	# function for connecting to server via UDP
	def startUDPService(self):
		port = "3005"

		compose = "AT+NSOCR=DGRAM,17,"
		compose += str(self.port_number)
		compose += ",0"

		self.sendATComm(compose,"OK\r\n")

	# fuction for sending data via udp.
	def sendDataUDP(self, data):
		compose = "AT+NSOST=0,"
		compose += str(self.ip_address)
		compose += ","
		compose += str(self.port_number)
		compose += ","
		compose += str(len(data))
		compose += ","
		compose += hex(data)

		self.sendATComm(compose,"\r\n")

	#function for closing server connection
	def closeConnection(self):
		self.sendATComm("AT+NSOCL=0","\r\n")
			
	# 
	def readAccel(self):
		mma = MMA8452Q()
		return mma.readAcc()
 
	#
	def readAdc(self, channelNumber):
		''' Only use 0,1,2,3(channel Number) for readAdc(channelNumber) function '''
		adc=ADS1015(address=0x49, busnum=1)
		adcValues = [0] * 4
		adcValues[channelNumber] = adc.read_adc(channelNumber, gain=1)
		return adcValues[channelNumber]

	#
	def readTemp(self):
		hdc1000 = SDL_Pi_HDC1000()
		hdc1000.setTemperatureResolution(HDC1000_CONFIG_TEMPERATURE_RESOLUTION_14BIT)
		return  hdc1000.readTemperature()

	# 
	def readHum(self):
		hdc1000 = SDL_Pi_HDC1000()
		hdc1000.setHumidityResolution(HDC1000_CONFIG_HUMIDITY_RESOLUTION_14BIT)
		return hdc1000.readHumidity()

	#	
	def readLux(self):
		adc=ADS1015(address=0x49, busnum=1)
		rawLux = adc.read_adc(LUX_CHANNEL, gain=1)
		lux = (rawLux * 100) / 1580
		return lux

	#
	def turnOnRelay(self):
		GPIO.setup(RELAY, GPIO.OUT)
		GPIO.output(RELAY, 1)

	#
	def turnOffRelay(self):
		GPIO.setup(RELAY, GPIO.OUT)
		GPIO.output(RELAY, 0)

	#
	def readUserButton(self):
		GPIO.setup(USER_BUTTON, GPIO.IN)
		return GPIO.input(USER_BUTTON)

	#
	def turnOnUserLED(self):
		GPIO.setup(USER_LED, GPIO.OUT)
		GPIO.output(USER_LED, 1)

	#
	def turnOffUserLED(self):
		GPIO.setup(USER_LED, GPIO.OUT)
		GPIO.output(USER_LED, 0)
