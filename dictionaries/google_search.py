name = "googleSearch"
languages = ["English","French"] 
langCodes = ["EN","FR"]
countryCodes = ["US","FR"]
import dict_types as dt
from bs4 import BeautifulSoup
from collections import namedtuple

def createUrl(word,requestLang):
  for i,lang in enumerate(languages):
    if requestLang == lang:
      return "https://www.google.com/search?q=\""+ word.lower() +"\"" + "&cr=country"+countryCodes[i] + "&lr=lang_"+langCodes[i] + "&hl="+langCodes[i]
  raise ValueError("Could not find " + str(requestLang) + " in " + str(name) + "'s language list. Available langs : " + str(languages) )
