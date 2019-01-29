name          = "larousse" 
languages  = ["French"]
dictUrls      = ["https://www.larousse.fr/dictionnaires/francais/"]

from bs4 import BeautifulSoup
import unidecode

def createUrl(word,requestLang):
  word = unidecode.unidecode(word)
  if requestLang == languages[0]:
      return dictUrls[0] + word
  raise ValueError("Could not find " + requestLang + " in " + name + "'s language list. Available langs : " + str(languages) )


def getDefinitionsFromHtml(html):
  definitionsList = []
  s = BeautifulSoup(html,"html.parser")
  for element in s.find_all("li",class_ = "DivisionDefinition"):
    definitionsList.append(str(element.find(text=True, recursive=False)))
  return definitionsList
