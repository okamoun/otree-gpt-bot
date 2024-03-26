from otree.api import (
    models,
    widgets,
    BaseConstants,
    BaseSubsession,
    BaseGroup,
    BasePlayer,
    Currency as c,
    currency_range,
)

doc = ''

class C(BaseConstants):
    NAME_IN_URL = 'basic1'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
class Subsession(BaseSubsession):
    pass
class Group(BaseGroup):
    pass

class Player(BasePlayer):

    prefered_color =  models.StringField(choices=['1-White','2-Black','3-blue','4-red','5-green'],
                                         label='What is your prefered color',
                             widget=widgets.RadioSelect)
    prefered_bike =  models.StringField(choices=['1-White bike','2-Black bike','3-blue bike','4-red bike','5-green bike'],
                                         label='What bike do you prefer',
                             widget=widgets.RadioSelect)

def my_function(player: Player):
    pass
