from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import C


class Profile(Page):
    form_model = 'player'
    form_fields = ['political_ide', 'political_aff', 'political_gov_sup','next_election', 'sex','age','status', 'educ','religion']
    form_fields_short = ['political_ide' , 'sex','age', 'educ','religion']



page_sequence = [Profile]