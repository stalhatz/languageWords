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

def breakUpDefinitionLine(_def):
  tagsList = []
  splitList = _def.split(")")
  lastElement = _def
  for i,element in enumerate(splitList):
    if element.strip().startswith("("):
      tag = element.strip().strip("(")
      tagsList.append(tag)
    else:
      lastElement = element
      break
  lEIndex = _def.find(lastElement)
  definition = _def[lEIndex:]
  return tagsList,definition

def getDefinitionsFromHtml(html,language):
  Definition = namedtuple('definition', ('definition', 'type'))
  definitionsList = []
  s = BeautifulSoup(html,"html.parser")
  for element in s.select("ol > li"):
    _def = element.text.split("\n")[0]
    _,_def = breakUpDefinitionLine(_def)
    definitionsList.append(Definition( _def , "definition") )
  for element in s.select("ol > li > ul > li"):
    definitionsList.append(Definition(element.text.split("\n")[0] , "example") )
  return definitionsList

def getTagsFromHtml(html,language):
  tagsList = []
  s = BeautifulSoup(html,"html.parser")
  if language == "French":
    grammaticalTag = s.select(".mw-headline > .titredef")[0].text
    tagsList.append(grammaticalTag)
  for element in s.select("ol > li"):
    tags,_ = breakUpDefinitionLine(element.text.split("\n")[0])
    tagsList += tags
  print (tagsList)
  return tagsList




