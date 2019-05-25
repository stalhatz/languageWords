
name = "googleNews"
languages = ["English","French"] 
import dict_types as dt
from bs4 import BeautifulSoup
from collections import namedtuple

def createUrl(word,requestLang):
  for i,lang in enumerate(languages):
    if requestLang == lang:
      return "https://www.google.com/search?q="+ word.lower() +"&tbm=nws" 
  raise ValueError("Could not find " + requestLang + " in " + name + "'s language list. Available langs : " + str(languages) )

def getDefinitionsFromHtml(html,language):
  definitionsList = []
  titles = []
  texts  = []
  s = BeautifulSoup(html,"html.parser")
  for element in s.select("h3 > a"):
    titles.append(element.text.split("\n")[0])
  for element in s.select(".st"):
    texts.append(element.text.split("\n")[0])
  for title,text in zip(titles,texts):
    definitionsList.append(dt.Definition(title + "\n" + text , "example") )
  return definitionsList
