#!/bin/bash

cd /home/russell/Desktop/russell_j/HAB_project/flight_data_2.0/

#This function returns a time/date string that is file-name friendly.
getDate()
{
    echo $(date) | sed -e "s/ /_/g" | sed -e "s/:/-/g"
}

#This assigns the output of the "getDate()" function to the variable "DATE"
DATE=$(getDate) 

#This runs the flight controller and writes the outputs to timestamped files.
./flight_controller_2.py 1> fc.out_$DATE 2> fc.err_$DATE

