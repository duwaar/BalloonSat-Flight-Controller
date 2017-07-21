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
        trigger_pin = 36
        comfort_led = 37
        launch(trigger_pin, comfort_led)

        #Here, the heater pin is defined and set up.
        heater_pin = 33
        GPIO.setup(heater_pin, GPIO.OUT)


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
        Vref            = 5.09
        CLK             = 11
        Dout            = 13
        Din             = 15
        CS              = 16

        #Sensors.
        camera          = Camera('Camera')
        gps             = GPS('GPS')
        #geiger          = CountSensor('Geiger_counter', 7)
        thermocouple    = MCP3008('Outside_temp', Vref, CLK, Dout, Din, CS, [0,0,0], '(volts - 1.25) / 0.005')
        #convert volts to *F then *F to *C for the inside temp.
        inside          = MCP3008('Inside_temp', Vref, CLK, Dout, Din, CS, [0,0,1], '((volts * 100) - 32) / 9 * 5')
        light           = MCP3008('Light', Vref, CLK, Dout, Din, CS, [0,1,0], 'volts')
        pressure        = MCP3008('Pressure', Vref, CLK, Dout, Din, CS, [0,1,1], '(volts - 0.438) / 0.0046')

        #Queue.
        #If camera fails, the next thing in the queue gets messed up. IDK why.
        queue = [gps, thermocouple, inside, light, pressure, camera]

        ###############################################################


        #Try to start all the sensors with their identically named "start()"
        #methods, but kick them out if they give you any trouble.
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
                try:
                    sensor.write()
                    print(sensor.name, sensor.get())
                #except:
                    #print(sensor.name, 'raised an error.')
                finally:
                    pass

            #Report success. Shout it from the rooftops . . . or from a balloon.
            print('Data collected at', asctime())
            blinky(comfort_led, 1)

            #Check the temperature, and turn on the heater if necesary.
            try:
                temp = inside.get()
                heater(heater_pin, temp)
            except:
                print('The heater has failed.')
            finally:
                pass

            #The following checks for a button push.
            flying = not landing(trigger_pin)

            #Make the display easier to read.
            sleep(1)
            system('clear')


    #Here are statements for dealing with errors that the rest of the code cannot handle.
    except KeyboardInterrupt:
        print('The flight controller was terminated by the user.')


    #Here is the shutdown procedure that must always take place.
    finally:
        #We want to stop the sensors, but things may have gotten a bit out of hand by
        #this time. Hence, the try: finally: statement.
        for sensor in queue:
            try:
                sensor.stop()
            except:
                print(sensor.name, 'failed while stopping.')
            finally:
                pass

        print('Payload was recovered safely at', asctime())
        for i in range(5):
            blinky(comfort_led, 0.2)

        #Put this at the end, ding-dong. You know, AFTER all the GPIO operations.
        GPIO.cleanup()

        system('mv *.txt data/')
        system('mv *.jpg pictures/')
        date_str = asctime().replace(' ', '-')
        move = 'mv fc.out fc.out' + date_str + ' && mv fc.err fc.err' + date_str
        system(move)

main()
