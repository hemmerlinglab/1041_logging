import serial
import numpy as np
import time
from datetime import datetime

# Configurations about the Arduino output
serial_port = 'COM7'    # The port that data comes out
baud_rate = 9600        # sampling rate

# Connect to the Arduino
try:
    ser = serial.Serial(serial_port, baud_rate)
except:
    try:
        ser.close()
    except:
        print ("Serial port already closed" )
    ser = serial.Serial(serial_port, baud_rate)

############################################
####      Data from roughing gauge      ####
############################################

'''Returned pressure is a string, not a float point number'''
def readout_275gauge(address = '01'):

    serial_port = 'COM6'
    baud_rate = 19200

    # connect to the pressure gauge
    try:
        ser = serial.Serial(
                serial_port,
                baud_rate,
                timeout = 0.5,
                bytesize = serial.EIGHTBITS,
                stopbits = serial.STOPBITS_ONE,
                parity = serial.PARITY_NONE,
                dsrdtr = True
                )
    except:
        try:
            ser.close()
        except:
            print("Serial port already closed!")
        ser = serial.Serial(serial_port, baud_rate)
    ser.flushInput()

    # readout pressure
    cmd = '#' + address + 'RD \x0D'
    ser.write(cmd.encode('utf-8'))
    recv = ser.read(13)
    pressure = recv.decode()[4:12]

    ser.close()

    return pressure

##########################################################
####      Receive measured data from serial port      ####
##########################################################

''' Handling Type 1 error: Sometimes the message carries some mysterious 
'\xff' etc things, which would make decode() to generate some error, so 
we use the procedure below to avoid such error.'''
def read_series(cycle=7):

    while True:
        hlp = ser.read(8*cycle)
        try:
            hlp = hlp.decode()
            break
        except:
            print('Type 1 error occured!')
            continue

    return hlp

#########################################
####      Extract data from hlp      ####
#########################################

# Voltage of room temperature chamber begins with 4
# Voltage of cryo dewar begins with 5

'''Handling Type 2 error: Sometimes some bytes of the message shifts
and destroys the recorded values, in the procedure below, we request
the message again when this error occurs.'''
def get_voltages():

    converted = False
    while not converted:
        hlp = read_series()
        for i, char in enumerate(hlp):
            try:
                if (char == '\n') and (hlp[i+1] == '4'):
                    voltage_room = float(hlp[i+2:i+6])
                    voltage_cryo = float(hlp[i+9:i+13])
                    voltage_ICR = float(hlp[i+16:i+20])
                    voltage_ICH = float(hlp[i+23:i+27])
                    converted = True
                    break
            except:
                print('Type 2 error occured!')
                break

    return voltage_room, voltage_cryo, voltage_ICR, voltage_ICH

####################################################################
####      Correct errors and convert voltages to pressures      ####
####################################################################

'''Handling Type 3 error: Since the message shift is random. It is possible
that some value shifts to another value. To prevent this, we request multiple
values each time for error correction.'''
def correct(vols, TOL=0.1):

    ptp = vols.ptp()
    if ptp > TOL:
        print('Type 3 error occured!')
        good_datas = abs(vols - np.median(vols)) < TOL
        voltage = vols[good_datas].mean()
    else:
        voltage = vols.mean()

    return voltage

def T(R):

    A = 3.354016E-03
    B = 2.460382E-04
    C = 3.405377E-06
    D = 1.034240E-07
    R25 = 1E+05

    hlp = np.log(R/R25)
    TK = 1 / (A + B * hlp + C * hlp ** 2 + D * hlp ** 3)
    TC = TK - 273.15

    return TC

def convert(v_room, v_cryo, v_ICR, v_ICH):

    R0_ICR = 1E+05
    R0_ICH = 1E+05
    V_s = 3.3

    p_room = 10 ** (v_room * 3 - 10)
    p_cryo = 10 ** (v_cryo * 3 - 10)

    R_ICR = v_ICR / (V_s - v_ICR) * R0_ICR
    R_ICH = v_ICH / (V_s - v_ICH) * R0_ICH
    T_ICR = T(R_ICR)
    T_ICH = T(R_ICH)

    return p_room, p_cryo, T_ICR, T_ICH

