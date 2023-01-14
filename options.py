"""
Code related to search and prompt options
"""

class SearchOptions:
    """
    Class to define options for searching
    """
    via: str
    berth_only: bool = False
    long: bool = False
    direct_only: bool = False
    max_duration: int

    def __init__(self, via=None, max_duration=None, berth_only=False,
                 direct_only=False) -> None:
        self.via = via
        self.berth_only = berth_only
        self.direct_only = direct_only
        self.max_duration = max_duration


class PromptOptions:
    """
    Class to define options for prompting
    """

    verbosity: bool
    quiet: bool
    debug: bool
    long: bool

    def __init__(self, verbosity=False, quiet=False, debug = False, long = False):
        self.verbosity = verbosity
        self.quiet = quiet
        self.debug = debug
        self.long = long


class Options:
    """
    Options used during search
    """
    search_options: SearchOptions
    prompt_options: PromptOptions
    def __init__(self, search_options, prompt_options):
        self.search_options = search_options
        self.prompt_options = prompt_options
