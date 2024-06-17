import json
import logging
import os
import pandas as pd
from otree.api import Currency as c, currency_range,Page,Submission
import time
from html.parser import HTMLParser
from gpt_tools import QueryWithCache,ProfileToPromptUS
from bs4 import BeautifulSoup,element
import otree.api
import traceback

def log_traceback(ex, ex_traceback=None):
    if ex_traceback is None:
        ex_traceback = ex.__traceback__
    tb_lines = [ line.rstrip('\n') for line in
                 traceback.format_exception(ex.__class__, ex, ex_traceback)]
    logging.info(tb_lines)

logging.basicConfig(level=logging.DEBUG)
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



class GPTSoup(BeautifulSoup):
    fields = {}

    def get_all_fields(self,f, buf_text=''):
        l = []
        n = 0
        if isinstance(f, str):
            return []
        for t in f.contents:

            if isinstance(t, str):
                n += 1
                if not(isinstance(t,element.Comment)):
                    buf_text=buf_text+t.get_text()
            elif t.name == 'input':
                l.append(
                    {"field_type": t.name, "id": t.attrs.get("id"), "text": buf_text, "type": t.get("type", "text")})
                buf_text = ''
            elif t.name == 'select':
                choices = [[c.attrs.get("value", "")] for c in t.find_all('option')]
                l.append({"field_type": t.name, "id": t.attrs.get("id"), "text": buf_text, "choices": choices})
                buf_text = ''
            elif t.name in ['p'] and len(t.find_all()) > 1:
                new_fields = self.get_all_fields(t, buf_text=buf_text)
                if len(new_fields) > 0:
                    l = l + new_fields
                    buf_text = ''

            elif t.name in ['p', 'label']:
                buf_text = buf_text + " " + t.get_text()
            elif t.name == 'control':
                td = self.get_control_details(t)
                td["text"] = buf_text
                l.append(td)
                buf_text = ''
            elif t.name == 'div' and 'controls' in t.attrs.get('class', ''):
                td = self.get_control_details(t)
                td["text"] = buf_text
                l.append(td)
                buf_text = ''
            elif t.name == 'th' :
                buf_text = buf_text+ ' '+t.get_text()
            elif t.name == 'table' :
                table_fields = self.get_all_fields(t, buf_text=buf_text)
                buf_text = buf_text+ ' '+t.get_text()
                td = self.get_control_details(t)
                td['table_fields'] = table_fields
                td['text'] = buf_text
                td['field_type'] = 'table'
                td['id'] = None
                l.append(td)
            elif t.name in ['div', 'form','tr','td']:
                new_fields = self.get_all_fields(t, buf_text=buf_text)
                if len(new_fields) > 0:
                    l = l + new_fields
                    buf_text = ''
        self.fields = l
        return l

    def get_control_details(self,tcontrol):
        id = tcontrol.attrs.get('id', None)
        if len(tcontrol.find_all('select')) > 0:
            # case of selct options
            options = [[c.attrs.get('value'), c.get_text()] for c in tcontrol.find_all('option') if
                       c.attrs.get('value') != ""]
            select_tag = tcontrol.find_all('select')[0]
            r = {"field_type": select_tag.name, "id": select_tag.attrs.get('id'), "choices": options}
            return r
        if id is None:
            for c in tcontrol.find_all('div'):
                if id is None:
                    print(c.name)
                    id = c.attrs.get('id', None)
        if id is None:
            for c in tcontrol.find_all('input'):
                if id is None:
                    print(c.name)
                    id = c.attrs.get('id', None)
        if id is None:
            for c in tcontrol.find_all('textarea'):
                if id is None:
                    print(c.name)
                    id = c.attrs.get('id', None)
        labels = {c.attrs.get('for'): c.get_text() for c in tcontrol.find_all('label')}
        input = {c.attrs.get('id'): c.attrs.get('value') for c in tcontrol.find_all('input')}
        types = [c.attrs.get('type') for c in tcontrol.find_all('input')]

        if len(input) == 1:
            input_tag = tcontrol.find_all('input')[0]
            r = {"field_type": input_tag.attrs.get('type', 'text'), "id": input_tag.attrs.get('id', id)}

        elif len(input) == 0:
            logging.warning(f'no input found in control {tcontrol}')
            r = {"field_type": 'text', "id": id}

        else:
            l = [[input[k], labels.get(k, k)] for k in input]

            r = {"field_type": types[0], "id": id, "choices": l}

        return r
    def get_all_field_in_html(self):
        fields_list=[]
        for f in self.find_all('form'):
            fields_list=fields_list+self.get_all_fields(f)
        if len(fields_list)==0 :
            logging.warning(f'no fields found in html {self}')
        return fields_list

    @staticmethod
    def match_answer_to_choices(answer, choices):
        logging.info(f'match_answer_to_choices answer for answer {answer} for field {choices}')
        candidates = [c for c in choices if c[0] == answer]
        if len(candidates)== 1 :
            return candidates[0]
        elif len(candidates)>1:
            logging.warning(f'multiple candidates {candidates} for answer {answer} and choices {choices}')
            return candidates[0]
        candidates = [c for c in choices if (str(c[1]).lower() == str(answer).lower()
                                             or str(c[0]).lower() == str(answer).lower())]
        if len(candidates) == 1:
            return candidates[0]
        elif len(candidates) > 1:
            logging.warning(f'multiple candidates {candidates} for answer {answer} and choices {choices}')
            return candidates[0]
        candidates_in=  [c for c in choices if  answer.startswith(str(c[0])) ]
        if len(candidates_in)== 1 :
            logging.warning(f'using matchingfor answer {answer} and choices {choices}->    {candidates_in[0]} ')
            return candidates_in[0]
        elif len(candidates_in)>1:
            logging.warning(f'multiple candidates {candidates_in} for answer {answer} and choices {choices}')
            return candidates_in[0]
        else :
            return None

    @staticmethod
    def clean_form_answers(answer_dict,fields_list):
        logging.debug(f'cleaning answer for  {answer_dict} for fields {fields_list}')
        new_answer_dict=answer_dict.copy()
        for f in fields_list:
            logging.info(f'cleaning answer  for field {f}')
            if f['f_id'] in answer_dict:
                a_f_id = f['f_id']
                f_id = f['f_id']

            elif f['f_id'].lower() in answer_dict:
                a_f_id = f['f_id'].lower()
                f_id= f['f_id']

                new_answer_dict[f_id]=new_answer_dict[a_f_id]
                new_answer_dict.pop(a_f_id)
            elif len(fields_list)==1 and len(answer_dict)==1:
                a_f_id = list(answer_dict.keys())[0]
                f_id = f['f_id']
                new_answer_dict[f_id] = new_answer_dict[a_f_id]
                new_answer_dict.pop(a_f_id)

            else :

                a_f_id= None
                f_id = None
            if 'choices' in f and a_f_id is not None:
                logging.info(f'using match function for choices ')
                answer=GPTSoup.match_answer_to_choices( new_answer_dict [f_id],f['choices'])
                logging.info(f'answer {answer} for field {f}')

                if answer is  None:
                    new_answer_dict.pop(f['f_id'])
                else :
                    new_answer_dict[f['f_id']]=answer[0]
                    logging.info(f'cleaning result{new_answer_dict} ')
            else :
                logging.info(f'not using match function for choices for {f_id} ')
        return new_answer_dict
