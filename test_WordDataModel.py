import random
from dataModels import WordDataModel
import pytest
import io
#@pytest.mark.parametrize("messages", [
#    ["newTask","newTask","endTask","endTask"],
#    ["newTask","slack","slack","endTask"],
#    ["newTask","slack","slack","endTask", "newTask"]
#])
#def test_handleMsg(messages):
#  handleMsg(messages)
  
@pytest.mark.parametrize("numWords", [
    100
])
def test_add_removeWord(numWords , wordLength = 10):
  model = WordDataModel()
  letters = list("abcdefghijklmnopqrstuvwxyz")
  for word in range(numWords):
    word = []
    for i in range(wordLength):
      j = random.randint(0,25)
      word += letters[j]
    model.addWord("".join(word))
  assert len(model.wordTable) == numWords
  words = model.getWords()
  for word in words:
    model.removeWord(word)
  assert len(model.wordTable) == 0
  #Remove word that does not exist
  with pytest.raises(KeyError) as e_info:
    model.removeWord("aWord")

@pytest.mark.parametrize("numWords", [
    100
])

def test_save_load(numWords , wordLength = 10):
  model = WordDataModel()
  letters = list("abcdefghijklmnopqrstuvwxyz")
  for word in range(numWords):
    word = []
    for i in range(wordLength):
      j = random.randint(0,25)
      word += letters[j]
    model.addWord("".join(word))
  memoryFile = io.BytesIO()
  model.saveData(memoryFile)
  memoryFile.seek(0)
  model.loadData(memoryFile)
  assert len(model.wordTable) == numWords
