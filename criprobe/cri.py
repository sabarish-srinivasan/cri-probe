import re


class CriProbe:

    def __init__(self, simulated=False):
        # Perform autodetect here
        # When no probes are detected we'll create CR-100 and CR-250 simulated probes
        # these simulated probes will primarily be used for unit testing
        if simulated:
            self.probes = [{'Type': 'CR-100'},
                           {'Type': 'CR-250'}]
        else:
            self.probes = None
