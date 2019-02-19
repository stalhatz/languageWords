name = "wiktionary"
languages = ["English","French"] 
dictUrls     = ["https://en.wiktionary.org/wiki/","https://fr.wiktionary.org/wiki/"]

from bs4 import BeautifulSoup
from collections import namedtuple

def createUrl(word,requestLang):
  for i,lang in enumerate(languages):
    if requestLang == lang:
      return dictUrls[i] + word.lower()
  raise ValueError("Could not find " + requestLang + " in " + name + "'s language list. Available langs : " + str(languages) )

def getDefinitionsFromHtml(html):
  Definition = namedtuple('definition', ('text', 'type'))
  definitionsList = []
  s = BeautifulSoup(html,"html.parser")
  for element in s.select("ol > li"):
    definitionsList.append(Definition(element.text.split("\n")[0] , "definition") )
  for element in s.select("ol > li > ul > li"):
    definitionsList.append(Definition(element.text.split("\n")[0] , "example") )
  return definitionsList
