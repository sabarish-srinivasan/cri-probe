import serial.tools.list_ports
import re

if __name__ == '__main__':
    ports = serial.tools.list_ports.comports()

    for port in ports:
        print(type(port))
        m = re.search(r'A\d\d\d\d\d\d', port.device)
        if m:
            print(port.device)




