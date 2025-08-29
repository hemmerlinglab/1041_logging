import serial
import os
import datetime
import time

#serial_port = '/dev/ArduinoChill';
serial_port = '/dev/ttyACM0'
baud_rate = 9600; #In arduino, Serial.begin(baud_rate)
    
log_file_path = '/home/lab-42/skynet/Logs/PulseTube_Chilled_Water/'

#output_file = open(write_to_file_path, "w+");
try:
    ser = serial.Serial(serial_port, baud_rate)
except:
    try:
        ser.close()
    except:
        print("Serial port already closed") 
    ser = serial.Serial(serial_port, baud_rate)
    
#while True:
if True:
    reading = True
    line = ''
    while reading == True:
        #print(line)
        if '\r\n' not in line:
            raw_line = ser.readline();
            new_line = raw_line.decode("utf-8") #ser.readline returns a binary, convert to string
            line += new_line
        else:
            keys = [',temp,',',flow,',',pressure,',',hornet_pressure,',',UCR_in,',',UCR_out','uhv']

            keycheck = 0
            for key in keys:
                if key in line:
                    keycheck += 1

            #print('keycheck:',keycheck)
            if keycheck == len(keys)-1:
                reading = False
            else:
                line = ''
    
    
    #print(line);

    #output_file.write(line);

    my_today = datetime.datetime.today()
    today = str(my_today.strftime('%Y-%m-%d'))
    log_filename = today + '_chilled_water_pulsetube.log'

    if os.path.isfile(log_file_path + log_filename):
        log_file = open(log_file_path + log_filename, 'a')
    else:    
        log_file = open(log_file_path + log_filename, 'w')
            
    
    curr_time = str(my_today.strftime('%Y/%m/%d-%H:%M:%S'))
    hlp = curr_time + ","
            
    hlp += line
    #hlp = hlp[:-1] # delete last comma
    
    print (hlp)            
    
    log_file.write(hlp)# + "\n")
 
    log_file.close()
    
    #time.sleep(30)

ser.close()
    
