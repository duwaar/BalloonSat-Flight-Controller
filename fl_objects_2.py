#!/usr/bin/python3.4
'''
This is the flight controller program for a high-altitude balloon.
The classes contained herein allow for easy interface with various
digital and analog sensors.

Russell Jeffery
4 August 2016
'''

import RPi.GPIO as GPIO
import picamera
from gps3 import agps3
from os import system, popen
from time import time, sleep, asctime

#All classes defined herein use the board numbering system.
GPIO.setmode(GPIO.BOARD)

class Sensor(object):
    #######################################################
    '''
    Because it simplifies the flight controller code if I can treat
    all the sensors the same (using the same methods), I made this
    base class so the code doesn't crash if I make the mistake of
    calling a method I have not defined.

    Some of these methods, you will notice, have no explanations.
    For explanations of what these methods are meant to do, see the
    comments on the specific subclass you are interested in.
    '''
    #######################################################

    def __init__(self, name='default'):
        print('There is no class defined for', name)

    def _name_file(self):
        #----------------------------------------
        '''
        _name_file() -> string

        Generates a string that consists of the name of the sensor,
        plus a timestamp.
        '''
        #----------------------------------------

        #Get the timestamp and replace " " with "_".
        date = asctime().replace(' ', '_')
        file_name = self.name + '_data_' + date + '.txt'

        return file_name


    def start(self):
        print('Method not defined for this subclass.')

    def get(self):
        print('Method not defined for this subclass.')

    def read(self):
        #----------------------------------------
        '''
        You should not use this method. I include it here only to
        ease debugging.
        '''
        #----------------------------------------
        print('Obslete method.')

    def write(self):
        print('Method not defined for this subclass.')

    def stop(self):
        print('Method not defined for this subclass.')