class GPTBotDyna(otree.api.Bot):
    template_path = os.path.dirname(os.path.realpath(__file__)) + "/template_otree_file.html"
    pages_seq=[]
    openai = QueryWithCache()
    default_engine_param={'n':2}
    prompt_template2 = 'create a json file with the answer for each field of the html form {myhtml}'
    prompt_template = 'create json to fill the html form , do not leave any filed empty or blanc, return only the json no comment :  {myhtml}'
    prompt_template_diag = '{text} give the answer in json format'
    prompt_template_diag_radio = '{text},  choose an answer among {choices_txt} give the answer in json format'
    prompt_template_diag_number = '{text} give the  answer as a number in json format'
    prompt_template_diag_table = '{text} give the  answer  in json format'

    ptp=ProfileToPromptUS()
    use_profile=True
    profile_file="/Users/olivierkamoun/PycharmProjects/tau_thesis_tools/court_survey/data/default_profile.csv"
    use_chatCompletion=True
    sleep_before_start=0
    folder_log_root ="log/"
    background_file = None
    initial_system_message = None
    folder_log ="log/"
    active_fill_form=None
    bot_type='html'
    cross_round_memory = False

    def get_profile_id(self):
        profile_id = self.participant.id_in_session -1  + (self.round_number-1) * self.session.num_participants
        logging.info(f"get_profile_id {self.participant.id_in_session} {self.round_number } profile id : {profile_id}")
        return profile_id


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ## use logfolder per session to avoid conflict between bots cretae a floder for each session id
        self.folder_log = self.folder_log_root + str(self.session.code) + "/"
        if not os.path.exists(self.folder_log):
            os.makedirs(self.folder_log)
            os.makedirs(self.folder_log+"cache/")
        use_cache = self.session.config.get('gpt_cache', True)
        if not(use_cache):
            # create local folder for cache faster and no shared cache
            self.openai = QueryWithCache(cache_folder=self.folder_log+"cache/")
        self.bot_type = self.session.config.get('BotType',
                                                    self.bot_type)
        self.active_fill_form = getattr(self, 'fill_html_form_'+self.bot_type)
        self.use_profile = self.session.config.get('use_profile', self.use_profile)
        self.profile_file = self.session.config.get('profile_file',self.profile_file)


        profile_seq = getattr(self, 'profile_seq', None)
        self.profile_seq = self.session.config.get('profile_seq', None)
        if self.profile_seq is not None :
            self.ptp.profile_seq = self.profile_seq
        else :
            self.profile_seq =  self.ptp.profile_seq
            self.session.config['profile_seq'] = self.profile_seq
        ## move to profile object to be shared between bots
        pd_profile=pd.read_csv(self.profile_file)
        logging.info(f"pd_profile reading profile file {self.profile_file} number of records {len(pd_profile)} participant {self.participant.id_in_session} ")
        self.dict_profile = pd_profile.to_dict(orient='records')


        self.default_engine_param = self.session.config.get('default_engine_param', self.default_engine_param)



        if "default_engine_param" in self.session.config:
            self.default_engine_param.update(self.session.config['default_engine_param'])

        session_details = {'nb profile in file ': len(pd_profile), 'profile file ': self.profile_file,
                           'use_profile': self.use_profile, 'default_engine_param': self.default_engine_param,
                           'bot_type': self.bot_type, 'cross_round_memory': self.cross_round_memory,
                           'profile promt generation': str(type(self.ptp))}

        json.dump(session_details, open(self.folder_log + "session_details.json", 'w'), indent=4)
        folder_name = "participant_memory"
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
            logging.info(f"folder {folder_name} created")
        else:
            logging.info(f"folder {folder_name} exist")
    def play_round(self):


        use_cache = self.session.config.get('gpt_cache', True)
        if self.case == 'gpt':
            for page in self.pages_seq:
                logging.info("Page name " + page.__name__ + " player " + self.participant._current_page_name)
                if page.__name__ != self.participant._current_page_name:
                    logging.warning(f'skipping page {page.__name__} should be {self.participant._current_page_name}')
                    continue
                dform = self.active_fill_form(page, self.html, use_cache=use_cache,use_profile=self.use_profile)
                yield Submission(page,dform , check_html=False)








    def prompt_for_default(self,f):
        text=f['text']
        fprompt = f"f'{self.prompt_template_diag}'"
        prompt = eval(fprompt)
        logging.debug(f'prompt for field {f} : {prompt} ')
        return prompt

    def prompt_for_number(self,f):
        text=f['text']
        fprompt = f"f'{self.prompt_template_diag}'"
        prompt = eval(fprompt)
        logging.debug(f'prompt for field {f} : {prompt} ')
        return prompt


    def prompt_for_radio(self,f):
        text = f['text']
        choices = f['choices']
        logging.debug(f'prompt radio for field {f} ')

        if min([c[0]==c[1] for c in choices])==True:
            # case value and label the same
            choices_txt = str([c[0] for c in choices])
        else :
            choices_txt = str([ f'{c[0]} for {c[1]} ,' for c in choices])
        fprompt = f"f'{self.prompt_template_diag_radio}'"
        prompt = eval(fprompt)

        logging.debug(f'prompt for field {f} : {prompt} ')
        return prompt

    def prompt_for_table(self,f):
        text = f['text']
        fprompt = f"f'{self.prompt_template_diag_table}'"
        prompt = eval(fprompt)

        logging.debug(f'prompt for field {f} : {prompt} ')
        return prompt


    prompt_ft={'default':prompt_for_default,'radio':prompt_for_radio,'number':prompt_for_number,'table':prompt_for_table}

    def response_to_form(self,f,results):
        logging.info(f'response_to_form f:{f} result:{results}')
        best_form_clean_len = 100
        best_form_field = {}
        if 'table_fields' in f :
            nb_fields= len(f['table_fields'])
            tf=  f['table_fields']
        elif isinstance(f,list):
            nb_fields = len(f)
            tf = f
        else :
            nb_fields=1
            tf  = [f]
        for i in tf :
            i["f_id"]=i["id"].replace("id_", "")
        logging.debug(f'nb_fields {nb_fields} tf {tf}')
        for c in results:
            dform_txt = c
            try:
                logging.info(f'analysisng {dform_txt}')
                dform = json.loads(dform_txt)
                if len(dform) > nb_fields:
                    clean_dform = {k: v for k, v in dform.items() if v is not None and len(str(v)) > 0}
                else :
                    clean_dform = dform
                clean_dform=self.htmlParse.clean_form_answers(clean_dform,tf)
                clean_dform_len = len(clean_dform)
                logging.info(f'clean  {clean_dform} using {dform_txt} nb_fields {nb_fields}')

                if clean_dform_len == nb_fields:
                    logging.info(f'same number of fields  { {tf[i]["f_id"]:  list(clean_dform.keys())[i] for i in range(nb_fields)} }')
                    l1 = [tf[i]['f_id'] for i in range(nb_fields)]
                    l2 = list(clean_dform.keys())
                    l1.sort()
                    l2.sort()
                    logging.info(f'fields {l1} {l2}')
                    best_form_field = {l1[i]: clean_dform[l2[i]] for i in range(nb_fields)}
                    break
                elif isinstance(clean_dform[list(clean_dform.keys())[0]],list) and len(clean_dform[list(clean_dform.keys())[0]])==nb_fields:
                    best_form_field = {tf[i]['f_id']: clean_dform[list(clean_dform.keys())[0]][i] for i in range(nb_fields)}
                    break
                elif clean_dform_len < best_form_clean_len:
                    ##TODO check if all fields are in the form map to closest field name
                    best_form_field = {tf[i]['f_id']: clean_dform[list(clean_dform.keys())[i]] for i in range(nb_fields)}
                    logging.info(f'multiple values return {best_form_clean_len} using {clean_dform} nb field {nb_fields}')
                    best_form_clean_len = clean_dform_len
            except Exception as e:
                logging.error(f"error in analysing {dform_txt} {e}")
                log_traceback(e)

        ##TODO main table worke
        return best_form_field


    def fill_html_form_html(self, page, html, use_cache=True,engine_param={},remove=['debug'],use_profile=True,use_participant_memory='PAQ' ):

        remove_list = ['debug', 'script']
        ep=self.default_engine_param.copy()
        self.default_engine_param.update(engine_param)

        ## read html template from file template_otree.html
        with open(self.template_path, "r") as f:
            html_header = f.read()
        page_name = "page_" + page.__name__
        myhtml_raw = html_header+str(html)[3:]
        with open(self.folder_log+page_name + '_raw.html', 'w') as file:
            file.write(myhtml_raw)
        h = myhtml_raw
        logging.debug(f"html before  {h}")
        if 'debug' in remove:
            logging.debug(f"removing debug")
            if h.find('<div class="card debug-info">') > 0:
                h = h[:h.find('<div class="card debug-info">')] + h[h.find('</body>'):]
        if 'script' in remove:
            logging.info(f"removing script")
            if h.find('<script') > 0:
                h = h[:h.find('<script')] + h[h.find('</body>'):]
        myhtml = h
        logging.debug(f"generate prompt using   {self.prompt_template}")
        fprompt = f"f'{self.prompt_template}'"
        prompt = eval(fprompt)

        logging.debug(f"generate prompt   {prompt}")

        if 'P' in use_participant_memory:
            ## check if file exists
            if self.cross_round_memory:
                memory_file = "participant_memory/"+ self.participant.code + '.json'
            else :
                memory_file = "participant_memory/"+ self.participant.code + '_'+str(self.get_profile_id())+'.json'
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
            results = [c.message.content for c in r.choices]

        else :
            with open(self.folder_log+page_name + 'prompt.html', 'w') as file:
                file.write(prompt)
            r = self.openai.exec_open_ai(prompt,use_cache=use_cache,
                                         engine_param=ep,use_chat_completion=False)
            results = [c['text'] for c in r['choices']]
        with open(self.folder_log+page_name + '_r.json', 'w') as file:
                file.write(str(results))

        self.htmlParse = GPTSoup(h, 'html.parser')
        field_list = self.htmlParse.get_all_field_in_html()

        logging.info(f"html prompt field_list {field_list}")
        clean_dform = self.response_to_form(field_list,results)
        logging.info(f"html prompt clean_dform {clean_dform}")

        best_form= clean_dform

        if 'A' in use_participant_memory:
            memory = memory + [{"role": "assistant", "content": json.dumps(best_form)}]
            json.dump(memory, open(memory_file, 'w'))
        best_form['participant_id']=self.participant.id_in_session
        return best_form


    def fill_html_form_dialog(self, page, html, use_cache=True,engine_param={},remove=['debug'],use_profile=True,use_participant_memory='PAQ' ):

        remove_list = ['debug', 'script']
        ep=self.default_engine_param.copy()
        self.default_engine_param.update(engine_param)
        ## read html template from file template_otree.html
        with open(self.template_path, "r") as f:
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
        self.htmlParse = GPTSoup(h, 'html.parser')
        field_list = self.htmlParse.get_all_field_in_html()

        logging.info('all fields in html '+ str(field_list))
        best_form={}
        for f in field_list :
            text = f['text']
            pf = self.prompt_ft.get(f.get('field_type','text'),self.prompt_ft['default'])
            prompt =pf(self,f)
            logging.info(f'prompt for field {f} : {prompt} ' )

            if 'P' in use_participant_memory:
                ## check if file exists
                memory_file = "participant_memory/"+ self.participant.code + '.json'
                if os.path.exists(memory_file):
                    memory=json.load(open(memory_file))
                    logging.info(f"memory file exists {memory_file} {memory}")
                else:

                    if self.initial_system_message is not None :
                        memory = [{"role": "system", "content": self.initial_system_message}]
                    else :
                        memory = []
                    if self.background_file is not None:
                        logging.info(f"reading background file   {self.background_file}")
                        with open(self.background_file) as f:
                            background = f.read()
                        memory = memory + [{"role": "system", "content": background}]
                    else:
                        logging.info(f"no background file ")
                    if use_profile:
                        logging.info(f"creating profile for participant  {self.participant.id_in_session} profile id {self.get_profile_id() }")
                        part_profile_dict = self.dict_profile[self.get_profile_id() ]
                        ## if profile_id in player object


                        logging.info(f"part_profile_dict {part_profile_dict}")
                        # sleep before start base on prticipant id
                        if self.sleep_before_start > 0:
                            logging.info(f"sleeping before start {self.sleep_before_start * (self.participant.id_in_session - 1)}")
                            time.sleep(self.sleep_before_start * (self.participant.id_in_session - 1))
                        if self.use_chatCompletion:
                            system_message = self.ptp.get_system_message(part_profile_dict)
                            memory = memory+[{"role": "system", "content": system_message}]



                if self.use_chatCompletion:

                    messages=memory+ [{"role":"user","content":prompt}]
                    if 'Q' in use_participant_memory:
                        memory= memory + [{"role":"user","content": prompt}]
                else :
                    prof_promt= self.ptp.get(part_profile_dict)
                    prompt = f"{prof_promt}  {prompt}"



            if self.use_chatCompletion:

                with open(self.folder_log + page_name + 'messages.json', 'w') as file:
                    json.dump(messages,file)
                r = self.openai.exec_open_ai(use_cache=use_cache,
                                             engine_param=ep,messages=messages,use_chat_completion=True)
                results = [c.message.content for c in r.choices]

            else :
                with open(self.folder_log+page_name + 'prompt.html', 'w') as file:
                    file.write(prompt)
                r = self.openai.exec_open_ai(prompt,use_cache=use_cache,
                                             engine_param=ep,use_chat_completion=False)
                results = [c['text'] for c in r['choices']]
            with open(self.folder_log+page_name + '_r.json', 'w') as file:
                    file.write(str(results))


            test_form = True

            best_form_field = self.response_to_form(f,results)

            best_form.update(best_form_field)
            if 'A' in use_participant_memory:
                memory = memory + [{"role": "assistant", "content": json.dumps(best_form_field)}]
                json.dump(memory, open(memory_file, 'w'))
            logging.info(f"best form {best_form}")
        return best_form










