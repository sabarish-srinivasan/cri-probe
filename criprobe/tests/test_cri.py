import unittest
import warnings
from unittest.mock import patch
import criprobe as cri
import re
import numpy as np


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
                self.assertGreater(np.all(result['xy']), 0)
            for result in p.read_measure('Y'):
                self.assertGreater(result['Y'], 0)
        else:
            warnings.warn('No real probes detected')

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
        result_xy = p.read_measure('xy')
        result_Y = p.read_measure('Y')
        for probe_dict in result_xy:
            self.assertEqual(probe_dict['xy'].tolist(), [0.3754, 0.3773])
        for probe_dict in result_Y:
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
                                         b'OK:0:RC InstrumentType:1\r\n',
                                         b'OK:0:M:No errors\r\n',
                                         b'OK:0:RM xy:0.3754,0.3773\r\n',
                                         b'OK:0:RM Y:2.239e+00\r\n']

        p = cri.CriProbe()
        p.measure()
        with self.assertRaises(ValueError) as cm:
            p.read_measure('xy', degree=10)
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
    def test_valid_degree(self, mock_send_command, mock_open_port, mock_get_ports):
        test_port = TestPort()
        mock_get_ports.return_value = [test_port]
        mock_open_port.return_value = 'Mock Port'
        mock_send_command.side_effect = [b'OK:0:RC ID:A00489\r\n',
                                         b'OK:0:RC Model:CR-100\r\n',
                                         b'OK:0:RC InstrumentType:2\r\n',
                                         b'OK:0:M:No errors\r\n',
                                         b'OK:0:RM xy:\r\n']

        with self.assertRaises(ValueError) as cm:
            p = cri.CriProbe()
            p.measure()
            p.read_measure('xy', degree=4)
        err = cm.exception
        self.assertEqual(str(err), 'Degree of 2 or 10 required')

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
                                         b'OK:0:M:No errors\r\n',
                                         b'OK:0:RM xy:\r\n']

        with self.assertRaises(ValueError) as cm:
            p = cri.CriProbe()
            p.measure()
            p.read_measure('xy')
        err = cm.exception
        self.assertEqual(str(err), 'Invalid measurement')

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
                                         b'OK:0:M:No errors\r\n',
                                         b'OK:0:RM Y:\r\n']

        with self.assertRaises(ValueError) as cm:
            p = cri.CriProbe()
            p.measure()
            p.read_measure('Y')
        err = cm.exception
        self.assertEqual(str(err), 'Invalid measurement')

    @patch('criprobe.CriProbe.get_ports', autospec=True)
    @patch('criprobe.CriProbe.open_port', autospec=True)
    @patch('criprobe.CriProbe.send_command', autospec=True)
    def test_RM_time(self, mock_send_command, mock_open_port, mock_get_ports):
        test_port = TestPort()
        mock_get_ports.return_value = [test_port]
        mock_open_port.return_value = 'Mock Port'
        mock_send_command.side_effect = [b'OK:0:RC ID:A00489\r\n',
                                         b'OK:0:RC Model:CR-100\r\n',
                                         b'OK:0:RC InstrumentType:2\r\n',
                                         b'OK:0:M:No errors\r\n',
                                         b'OK:0:RM Time:NA\r\n']

        p = cri.CriProbe()
        p.measure()
        result = p.read_measure('Time')
        for probe_dict in result:
            self.assertEqual(probe_dict['Time'], 'NA')

    @patch('criprobe.CriProbe.get_ports', autospec=True)
    @patch('criprobe.CriProbe.open_port', autospec=True)
    @patch('criprobe.CriProbe.send_command', autospec=True)
    def test_RM_mode(self, mock_send_command, mock_open_port, mock_get_ports):
        test_port = TestPort()
        mock_get_ports.return_value = [test_port]
        mock_open_port.return_value = 'Mock Port'
        mock_send_command.side_effect = [b'OK:0:RC ID:A00489\r\n',
                                         b'OK:0:RC Model:CR-100\r\n',
                                         b'OK:0:RC InstrumentType:2\r\n',
                                         b'OK:0:M:No errors\r\n',
                                         b'OK:0:RM Mode:Colorimeter\r\n']

        p = cri.CriProbe()
        p.measure()
        result = p.read_measure('Mode')
        for probe_dict in result:
            self.assertEqual(probe_dict['Mode'], 'Colorimeter')

    @patch('criprobe.CriProbe.get_ports', autospec=True)
    @patch('criprobe.CriProbe.open_port', autospec=True)
    @patch('criprobe.CriProbe.send_command', autospec=True)
    def test_RM_exposure(self, mock_send_command, mock_open_port, mock_get_ports):
        test_port = TestPort()
        mock_get_ports.return_value = [test_port]
        mock_open_port.return_value = 'Mock Port'
        mock_send_command.side_effect = [b'OK:0:RC ID:A00489\r\n',
                                         b'OK:0:RC Model:CR-100\r\n',
                                         b'OK:0:RC InstrumentType:2\r\n',
                                         b'OK:0:M:No errors\r\n',
                                         b'OK:0:RM Exposure:111.622 msec\r\n']

        p = cri.CriProbe()
        p.measure()
        result = p.read_measure('Exposure')
        for probe_dict in result:
            self.assertEqual(probe_dict['Exposure'], 111.622)
            self.assertEqual(probe_dict['Unit'], 'msec')

    @patch('criprobe.CriProbe.get_ports', autospec=True)
    @patch('criprobe.CriProbe.open_port', autospec=True)
    @patch('criprobe.CriProbe.send_command', autospec=True)
    def test_RM_RangeMode(self, mock_send_command, mock_open_port, mock_get_ports):
        test_port = TestPort()
        mock_get_ports.return_value = [test_port]
        mock_open_port.return_value = 'Mock Port'
        mock_send_command.side_effect = [b'OK:0:RC ID:A00489\r\n',
                                         b'OK:0:RC Model:CR-100\r\n',
                                         b'OK:0:RC InstrumentType:2\r\n',
                                         b'OK:0:M:No errors\r\n',
                                         b'OK:0:RM RangeMode:Auto\r\n']

        p = cri.CriProbe()
        p.measure()
        result = p.read_measure('RangeMode')
        for probe_dict in result:
            self.assertEqual(probe_dict['RangeMode'], 'Auto')

    @patch('criprobe.CriProbe.get_ports', autospec=True)
    @patch('criprobe.CriProbe.open_port', autospec=True)
    @patch('criprobe.CriProbe.send_command', autospec=True)
    def test_RM_SyncFreq(self, mock_send_command, mock_open_port, mock_get_ports):
        test_port = TestPort()
        mock_get_ports.return_value = [test_port]
        mock_open_port.return_value = 'Mock Port'
        mock_send_command.side_effect = [b'OK:0:RC ID:A00489\r\n',
                                         b'OK:0:RC Model:CR-100\r\n',
                                         b'OK:0:RC InstrumentType:2\r\n',
                                         b'OK:0:M:No errors\r\n',
                                         b'OK:0:RM SyncFreq:0.00 Hz\r\n']

        p = cri.CriProbe()
        p.measure()
        result = p.read_measure('SyncFreq')
        for probe_dict in result:
            self.assertEqual(probe_dict['SyncFreq'], 0.00)
            self.assertEqual(probe_dict['Unit'], 'Hz')

    @patch('criprobe.CriProbe.get_ports', autospec=True)
    @patch('criprobe.CriProbe.open_port', autospec=True)
    @patch('criprobe.CriProbe.send_command', autospec=True)
    def test_RM_CCT(self, mock_send_command, mock_open_port, mock_get_ports):
        test_port = TestPort()
        mock_get_ports.return_value = [test_port]
        mock_open_port.return_value = 'Mock Port'
        mock_send_command.side_effect = [b'OK:0:RC ID:A00489\r\n',
                                         b'OK:0:RC Model:CR-100\r\n',
                                         b'OK:0:RC InstrumentType:2\r\n',
                                         b'OK:0:M:No errors\r\n',
                                         b'OK:0:RM CCT:5577,-0.0100\r\n']

        p = cri.CriProbe()
        p.measure()
        result = p.read_measure('CCT')
        for probe_dict in result:
            self.assertEqual(probe_dict['CCT'].tolist(), [5577.0, -0.01])

    @patch('criprobe.CriProbe.get_ports', autospec=True)
    @patch('criprobe.CriProbe.open_port', autospec=True)
    @patch('criprobe.CriProbe.send_command', autospec=True)
    def test_RM_radiometric(self, mock_send_command, mock_open_port, mock_get_ports):
        test_port = TestPort()
        mock_get_ports.return_value = [test_port]
        mock_open_port.return_value = 'Mock Port'
        mock_send_command.side_effect = [b'OK:0:RC ID:A00489\r\n',
                                         b'OK:0:RC Model:CR-100\r\n',
                                         b'OK:0:RC InstrumentType:2\r\n',
                                         b'OK:0:M:No errors\r\n',
                                         b'OK:0:RM Radiometric:0,3.209e-01,8.835e+17\r\n']

        p = cri.CriProbe()
        p.measure()
        result = p.read_measure('Radiometric')
        for probe_dict in result:
            self.assertEqual(probe_dict['Radiometric'].tolist(), [0, 3.209e-01, 8.835e+17])

    @patch('criprobe.CriProbe.get_ports', autospec=True)
    @patch('criprobe.CriProbe.open_port', autospec=True)
    @patch('criprobe.CriProbe.send_command', autospec=True)
    def test_RM_spectrum(self, mock_send_command, mock_open_port, mock_get_ports):
        test_port = TestPort()
        mock_get_ports.return_value = [test_port]
        mock_open_port.return_value = 'Mock Port'
        mock_send_command.side_effect = [b'OK:0:RC ID:A00489\r\n',
                                         b'OK:0:RC Model:CR-100\r\n',
                                         b'OK:0:RC InstrumentType:2\r\n',
                                         b'OK:0:M:No errors\r\n',
                                         b'OK:0:RM Spectrum:380.0,780.0,2.0,201\r\n'
                                         b'2.119e-24\r\n'
                                         b'1.913e-24']

        p = cri.CriProbe()
        p.measure()
        result = p.read_measure('Radiometric')
        for probe_dict in result:
            self.assertEqual(probe_dict['Radiometric'].tolist(), [380.0, 780.0, 2.0, 201, 2.119e-24, 1.913e-24])


if __name__ == '__main__':
    unittest.main()
