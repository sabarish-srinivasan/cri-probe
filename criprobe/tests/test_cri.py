import unittest
import criprobe as cri


class MyTestCase(unittest.TestCase):
    def test_init(self):
        # Create a simulated probe object
        p = cri.CriProbe(simulated=True)

        # Check the simulated probes
        self.assertEqual(p.probes[0], {'Type': 'CR-100'})
        self.assertEqual(p.probes[1], {'Type': 'CR-250'})


if __name__ == '__main__':
    unittest.main()