class AnalogSensor(Sensor):
    #######################################################
    '''
    Several of my sensors produce some kind of analog output, so I
    decided that having this class would make the code look nicer.
    '''
    ########################################################

    def __init__(self, name, Vref, CLK, Dout, Din, CS, pin=[0,0,0], offset=0, slope=1):
        #----------------------------------------
        '''
        AnalogSensor(string, float, pin, pin, pin, pin, 3-element list, 2-element list) -> sensor object

        --Name:     The sensor name that will appear in the title of the data file.
        --Pin:      The channel of the MCP3008 to which the sensor will be connected. (see datasheet)
        --Vref:     The voltage applied to the reference pin of the MCP3008 (see datasheet)

        Assuming that the relationship between voltage and the desired unit is linear.
        --slope:    The slope of the relationship (found in a datasheet or through calibration).
        --offset:   The offset of the relationship (found in a datasheet or through calibration).
        '''
        #----------------------------------------

        #self.pin will correspond to the ADC pins of each temp sensor.
        self.name = name
        self.pin = pin
        self.Vref = Vref

        #These are the same pin names used in the MCP3008 datasheet.
        self.CLK = CLK
        GPIO.setup(self.CLK, GPIO.OUT)
        self.Dout = Dout
        GPIO.setup(self.Dout, GPIO.IN)
        self.Din = Din
        GPIO.setup(self.Din, GPIO.OUT)
        self.CS = CS
        GPIO.setup(self.CS, GPIO.OUT)

        #These are for unit convertions.
        self.slope = slope
        self.offset = offset


    def _clk(self):
        #----------------------------------------
        '''
        _clk() -> clock pin set high, then low

        This makes the code a bit cleaner.
        '''
        #----------------------------------------

        GPIO.output(self.CLK, True)
        GPIO.output(self.CLK, False)
        sleep(0.0001)


    def _read_chip(self):
        #----------------------------------------
        '''
        _read_chip() -> floating point number

        Talks serial to the ADC chip MCP3008 and returns
        the voltage applied to the specified pin.
        '''
        #----------------------------------------

        #From the datasheet: "The first clock received with self.CS low
        #and self.Din high will constitute a start bit."
        GPIO.output(self.CS, False)
        GPIO.output(self.Din, True)
        sleep(0.0002)
        self._clk()

        #The next four input bits tell the chip how to measure the
        #analog input voltage. The first determines single/diff,
        #and the next three tell which pin/pins to read from.
        command = [1] #1 => single-ended. pin number to follow.
        for i in self.pin:
            command.append(i) #add the pin address to the command

        #now read in the command
        for bit in command:
            GPIO.output(self.Din, bit) #set the input
            self._clk() #clock that pupper in

        #". . . One more clock is required to complete the sample and hold period."
        self._clk()

        #clear the binary buffer
        binary = ''
        #The next 10 clocks will output the result of the conversion with MSB first . . . "
        for bit in range(10):
            self._clk()
            if GPIO.input(self.Dout) == True:
                binary = binary + '1'
            else:
                binary = binary + '0'

        #turn the chip off
        GPIO.output(self.CS, True)

        #int converts the binary to a decimal. 1023 is the max decimal from the ADC.
        ratio = int(binary, 2) / 1023
        voltage = ratio * self.Vref #self.Vref is the voltage represented by the 1023 output.

        return voltage


    def _avg_calc(self):
        #----------------------------------------
        '''
        _avg_calc() -> floating point number

        This takes 100 readings from the sensor and returns the mean.
        '''
        #----------------------------------------

        Vavg = 0
        for i in range(100):
            #get the ratio on pin 0
            voltage = _read_chip(self.pin, self.Vref)
            #add last measurement to the running average
            Vavg = Vavg + voltage

        #calculate the average
        Vavg = round((Vavg / 100), 2)

        return Vavg


    def _name_file(self):
        #----------------------------------------
        '''
        _name_file(self) -> string

        This generates a date string and adds that
        to the file name to prevent accidental overwrites.
        '''
        #----------------------------------------

        #the following makes a file with the date in the name to *hopefully* help prevent overwrites.
        date = asctime() #asctime() returns the date/time as a string with spaces.
        date = date.replace(' ', '_') #make it more file-name friendly.
        file_name = self.name + '_data_' + date + '.txt' #stick the date/time str into the file name

        return file_name


    def _volts_to_unit(self, volts):
        #----------------------------------------
        '''
        _volts_to_unit(volts) -> float

        This is the function that converts the voltage from the ADC
        to units of pressure, temperature, etc.
        '''
        #----------------------------------------

        units = volts * self.slope - self.offset
        return units
 
    def start(self):
        #----------------------------------------
        '''
        start()

        This creates the data variables and the data file.
        '''
        #----------------------------------------

        #open a file for the data
        self.file_name = self._name_file()
        self.data_file = open(self.file_name, 'a')
        self.data_file.write('\nNew data.\n\n')
        self.data_file.close()

        print(self.name, 'has started.')


    def get(self):
        #----------------------------------------
        '''
        get() -> float

        Return a sensor reading. This is used to collect
        a point of data, or to pull a reading out and use
        it for something else (i.e. get the temperature
        inside the payload for the heater controller).
        '''
        #----------------------------------------

        #This reads the binary from the ADC chip.
        raw = self._read_chip()

        #This converts the binary into human-readable, decimal units.
        volts = self._volts_to_unit(raw)

        #And here is what you get.
        return volts

       
    def write(self):
        #----------------------------------------
        '''
        write()

        Gets a reading and writes it to a file.
        '''
        #----------------------------------------

        #Open the file.
        self.data_file = open(self.file_name, 'a')

        #collect the data.
        volts = self.get()

        #write the data to the data file.
        datum = str(asctime()) + ',' + str(volts) + '\n'
        self.data_file.write(datum)
        self.data_file.close()


    def stop(self):
        #----------------------------------------
        '''
        stop()

        Prints a shutdown message to standard out.
        '''
        #----------------------------------------

        print(self.name, 'has finished.')


