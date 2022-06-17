import unittest
from unittest.mock import patch
import criprobe as cri
import re


class TestPort:
    def __init__(self):
        self.device = '/dev/cu.usbmodemA004891'

# Save this idea for later
# def send_cmd_sim(port, cmd):
#     if cmd == b'RC ID\r\n':
#         return b'OK:0:RC ID:A00489\r\n'
#     if cmd == b'RC Model\r\n':
#         return b'OK:0:RC Model:CR-100\r\n'
#     if cmd == b'RC InstrumentType\r\n':
#         return b'OK:0:RC InstrumentType:1\r\n'


class MyTestCase(unittest.TestCase):
    def test_init(self):
        # Create a simulated probe object
        p = cri.CriProbe(simulated=True)

        # Check the simulated probes
        p0 = {'Device': '/dev/cu.usbmodemA199991', 'ID': 'A19999', 'Model': 'CR-100', 'Type': 'Colorimeter'}
        self.assertEqual(p.probes[0], p0)

        p1 = {'Device': '/dev/cu.usbmodemA299991', 'ID': 'A29999', 'Model': 'CR-250', 'Type': 'Spectroradiometer'}
        self.assertEqual(p.probes[1], p1)

    def test_init_real_probe(self):
        # this test will only be meaningful if real probes are connected
        # if no probes are connected it will simply pass
        p = cri.CriProbe()

        # Only check results if there are real probes attached
        if p.probes:
            # check to make sure each probe in the list has valid info
            for probe in p.probes:
                print(probe)
                self.assertTrue(re.search(r'A\d{5}', probe['ID']))
                self.assertTrue(re.search(r'CR-\d{3}', probe['Model']))
                self.assertTrue(probe['Type'] == 'Photometer' or probe['Type'] == 'Colorimeter' or probe[
                    'Type'] == 'Spectroradiometer')
        else:
            pass

    @patch('criprobe.CriProbe.get_ports', autospec=True)
    @patch('criprobe.CriProbe.send_command', autospec=True)
    def test_init_patch(self, mock_send_command, mock_get_ports):
        test_port = TestPort()
        mock_get_ports.return_value = [test_port]
        mock_send_command.side_effect = [b'OK:0:RC ID:A00489\r\n',
                                         b'OK:0:RC Model:CR-100\r\n',
                                         b'OK:0:RC InstrumentType:1\r\n']
        p = cri.CriProbe()
        # Check and make sure the probe has the right info
        if p.probes:
            for probe in p.probes:
                print(probe)
                self.assertEqual(probe['Device'], '/dev/cu.usbmodemA004891')
                self.assertEqual(probe['ID'], 'A00489')
                self.assertEqual(probe['Model'], 'CR-100')
                self.assertEqual(probe['Type'], 'Photometer')


if __name__ == '__main__':
    unittest.main()
