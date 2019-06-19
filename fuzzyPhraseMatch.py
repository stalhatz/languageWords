import jellyfish
import string
import argparse
import re
import numpy as np
from collections import Counter
from collections import namedtuple

Scoring = namedtuple('Scoring', ('score', 'sourceId' , 'targetId', 'sourceWord', 'targetWord'))
Matching = namedtuple('Matching', ('start','end','sourceWord'))
def customSplit(s):
  i= 0
  pList = list(string.punctuation + " ")
  inWord = False
  words = []
  startEnds = []
  while True:
    try:
      c = s[i]
    except IndexError:
      if inWord:
        w_end = i
        startEnds.append( (w_start,w_end) )
        words.append(s[w_start:w_end])
      break
    if c in pList:
      if inWord:
        w_end = i
        startEnds.append( (w_start,w_end) )
        words.append(s[w_start:w_end])
      inWord = False
    else:
      if not inWord:
        w_start = i
      inWord = True
    i += 1
  return words,startEnds


def getIndexesAboveThreshold(allScores, threshold):
  indexes = []
  for i,scoreRecs in enumerate(allScores):
    scores = [ s.score for s in scoreRecs]
    minScore = min(scores)
    minIndex = scores.index(minScore)
    if minScore < threshold:
      indexes.append( scoreRecs[minIndex] )      
  return indexes

def numOfSourceWordsPresent(indexes):
  presentIndexes = []
  for index in indexes:
    presentIndexes.append(index.sourceWord)
  return len(set(presentIndexes))

def getTargetDuplicates(indexes):
  dups = {}
  duplicates = {}
  for index in indexes:
    try:
      l = dups[index.sourceWord] 
    except KeyError:
      l = []
      dups[index.sourceWord] = l
    l.append(index.targetWord)

  return dups

def matchphrases(sourcePhrase, targetPhrase, threshold = 0.25):
  sourcePhrase = sourcePhrase.lower()
  targetPhrase = targetPhrase.lower()

  words1,startEnds1 = customSplit(sourcePhrase)
  words2,startEnds2 = customSplit(targetPhrase)
  # print(sourcePhrase)
  # print(startEnds1)
  # print(words1)
  # print(targetPhrase)
  # print(startEnds2)
  # print(words2)
  allScores = []
  for j,w2 in enumerate(words2):
    scores = []
    for i,w1 in enumerate(words1):
      scores.append( Scoring( jellyfish.levenshtein_distance(w1,w2) / max(len(w1) , len(w2)) , i , j , w1 , w2)  )
    allScores.append( scores)
  
  # print(allScores)
  tIndexes = getIndexesAboveThreshold(allScores,threshold)
  #numberPresent = numOfSourceWordsPresent(tIndexes)
  #duplicates = getTargetDuplicates(tIndexes)
  matchings = []
  for tIndex in tIndexes:
    targetStart = startEnds2[tIndex.targetId][0]
    targetEnd   = startEnds2[tIndex.targetId][1]
    sourceWord  = tIndex.sourceWord
    matchings.append(Matching(targetStart,targetEnd,sourceWord))
  return matchings

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Process some integers.')
  parser.add_argument('-t', nargs='?', default=0.5,type = float)
  parser.add_argument('-s', nargs='?', default=0.5)
  args = parser.parse_args()
  
  matchings = matchphrases("Hello world" , "Hello, the world is a cruel place. Mold is hello on a mellow..." , args.t)
  print(matchings)