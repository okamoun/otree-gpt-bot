import logging
import pandas as pd


class ProfileToPromptUS():
    # create a chet gpt prompt to define the profile of the person base on age, sex, and religion

    def __init__(self, profile_dict=None,profile_seq=None):
        self.profile_dict = profile_dict
        self.profile_templates = {
            "age": self.age_promt,
            "sex": self.sex_promt,
            "political_ide": self.political_ide_promt,
            "last_elect": self.last_elect_promt,
            "educ": self.educ_promt,
            "religion": self.religion_promt,
            "residence": self.residence_promt,
            "ownhome": self.ownhome_promt,
        }
        if profile_seq is not None:
            self.profile_seq = profile_seq
        else :
            self.profile_seq = [
                "sex", "age",
                "last_elect",
                "educ",
                "religion"
            ]

    def clean_value(self, field_name):
        c = str(self.profile_dict[field_name])
        return c

    def age_promt(self):
        if pd.isna(self.profile_dict['birthyr']):
            return ""
        else:
            age = 2020 - self.profile_dict['birthyr']

        return f"with age of  {round(age)} years old"

    def sex_promt(self):
        s_dist = {1: 'man', 2: 'woman', 'M': 'man', 'F': 'woman', 'Female': 'woman',
                  'Male': 'man', '2-Female': 'woman'}

        return f" {s_dist.get(self.clean_value('gender'), 'man')}"

    def political_ide_promt(self):
        c = self.clean_value('political_ide')
        if c is not None:
            return f" politically   {c} "
        else:
            return ""

    def last_elect_promt(self):
        c = self.clean_value('CC19_313')
        if c is not None:
            return f" during last election you  voted for a  {c}"
        else:
            return ""



    def educ_promt(self):
        c = self.clean_value('educ')

        educ_dict = {'No HS':'no High School','2-year':'2 years in college','4-year':'4 years in college','Post-grad':'post graduate studies'}

        if c is not None:
            return f" level of education is {educ_dict.get(c,c)} "
        else:
            return ""

    def religion_promt(self):
        c = self.clean_value('religpew')
        if c is not None:
            return f"  your religion is      {c}"
        else:
            return ""

    def residence_promt(self):
        c = self.clean_value('inputstate')
        if c is not None:
            return f"  you live in  {c} "
        else:
            return ""

    def ownhome_promt(self):
        c = self.clean_value('ownhome')
        if c is not None:
            return f"  you {c} your home "
        else:
            return ""

    def get(self, prof_dict=None):
        if prof_dict is None:
            prof_dict = self.profile_dict
        else:
            self.profile_dict = prof_dict

        prompt = "answer as "
        plist = [self.profile_templates[p]() for p in self.profile_seq]
        logging.info(f"full list of profile plist {plist}")
        plist = [p for p in plist if p != ""]
        prompt = prompt + ",".join(plist)

        return prompt

    def get_system_message(self, prof_dict=None, dict_only=False):
        logging.info(f"get_system_message with dict {prof_dict}")
        if prof_dict is None:
            prof_dict = self.profile_dict
        else:
            self.profile_dict = prof_dict

        prompt = "Act like a "

        if dict_only:
            return {p: self.profile_templates[p]() for p in self.profile_seq}
        else:
            for p in self.profile_seq:
                prompt = prompt + self.profile_templates[p]() + ","
            logging.info(f"resulting prompt  {prompt}")
            return prompt
