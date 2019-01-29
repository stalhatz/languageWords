name = "wiktionary"
languages = ["English","French"] 
dictUrls     = ["https://en.wiktionary.org/wiki/","https://fr.wiktionary.org/wiki/"]

from bs4 import BeautifulSoup

def createUrl(word,requestLang):
  for i,lang in enumerate(languages):
    if requestLang == lang:
      return dictUrls[i] + word
  raise ValueError("Could not find " + requestLang + " in " + name + "'s language list. Available langs : " + str(languages) )

def getDefinitionsFromHtml(html):
  definitionsList = []
  s = BeautifulSoup(html,"html.parser")
  for element in s.select("ol > li"):
    definitionsList.append(element.text.split("\n")[0])
  return definitionsList
