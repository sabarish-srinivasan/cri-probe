import re
import serial
import serial.tools.list_ports


class CriProbe:

    def __init__(self, simulated=False):

        # Autodetects CRI probe/s. When no probe/s detected, creates CR-100 and CR-250 simulated probes.

        if simulated:
            self.probes = [{'Type': 'CR-100'},
                           {'Type': 'CR-250'}]
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
                            reg_id = id.group(1)
                            probe_id = str(reg_id)
                        probe_info['ID'] = probe_id

                        cri_probe.write(b'RC Model\r\n')
                        probe_result = cri_probe.readline()
                        model = re.search(r'(CR-\d{3})', str(probe_result))
                        if model:
                            reg_model = model.group(1)
                            probe_model = str(reg_model)
                        probe_info['Model'] = probe_model

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

                        self.probes.append(probe_info)
