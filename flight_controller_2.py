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


    try:
        #Here, the launch function awaits input from the user.
        trigger_pin = 22
        comfort_led = 29
        launch(trigger_pin, comfort_led)


        ###############################################################
        '''
        If you are in the business of adding or removing sensors, you are in the right
        place!  To add a sensor, you must at least instantiate the object and add it
        to the queue.  It may also be helpful to define some common variables if you
        have, for example, several sensors that will use the same ADC chip.

        --Variables:    Define any variables that you will need for several sensors.
        --Sensors:      Instantiate the sensor objects.
        --Queue:        Add the sensors to the start/write/stop queue.

        '''

        #Variables.
        Vref            = 5.46
        CLK             = 16
        Dout            = 15
        Din             = 13
        CS              = 11


        #Sensors.
        camera          = Camera('Camera')
        gps             = GPS('GPS')
        thermocouple    = AnalogSensor('Outside_temp', Vref, CLK, Dout, Din, CS, [0,0,0], -250, 200)

        #Queue.
        queue = [camera, gps, thermocouple]

        ###############################################################


        #Start all the sensors with their identically named "start()" methods, and kick
        #them out if they give you any trouble.
        for sensor in queue:
            try:
                sensor.start()
            except:
                queue.remove(sensor)
                print(sensor.name, 'failed to start. It was kicked out of the queue.')
            finally:
                pass
        

        #This is the main loop that is going to be running for most of the flight.
        flying = True
        while flying:
            #Get all the data.
            for sensor in queue:
                sensor.write()

            #Report success. Shout it from the rooftops . . . or from a balloon.
            print('Data collected at', asctime())
            blinky(comfort_led, 1)

            #The following checks for a button push.
            flying = not landing(trigger_pin)


    #Here are statements for dealing with errors that the rest of the code cannot handle.
    except KeyboardInterrupt:
        print('The flight controller was terminated by the user.')


    #Here is the shutdown procedure that must always take place.
    finally:
        #We want to stop the sensors, but things may have gotten a bit out of hand by
        #this time. Hence, the try: finally: statement.
        try:
            for sensor in queue:
                sensor.stop()
        except:
            print('Failed to stop the sensors.')
        finally:
            pass

        GPIO.cleanup()
        print('Payload was recovered safely at', asctime())


main()
