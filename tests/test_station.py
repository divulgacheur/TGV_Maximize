import unittest

from station import Station

paris = Station("Test Station", identifier='870001')
ventimiglia = Station("Ventimiglia", identifier='34248')


class StationTest(unittest.TestCase):
    """
    Test the Station class
    """

    def test_station(self):
        """
        Test the Station class
        :return:
        """
        self.assertEqual(paris.name, "Test Station")
        self.assertEqual(paris.identifier, '870001')

    def test_station_country(self):
        """
        Test the country of the station
        """
        self.assertEqual(paris.is_in_france(), True, "Station must be in France")
        self.assertEqual(ventimiglia.is_in_france(), False, "Station must not be in France")
