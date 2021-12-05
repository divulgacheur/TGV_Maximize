import unittest
from datetime import datetime

from Proposal import Proposal

a = Proposal(121, 0, datetime(2021, 12, 1, 7, 17), 'Paris', datetime(2021, 12, 1, 9, 23), 'Lyon', 'TGV InOui',
             'TGV 4173', 8)
b = Proposal(118, 0, datetime(2021, 12, 1, 7, 20), 'Paris', datetime(2021, 12, 1, 9, 29), 'Lyon', 'TGV InOui',
             'TGV 4174', 3)
not_free = Proposal(124, 5, datetime(2021, 12, 1, 7, 20), 'Paris', datetime(2021, 12, 1, 9, 29), 'Lyon', 'TGV InOui',
                    'TGV 4171', 2)
ter = Proposal(247, 0, datetime(2021, 12, 1, 7, 20), 'Paris', datetime(2021, 12, 1, 9, 29), 'Lyon', 'TER', 'TER 24762',
               67)
direct_journey_max_duration = 125


class RemoveDuplicatesTest(unittest.TestCase):

    def test_empty(self):
        self.assertEqual(Proposal.remove_duplicates([]), [], "Should be empty list")

    def test_simple(self):
        self.assertEqual(Proposal.remove_duplicates([a, a, b]), [a, b], "Should be a and b")


class FilterProposals(unittest.TestCase):

    def test_empty(self):
        self.assertEqual(Proposal.filter_proposals([], direct_journey_max_duration), [], "Should be empty list")

    def test_simple(self):
        self.assertEqual(Proposal.filter_proposals([a, b, not_free, ter], direct_journey_max_duration), [a, b],
                         "Should be a and b")

    def test_with_options(self):
        self.assertEqual(
            Proposal.filter_proposals([a, b, not_free, ter], direct_journey_max_duration, get_non_tgvmax=True),
            [a, b, not_free],
            "Should be a, b and not_free")
