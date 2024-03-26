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
    NAME_IN_URL = 'thanks'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
class Subsession(BaseSubsession):
    pass
class Group(BaseGroup):
    pass

def double_list(l):
    return [[i,i] for i in l ]

class Player(BasePlayer):
    pass

choices_list=dict()

def my_function(player: Player):
    pass
