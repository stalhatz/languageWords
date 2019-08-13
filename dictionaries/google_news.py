
name = "googleNews"
languages = ["English","French"] 
langCodes = ["EN","FR"]
countryCodes = ["US","FR"]
import dict_types as dt
from bs4 import BeautifulSoup
from collections import namedtuple

def createUrl(word,requestLang):
  for i,lang in enumerate(languages):
    if requestLang == lang:
      return "https://www.google.com/search?q=\""+ word.lower() +"\"&tbm=nws" + "&cr=country"+countryCodes[i] + "&lr=lang_"+langCodes[i]+ "&hl="+langCodes[i]
  raise ValueError("Could not find " + str(requestLang) + " in " + str(name) + "'s language list. Available langs : " + str(languages) )

def getUrlFromHrefArg(hrefArg):
  httpPos = hrefArg.find("http")
  usgPos  = hrefArg.find("&usg=")
  saPos   = hrefArg.find("&sa=")
  vedPos   = hrefArg.find("&ved=")
  if usgPos == -1 : usgPos = len(hrefArg)
  if saPos  == -1 : saPos  = len(hrefArg)
  if vedPos == -1 : vedPos = len(hrefArg)
  endPos = min( (usgPos , saPos , vedPos) )
  return hrefArg[httpPos:endPos]


def getDefinitions(html,language):
  definitionsList = []
  titles = []
  texts  = []
  hyperlinks = []
  s = BeautifulSoup(html,"html.parser")
  for element in s.select("h3 > a"):
    titles.append(element.text.split("\n")[0])
    url = getUrlFromHrefArg(element.attrs["href"])
    hyperlinks.append(url)
  for element in s.select(".st"):
    texts.append(element.text.split("\n")[0])
  for i,title in enumerate(titles):
    definitionsList.append(dt.Definition(definition = title + "\n" + texts[i] , type = "example" , hyperlink = hyperlinks[i]) )
  return definitionsList
