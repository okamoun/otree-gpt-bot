from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import C




class Thanks(Page):
    form_model = 'player'
page_sequence = [Thanks]