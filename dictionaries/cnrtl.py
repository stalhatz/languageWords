name = "cnrtl"
languages = ["French"] 
dictUrls     = ["http://www.cnrtl.fr/definition/"]

from bs4 import BeautifulSoup
from collections import namedtuple

def createUrl(word,requestLang):
  for i,lang in enumerate(languages):
    if requestLang == lang:
      return dictUrls[i] + word.lower()
  raise ValueError("Could not find " + requestLang + " in " + name + "'s language list. Available langs : " + str(languages) )

def getDefinitionsFromHtml(html):
  Definition = namedtuple('definition', ('definition', 'type'))
  definitionsList = []
  s = BeautifulSoup(html,"html.parser")
  for element in s.select(".tlf_cdefinition") :
    definitionsList.append(Definition(element.text.split("\n")[0] , "definition") )
  for element in s.select(".tlf_csyntagme > i"):
    definitionsList.append(Definition(element.text.split("\n")[0] , "example") )
  return definitionsList