def get_pressure_temperature(repeat=5, TOL=0.1):

    vols_room = np.zeros(repeat)
    vols_cryo = np.zeros(repeat)
    vols_ICR = np.zeros(repeat)
    vols_ICH = np.zeros(repeat)
    for i in range(repeat):
        vols_room[i], vols_cryo[i], vols_ICR[i], vols_ICH[i] = get_voltages()

    voltage_room = correct(vols_room, TOL)
    voltage_cryo = correct(vols_cryo, TOL)
    voltage_ICR = correct(vols_ICR, TOL)
    voltage_ICH = correct(vols_ICH, TOL)

    pressure_room, pressure_cryo, temperature_ICR, temperature_ICH = convert(voltage_room, voltage_cryo, voltage_ICR, voltage_ICH)

    return pressure_room, pressure_cryo, temperature_ICR, temperature_ICH

#######################################################
####      Test the performance of the program      ####
#######################################################

# Test the error of the result and speed of the program
def test_performance(sample=100):

    dataset = np.zeros((2,sample))
    start_time = time.time()
    for i in range(sample):
        dataset[0,i], dataset[1,i] = get_pressure()
    print('It takes ' + str(time.time()-start_time) + ' seconds to sample ' + str(sample) + ' data.')

    avg_room = dataset[0].mean()
    std_room = dataset[0].std()
    err_room = std_room / avg_room
    avg_cryo = dataset[1].mean()
    std_cryo = dataset[1].std()
    err_cryo = std_cryo / avg_cryo
    
    print('Measurement Result')
    print('Room Temperature: \t' + str(avg_room) + ' +/- ' + str(std_room) + ' (' + str(err_room * 100) + '%)')
    print('Cryogenic Dewar: \t' + str(avg_cryo) + ' +/- ' + str(std_cryo) + ' (' + str(err_cryo * 100) + '%)')

#test_performance()
'''
Test Result:
    1. Increase the number of repeat in get_pressure does not increase the accuracy.
    2. With repeat = 5, it takes ~0.145s to get one datapoint.
    3. Errors happen mostly at the beginning of the run, but still happens occasionally later.
'''

################################################
####      Write the data to a log file      ####
################################################

def get_log_text():

    # Save the currrent datetime as a string
    now = datetime.now()
    date_time = now.strftime('%Y/%m/%d-%H:%M:%S')

    # Read pressure and create log text
    pressure_room, pressure_cryo, temperature_ICR, temperature_ICH = get_pressure_temperature()
    pressure_rough = readout_275gauge()
    str_room = date_time + ',' + str(pressure_room) + '\n'
    str_cryo = date_time + ',' + str(pressure_cryo) + '\n'
    str_rough = date_time + ',' + pressure_rough + '\n'
    str_temp = date_time + ',ICR temp,' + str(temperature_ICR) + ',ICH temp,' + str(temperature_ICH) + '\n'

    return str_room, str_cryo, str_rough, str_temp

########################
####      Main      ####
########################

path_rough = 'Z:\\Logs\\1041_Dewar_Foreline\\'
path_room = 'Z:\\Logs\\1041_Chamber_Pressure\\'
path_cryo = 'Z:\\Logs\\1041_Dewar_Pressure\\'
path_temp = 'Z:\\Logs\\1041_Chilled_Water\\'

now = datetime.now()
current_date = now.strftime('%Y-%m-%d')

while True:

    with open(path_room + current_date + '_chamber.log', 'a') as file_room, open(path_cryo + current_date + '_dewar.log', 'a') as file_cryo, open(path_rough + current_date + '_foreline.log', 'a') as file_rough, open(path_temp + current_date + '_temperature.log', 'a') as file_temp:

        while True:

            now = datetime.now()
            date = now.strftime('%Y-%m-%d')

            if date == current_date:
                written = False
                while not written:
                    try:
                        str_room, str_cryo, str_rough, str_temp = get_log_text()
                        file_room.write(str_room)
                        file_cryo.write(str_cryo)
                        file_rough.write(str_rough)
                        file_temp.write(str_temp)
                        file_room.flush()
                        file_cryo.flush()
                        file_rough.flush()
                        file_temp.flush()
                        time.sleep(60)
                        written = True
                    except:
                        print('Other Error Occurred!')
            else:
                current_date = date
                break

ser.close()
