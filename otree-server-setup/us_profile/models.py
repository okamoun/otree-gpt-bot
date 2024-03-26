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
    NAME_IN_URL = 'us_profile'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
class Subsession(BaseSubsession):
    pass
class Group(BaseGroup):
    pass

def double_list(l):
    return [[i,i] for i in l ]
choices_list={'court_decision':['1-Generally to the left','2-Generally to the right','3-Case by case basis' ],
                  'political_ide':['1-Very left wing', '2-Left of center','3-neutral', '4-Right of center',
                                   '5-Very right wing','99-Don’t know'],
                  'political_aff': ['1-Voted for a party not in the coalition','2-Voted for a party in the coalition',
                                    '3-Didn''t vote','4-Not israeli voter'],
                  'political_gov_sup':['1-Strongly Oppose', '2-Somewhat Oppose',
                                       '3-Neutral (Neither Oppose or Support)', '4-Somewhat Support', '5-Strongly Support'],
                  'status':['1-Foreign', '2-New Immigrant', '3-US born'],
                  'sex':['1-Male', '2-Female', '3-Other'],
                  'educ':['1-Did not finish high school', '2-High school graduate', '3-Some college', '4-College graduate',
                   '5-Post graduate degree'],
                  'court_knowledge':['1-Very knowledgeable', '2-Somewhat knowledgeable', '3-Average knowledge',
                   '4-Not very knowledgeable', '5-I don’t know anything about the Court '],
                  'court_interest':['1-Not at all interested', '2-Somewhat interested', '3-Very interested'],
                  'court_interst_since':['1-I’ve always been interested in the Court', '2-My interest in the Court is more recent',
                   '3-I am not interested in the court'],
                   'religion':['1-Jew','2-Muslim','3-Christian','4-Druze',
                                     '5-Other','6-No religion/atheist','88- Don''t know','99- Does not apply'] ,
                    'non_jews_religiosity':['1- Very religious','2- Religious','3- Not so religious',
                                            '4- Not religious at all','88- Don''t know','99- Does not apply'],
                    'jews_religiosity':['1- Ultra-religious (haredi)','2- Religious','3- Traditional but religious',
                                            '4- Traditional but not so religious','5-Non-religious; secular','88- Don''t know','99- Does not apply'],
                    'next_election':['1-The current coalition','2-The opposition','3-other']}
choice_support_list = ['1-strongly support',  '2-somewhat support',
                       '3-slightly support',  '4-slightly oppose',
                       '5-somewhat oppose','6-strongly oppose']

choice_relig= [[1,'Protestant'],[2,'Roman Catholic'],[3,'Mormon'],[4 ,'Eastern or Greek Orthodox'],[5,'Jewish'],
               [6,'Muslim'],[7,'Buddhist'],[8,'Hindu'],[9,'Atheist'],[10,'Agnostic'],
               [11,'Nothing in particular'],[12,'Something else']]

class Player(BasePlayer):
    sex = models.StringField(choices=double_list(choices_list['sex']), label='What is your sex',
                             widget=widgets.RadioSelect)
    educ = models.StringField(choices=double_list(choices_list['educ']), label='Level of education', widget=widgets.RadioSelect)
    age = models.IntegerField( label='What is your age')
    race =  models.StringField(choices=['1-White','2-Black','3-Hispanic','4-Asia','5-Native American',
                               '6-Mixed','7-Other','8-Middle eastern'], label='What is your race',
                             widget=widgets.RadioSelect)

    political_ide = models.StringField(choices=double_list(choices_list['political_ide']), label='What is your political ideology?', widget=widgets.RadioSelect)

    political_us_ide = models.StringField(choices=['1-Democrate','2-Republican','3-Neutral'], label='What is your political ideology?', widget=widgets.RadioSelect)
    political_aff = models.StringField(choices=['1-Democratic candidate','2-Republican candidate','3-Someone else',
                                                '4-didn''t vote','5-I don''t recall','8-skipped'], label='Who did you vote for during last House vote in 2018??', widget=widgets.RadioSelect)
    political_gov_sup = models.StringField(choices=double_list(choices_list['political_gov_sup']), label='Please indicate your level of support or opposition to the current US government', widget=widgets.RadioSelect)
    religion = models.StringField(choices=choice_relig, label='What is your religion ',
                                widget=widgets.RadioSelect)
    non_jews_religiosity = models.StringField(choices=double_list(choices_list['non_jews_religiosity']), label='Do you consider yourself as being',
                                widget=widgets.RadioSelect)
    jews_religiosity = models.StringField(choices=double_list(choices_list['jews_religiosity']), label='Do you consider yourself as being',
                                widget=widgets.RadioSelect)
    next_election = models.StringField(choices=double_list(choices_list['next_election']), label='Who do you think will win next election?', widget=widgets.RadioSelect)
    status = models.StringField(choices=double_list(choices_list['status']), label='What is your status', widget=widgets.RadioSelect)
    profile_id= models.StringField(label='Please enter your ID')


def my_function(player: Player):
    pass
