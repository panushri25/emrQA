from nltk.stem import WordNetLemmatizer
import nltk
from nltk.corpus import stopwords

## Open common names to use in is_common_noun function ##
file = open("generation/i2b2_relations/common_names.txt") ## you can use any set of common nouns to filter, here we call the top 500 high frequency words occuring in our templates as commoun nouns ##
data = file.readlines()
file.close()
common_nouns = [line.strip() for line in data]

## Get Stop words ##

stopWords = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

## Functions For Use ##

def concept_is_CommonNoun(concept):
    '''
    Return 1 if the concept is a common noun
    :param concept:
    :return:
    '''

    tags = nltk.pos_tag(nltk.word_tokenize(concept))
    [words, tag] = zip(*tags)

    words = list(words)

    nouns = []
    if tag[0] in ["DT", "PRP", "PRP$"]:
        words[0] = ""
        for idx in range(1, len(tag)):
            if words[idx] in stopWords:
                continue
            nouns.append(words[idx])
    else:
        for idx in range(len(tag)):
            if words[idx] in stopWords:
                continue
            nouns.append(words[idx])

    flag = 0
    for noun in nouns:
        if (lemmatizer.lemmatize(noun) in common_nouns) or (noun in common_nouns):
            flag = 1
        else:
            flag = 0
            break

    '''
    if flag == 1:
        print(" ".join(words).strip(), tags)
    '''
    return flag

def concept_is_PastTense(concept):
    '''
    Return 1 if the concept ends in past tense
    :param concept:
    :return:
    '''
    text = nltk.word_tokenize(concept)
    tagged = nltk.pos_tag(text)

    tense = {}
    tense["future"] = len([word for word in tagged[-1:] if word[1] == "MD"])
    tense["present"] = len([word for word in tagged[-1:] if word[1] in ["VBP", "VBZ", "VBG"]])
    tense["past"] = len([word for word in tagged[-1:] if word[1] in ["VBD", "VBN"]])

    if tense["past"] > 0:
        flag = 1
    else:
        flag = 0

    return flag

'''
import sys
sys.path.insert(0, '/home/anusri/Desktop/IBM/GetUMLS/QuickUMLS')
import quickumls
matcher = quickumls.QuickUMLS("/home/anusri/Desktop/IBM/GetUMLS/installation")

## Get UMLS semantic mapping ##
sfile = open("/home/anusri/Desktop/IBM/GetUMLS/QuickUMLS/SemanticTypes_2013AA.txt")
data = sfile.readlines()
sfile.close()
mapping = {}
for line in data:
    words = line.split("|")
    short_type = words[1]
    full_type = words[0]
    mapping[short_type] = full_type
    
def concept_is_Disease(concept):
    #if concept_is_CommonNoun(concept) == 1:
     #   return 0

    SemanticTypes = CheckSemanticType(concept)

    otype = disease
    for (word,wtype) in SemanticTypes:
        for type in wtype:
            if (type in otype):
                return 1


    return 0
def concept_is_Symptom(concept):
    # if concept_is_CommonNoun(concept) == 1:
    #   return 0

    SemanticTypes = CheckSemanticType(concept)
    for (word, wtype) in SemanticTypes:
        for type in wtype:
            if (type in symptoms):
                return 1

    return 0
def concept_is_MentalDisease(concept):
    # if concept_is_CommonNoun(concept) == 1:
    #   return 0

    SemanticTypes = CheckSemanticType(concept)


    for (word, wtype) in SemanticTypes:
        for type in wtype:
            if (type in mental_disease):
                return 1

    return 0
def concept_is_VirusBacterium(concept):
    # if concept_is_CommonNoun(concept) == 1:
    #   return 0

    SemanticTypes = CheckSemanticType(concept)

    for (word, wtype) in SemanticTypes:
        for type in wtype:
            if type in bacteria:
                return 1

    return 0
def concept_is_Injury(concept):
    # if concept_is_CommonNoun(concept) == 1:
    #   return 0

    SemanticTypes = CheckSemanticType(concept)


    for (word, wtype) in SemanticTypes:
        for type in wtype:
            if (type in injury):
                return 1

    return 0
def concept_is_Abnormality(concept):
    # if concept_is_CommonNoun(concept) == 1:
    #   return 0

    SemanticTypes = CheckSemanticType(concept)


    for (word, wtype) in SemanticTypes:
        for type in wtype:
            if (type in abnormality):
                return 1

    return 0
def concept_is_AbnormalTestResult(concept):
    # if concept_is_CommonNoun(concept) == 1:
    #   return 0

    SemanticTypes = CheckSemanticType(concept)


    for (word, wtype) in SemanticTypes:
        for type in wtype:
            if (type in lab_result):
                return 1

    return 0
def CheckSemanticType(text):
    types = []
    out = matcher.match(text, best_match=True, ignore_syntax=False)
    for words in out:
        word = words[0]["ngram"]
        temp = []
        for type in list(words[0]["semtypes"]):
            temp.append(mapping[type])
        types.append((word,temp))
    return types

## Functions for script check ##

#TenseFilter()


def determine_tense_input(sentance):
    text = nltk.word_tokenize(sentance)
    tagged = nltk.pos_tag(text)

    tense = {}
    tense["future"] = len([word for word in tagged[-1:] if word[1] == "MD"])
    tense["present"] = len([word for word in tagged[-1:] if word[1] in ["VBP", "VBZ", "VBG"]])
    tense["past"] = len([word for word in tagged[-1:] if word[1] in ["VBD", "VBN"]])
    return tense
    
def TenseFilter():

    file = open("problem-concept.txt")
    data = file.readlines()
    file.close()

    concepts = [line.strip() for line in data]

    past = []
    future = []

    for concept in concepts:
        tense = determine_tense_input(concept)
        if tense["past"] > 0:
            past.append(concept)
        if tense["future"] > 0:
            future.append(concept)
    
    #for word in past:
    #    term = word.strip().split(" ")
    #    if len(term) > 1:
    #        term = term[-1]
    #    else:
    #        term = term[0]
    #    print(term)
    #    print(word,en.verb.present(term))

    print(past)
    print(future)

#FilterCommonNouns()

'''