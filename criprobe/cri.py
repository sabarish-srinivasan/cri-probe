import re
import serial
import serial.tools.list_ports


class CriProbe:

    def __init__(self, simulated=False):

        # Autodetects CRI probe/s.

        if simulated:
            # Create two simulated probes which mirror the ID, Model, and Type
            # information that would be found during real probe autodetect.
            self.probes = [{'ID': 'A19999',
                            'Model': 'CR-100',
                            'Type': 'Colorimeter'
                            },
                           {'ID': 'A29999',
                            'Model': 'CR-250',
                            'Type': 'Spectroradiometer'
                            }]
        else:
            self.probes = []
            ports = serial.tools.list_ports.comports()
            for port in ports:
                if re.search(r'A\d{6}', port.device):
                    with serial.Serial(port.device, 115200, timeout=1) as cri_probe:
                        probe_info = {}

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
