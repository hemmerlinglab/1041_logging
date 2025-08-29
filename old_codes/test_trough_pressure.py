import serial
import datetime
import time

def save_data(log_file_path, filename, data):

    # save single data point
    return

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

if __name__ == '__main__':

    while True:
        print(readout_275gauge())
        time.sleep(1)
