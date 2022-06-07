import unittest
import criprobe as cri
import re


class MyTestCase(unittest.TestCase):
    def test_init(self):
        # Create a simulated probe object
        p = cri.CriProbe(simulated=True)

        # Check the simulated probes
        p0 = {'ID': 'A19999', 'Model': 'CR-100', 'Type': 'Colorimeter'}
        self.assertEqual(p.probes[0], p0)

        p1 = {'ID': 'A29999', 'Model': 'CR-250', 'Type': 'Spectroradiometer'}
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
                self.assertTrue(probe['Type'] == 'Photometer' or probe['Type'] == 'Colorimeter' or probe['Type'] == 'Spectroradiometer')
        else:
            pass


if __name__ == '__main__':
    unittest.main()
