import random
from dataModels import DefinitionDataModel
import pytest
import io
import pandas
import sys

fake_dictionary_file_contents = """
name = "fake"
languages = ["Lang1","Lang2"] 
dictUrls     = ["https://fake1.com","https://fake2.com"]

def createUrl(word,requestLang):
  return dictUrls[0] + "/" + word

def getDefinitionsFromHtml(html):
  definitionsList = []
  definitionsList.append("fakeDefinition")
  return definitionsList
  """

def nullinit(self):
  super(DefinitionDataModel, self).__init__()

def test_findModules(tmp_path,monkeypatch):
    fakeDict_dir  = tmp_path /"dicts"
    fakeDict_dir.mkdir()
    fakeDict_path = fakeDict_dir / "fakeDict.py"
    fakeInit_path = fakeDict_dir / "__init__.py"
    fakeInit_path.write_text(" ")
    fakeDict_path.write_text(fake_dictionary_file_contents)
    a = DefinitionDataModel()
    aDicts = a.findModules(str(tmp_path) , "dicts")
    assert "fake" in aDicts
    assert aDicts["fake"].name == "fake"
    assert aDicts["fake"].languages[0] == "Lang1"
    assert aDicts["fake"].languages[1] == "Lang2"
    assert aDicts["fake"].getDefinitionsFromHtml("")[0] == "fakeDefinition"
