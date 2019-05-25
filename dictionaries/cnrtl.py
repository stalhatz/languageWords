

name = "cnrtl"
languages = ["French"] 
dictUrls     = ["http://www.cnrtl.fr/definition/"]
import dict_types as dt
from bs4 import BeautifulSoup
import os

abbreviations = {}
def load_abbreviations():
  path = os.path.dirname(os.path.abspath(__file__))
  filename = "tlfi_abbreviations.txt"
  filename = os.path.join(path,filename)
  with open(filename,"r") as aFile:
    for line in aFile:
      splitChar = "."
      splitList = line.rsplit( splitChar, 1)
      if len(splitList) == 1:
        splitChar = chr(176)
        splitList = line.rsplit( splitChar,1 )
      abbr = splitList[0]
      tags = splitList[1]
      tag  = tags.split(",")[0]
      abbreviations[abbr + splitChar] = tag.strip()

def createUrl(word,requestLang):
  for i,lang in enumerate(languages):
    if requestLang == lang:
      return dictUrls[i] + word.lower()
  raise ValueError("Could not find " + requestLang + " in " + name + "'s language list. Available langs : " + str(languages) )

def getDefinitionsFromHtml(html,language):
  
  definitionsList = []
  s = BeautifulSoup(html,"html.parser")
  for element in s.select(".tlf_cdefinition") :
    definitionsList.append(dt.Definition(element.text.split("\n")[0] , "definition") )
  for element in s.select(".tlf_csyntagme > i"):
    definitionsList.append(dt.Definition(element.text.split("\n")[0] , "example") )
  return definitionsList

def getTagsFromHtml(html,language):
  tagsList = []
  s = BeautifulSoup(html,"html.parser")
  for element in s.select(".tlf_cdomaine > i"):
    splitList = element.text.split()
    wordList = []
    for word in splitList:
      if ("." in word) or (chr(176) in word):
        abbr = word.rsplit(".",1)[0] + "."
        if abbr.lower() in abbreviations:
          _word = abbreviations[abbr.lower()]
          tagsList.append(_word)
      else:
        _word = word
  print(tagsList)
  return tagsList

load_abbreviations()