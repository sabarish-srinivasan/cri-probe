import serial.tools.list_ports

if __name__ == '__main__':
    ports = serial.tools.list_ports.comports()
    for p in ports:
        print(p)
