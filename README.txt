=======================================================
 Otree extension to use CathGPT as participant
=======================================================
The otree-server-setup directory contain an example of the setup

How to use with your project :
 - copy the gpt_tools directory in your otree project directory
  -run pip install -r requirements.txt
  - start otreee server with the command `otree devserver`
  - in you otree project add or modify test.py to add the gpt bots(see sample_test.py)
        module_path = os.path.abspath(os.path.join('../../otree-gpt-bot'))
        if module_path not in sys.path:
            sys.path.append(module_path)

        from gpt_tools import GPTBotDyna
        class PlayerBot(Bot,GPTBotDyna):
            pages_seq = pages.page_sequence

            cases = ['gpt']
            use_profile = True

  - Check the config setting you want to use: the  item you can add to the settings are :
         gpt_cache=False, (default is True)
          profile_file= (full path to the profile file)
          BotType='dialog' (dialog or html)
  - to launches the gpt bots :  otree browser_bots #SETTING_NAME #NB_PARTICIPANTS exam[le : otree browser_bots basic1anddialog 10
