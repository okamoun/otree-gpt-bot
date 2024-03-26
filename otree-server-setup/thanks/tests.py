from otree.api import Currency as c, currency_range
from . import pages
from ._builtin import Bot
from .models import C,choices_list

class PlayerBot(Bot):

    cases = ['gpt']
    start_after=5



    inputs_cases= {'basic':{''}}

    def form_for_case(self,field_name,i,choice_list = choices_list):
        if field_name in choice_list:
            return choice_list[field_name][i % len(choice_list[field_name])]
        else :
            return '0'



    def play_round(self):
            yield (pages.page_sequence[0])

    def play_round_MAN(selfs):
        yield (pages.Decisions,{'court_decision':'1-generally to the left'})
        yield (pages.Profile,  {'age': '0', 'political_ide': '1-very left wing', 'political_aff': '1-voted for a party not in the coalition', 'political_gov_sup': '1-Strongly Oppose', 'sex': '1-Male', 'status': '1-Foreign', 'educ': '1-Did not finish high school'})

