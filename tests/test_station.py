import unittest

from Station import Station

paris = Station("Test Station", identifier='870001')
ventimiglia = Station("Ventimiglia", identifier='34248')


class StationTest(unittest.TestCase):

    def test_station(self):
        self.assertEqual(paris.name, "Test Station")
        self.assertEqual(paris.id, '870001')

    def test_station_country(self):
        self.assertEqual(paris.is_in_france(), True, "Station must be in France")
        self.assertEqual(ventimiglia.is_in_france(), False, "Station must not be in France")

    def test_station_distance(self):
        pass