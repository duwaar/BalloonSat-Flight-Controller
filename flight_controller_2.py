#!/usr/bin/python3.4
'''
This is the flight controller program for a high-altitude balloon
payload. The process herein allows for easy adding and removing of
sensors, and simple, clear user interface on launch day.

Russell Jeffery
14 July 2017
'''

from fl_objects_2 import *

def main():
    #------------------------------------------------------------------
    '''
    This is the body of the program.
    '''
    #------------------------------------------------------------------

    #Here, the launch function awaits input from the user.
    trigger_pin = 22
    comfort_led = 29
    launch(trigger_pin, comfort_led)

    #This next bit is the startup procedure.
    try:
        ###############################################################
        '''
        If you are in the business of adding or removing sensors, you
        are in the right place!

        --Variables:    Define any variables that you will need for
        several sensors.
        --Sensors:      Instantiate the sensor objects.
        --Queue:        Add the sensors to the start/write/stop queue.

        '''

        #Variables.
        Vref = 5.46

        #Sensors.

        #Queue.
        sensors = []

        ###############################################################

    except KeyboardInterrupt:
        print('flight_controller_2.py was terminated by the user.')

    finally:
        #Stop all the sensors.

        GPIO.cleanup()


main()
