import re
import serial
import serial.tools.list_ports
import numpy as np


class CriProbe:
    def __init__(self, simulated=False):
        # Autodetects CRI probe/s.
        if simulated:
            # Create two simulated probes which mirror the ID, Model, and Type
            # information that would be found during real probe autodetect.
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
                    instrument_type = re.search(r'(\d)', str(probe_result))
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
        return serial.Serial(device, 115200, timeout=1)

    def send_command(self, port, cmd):
        cmd_bytes = bytes(cmd, 'utf-8') + b'\r\n'
        port.write(cmd_bytes)
        probe_result = port.readline()
        return probe_result

    def measure_xyY(self, degree=2):

        # Return *CIE xyY* values of sample.

        result = []
        for probe in self.probes:
            with serial.Serial(probe['Device'], 115200, timeout=60) as cri_probe:
                response = {}

                cri_probe.write(b'RC InstrumentType\r\n')
                probe_result = cri_probe.readline()
                instrument_type = re.search(r'(\d)', str(probe_result))
                if instrument_type:
                    reg_type = instrument_type.group(1)

                if degree == 2:
                    # Trigger a measurement for xyY (default 2-degrees).
                    cri_probe.write(b'M\r\n')
                    result.append(cri_probe.readline())
                    cri_probe.write(b'RM xy\r\n')
                    result.append(cri_probe.readline())
                    cri_probe.write(b'RM Y\r\n')
                    result.append(cri_probe.readline())

                    # Validate result.
                    if 'OK:0:M:No errors' not in str(result[0]):
                        if 'Light intensity too low or unmeasurable' in str(result[0]):
                            return {'x': np.nan, 'y': np.nan, 'Y': np.nan}
                        else:
                            raise ValueError(str(result[0]))

                    # Find and return xyY measurement.
                    xy_val = re.search(r'xy:([\d\.]+),([\d\.]+)', str(result[1]))
                    if xy_val:
                        response['x'] = xy_val.group(1)
                        response['y'] = xy_val.group(2)
                    else:
                        raise ValueError('xy')

                    Y_val = re.search(r'Y:([\d\.e\+\-]+)', str(result[2]))
                    if Y_val:
                        response['Y'] = Y_val.group(1)
                    else:
                        raise ValueError('Y')

                elif degree == 10:
                    # RM xyY10 is only valid if Instrument Type is 2 (Spectroradiometer).
                    if int(reg_type) == 2:

                        # Trigger a measurement for xyY (10-degrees).
                        cri_probe.write(b'M\r\n')
                        result.append(cri_probe.readline())
                        cri_probe.write(b'RM xy10\r\n')
                        result.append(cri_probe.readline())
                        cri_probe.write(b'RM Y10\r\n')
                        result.append(cri_probe.readline())

                        # Validate result.
                        if 'OK:0:M:No errors' not in str(result[0]):
                            if 'Light intensity too low or unmeasurable' in str(result[0]):
                                return {'x10': np.nan, 'y10': np.nan, 'Y10': np.nan}
                            else:
                                raise ValueError(str(result[0]))

                        # Find and return xyY10 measurement.
                        xy10_val = re.search(r'xy10:([\d\.]+),([\d\.]+)', str(result[1]))
                        if xy10_val:
                            response['x10'] = xy10_val.group(1)
                            response['y10'] = xy10_val.group(2)
                        else:
                            raise ValueError('xy10')

                        Y10_val = re.search(r'Y10:([\d\.e\+\-]+)', str(result[2]))
                        if Y10_val:
                            response['Y10'] = Y10_val.group(1)
                        else:
                            raise ValueError('Y10')

                    else:
                        raise RuntimeError('RM xyY10 Only Valid if Instrument Type is Spectroradiometer.')

                else:
                    raise ValueError('Degree of 2 or 10 Required')

            return response