class CountSensor(Sensor):
    #######################################################
    '''
    The GeigerCounter is set up to monitor a pin by waiting for
    a pulse. It counts these pulses and writes the count to a file.

    * * * * * IMPORTANT * * * * *
    I have not figured out how to do this without global variables.
    That means that you can only have ONE counter sensor per payload.
    '''
    ########################################################

    def __init__(self, name, pin):

        #set up the I/O pin
        self.signalPin = pin
        GPIO.setup(self.signalPin, GPIO.IN)

        #I can't find a way to do the counter without global variables b/c 
        #the event detection will only pass in the pin number as a parameter.
        global COUNT
        COUNT = 0


    def _signal(self, pin):
        #----------------------------------------
        '''
        _signal(pin)

        Called when a rising edge is detected on the given pin. Adds
        one to the running count of pulses since the previous reading.
        '''
        #----------------------------------------

        #grab those global variables
        global COUNT
        COUNT += 1
        

    def start(self):
        #----------------------------------------
        '''
        start()

        Creates the data files, starts the counter counting, initiates
        the data variables, and prints a message.
        '''
        #----------------------------------------

        #open a file for the data
        self.file_name = self._name_file()
        self.data_file = open(self.file_name, 'a')
        self.data_file.write('\nNew data.\n\n')
        self.data_file.close()

        #set up the data variables and event detection.
        GPIO.add_event_detect(self.signalPin, GPIO.RISING, callback=self._signal) #set up the event detection
        global COUNT
        self.start_time = time()

        #send a message
        print(self.name, 'has started.')


    def get(self):
        #----------------------------------------
        '''
        get() -> float

        Returns the calculated Counts Per Minute. This can be used to
        collect a point of data, or to pull a reading out and use it
        for something else (i.e. get the temperature inside the
        payload for the heater controller).
        '''
        #----------------------------------------

        #This gets the change in time and the number of counts.
        sample_time = time() - self.start_time
        global COUNT

        #This calculates counts per minute.
        CPM = COUNT / sample_time / 60

        return CPM


    def write(self):
        #----------------------------------------
        '''
        write()

        This writes the data that the counter has collected since the previous reading.
        '''
        #----------------------------------------
        
        #Get the data.
        CPM = self.get()

        #Open the file.
        self.data_file = open(self.file_name, 'a')

        #write comma delimited data to a file
        report = asctime() + ',' + str(CPM) + '\n'
        self.data_file.write(report)
        self.data_file.close()

        #reset the data variables
        self.start_time = time()
        COUNT = 0


    def stop(self):
        #----------------------------------------
        '''
        stop()

        Prints a shutdown message to standard out.
        '''
        #----------------------------------------

        print(self.name, 'has finished.')


class GPS(Sensor):
    ########################################################
    '''
    This uses the agps3 class from the gps3 module to interface
    with a GNSS unit via the Adafruit USB serial cable.
    '''
    ########################################################

    def __init__(self, name):
        self.name = name

    def start(self):
        #----------------------------------------
        '''
        start()

        Starts the connection with the GPS board, opens a data file, and
        prints a message to standard out.
        '''
        #----------------------------------------

        #begin by starting the GPS daemon.
        system('gpsd /dev/ttyUSB0')
        #instantiate a socket object, which is an interface with the GPS daemon.
        self.gps_socket = agps3.GPSDSocket()
        #instantiate a dot object--basically, one data point--which unpacks the GPS data into attribute values.
        self.dot = agps3.Dot()
        #now start the stream of data
        self.gps_socket.connect()
        self.gps_socket.watch()

        #open a file for the data
        self.file_name = self._name_file()
        self.data_file = open(self.file_name, 'a')
        self.data_file.write('\nNew data.\n\n')
        self.data_file.close()

        #print a confirmation.
        print(self.name, 'has started.')


    def get(self):
        #----------------------------------------
        '''
        get() -> list

        This collects a point of data. Because you
        will probably want to read the data from the
        file at some point, the format is as follows
        (all in one line, of course):

        time(python),time(gps),time error,lat,lon,alt,
            lat err,lon err,alt err,track(heading),speed,
            climb(rate),track err,speed err,climb err
        '''
        #----------------------------------------

        #Apparently this is the black magic that gets the data.
        for new_data in self.gps_socket:
            if new_data:
                self.dot.unpack(new_data)
                #I only want a single data point, not a continuous stream.
                break

        #Write the data to a comma-delimited file.
        gpsd_readout = [asctime(), self.dot.time, self.dot.ept,\
                        self.dot.lat, self.dot.lon, self.dot.alt,\
                        self.dot.epx, self.dot.epy, self.dot.epv,\
                        self.dot.track, self.dot.speed, self.dot.climb,\
                        self.dot.epd, self.dot.eps, self.dot.epc]

        return gpsd_readout


    def write(self):
        #----------------------------------------
        '''
        write()

        This collects data and writes it to a file.
        '''
        #----------------------------------------

        #Open the file.
        self.data_file = open(self.file_name, 'a')

        #Retrieve the data.
        gpsd_readout = self.get()

        #Reverse the list so list.pop() will get them in the right order.
        gpsd_readout.reverse()
        #compile all the data
        data = ''
        #The reason that I don't just use
        #    for field in gpsd_readout:
        #is that I need the index to avoid putting a comma at the end of every line.
        fields = len(gpsd_readout)
        for i in range(fields):
            data = data + str(gpsd_readout.pop())
            #Add a comma after each field except the last one.
            if len(gpsd_readout) != 0:
                data = data + ','
        #Add a newline character after at the tail end of it all.
        data = data + '\n'

        #Now write that puppy, and put it to bed.
        self.data_file.write(data)
        self.data_file.close()


    def stop(self):
        #----------------------------------------
        '''
        stop()

        Closes the socket connection with the GPS unit and prints a
        stop message to standard out.
        '''
        #----------------------------------------
        
        #Shut it all down.
        self.gps_socket.close()

        #print a confirmation.
        print(self.name, 'has finished.')


