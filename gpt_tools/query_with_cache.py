
import time
import numpy as np
import openai

import json
import os
import logging
import hashlib

import requests.exceptions

logger= logging.getLogger()
#
# ==========================================================================
#

## get API KEy from environment



import random
logging.basicConfig(level=logging.WARNING)


openai.api_key =  os.getenv('OPEN_API_KEY')

result_file_name= 'open_ai_result.csv'
logging.info(f"openai.api_key: {openai.api_key}")

# define a retry decorator
def retry_with_exponential_backoff(
    func,
    initial_delay: float = 1,
    exponential_base: float = 2,
    jitter: bool = True,
    max_retries: int = 10,
    errors: tuple = (openai.RateLimitError,requests.exceptions.Timeout,
                     requests.exceptions.ReadTimeout),
):

    """Retry a function with exponential backoff."""

    def wrapper(*args, **kwargs):
        # Initialize variables
        num_retries = 0
        delay = initial_delay

        # Loop until a successful response or max_retries is hit or an exception is raised
        while True:
            try:
                return func(*args, **kwargs)

            # Retry on specified errors
            except errors as e:
                # Increment retries
                num_retries += 1

                # Check if max retries has been reached
                if num_retries > max_retries:
                    raise Exception(
                        f"Maximum number of retries ({max_retries}) exceeded."
                    )

                # Increment the delay
                delay *= exponential_base * (1 + jitter * random.random())
                logging.warning(f"retrying {func.__name__} after {delay} seconds error was {e}")
                # Sleep for the delay
                time.sleep(delay)

            # Raise exceptions for any errors not specified
            except Exception as e:
                logging.error(f"Exception raised: {type(e)} {e}")
                raise e

    return wrapper


@retry_with_exponential_backoff
def completions_with_backoff(**kwargs):
    return openai.Completion.create(**kwargs)

@retry_with_exponential_backoff
def chat_completions_with_backoff(**kwargs):
    response = openai.chat.completions.create(**kwargs)
    return response
#    res=[]
#    for c in response.choices:
#        res.append({'index':c.index,
#                    'message':{'role':c.message.role,'content':c.message.content}})
#    return  {'id':response.id,'object':response.object,'created':response.created,
#             'model':response.model, 'choices': res}


def object_tojson(obj):
    return json.loads(json.dumps(obj, default=lambda o: o.__dict__,
                      sort_keys=True, indent=4))



class QueryWithCache():
    xapikeylist = []

    nb_calls =0
    nb_call_using_cache=0

    prompts=set()
    q_status=dict()


    def __init__(self,cache_file_name="cache_file.json",cache_folder="cache/"):
        self.cache_folder = cache_folder
        self.cache_file_name = self.cache_folder+cache_file_name
        self.load_cache()
        self.default_engine_papram2 = {"engine": "text-davinci-003",
                                        "temperature": 0.7,
                                        "max_tokens": 256,# "top_p" : 1,
                                          "logprobs":100, "request_timeout":30}
        self.default_engine_papram_mintemp = {"model": "gpt-3.5-turbo",
                                        "temperature": 0,
                                        "max_tokens": 256,
                                          "top_p" : 0,
                                            "frequency_penalty" : 0,
                                            "presence_penalty" : 0
        }

        self.default_engine_papram = {"model": "gpt-3.5-turbo",
                                        "temperature": 1,
                                        "max_tokens": 256
        }

    def load_cache(self):
        try:
            with open(self.cache_file_name, 'r') as f:
                self.cache_status = json.load(f)
        except FileNotFoundError:
            self.cache_status = {}

    def get_cache_size(self):
        return len(self.cache_status)
    def getapikey(self):
        if self.xapikey is None:
            self.xapikey = self.xapikeylist[0]
            self.xapikeylist=self.xapikeylist[1:]
        return self.xapikey

    def exec_open_ai(self,prompt=None, use_cache=True,ID="",engine_param=None,messages=None,
                     use_chat_completion=True):
        e_param = self.default_engine_papram.copy()
        e_param.update(engine_param)
        self.nb_calls+=1
        if use_chat_completion:
            prompt_hash = hashlib.sha224((str(messages)+str(e_param)).encode('utf-8')).digest().hex()
        else:
            prompt_hash = hashlib.sha224((prompt+str(e_param)).encode('utf-8')).digest().hex()
        unique_key = ID + "-" + prompt_hash
        self.prompts.add(prompt_hash)
        result = None
        if use_cache:
            if unique_key in self.cache_status:
                with open(self.cache_folder + unique_key + ".json", "r") as f:
                    result =  json.load(f)

            elif os.path.isfile(self.cache_folder + unique_key + ".json"):
                with open(self.cache_folder + unique_key + ".json", "r") as f:
                    result = json.load(f)
                self.cache_status[unique_key] = prompt
                with open(self.cache_file_name, 'w') as f:
                    # Dump the dictionary to the file
                    json.dump(self.cache_status, f)

        if result is None :
            # Select your transport with a defined url endpoint
            if use_chat_completion:
                ## chat completion
                logging.debug(f"using chat completion with messages {messages}")
                result = chat_completions_with_backoff(messages=messages, **e_param)
                self.cache_status[unique_key] = messages
            else :
                # Execute the query on the transport
                result = completions_with_backoff( prompt=prompt,**e_param )
                self.cache_status[unique_key] = prompt

            with open(self.cache_folder+unique_key+".json", "w") as outfile:
                logging.debug(f"writing cache file {unique_key}")

                json.dump(object_tojson(result), outfile)

            with open(self.cache_file_name , 'w') as f:
                # Dump the dictionary to the file
                json.dump(self.cache_status,f )
        else :
            self.nb_call_using_cache+=1
        print(f"cache analysis  {self.nb_call_using_cache}  / {self.nb_calls} cache size {self.get_cache_size()}")
        return result

    def cache_summary(self):
        return{"cache_size":self.get_cache_size(), "nb_calls":self.nb_calls,"nb prompts":len(self.prompts)}



def uniqvals( users, field ):
    vals = [ users[id][field] for id in users.keys() ]
    return list(set(vals))


