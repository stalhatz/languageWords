import random
from dataModels import DefinitionDataModel
import pytest
import io
import pandas as pd
import sys
import requests
from functools import partial
from itertools import product

@pytest.fixture(scope="session")
def initDefDM():
  a = DefinitionDataModel.getInstance()
  words       = ["aWord" , "bWord", None]
  definitions = ["aDef" , "bDef" ,None]
  now = pd.Timestamp.now()
  timestamps  = [now, now - pd.Timedelta(days = 1) , None]
  dictionaries = ["aDict","bDict",None]
  types       = ["aType" , "bType", None]
  markups     = ["aMark" , "bMark", None]
  valueList = [words,definitions,timestamps,dictionaries,types,markups]
  for i in product(*valueList):
    record = DefinitionDataModel.Definition(*i)
    a.addDefinition(record)
  return a

def test_getDefinition(initDefDM):
  a = initDefDM
  definitions = a.getDefinitionsForWord("aWord")
  assert(len(definitions) == pow(3,5) )
  definitions = a.getDefinition( DefinitionDataModel.Definition(text = "aWord") )
  assert(len(definitions) == pow(3,5) )
  definitions = a.getDefinition( DefinitionDataModel.Definition(text = "aWord" , definition = "aDef") )
  assert(len(definitions) == pow(3,4) )

def test_replaceDefinition(initDefDM):
  a = initDefDM
  a.replaceWord("bWord","newWord")
  
  definitions = a.getDefinitionsForWord("bWord")
  assert(len(definitions) == 0 )
  
  definitions = a.getDefinitionsForWord("newWord")
  assert(len(definitions) == pow(3,5) )

  # We can not for the time being replace multiple Markups  
  # query = DefinitionDataModel.Definition(text = "newWord")
  # a.replaceMarkups(query, "Hello")
  # query = DefinitionDataModel.Definition(markups = "Hello")
  # definitions = a.getDefinition(query)
  # assert(len(definitions) == pow(3,5) )

  query = DefinitionDataModel.Definition(text = "newWord")
  a.replaceDefinition(query,"Hello World")
  query = DefinitionDataModel.Definition(definition = "Hello World")
  definitions = a.getDefinition(query)
  assert(len(definitions) == pow(3,5) )



