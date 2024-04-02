import json
import logging
import os
import pandas as pd
from otree.api import Currency as c, currency_range,Page,Submission
import time
from html.parser import HTMLParser
from gpt_tools import QueryWithCache,ProfileToPromptIL
from bs4 import BeautifulSoup
import otree.api
logging.basicConfig(level=logging.WARNING)
pages=[]
class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.fields = {}


    def handle_starttag(self, tag, attrs):
        if tag in ['input', 'select', 'textarea']:
            attrs_dict = dict(attrs)
            field_name = attrs_dict.get('name')
            if field_name:
                if tag == 'select':
                    self.fields[field_name] = []
                elif tag == 'input' and attrs_dict.get('type') == 'radio':
                    value = attrs_dict.get('value', '')
                    field_values = self.fields.get(field_name, [])
                    field_values.append(value)
                    self.fields[field_name] = field_values

    def handle_data(self, data):
        if data.strip() and len(self.fields) > 0:
            field_name = next(reversed(self.fields))
            field_values = self.fields[field_name]
            field_values.append(data.strip())
            self.fields[field_name] = field_values





class GPTBot(otree.api.Bot):
    pages_seq=[]
    openai = QueryWithCache()
    default_engine_param={'n':2}
    prompt_template2 = 'create a json file with the answer for each field of the html form {myhtml}'
    prompt_template = 'create json to fill the html form , do not leave any filed empty or blanc, return only the json no comment :  {myhtml}'
    ptp=ProfileToPromptIL()
    use_profile=True
    profile_file="/Users/olivierkamoun/PycharmProjects/tau_thesis_tools/court_survey/data/default_profile.csv"
    use_chatCompletion=True
    sleep_before_start=0
    folder_log ="/Users/olivierkamoun/PycharmProjects/otree-survey/log/"
    background_file = None

    def get_profile_id(self):
        return self.participant.id_in_session -1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.profile_file = self.session.config.get('profile_file',
                                                    self.profile_file)
        pd_profile=pd.read_csv(self.profile_file)
        logging.info(f"pd_profile reading profile file {self.profile_file} number of records {len(pd_profile)}")
        self.dict_profile = pd_profile.to_dict(orient='records')

        self.use_profile =self.session.config.get('use_profile',self.use_profile)
        self.default_engine_param = self.session.config.get('default_engine_param',self.default_engine_param)
        session_details={'nb profile in file ':len(pd_profile), }
        ## check if folder exist else create it
        folder_name = 'participant_memory'



    def play_round(self):
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
            logging.info(f"folder {folder_name} created")
        else:
            logging.info(f"folder {folder_name} exist")
        use_cache = self.session.config.get('gpt_cache', True)
        if self.case == 'gpt':
            for page in self.pages_seq:
                logging.info("Page name " + page.__name__ + " player " + self.participant._current_page_name)
                if page.__name__ != self.participant._current_page_name:
                    logging.warning(f'skipping page {page.__name__} should be {self.participant._current_page_name}')
                    continue
                dform = self.fill_html_form(page, self.html, use_cache=use_cache)
                yield Submission(page,dform , check_html=False)




    def fill_html_form(self, page, html, use_cache=True,engine_param={},remove=['debug'],use_profile=True,use_participant_memory='PAQ' ):

        remove_list = ['debug', 'script']
        ep=self.default_engine_param.copy()
        self.default_engine_param.update(engine_param)
        ## read html template from file template_otree.html
        template_path= os.path.abspath(os.path.join('./template_otree_file.html'))
        with open(template_path, "r") as f:
                html_header = f.read()
        page_name = "page_" + page.__name__
        myhtml_raw = html_header+str(html)[3:]
        with open(self.folder_log+page_name + '_raw.html', 'w') as file:
            file.write(myhtml_raw)
        h = myhtml_raw
        logging.debug(f"html before  {h}")
        if 'debug' in remove:
            logging.info(f"removing debug")
            if h.find('<div class="card debug-info">') > 0:
                h = h[:h.find('<div class="card debug-info">')] + h[h.find('</body>'):]
        if 'script' in remove:
            logging.info(f"removing script")
            if h.find('<script') > 0:
                h = h[:h.find('<script')] + h[h.find('</body>'):]
        myhtml = h
        logging.info(f"generate prompt using   {self.prompt_template}")
        fprompt = f"f'{self.prompt_template}'"
        prompt = eval(fprompt)

        logging.debug(f"generate prompt   {prompt}")

        if 'P' in use_participant_memory:


            ## check if file exists
            memory_file = "participant_memory/"+ self.participant.code + '.json'
            if os.path.exists(memory_file):
                memory=json.load(open(memory_file))
                logging.info(f"memory file exists {memory_file} {memory}")
            elif use_profile:
                logging.info(f"creating profile for participant  {self.participant.id_in_session} profile id {self.get_profile_id() }")
                part_profile_dict = self.dict_profile[self.get_profile_id() ]
                logging.info(f"part_profile_dict {part_profile_dict}")
                # sleep before start base on prticipant id
                if self.sleep_before_start > 0:
                    logging.info(f"sleeping before start {self.sleep_before_start * (self.participant.id_in_session - 1)}")
                    time.sleep(self.sleep_before_start * (self.participant.id_in_session - 1))
                if self.use_chatCompletion:
                    system_message = self.ptp.get_system_message(part_profile_dict)
                    memory = [{"role": "system", "content": system_message}]
                if self.background_file is not None:
                    logging.info(f"reading background file   {self.background_file}")
                    with open(self.background_file) as f:
                        background = f.read()
                    memory = memory + [{"role": "system", "content": background}]
                else :
                    logging.info(f"no background file ")
            else :
              memory = []

            if self.use_chatCompletion:


                messages=memory+ [{"role":"user","content":prompt}]
                if 'Q' in use_participant_memory:
                    htmlParse = BeautifulSoup(myhtml, 'html.parser')
                    memory= memory + [{"role":"user","content": htmlParse.getText()}]
            else :
                prof_promt= self.ptp.get(part_profile_dict)
                prompt = f"{prof_promt}  {prompt}"
        elif self.use_chatCompletion:
            messages = [ {"role": "user", "content": prompt}]


        with open(self.folder_log+page_name + '.html', 'w') as file:
            file.write(myhtml)


        if self.use_chatCompletion:

            with open(self.folder_log + page_name + 'messages.json', 'w') as file:
                json.dump(messages,file)
            r = self.openai.exec_open_ai(use_cache=use_cache,
                                         engine_param=ep,messages=messages,use_chat_completion=True)
            results = [c['message']['content'] for c in r['choices']]

        else :
            with open(self.folder_log+page_name + 'prompt.html', 'w') as file:
                file.write(prompt)
            r = self.openai.exec_open_ai(prompt,use_cache=use_cache,
                                         engine_param=ep,use_chat_completion=False)
            results = [c['text'] for c in r['choices']]
        with open(self.folder_log+page_name + '_r.json', 'w') as file:
                file.write(str(results))


        test_form = True
        best_form = {}
        best_form_clean_len= 0
        for c in results:
            dform_txt = c
            try :
                dform = json.loads(dform_txt)
                fields_with_id={c[3:]:dform[c] for c in dform.keys() if c.startswith("id_")}
                fields_with_id_and_nb = {c.split('-')[0]: fields_with_id[c] for c in fields_with_id.keys() if len(c.split('-'))>0}
                dform.update(fields_with_id)
                dform.update(fields_with_id_and_nb)
                clean_dform_len = len({k:v for k, v in dform.items() if v is not None and len(str(v))>0})
                if clean_dform_len == len(dform):
                    best_form = dform
                    break
                elif clean_dform_len > best_form_clean_len :
                    best_form_clean_len = clean_dform_len
                    best_form = dform
            except Exception as e:
                logging.error(f"error in eval {dform_txt} {e}")
        if 'A' in use_participant_memory:
            memory = memory + [{"role": "assistant", "content": json.dumps(best_form)}]
            json.dump(memory, open(memory_file, 'w'))
        best_form['participant_id']=self.participant.id_in_session
        return best_form
