import unittest
from datetime import datetime

from proposal import Proposal

normal_train = Proposal(121, 0, datetime(2021, 12, 1, 7, 17), 'Paris',
                        datetime(2021, 12, 1, 9, 23), 'Lyon', 'TGV InOui', '4173', 8)

another_normal = Proposal(118, 0, datetime(2021, 12, 1, 7, 20), 'Paris',
                          datetime(2021, 12, 1, 9, 29), 'Lyon', 'TGV InOui', '4174', 3)

not_free = Proposal(124, 5, datetime(2021, 12, 1, 7, 20), 'Paris',
                    datetime(2021, 12, 1, 9, 29), 'Lyon', 'TGV InOui', 'TGV 4171', 2)

ter = Proposal(247, 0, datetime(2021, 12, 1, 7, 20), 'Paris',
               datetime(2021, 12, 1, 9, 29), 'Lyon', 'TER', 'TER 24762', 67)

MAX_DURATION = 125


class RemoveDuplicatesTest(unittest.TestCase):
    """
    Test the remove_duplicates function
    """

    def test_empty(self):
        """
        Test the remove_duplicates function with an empty list
        """

        self.assertEqual(Proposal.remove_duplicates([]), [], "Should be empty list")

    def test_simple(self):
        """
        Test the remove_duplicates function with a simple list
        """
        self.assertEqual(Proposal.remove_duplicates([normal_train, normal_train, another_normal]),
                         [normal_train, another_normal],
                         "Should be a and b")


class FilterProposals(unittest.TestCase):
    """
    Test the filter_proposals function
    """

    def test_empty(self):
        """
        Test the filter_proposals function with an empty list
        """
        self.assertEqual(Proposal.filter([], MAX_DURATION),
                         [],
                         "Should be empty list")

    def test_simple(self):
        """
        Test the filter_proposals function with a simple list
        """
        self.assertEqual(Proposal.filter([normal_train, another_normal, not_free, ter],
                                         MAX_DURATION),
                         [normal_train, another_normal],
                         "Should be a and b")

    def test_with_options(self):
        """
        Test the filter_proposals function with a simple list but also with SearchOptions
        to allow non tgvmax eligible trains
        """

        self.assertEqual(
            Proposal.filter([normal_train, another_normal, not_free, ter],
                            MAX_DURATION, get_non_tgvmax=True),
            [normal_train, another_normal, not_free],
            "Should be a, b and not_free")


class Display(unittest.TestCase):
    """
    Test the display function
    """

    def test_simple(self):
        """
        Test the display function with a simple list
        """
        self.assertEqual(normal_train.print(long=False), [normal_train, another_normal],
                         "Should be a and b")

    def test_with_options(self):
        """
        Test the display function with a simple list but also with SearchOptions
        """
        self.assertEqual(
            Proposal.filter([normal_train, another_normal, not_free, ter],
                            MAX_DURATION, get_non_tgvmax=True),
            [normal_train, another_normal, not_free], "Should be a, b and not_free")
