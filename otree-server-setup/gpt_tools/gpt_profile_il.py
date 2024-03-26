import logging
import pandas as pd


class ProfileToPromptIL():
    ##create a chet gpt prompt to define the profile of the person base on age, sex, and religion
    prep_prompt = "answer as "

    def __init__(self, profile_dict=None):
        self.profile_dict = profile_dict
        self.profile_templates = {
            "age": self.age_promt,
            "sex": self.sex_promt,
            "political_ide": self.political_ide_promt,
            "last_elect": self.last_elect_promt,
            "status": self.status_promt,
            "educ": self.educ_promt,
            "religion": self.religion_promt,
        }

        self.profile_seq = [
            "sex", "age",
            "political_ide",
            "last_elect",
            "status",
            "educ",
            "religion"
        ]

    def clean_value(self, field_name):
        c = str(self.profile_dict[field_name]).split('-')

        if len(c) > 1:
            return c[-1]
        else:
            return None

    def age_promt(self):
        if pd.isna(self.profile_dict['age']):
            return ""
        return f"with age of  {round(self.profile_dict['age'])} years old"

    def sex_promt(self):
        s_dist = {'M': 'man', 'F': 'woman', 'Female': 'woman',
                  'Male': 'man', '2-Female': 'woman'}

        return f" {s_dist.get(self.clean_value('sex'), 'man')}"

    def political_ide_promt(self):
        c = self.clean_value('political_ide')
        if c is not None:
            return f" politically   {c} "
        else:
            return ""

    def last_elect_promt(self):
        c = self.clean_value('political_aff')
        if c is not None:
            return f" during last election you    {c}"
        else:
            return ""

    def status_promt(self):
        s_dist = {'1-Foreign': 'not israeli', '2-New Immigrant': 'new imigrant in Israael',
                  '3-Israeli born': ' born in Israel'}
        return f" you are  {s_dist.get(self.profile_dict['status'], '')}"

    def educ_promt(self):
        c = self.clean_value('educ')
        if c is not None:
            return f" level of education is   {c} "
        else:
            return ""

    def religion_promt(self):
        c = self.clean_value('religion')

        if c == "Jew":
            c = self.clean_value('jews_religiosity')
            return f"  jewish     {c}"
        else:
            d = self.clean_value('non_jews_religiosity')
            return f"  {c} {d} "

    def get(self, prof_dict=None):
        if prof_dict is None:
            prof_dict = self.profile_dict
        else:
            self.profile_dict = prof_dict

        prompt = self.prep_prompt
        plist = [self.profile_templates[p]() for p in self.profile_seq]
        logging.info(f"full list of profile plist {plist}")
        plist = [p for p in plist if p != ""]
        prompt = prompt + ",".join(plist)

        return prompt

    def get_system_message(self, prof_dict=None):
        logging.info(f"get_system_message with dict {prof_dict}")
        if prof_dict is None:
            prof_dict = self.profile_dict
        else:
            self.profile_dict = prof_dict

        prompt = "Act like a "
        for p in self.profile_seq:
            prompt = prompt + self.profile_templates[p]() + ","
        logging.info(f"resulting prompt  {prompt}")
        return prompt
