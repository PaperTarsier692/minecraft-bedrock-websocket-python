'''Some useful (and necessary functions for my MCBE-DC Sync project'''
import re #Removing Emojis

def auto_convert(value):
    '''Converts the given string into the best value for it\n
    Examples:\n
    auto_convert('1') -> 1\n
    auto_convert('true') -> True
    '''
    try: return int(value)
    except ValueError:
        try: return float(value)
        except ValueError:
            if value.lower() in ['true', 'false']: return value.lower() == 'true'
            else: return value

def get_key(val, dict):
    '''Gets the given key in a dictionary\n
    Example: dict = {'fruit': 'apple'}\n
    get_key('apple', dict) -> fruit'''
    for key, value in dict.items():
      if val == value:
         return key
    return False

def remove_emojis(text):
    '''Removes Emojis from the given text'''
    regrex_pattern = re.compile(pattern = "["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
                           "]+", flags = re.UNICODE)
    return regrex_pattern.sub(r'',text)

def yes_no(text, color = ''):
    '''Asks the user, if he wants to do something\n
    Example: yes_no('Close the programm?', 'red')'''
    color = color.replace('red', "\033[91m").replace('yellow', "\033[93m").replace('green', "\033[92m").replace('blue', "\033[94m")
    answer = input(color + text + "\033[0m")
    if answer.lower() not in ['y', 'j', 'n']:
        yes_no(text)
    return answer.lower().replace('j', 'y') == 'y'

def print_color(text:str):
    '''Print something with the given color\n
    Example: print_color('//red// Text')''' 
    text = text.replace('//red// ', "\033[91m").replace('//yellow// ', "\033[93m").replace('//green// ', "\033[92m").replace('//blue// ', "\033[94m")
    print(text + "\033[0m")
