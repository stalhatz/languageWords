

name = "wikipedia"
languages = ["English","French"] 
dictUrls     = ["https://en.wikipedia.org/wiki/","https://fr.wikipedia.org/wiki/"]

import dict_types as dt
from collections import namedtuple
import wikipedia
from wikipedia.exceptions import WikipediaException
from wikipedia.exceptions import DisambiguationError
def createUrl(word,requestLang):
  for i,lang in enumerate(languages):
    if requestLang == lang:
      return dictUrls[i] + word.lower()
  raise ValueError("Could not find " + requestLang + " in " + name + "'s language list. Available langs : " + str(languages) )

def loadData(url):
  word = url.split('/')[-1]
  language = url.split('/')[2].split('.')[0]
  wikipedia.set_lang(language)
  try:
    return wikipedia.summary(word)
  except DisambiguationError as e:
    try:
      return wikipedia.summary(e.args[1][0])
    except WikipediaException as e:
      raise ConnectionError(str(e))      
  except WikipediaException as e:
    raise ConnectionError(str(e))

def getDefinitions(data,language):
  definitionsList = []
  definitions = data.split("\n")
  for definition in definitions:
    if len(definition) > 5:
      definitionsList.append(dt.Definition(definition , "definition") )
  return definitionsList