class Camera(Sensor):
    ########################################################
    '''
    This is a nice case for the picamera to go in so that it looks like
    all the other sensor objects I made.
    '''
    ########################################################
    
    def __init__(self, name):
        self.name = name

    def start(self):
        try:
            self.camera = picamera.PiCamera()
            print('Camera has started.')
        except:
            print('Camera failed to start.')
        finally:
            #The "finally" is needed so that the program continues if an
            #exception is raised, but I don't actually need to do anything here.
            pass

    def write(self):
        #----------------------------------------
        '''
        write()

        This uses the camera object from the PiCamera module
        to take a picture with a timestamp in the name.
        '''
        #----------------------------------------

        #generate a time stamp, replacing spaces with file-friendly underlines
        date_time = asctime().replace(' ', '_')

        #each picture will have a unique name
        name = 'picture_' + date_time + '.jpg'

        #take a picture
        self.camera.capture(name)

    def stop(self):
        self.camera.close()
        print('Camera stopped.')


       


def blinky(LED, speed):
    #----------------------------------------
    '''
    blinky(pin, seconds) -> single pulse

    Given the pin of an LED and a time in seconds,
    this turns the LED on for the first half of
    that time and off for the second half.

    * * * * * IMPORTANT * * * * *
    Before using this function, you must first do
    one of two things:
    --Use the "launch()" function which sets-up a
      GPIO output on the LED pin that you pass in
    --Set up your own dang output pin.
    '''
    #----------------------------------------

    #Wax on.
    GPIO.output(LED, True)
    sleep(speed / 2)
    #Wax off.
    GPIO.output(LED, False)
    sleep(speed / 2)


def launch(trigger_pin, LED):
    #----------------------------------------
    '''
    launch(pin, pin)

    Stops the program until the specified pin is pulled low for 2 seconds,
    signaling the user's desire for the program to begin. After that, an
    LED is lit to provide a sense of comfort and security to the user.
    '''
    #----------------------------------------

    #A switch is wired between pin 3 and ground. When pin 4 falls, start recording data.
    GPIO.setup(trigger_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(LED, GPIO.OUT)
    GPIO.output(LED, False)
    print('Waiting for signal.')

    #Wait for the switch to turn on, and debounce for 2 seconds.
    signal = False
    while not signal:
        blinky(LED, 2)
        if GPIO.input(trigger_pin) == False:
            sleep(2)
            if GPIO.input(trigger_pin) == False:
                signal = True

    #Simulates all the comforts of the terminal.
    GPIO.output(LED, True)
    sleep(1)


def landing(trigger_pin):
    #----------------------------------------
    '''
    landing(pin) -> bool

    Checks for a low signal on the specified pin. If it is still there 10
    seconds later, that means the payload has landed and has been recovered.
    In that case, return the boolean value "True". Otherwise, return "False".
    '''
    #----------------------------------------

    landed = False

    if GPIO.input(trigger_pin) == False:
        sleep(10)
        if GPIO.input(trigger_pin) == False:
            landed = True
            print('Recieved stop signal. Shutting down.')

    return landed


   
def check_mem(): 
    #---------------------------------------- 
    ''' 
    check_mem() -> integer
    
    This returns the amount of free memory remaining in kilobytes.
    ''' 
    #---------------------------------------- 
 
    #"free" displays basic memory info. 
    info = popen('df') 
    info.readline() #the first line is only labels 
    space = info.readline().split() 
    free = int(space[3]) 
 
    return free 
   

################################################
'''
Make something that controls the temperature
inside the payload box.
'''
################################################


