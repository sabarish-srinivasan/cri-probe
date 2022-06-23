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
                self.assertEqual(probe['Type'], 'Colorimeter')

    def test_real_measure_xyY(self):
        # this test will only be meaningful if real probes are connected
        # if no probes are connected it will simply pass
        p = cri.CriProbe()

        # If there is a probe try to measure xyY
        if p.probes:
            p.measure()
            for result in p.read_measure('xy'):
                self.assertGreater(np.all([float(x) for x in result['xy'].split(',')]), 0)
            for result in p.read_measure('Y'):
                self.assertGreater(float(result['Y']), 0)
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
        p.measure()
        result = p.read_measure('xy')
        for probe_dict in result:
            self.assertEqual(probe_dict['Probe ID'], 'A00489')
            self.assertIs(probe_dict['xy'], np.nan)

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
        p.measure()
        result = p.read_measure('xy')
        for probe_dict in result:
            self.assertEqual(probe_dict['x'], 0.3754)
            self.assertEqual(probe_dict['y'], 0.3773)
            self.assertEqual(probe_dict['Y'], 2.239e+00)

    @patch('criprobe.CriProbe.get_ports', autospec=True)
    @patch('criprobe.CriProbe.open_port', autospec=True)
    @patch('criprobe.CriProbe.send_command', autospec=True)
    def test_invalid_10degree_type(self, mock_send_command, mock_open_port, mock_get_ports):
        test_port = TestPort()
        mock_get_ports.return_value = [test_port]
        mock_open_port.return_value = 'Mock Port'
        mock_send_command.side_effect = [b'OK:0:RC ID:A00489\r\n',
                                         b'OK:0:RC Model:CR-100\r\n',
                                         b'OK:0:RC InstrumentType:1\r\n']

        p = cri.CriProbe()
        with self.assertRaises(RuntimeError) as cm:
            p.measure()
            p.read_measure('xy', degree=10)
            p.read_measure('Y', degree=10)
            err = cm.exception
            self.assertEqual(str(err), '10 degree only valid if instrument type is spectroradiometer')

    @patch('criprobe.CriProbe.get_ports', autospec=True)
    @patch('criprobe.CriProbe.open_port', autospec=True)
    @patch('criprobe.CriProbe.send_command', autospec=True)
    def test_invalid_probe_id(self, mock_send_command, mock_open_port, mock_get_ports):
        test_port = TestPort()
        mock_get_ports.return_value = [test_port]
        mock_open_port.return_value = 'Mock Port'
        mock_send_command.side_effect = [b'OK:0:RC ID:B00489\r\n',
                                         b'OK:0:RC Model:CR-100\r\n',
                                         b'OK:0:RC InstrumentType:1\r\n']

        with self.assertRaises(RuntimeError) as cm:
            cri.CriProbe()
        err = cm.exception
        self.assertEqual(str(err), 'CRI Probe ID Not Found')

    @patch('criprobe.CriProbe.get_ports', autospec=True)
    @patch('criprobe.CriProbe.open_port', autospec=True)
    @patch('criprobe.CriProbe.send_command', autospec=True)
    def test_invalid_probe_model(self, mock_send_command, mock_open_port, mock_get_ports):
        test_port = TestPort()
        mock_get_ports.return_value = [test_port]
        mock_open_port.return_value = 'Mock Port'
        mock_send_command.side_effect = [b'OK:0:RC ID:A00489\r\n',
                                         b'OK:0:RC Model:F-150\r\n',
                                         b'OK:0:RC InstrumentType:1\r\n']

        with self.assertRaises(RuntimeError) as cm:
            cri.CriProbe()
        err = cm.exception
        self.assertEqual(str(err), 'CRI Probe Model Not Found')

    @patch('criprobe.CriProbe.get_ports', autospec=True)
    @patch('criprobe.CriProbe.open_port', autospec=True)
    @patch('criprobe.CriProbe.send_command', autospec=True)
    def test_invalid_probe_type(self, mock_send_command, mock_open_port, mock_get_ports):
        test_port = TestPort()
        mock_get_ports.return_value = [test_port]
        mock_open_port.return_value = 'Mock Port'
        mock_send_command.side_effect = [b'OK:0:RC ID:A00489\r\n',
                                         b'OK:0:RC Model:CR-100\r\n',
                                         b'OK:0:RC InstrumentType:\r\n']

        with self.assertRaises(RuntimeError) as cm:
            cri.CriProbe()
        err = cm.exception
        self.assertEqual(str(err), 'CRI Probe Type Not Found')

    @patch('criprobe.CriProbe.get_ports', autospec=True)
    @patch('criprobe.CriProbe.open_port', autospec=True)
    @patch('criprobe.CriProbe.send_command', autospec=True)
    def test_photometer_type(self, mock_send_command, mock_open_port, mock_get_ports):
        test_port = TestPort()
        mock_get_ports.return_value = [test_port]
        mock_open_port.return_value = 'Mock Port'
        mock_send_command.side_effect = [b'OK:0:RC ID:A00489\r\n',
                                         b'OK:0:RC Model:CR-100\r\n',
                                         b'OK:0:RC InstrumentType:0\r\n']

        p = cri.CriProbe()
        if p.probes:
            for probe in p.probes:
                self.assertEqual(probe['Type'], 'Photometer')

    @patch('criprobe.CriProbe.get_ports', autospec=True)
    @patch('criprobe.CriProbe.open_port', autospec=True)
    @patch('criprobe.CriProbe.send_command', autospec=True)
    def test_spectroradiometer_type(self, mock_send_command, mock_open_port, mock_get_ports):
        test_port = TestPort()
        mock_get_ports.return_value = [test_port]
        mock_open_port.return_value = 'Mock Port'
        mock_send_command.side_effect = [b'OK:0:RC ID:A00489\r\n',
                                         b'OK:0:RC Model:CR-100\r\n',
                                         b'OK:0:RC InstrumentType:2\r\n']

        p = cri.CriProbe()
        if p.probes:
            for probe in p.probes:
                self.assertEqual(probe['Type'], 'Spectroradiometer')

    @patch('criprobe.CriProbe.get_ports', autospec=True)
    @patch('criprobe.CriProbe.open_port', autospec=True)
    @patch('criprobe.CriProbe.send_command', autospec=True)
    def test_spectroradiometer_type(self, mock_send_command, mock_open_port, mock_get_ports):
        test_port = TestPort()
        mock_get_ports.return_value = [test_port]
        mock_open_port.return_value = 'Mock Port'
        mock_send_command.side_effect = [b'OK:0:RC ID:A00489\r\n',
                                         b'OK:0:RC Model:CR-100\r\n',
                                         b'OK:0:RC InstrumentType:2\r\n']

        with self.assertRaises(ValueError) as cm:
            p = cri.CriProbe()
            p.measure()
            p.read_measure('xy')
        err = cm.exception
        self.assertEqual(str(err), 'Degree of 2 or 10 Required')

    @patch('criprobe.CriProbe.get_ports', autospec=True)
    @patch('criprobe.CriProbe.open_port', autospec=True)
    @patch('criprobe.CriProbe.send_command', autospec=True)
    def test_invalid_xy(self, mock_send_command, mock_open_port, mock_get_ports):
        test_port = TestPort()
        mock_get_ports.return_value = [test_port]
        mock_open_port.return_value = 'Mock Port'
        mock_send_command.side_effect = [b'OK:0:RC ID:A00489\r\n',
                                         b'OK:0:RC Model:CR-100\r\n',
                                         b'OK:0:RC InstrumentType:2\r\n',
                                         b'OK:0:RM xy:\r\n']

        with self.assertRaises(ValueError) as cm:
            p = cri.CriProbe()
            p.measure()
            p.read_measure('xy')
        err = cm.exception
        self.assertEqual(str(err), "[b'OK:0:RM xy:\\r\\n']" or "[b'OK:0:RM xy10:\\r\\n']")

    @patch('criprobe.CriProbe.get_ports', autospec=True)
    @patch('criprobe.CriProbe.open_port', autospec=True)
    @patch('criprobe.CriProbe.send_command', autospec=True)
    def test_invalid_Y(self, mock_send_command, mock_open_port, mock_get_ports):
        test_port = TestPort()
        mock_get_ports.return_value = [test_port]
        mock_open_port.return_value = 'Mock Port'
        mock_send_command.side_effect = [b'OK:0:RC ID:A00489\r\n',
                                         b'OK:0:RC Model:CR-100\r\n',
                                         b'OK:0:RC InstrumentType:2\r\n',
                                         b'OK:0:RM Y:\r\n']

        with self.assertRaises(ValueError) as cm:
            p = cri.CriProbe()
            p.measure()
            p.read_measure('Y')
        err = cm.exception
        self.assertEqual(str(err), "[b'OK:0:RM Y:\\r\\n']" or "[b'OK:0:RM Y10:\\r\\n']")


if __name__ == '__main__':
    unittest.main()
