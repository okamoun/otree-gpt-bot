from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import C


class Profile(Page):
    form_model = 'player'

    form_fields = ['prefered_bike','prefered_color']
    form_fields_b = [ 'prefered_color','prefered_bike']

page_sequence = [Profile]