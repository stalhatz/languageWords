import random
from dataModels import TagDataModel
import pytest
import io
import pandas
#@pytest.mark.parametrize("messages", [
#    ["newTask","newTask","endTask","endTask"],
#    ["newTask","slack","slack","endTask"],
#    ["newTask","slack","slack","endTask", "newTask"]
#])
#def test_handleMsg(messages):
#  handleMsg(messages)
  
def createMocTagModel(numWords,numTags):
  model = TagDataModel()
  letters = list("abcdefghijklmnopqrstuvwxyz")
  numWords = min(numWords,len(letters))
  numTags = min(numTags,len(letters))
  tagLetters = letters[:numTags]
  tagsToUse = [i + "Tag" for i in tagLetters]
  wordLetters = letters[:numWords]
  wordsToUse = [i + "Word" for i in wordLetters]
  for w in wordsToUse:
    model.addTagging(w,tagsToUse)
  return model,wordsToUse,tagsToUse

@pytest.mark.parametrize("numWords,numTags", [
    (10 , 10)
])
def test_addTagging(numWords , numTags):
  model,words,tags = createMocTagModel(numWords,numTags)
  assert len(model.getTags()) == numTags
  for w in words:
    assert len(model.getTagsFromIndex(w)) == numTags
  assert len(model.tagTable) == numWords * numTags

@pytest.mark.parametrize("numTaggingsPerWord", [
    5
])
def test_removeTagging(numTaggingsPerWord):
  numTags = 10
  numWords = 10
  model,words,tags = createMocTagModel(numWords,numTags)
  numTaggingsPerWord = min(numTaggingsPerWord , numTags)
  for w in words:
    for i,t in enumerate(tags):
      if i < numTaggingsPerWord:
        model.removeTagging(w,[t])
  assert len(model.getTags()) == numTags - numTaggingsPerWord
  for w in words:
    assert len(model.getTagsFromIndex(w)) == numTags - numTaggingsPerWord
  assert len(model.tagTable) == numWords * (numTags - numTaggingsPerWord)

def test_addRelation():
  numTags = 7
  numWords = 7
  model,words,tags = createMocTagModel(numWords,numTags)
  # create a 4-2-1 binary tree
  model.addRelation(tags[1],tags[0])
  model.addRelation(tags[2],tags[0])
  model.addRelation(tags[3],tags[1])
  model.addRelation(tags[4],tags[1])
  model.addRelation(tags[5],tags[2])
  model.addRelation(tags[6],tags[2])
  #Total parent of leaves
  for t in tags[3:]:
    print(model.getAllParentTags(t))
    assert len(model.getAllParentTags(t)) == 2
  #Total children of root
  print(model.getAllChildTags(tags[0]))
  assert len(model.getAllChildTags(tags[0])) == 6
  