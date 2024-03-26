from os import environ
import logging
SESSION_CONFIG_DEFAULTS = dict(real_world_currency_per_point=1, participation_fee=0)
SESSION_CONFIGS = [dict(name='basic1', num_demo_participants=4, gpt_cache=False,
                        app_sequence=['basic1',  'thanks'],
                        profile_file='/Users/olivierkamoun/PycharmProjects/tau_thesis_tools/kt_propect/data/modified_exclusions/pt_replication_modified_exclusions_data_shuffled.csv'
                        ),
                   dict(name='us_profile_html', num_demo_participants=20, gpt_cache=False,BotType='html',
                        profile_file='/Users/olivierkamoun/PycharmProjects/tau_thesis_tools/kt_propect/data/modified_exclusions/pt_replication_modified_exclusions_data_shuffled.csv',
                        app_sequence=['us_profile', 'thanks'],bot_num_rounds=4),
                    dict(name='us_profile_dialog', num_demo_participants=20, gpt_cache=False, BotType='dialog',
                            profile_file = '/Users/olivierkamoun/PycharmProjects/tau_thesis_tools/kt_propect/data/modified_exclusions/pt_replication_modified_exclusions_data_shuffled.csv',
                                   app_sequence = ['us_profile', 'thanks']),
                  
]
LANGUAGE_CODE = 'en'
REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = True
DEMO_PAGE_INTRO_HTML = ''
PARTICIPANT_FIELDS = []
SESSION_FIELDS = []

OTREE_PRODUCTION=True
ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

SECRET_KEY = 'blahblah'

# if an app is included in SESSION_CONFIGS, you don't need to list it here
INSTALLED_APPS = ['otree']


ROOMS = [
 
]
