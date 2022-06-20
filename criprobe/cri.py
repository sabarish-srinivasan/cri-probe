import re
import serial
import serial.tools.list_ports


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
