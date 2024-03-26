from otree.api import Currency as c, currency_range
from . import pages
from ._builtin import Bot

from gpt_tools import QueryWithCache,GPTBotDyna,GPTBotDialogue






class PlayerBot(Bot,GPTBotDyna):
    pages_seq = pages.page_sequence

    cases = ['gpt']
    use_profile = True




