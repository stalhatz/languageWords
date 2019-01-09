#We should create classes for offline and online dictionaries (subclasses of the same baseclass)
#For the time being it will just be functions
import unidecode
from bs4 import BeautifulSoup

def createUrl(dictName , word):
  if dictName == "wiktionary":
    url = "https://fr.wiktionary.org/wiki/" + word
  elif dictName == "larousse":
    unaccentedWord = unidecode.unidecode(word)
    url = "https://www.larousse.fr/dictionnaires/francais/" + unaccentedWord
  else:
    raise ValueError("Unsupported dictionary")
  return url

def getDefinitionsFromHtml(url, html):
  definitionsList = []
  s = BeautifulSoup(html,"html.parser")
  if "wiktionary" in url:
  #Wiktionary
    for element in s.select("ol > li"):
      definitionsList.append(element.text.split("\n")[0])
  elif "larousse" in url:
    #Larousse
    for element in s.find_all("li",class_ = "DivisionDefinition"):
      definitionsList.append(str(element.find(text=True,recursive=False) ))
      #print (self.definitionsList)
  return definitionsList