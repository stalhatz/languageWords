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

def getDefinitionsFromHtml(html,language):
  Definition = namedtuple('definition', ('definition', 'type'))
  definitionsList = []
  s = BeautifulSoup(html,"html.parser")
  for element in s.select("ol > li"):
    _def = element.text.split("\n")[0]
    if _def.strip().startswith("("):
      _def = _def.strip().split(")")[1].strip()
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
    _def = element.text.split("\n")[0]
    if _def.strip().startswith("("):
      tag = _def.strip().split(")")[0]
      tag = tag.strip().strip("(").strip(")")
      tagsList.append(tag)
  print (tagsList)
  return tagsList


