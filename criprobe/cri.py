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
            self.probes = [{'Device': '/dev/cu.usbmodemA199991',
                            'ID': 'A19999',
                            'Model': 'CR-100',
                            'Type': 'Colorimeter'
                            },
                           {'Device': '/dev/cu.usbmodemA299991',
                            'ID': 'A29999',
                            'Model': 'CR-250',
                            'Type': 'Spectroradiometer'
                            }]
        else:
            self.probes = []
            ports = serial.tools.list_ports.comports()
            for port in ports:
                if re.search(r'A\d{6}', port.device):
                    with serial.Serial(port.device, 115200, timeout=1) as cri_probe:
                        # Save the port device for later use
                        probe_info = {'Device': port.device}

                        cri_probe.write(b'RC ID\r\n')
                        probe_result = cri_probe.readline()
                        id = re.search(r'(A\d{5})', str(probe_result))
                        if id:
                            probe_info['ID'] = str(id.group(1))
                        else:
                            raise RuntimeError('CRI Probe ID Not Found')

                        cri_probe.write(b'RC Model\r\n')
                        probe_result = cri_probe.readline()
                        model = re.search(r'(CR-\d{3})', str(probe_result))
                        if model:
                            probe_info['Model'] = str(model.group(1))
                        else:
                            raise RuntimeError('CRI Probe Model Not Found')

                        cri_probe.write(b'RC InstrumentType\r\n')
                        probe_result = cri_probe.readline()
                        instrument_type = re.search(r'(\d)', str(probe_result))
                        if instrument_type:
                            reg_type = instrument_type.group(1)
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

    def measure_XYZ(self, degree=2):

        # Return *CIE XYZ* tristimulus values of sample.

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
                    # Trigger a measurement for XYZ (default 2-degrees).
                    cri_probe.write(b'M\r\n')
                    result.append(cri_probe.readline())
                    cri_probe.write(b'RM XYZ\r\n')
                    result.append(cri_probe.readline())

                    # Validate result.
                    if 'OK:0:M:No errors' not in str(result[0]):
                        if 'Light intensity too low or unmeasurable' in str(result[0]):
                            return {'XYZ': np.nan}
                        else:
                            raise ValueError(str(result[0]))

                    # Find and return XYZ measurement.
                    xyz_val = re.search(r'XYZ:([\d.e+-]+),([\d.e+-]+),([\d.e+-]+)', str(result[1]))
                    if xyz_val:
                        response['X'] = xyz_val.group(1)
                        response['Y'] = xyz_val.group(2)
                        response['Z'] = xyz_val.group(3)
                    else:
                        raise ValueError('XYZ')

                elif degree == 10:
                    # RM XYZ10 is only valid if Instrument Type is 2 (Spectroradiometer).
                    if int(reg_type) == 2:

                        # Trigger a measurement for XYZ10 (10-degrees).
                        cri_probe.write(b'M\r\n')
                        result.append(cri_probe.readline())
                        cri_probe.write(b'RM XYZ10\r\n')
                        result.append(cri_probe.readline())

                        # Validate result.
                        if 'OK:0:M:No errors' not in str(result[0]):
                            if 'Light intensity too low or unmeasurable' in str(result[0]):
                                return {'XYZ10': np.nan}
                            else:
                                raise ValueError(str(result[0]))

                        # Find and return XYZ10 measurement.
                        xyz_val = re.search(r'XYZ10:([\d.e+-]+),([\d.e+-]+),([\d.e+-]+)', str(result[1]))
                        if xyz_val:
                            response['X10'] = xyz_val.group(1)
                            response['Y10'] = xyz_val.group(2)
                            response['Z10'] = xyz_val.group(3)
                        else:
                            raise ValueError('XYZ10')

                    else:
                        raise RuntimeError('RM XYZ10 Only Valid if Instrument Type is Spectroradiometer.')

                else:
                    raise ValueError('Degree of 2 or 10 Required')

        return response
