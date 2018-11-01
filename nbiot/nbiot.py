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
	board = "" # Shield name
	ip_address = "" # ip address       
	domain_name = "" # domain name   
	port_number = "" # port number 
	timeout = TIMEOUT # default timeout for function and methods on this library.
	
	compose = ""
	response = ""

	SCRAMBLE_ON = "TRUE"
	SCRAMBLE_OFF = "FALSE"

	AUTO_ON = "TRUE"
	AUTO_OFF = "FALSE"
	
	# Default Initializer
	def __init__(self, serial_port="/dev/ttyS0", serial_baudrate=9600, board="Sixfab NB-IoT Shield"):
		
		self.board = board
    	
		ser.port = serial_port
		ser.baudrate = serial_baudrate
		ser.parity=serial.PARITY_NONE
		ser.stopbits=serial.STOPBITS_ONE
		ser.bytesize=serial.EIGHTBITS
		
		GPIO.setmode(GPIO.BCM)
		GPIO.setwarnings(False)
		
		GPIO.setup(RESET,GPIO.OUT)
		GPIO.output(RESET,GPIO.LOW)
		
		debug_print(self.board + " Class initialized!")
	
	# Function for clearing compose variable
	def clear_compose(self):
		self.compose = ""
		
	# Function for getting modem response
	def getResponse(self, desired_response):
		if (ser.isOpen() == False):
			ser.open()
			
		while 1:	
			self.response =""
			while(ser.inWaiting()):
				self.response += ser.read(ser.inWaiting()).decode('utf-8', errors='ignore')
			if(self.response.find(desired_response) != -1):
				debug_print(self.response)
				break
				
	# Function for sending at comamand to module
	def sendATCommOnce(self, command):
		if (ser.isOpen() == False):
			ser.open()		
		self.compose = ""
		self.compose = str(command) + "\r"
		ser.reset_input_buffer()
		ser.write(self.compose.encode())
		debug_print(self.compose)

	# Function for sending at command to BC95_AT.
	def sendATComm(self, command, desired_response, timeout = None):
		
		if timeout is None:
			timeout = self.timeout
			
		self.sendATCommOnce(command)
		
		f_debug = False
		
		timer = millis()
		while 1:
			if( millis() - timer > timeout): 
				self.sendATCommOnce(command)
				timer = millis()
				f_debug = False
			
			self.response =""
			while(ser.inWaiting()):
				try: 
					self.response += ser.read(ser.inWaiting()).decode('utf-8', errors='ignore')
					delay(100)
				except Exception as e:
					debug_print(e.Message)
				# debug_print(self.response)
					
			if(self.response.find(desired_response) != -1):
				debug_print(self.response)
				break

	# Function for saving conf. and reset BC95_AT module
	def resetModule(self):
		self.saveConfigurations()
		delay(200)
		self.sendATComm("AT+NRB","")


	# Function for save configurations tShield be done in current session. 
	def saveConfigurations(self):
		self.sendATComm("AT&W","OK\r\n")

	# Function for getting IMEI number
	def getIMEI(self):
		return self.sendATComm("AT+CGSN=1","OK\r\n")


	# Function for getting firmware info
	def getFirmwareInfo(self):
		return self.sendATComm("AT+CGMR","OK\r\n")

	# Function for getting hardware info
	def getHardwareInfo(self):
		return self.sendATComm("AT+CGMM","OK\r\n")

	# Function for setting autoconnect feature configuration 
	def setAutoConnectConf(self, autoconnect):
		self.compose = "AT+NCONFIG=AUTOCONNECT,"
		self.compose += autoconnect

		self.sendATComm(self.compose,"OK\r\n")
		self.clear_compose()

	# Function for setting scramble feature configuration 
	def setScrambleConf(self, scramble):
		self.compose = "AT+NCONFIG=CR_0354_0338_SCRAMBLING,"
		self.compose += scramble

		self.sendATComm(self.compose,"OK\r\n")
		self.clear_compose()

	# Function for getting self.ip_address
	def getIPAddress(self):
		return self.ip_address

	# Function for setting self.ip_address
	def setIPAddress(self, ip):
		self.ip_address = ip

	# Function for getting self.domain_name
	def getDomainName(self):
		return self.domain_name

	# Function for setting domain name
	def setDomainName(self, domain):
		self.domain_name = domain

	# Function for getting port
	def getPort(self):
		return self.port_number

	# Function for setting port
	def setPort(self, port):
		self.port_number = port

	# Function for getting timout in ms
	def getTimeout(self):
		return self.timeout

	# Function for setting timeout in ms    
	def setTimeout(self, new_timeout):
		self.timeout = new_timeout


	#******************************************************************************************
	#*** Network Service Functions ************************************************************
	#****************************************************************************************** 

	# Function for getting signal quality
	def getSignalQuality(self):
		return self.sendATComm("AT+CSQ","OK\r\n")

	# Function for connecting to base station of operator
	def connectToOperator(self):
		debug_print("Trying to connect base station of operator...")
		self.sendATComm("AT+CGATT=0","OK\r\n",8) # with 8 seconds timeout
		delay(1000)
		self.sendATComm("AT+CGATT=1","OK\r\n",8) # with 8 seconds timeout
		delay(2000)
		debug_print("Wait until getting <CGATT:1> response..." )
		self.sendATComm("AT+CGATT?","+CGATT:1\r\n")


	#******************************************************************************************
	#*** UDP Protocols Functions ********************************************************
	#******************************************************************************************
	
	# Function for connecting to server via UDP
	def startUDPService(self):
		port = "3005"

		self.compose = "AT+NSOCR=DGRAM,17,"
		self.compose += str(self.port_number)
		self.compose += ",0"

		self.sendATComm(self.compose,"OK\r\n")
		self.clear_compose()

	# Fuction for sending data via udp.
	def sendDataUDP(self, data):
		self.compose = "AT+NSOST=0,"
		self.compose += str(self.ip_address)
		self.compose += ","
		self.compose += str(self.port_number)
		self.compose += ","
		self.compose += str(len(data))
		self.compose += ","
		self.compose += hex(data)

		self.sendATComm(self.compose,"\r\n")
		self.clear_compose()

	# Function for closing server connection
	def closeConnection(self):
		self.sendATComm("AT+NSOCL=0","\r\n")
			
	# Function for reading accelerometer
	def readAccel(self):
		mma = MMA8452Q()
		return mma.readAcc()
 
	# Function for reading ADC
	def readAdc(self, channelNumber):
		''' Only use 0,1,2,3(channel Number) for readAdc(channelNumber) function '''
		adc=ADS1015(address=0x49, busnum=1)
		adcValues = [0] * 4
		adcValues[channelNumber] = adc.read_adc(channelNumber, gain=1)
		return adcValues[channelNumber]

	# Function for reading temperature
	def readTemp(self):
		hdc1000 = SDL_Pi_HDC1000()
		hdc1000.setTemperatureResolution(HDC1000_CONFIG_TEMPERATURE_RESOLUTION_14BIT)
		return  hdc1000.readTemperature()

	# Function for reading humidity
	def readHum(self):
		hdc1000 = SDL_Pi_HDC1000()
		hdc1000.setHumidityResolution(HDC1000_CONFIG_HUMIDITY_RESOLUTION_14BIT)
		return hdc1000.readHumidity()

	# Function for reading light resolution	
	def readLux(self):
		adc=ADS1015(address=0x49, busnum=1)
		rawLux = adc.read_adc(LUX_CHANNEL, gain=1)
		lux = (rawLux * 100) / 1580
		return lux

	# Function for turning on relay
	def turnOnRelay(self):
		GPIO.setup(RELAY, GPIO.OUT)
		GPIO.output(RELAY, 1)

	# Function for turning off relay
	def turnOffRelay(self):
		GPIO.setup(RELAY, GPIO.OUT)
		GPIO.output(RELAY, 0)

	# Function for reading user button
	def readUserButton(self):
		GPIO.setup(USER_BUTTON, GPIO.IN)
		return GPIO.input(USER_BUTTON)

	# Function for turning on user LED
	def turnOnUserLED(self):
		GPIO.setup(USER_LED, GPIO.OUT)
		GPIO.output(USER_LED, 1)

	# Function for turning off user LED
	def turnOffUserLED(self):
		GPIO.setup(USER_LED, GPIO.OUT)
		GPIO.output(USER_LED, 0)
