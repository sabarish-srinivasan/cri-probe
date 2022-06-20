import unittest
import warnings
from unittest.mock import patch
import criprobe as cri
import re
import numpy as np


# https://pyserial.readthedocs.io/en/latest/tools.html#serial.tools.list_ports.ListPortInfo
class TestPort:
    device = '/dev/cu.usbmodemA004891'


class MyTestCase(unittest.TestCase):
    def test_init(self):
        # Create a simulated probe object
        p = cri.CriProbe(simulated=True)

        # Check the simulated probes
        p0 = {'Port': 'Mock Port', 'ID': 'A19999', 'Model': 'CR-100', 'Type': 'Colorimeter'}
        self.assertEqual(p.probes[0], p0)

        p1 = {'Port': 'Mock Port', 'ID': 'A29999', 'Model': 'CR-250', 'Type': 'Spectroradiometer'}
        self.assertEqual(p.probes[1], p1)

    def test_init_real_probe(self):
        # this test will only be meaningful if real probes are connected
        # if no probes are connected it will simply pass
        p = cri.CriProbe()

        # Only check results if there are real probes attached
        if p.probes:
            # check to make sure each probe in the list has valid info
            for probe in p.probes:
                self.assertTrue(re.search(r'A\d{5}', probe['ID']))
                self.assertTrue(re.search(r'CR-\d{3}', probe['Model']))
                self.assertTrue(probe['Type'] == 'Photometer' or probe['Type'] == 'Colorimeter' or probe[
                    'Type'] == 'Spectroradiometer')
        else:
            warnings.warn('No real probes detected')

    @patch('criprobe.CriProbe.get_ports', autospec=True)
    @patch('criprobe.CriProbe.open_port', autospec=True)
    @patch('criprobe.CriProbe.send_command', autospec=True)
    def test_init_patch(self, mock_send_command, mock_open_port, mock_get_ports):
        test_port = TestPort()
        mock_get_ports.return_value = [test_port]
        mock_open_port.return_value = 'Mock Port'
        mock_send_command.side_effect = [b'OK:0:RC ID:A00489\r\n',
                                         b'OK:0:RC Model:CR-100\r\n',
                                         b'OK:0:RC InstrumentType:1\r\n']
        p = cri.CriProbe()
        # Check and make sure the probe has the right info
        if p.probes:
            for probe in p.probes:
                self.assertEqual(probe['Port'], 'Mock Port')
                self.assertEqual(probe['ID'], 'A00489')
                self.assertEqual(probe['Model'], 'CR-100')
                self.assertEqual(probe['Type'], 'Photometer')

    def test_real_measure_xyY(self):
        # this test will only be meaningful if real probes are connected
        # if no probes are connected it will simply pass
        p = cri.CriProbe()

        # If there is a probe try to measure xyY
        if p.probes:
            result = p.measure_xyY()
            self.assertGreater(result['x'], 0)
            self.assertGreater(result['y'], 0)
            self.assertGreater(result['Y'], 0)
        else:
            warnings.warn('No real probes detected')

    @patch('criprobe.CriProbe.get_ports', autospec=True)
    @patch('criprobe.CriProbe.open_port', autospec=True)
    @patch('criprobe.CriProbe.send_command', autospec=True)
    def test_measure_xyY_light_low(self, mock_send_command, mock_open_port, mock_get_ports):
        test_port = TestPort()
        mock_get_ports.return_value = [test_port]
        mock_open_port.return_value = 'Mock Port'
        mock_send_command.side_effect = [b'OK:0:RC ID:A00489\r\n',
                                         b'OK:0:RC Model:CR-100\r\n',
                                         b'OK:0:RC InstrumentType:1\r\n',
                                         b'ER:-305:M:Light intensity too low or unmeasurable\r\n']

        p = cri.CriProbe()
        result = p.measure_xyY()
        self.assertIs(result['x'], np.nan)
        self.assertIs(result['y'], np.nan)
        self.assertIs(result['Y'], np.nan)

    @patch('criprobe.CriProbe.get_ports', autospec=True)
    @patch('criprobe.CriProbe.open_port', autospec=True)
    @patch('criprobe.CriProbe.send_command', autospec=True)
    def test_measure_xyY_2deg(self, mock_send_command, mock_open_port, mock_get_ports):
        test_port = TestPort()
        mock_get_ports.return_value = [test_port]
        mock_open_port.return_value = 'Mock Port'
        mock_send_command.side_effect = [b'OK:0:RC ID:A00489\r\n',
                                         b'OK:0:RC Model:CR-100\r\n',
                                         b'OK:0:RC InstrumentType:1\r\n',
                                         b'OK:0:M:No errors\r\n',
                                         b'OK:0:RM xy:0.3754,0.3773\r\n',
                                         b'OK:0:RM Y:2.239e+00\r\n']

        p = cri.CriProbe()
        result = p.measure_xyY()
        self.assertEqual(result['x'], 0.3754)
        self.assertEqual(result['y'], 0.3773)
        self.assertEqual(result['Y'], 2.239e+00)


if __name__ == '__main__':
    unittest.main()
