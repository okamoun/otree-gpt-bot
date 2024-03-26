import logging
import pandas as pd


class ProfileToPromptKT():
    ##create a chet gpt prompt to define the profile of the person base on age, sex, and religion
    prep_prompt = "answer as "

    def __init__(self, profile_dict=None):
        self.profile_dict = profile_dict
        self.profile_templates = {
            "age": self.age_prompt,
            "sex": self.sex_prompt,
            "educ": self.educ_prompt,
            "religion": self.religion_prompt,
            "bill_payment": self.bill_payment_prompt,
            "Personal_Income": self.personal_income_prompt,
            "country": self.country_prompt,

        }

        self.profile_seq = [
            "sex", "age",
            "educ",
            "bill_payment",
            "Personal_Income",
            "country"
        ]

    def clean_value(self, field_name):
        c = str(self.profile_dict[field_name]).split('-')

        if len(c) > 1:
            return c[-1]
        else:
            return self.profile_dict[field_name]

    def age_prompt(self):
        if pd.isna(self.profile_dict['Age']):
            logging.warning(f"age is nan for {self.profile_dict}")
            return ""
        return f"with age of  {round(self.profile_dict['Age'])} years old"

    def sex_prompt(self):
        s_dist = {'M': 'man', 'F': 'woman', 'Female': 'woman',
                  'Male': 'man', '2-Female': 'woman'}

        return f" {s_dist.get(self.clean_value('Gender'), 'man')}"



    def bill_payment_prompt(self):
        bill_payment = self.clean_value('Bill_Payments')
        if bill_payment is not None:
            return f" every month    {bill_payment} "
        else:
            return ""
    def personal_income_prompt(self):
        income = self.clean_value('Personal_Income')
        if income is not None:
            return f" with a  yearly income is {income} USD  "
        else:
            return ""

    def educ_prompt(self):
        c = self.clean_value('Education')
        if c is not None:
            return f" with level of education of   {c}"
        else:
            return ""

    def country_prompt(self):
        c = self.clean_value('Country')
        if c is not None:
            return f" living in  {c}  "
        else:
            logging.warning(f"country is nan for {self.profile_dict}")
            return ""



    def religion_prompt(self):
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
        logging.info(f"get profile prompt with dict {self.profile_seq}")
        plist = [self.profile_templates[p]() for p in self.profile_seq]
        logging.info(f"full list of profile plist {plist}")
        plist = [p for p in plist if p != ""]
        prompt = prompt + ",".join(plist)
        logging.info(f"prompt for profile  {prompt}")
        return prompt

    def get_system_message(self, prof_dict=None):
        logging.info(f"get_system_message with dict {prof_dict} using profile kt")
        if prof_dict is None:
            prof_dict = self.profile_dict
        else:
            self.profile_dict = prof_dict
        logging.info(f"get profile profile seq {self.profile_seq}")
        prompt = "Act like a "
        for p in self.profile_seq:
            prompt = prompt + self.profile_templates[p]() + ","
        logging.info(f"resulting prompt  {prompt}")
        return prompt
