import re
import serial
import serial.tools.list_ports
import numpy as np


class CriProbe:
    def __init__(self, simulated=False):
        # Autodetects CRI probe/s
        if simulated:
            # Create two simulated probes which mirror the ID, Model, and Type
            # information that would be found during real probe autodetect
            self.probes = [{'Port': 'Mock Port',
                            'ID': 'A19999',
                            'Model': 'CR-100',
                            'Type': 'Colorimeter'
                            },
                           {'Port': 'Mock Port',
                            'ID': 'A29999',
                            'Model': 'CR-250',
                            'Type': 'Spectroradiometer'
                            }]
        else:
            self.probes = []
            ports = self.get_ports()
            for port in ports:
                if re.search(r'A\d{6}', port.device):
                    # Save the port device for later use
                    cri_probe = self.open_port(port.device)
                    probe_info = {'Port': cri_probe}

                    probe_result = self.send_command(cri_probe, 'RC ID')
                    id = re.search(r'(A\d{5})', str(probe_result))
                    if id:
                        probe_info['ID'] = str(id.group(1))
                    else:
                        raise RuntimeError('CRI Probe ID Not Found')

                    probe_result = self.send_command(cri_probe, 'RC Model')
                    model = re.search(r'(CR-\d{3})', str(probe_result))
                    if model:
                        probe_info['Model'] = str(model.group(1))
                    else:
                        raise RuntimeError('CRI Probe Model Not Found')

                    probe_result = self.send_command(cri_probe, 'RC InstrumentType')
                    instrument_type = re.search(r'InstrumentType:(\d)', str(probe_result))
                    if instrument_type:
                        reg_type = instrument_type.group(1)
                        probe_type = 'Unknown'
                        if int(reg_type) == 0:
                            probe_type = 'Photometer'
                        elif int(reg_type) == 1:
                            probe_type = 'Colorimeter'
                        elif int(reg_type) == 2:
                            probe_type = 'Spectroradiometer'
                        probe_info['Type'] = probe_type
                    else:
                        raise RuntimeError('CRI Probe Type Not Found')

                    self.probes.append(probe_info)

    def get_ports(self):
        return serial.tools.list_ports.comports()

    def open_port(self, device):
        # Allow up to 30 seconds for probe to return a measurement
        return serial.Serial(device, 115200, timeout=30)

    def send_command(self, port, cmd):
        cmd_bytes = bytes(cmd, 'utf-8') + b'\r\n'
        port.write(cmd_bytes)
        probe_result = port.readline()
        return probe_result

    def read_measure(self, measure_type, degree=2):
        final_result = []

        for probe in self.probes:
            response = {}

            # Setup RM command
            rm = 'RM ' + measure_type
            suffix = ''

            # RM commands change based on 2 or 10 degree
            if degree == 10:
                if measure_type != 'X' or 'Y' or 'Z' or 'XYZ' or 'xy':
                    raise ValueError('10 degree only valid with X, Y, Z, XYZ, and xy')
                if probe['Type'] != 'Spectroradiometer':
                    raise RuntimeError('10 degree only valid if instrument type is spectroradiometer')
                suffix = '10'
            elif degree != 2:
                raise ValueError('Degree of 2 or 10 required')

            # Create probe ID
            response['Probe ID'] = probe['ID']

            # RM
            rm += suffix
            result = self.send_command(probe['Port'], rm)
            str_result = str(result).split(':')
            measurement = str_result[3].strip("\\r\\n'")
            response[measure_type] = measurement
            final_result.append(response)

        return final_result

    def measure(self):
        result = []
        for probe in self.probes:
            # Initialize probe measurement
            result = self.send_command(probe['Port'], 'M')
        return result
