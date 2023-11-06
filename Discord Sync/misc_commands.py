import re
import sys

def auto_convert(value):
    try: return int(value)
    except ValueError:
        try: return float(value)
        except ValueError:
            if value.lower() in ['true', 'false']: return value.lower() == 'true'
            else: return value

def get_key(val, dict):
   for key, value in dict.items():
      if val == value:
         return key
   return False

def remove_emojis(text):
    regrex_pattern = re.compile(pattern = "["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
                           "]+", flags = re.UNICODE)
    return regrex_pattern.sub(r'',text)

def yes_no(text, color = ''):
    color = color.replace('red', "\033[91m").replace('yellow', "\033[93m").replace('green', "\033[92m").replace('blue', "\033[94m")
    answer = input(color + text + "\033[0m")
    if answer.lower() not in ['y', 'j', 'n']:
        yes_no(text)
    return answer.lower().replace('j', 'y') == 'y'

def print_color(text:str):
    '''Print something with the given color
    Example: print_color('//red// Text')''' 
    text = text.replace('//red// ', "\033[91m").replace('//yellow// ', "\033[93m").replace('//green// ', "\033[92m").replace('//blue// ', "\033[94m")
    print(text + "\033[0m")
