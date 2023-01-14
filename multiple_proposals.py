"""
Related code to proposal composed by several segments <=> Multiple proposal
"""
from typing import TYPE_CHECKING

from proposal import console
from options import SearchOptions, PromptOptions

if TYPE_CHECKING:
    from proposal import Proposal


class MultipleProposals:
    """
    Class that represents a multiple proposal, a proposal composed by several segments
    """

    def __init__(self, *proposals: 'Proposal'):
        self.proposals = proposals

    def print(self, opts: SearchOptions, color:bool = True) -> None:
        """
        Prints the MultipleProposals object in a human-readable format
        :param opts:
        :param color: Allow alternating background color on every other line
        :return: None
        """

        first = self.proposals[0]
        second = self.proposals[1]

        # For the berth only option, we exclude Intercites de Nuit proposals without a berth
        if opts.berth_only:
            for seg in self.proposals:
                if seg.metadata.transporter == 'IC NUIT' and 'berths' not in seg.metadata.remaining_seats:
                    return
        background_style = " on rgb(0,83,167)" if color else " on rgb(4,39,112)"
        time_style = "bold yellow"

        console.print(f'{first.departure_station.display_name.center(23)} ', style='default'+background_style, end='')
        console.print(f'{first.departure_date.strftime("%H:%M")}',style=time_style+background_style, highlight=False, end='')
        console.print(f' → {first.arrival_station.display_name.center(23)}', style='default'+background_style, end='' )
        console.print(f' {first.arrival_date.strftime("%H:%M")} ', style=time_style+background_style, highlight=False, end='')
        console.print(f' {first.metadata.transporter.center(10)} {first.metadata.vehicle_number.center(5)}' if opts.long else '', style='default' + background_style, end='')

        # If connection stations are different, i.e. Nimes <-> Nimes Pont du Gard,
        # display the name of two connection stations
        # Else, display only the station name once
        if second.departure_station.display_name != first.arrival_station.display_name:
            console.print(f' ⭾ {second.departure_station.display_name.center(23)}', style='default'+background_style, end='')
            console.print(f' {second.departure_date.strftime("%H:%M")}', style=time_style+background_style, highlight=False, end='')
        else:
            console.print(f' ⏲  {second.departure_date.strftime("%H:%M")}', style=time_style +background_style, highlight=False, end='')

        console.print(f' → {second.arrival_station.display_name.center(23)} ', style='default'+background_style, end='' )
        console.print(f'{second.arrival_date.strftime("%H:%M")} ', style=time_style+background_style, highlight=False, end='')
        console.print(
            f' {second.metadata.transporter.center(10)} {second.metadata.vehicle_number.center(5)}' if opts.long else '',
            f'| {second.display_seats() if second.get_remaining_seats() < first.get_remaining_seats() else first.display_seats()} ', style='default'+background_style
        )

    @staticmethod
    def display(segment1, segment2, search_opts: SearchOptions, prompt_opts: PromptOptions) -> None:
        """
        Display segments of multiple proposal
        :param segment1: list of proposals for the first segment
        :param segment2: list of proposals for the second segment
        :param search_opts: search options provided by the user
        :param prompt_opts: prompt options provided by the user

        :return:
        """
        background = 0
        proposal_found = False
        for proposal_1 in segment1:
            for proposal_2 in segment2:
                if proposal_2.departure_date > proposal_1.arrival_date:
                    if not proposal_found and prompt_opts.verbosity:
                        print("Segments 1 & 2 combined :")
                    MultipleProposals(proposal_1, proposal_2).print(search_opts, background%2==0)
                    proposal_found = True
                    background+=1

        if not proposal_found and prompt_opts.verbosity:
            print("Connection is physically impossible between available proposals")
