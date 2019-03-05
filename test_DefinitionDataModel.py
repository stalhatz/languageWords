import random
from dataModels import OnlineDefinitionDataModel
import pytest
import io
import pandas
import sys

fake_dictionary1_file_contents = """
name = "fake1"
languages = ["Lang1","Lang2"] 
dictUrls     = ["https://fake1_1.com","https://fake1_2.com"]

def createUrl(word,requestLang):
  return dictUrls[0] + "/" + word

def getDefinitionsFromHtml(html):
  definitionsList = []
  definitionsList.append("fake1Definition1")
  return definitionsList
  """
fake_dictionary2_file_contents = """
name = "fake2"
languages = ["Lang2","Lang3"] 
dictUrls     = ["https://fake2_2.com","https://fake2_3.com"]

def createUrl(word,requestLang):
  return dictUrls[0] + "/" + word

def getDefinitionsFromHtml(html):
  definitionsList = []
  definitionsList.append("fake2Definition1")
  return definitionsList
  """
fake_dict_contents = []
fake_dict_contents.append(fake_dictionary1_file_contents)
fake_dict_contents.append(fake_dictionary2_file_contents)

def nullinit(self):
  super(DefinitionDataModel, self).__init__()

@pytest.fixture(scope="session")
def dictDirectory(tmp_path_factory):
  _tmpDir = tmp_path_factory.mktemp("dicts")
  fakeDict_dir  = _tmpDir / "dicts"
  fakeDict_dir.mkdir()
  
  fakeInit_path = fakeDict_dir / "__init__.py"
  fakeInit_path.write_text(" ")
  for i,content in enumerate(fake_dict_contents):
    fakeDict_path = fakeDict_dir / ("fakeDict" + str(i) + ".py")
    fakeDict_path.write_text(content)
  return _tmpDir

def test_findModules(dictDirectory):
  a = OnlineDefinitionDataModel()
  aDicts = a.findModules(str(dictDirectory) , "dicts")
  assert "fake1" in aDicts
  assert aDicts["fake1"].name == "fake1"
  assert aDicts["fake1"].languages[0] == "Lang1"
  assert aDicts["fake1"].languages[1] == "Lang2"
  assert aDicts["fake1"].getDefinitionsFromHtml("")[0] == "fake1Definition1"

def test_getAvailable(dictDirectory):
  a = OnlineDefinitionDataModel()
  a.findModules(str(dictDirectory) , "dicts")
  assert( set(a.availableDicts) == set(["fake1" , "fake2"]))
  set(a.getAvailableLanguages()) == set(["Lang1","Lang2","Lang3"])

def test_selected(dictDirectory):
  a = OnlineDefinitionDataModel()
  a.findModules(str(dictDirectory) , "dicts")
  a.selectDictsFromNames(["fake1"])
  assert(a.getSelectedDicts()[0].name == "fake1")

def test_createUrl(dictDirectory):
  a = OnlineDefinitionDataModel()
  a.findModules(str(dictDirectory) , "dicts")
  a.language = "Lang1"
  a.selectDictsFromNames(["fake1"])
  assert( a.createUrl("word","fake1") == "https://fake1_1.com/word")
  
  with pytest.raises(KeyError) as e_info:
    a.createUrl("word","realDict")

  with pytest.raises(KeyError) as e_info:
    a.createUrl("word","fake2")

def test_getDefinition(dictDirectory):
  