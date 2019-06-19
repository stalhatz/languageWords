from fuzzyPhraseMatch import matchphrases
import pytest
import io

@pytest.mark.parametrize("phrases", [
    ("Hello","Hello World" , [(0,5)] , 0),
    ("Yellow","Hello World" ,[(0,5)] , 0),
    ("Hello","World Yellow" ,[(6,12)], 0.5),
    ("is","World is Yellow" ,[(6,8)] , 0),
    ("Hello World","He told her: Yellow World" ,[(13,19),(20,25)] , 0.4),
])
def test_matchphrases(phrases):
    sourcePhrase = phrases[0]
    targetPhrase = phrases[1]
    startEnds    = phrases[2]
    threshold    = phrases[3]
    matches = matchphrases(sourcePhrase,targetPhrase,threshold)
    print(matches)
    matches.sort(key = lambda k:k.start)  
    for i,match in enumerate(matches):
        startEnd     = startEnds[i]
        correct_start= startEnd[0]
        correct_end  = startEnd[1]
        assert(match.start == correct_start)
        assert(match.end   == correct_end)