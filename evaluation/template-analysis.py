import json
import csv
import os
import numpy as np
import collections
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--templates_dir', default='/home/anusri/Desktop/emrQA/templates', help='Directory containing template files in the given format')
args = parser.parse_args()

relations = ["reveals", "relates","causes","given","conducted","improves","worsens"]
Functions = ["CheckRange","CheckIfNull","sortBy"]
attributes = ["date","result","onsetdate","startdate","QuitDate","PackPerDay","status","abnormalResultFlag","adherence","enddate","IsTobaccoUser","sig",
              "YearsOfUse","diagnosisdate","dosage"]
attribute_values_defined = ["pending","currentDate"]

csv_reader = list(csv.reader(open(os.path.join(args.templates_dir,"templates-all.csv"))))
answer = "no"

question_lforms = []
for line in csv_reader[1:]:

    dataset = line[0]
    if dataset == "relations":
        check = line[5]
    else:
        check = line[4]

    ## analyze all logical forms or only the ones used with answers,

    if answer == "yes":
        if check != "none":
            if (line[2],line[3]) not in question_lforms:
                question_lforms.append((line[2],line[3]))
    else:
        if (line[2],line[3]) not in question_lforms:
            question_lforms.append((line[2],line[3]))


########################################################################################################
lforms = []
for (question_list,lform) in question_lforms:
    #print(lform)
    if lform not in lforms:
        lforms.append(lform.replace("\t", "").replace("|medication|","|treatment|"))

##########################################################################################################
#print(len(lforms))


lform_vocab = []
for lform in lforms:
    lform = lform.replace("-"," - ").replace("1","").replace("2","").replace("/"," / ").replace("<"," < ").replace(">"," > ").replace("("," ( ").replace(")"," ) ").replace("["," [ ").replace("]"," ] ").replace("{"," { ").replace("}"," } ").replace("="," = ").replace(",", " , ")
    if lform.count("(") != lform.count(")"):
        print("(")
        print(lform)
    if lform.count("{") != lform.count("}"):
        print("{")
        print(lform)
    if lform.count("[") != lform.count("]"):
        print('[')
        print(lform)


    tokens = [tok for tok in lform.split(" ") if tok != ""]
    lform_vocab += tokens

vocab_counter = collections.Counter(lform_vocab)
Events = []
arguments = []
arthemetic = []
brackets = []
Events = []
arthemetic = []
punctuations = []
attribute_values = []
Functions = []
Event_Combination = []
Relations_COmbination = []
brackets = []
arguments = []

for vocab in vocab_counter:
    if "Event" in vocab:
        Events.append(vocab)
    elif vocab in relations + Functions + attributes + attribute_values_defined:
        pass
    elif "." in vocab:
        attribute_values.append(vocab)
    elif vocab in [">","<","=","Y","N","x","-"]:
        arthemetic.append(vocab)
    elif vocab in ["OR", "AND"]:
        Event_Combination.append(vocab)
    elif vocab in ["/"]:
        Relations_COmbination.append(vocab)
    elif vocab in ["(",")","[","]","{","}"]:
        brackets.append(vocab)
    elif "|" in vocab:
        arguments.append(vocab)
    elif "," in vocab:
        punctuations.append(vocab)
    else:
        pass



arthemetic_questions = []
question_with_relation = []
medical_domain_qs = []
date_questions = []
time_questions = []
trend_question = []
events_used = {}
multiple_events = []
Lab_Questions = []
arthmetic_questions = []
indefinite_evidence = []
event_confirmation = []
current = []
property = 0.0
past = []
more_than_one = 0.0
attribute_questions = 0.0
event_questions = 0.0
medical_queston = 0.0

for event in Events:
    events_used[event] = 0

for lform in lforms:
    #print(lform)
    lform = lform.replace("-", " - ").replace("1", "").replace("2", "").replace("/", " / ").replace("<", " < ").replace(
        ">",
        " > ").replace(
        "(", " ( ").replace(")", " ) ").replace("[", " [ ").replace("]", " ] ").replace("{", " { ").replace("}",
                                                                                                            " } ").replace(
        "=", " = ").replace(",", " , ")

    if "( x )" in lform:
        #print(lform)
        event_questions += 1

    if "= "in lform:
        #print(lform)
        attribute_questions += 1

    if "." in lform:
        #print(lform)
        medical_queston += 1

    tokens = [tok for tok in lform.split(" ") if tok != ""]

    rel = set(tokens).intersection(set(relations))

    if len(set(["CheckRange", ">", "<", ]).intersection(tokens)) != 0:
        #print(lform)
        arthemetic_questions.append(lform)

    if len(rel) == 0:
        if "[" not in tokens:
            indefinite_evidence.append(lform)
        else:
            out = list((set(Events)).intersection(set(tokens)))  ## Event Property Questions
            for e in out:
                events_used[e] += 1
            property += 1
    else:
        question_with_relation.append(lform)

    if len(rel) > 0:
        more_than_one += 1

print("Arthemetic questions",len(arthemetic_questions)*100.0/len(lforms))
print("One or more than one relations", 100.0 * more_than_one/len(lforms))
print("Course Questions",100.0*event_questions/len(lforms))
print("Fine Questions",100.0*attribute_questions/len(lforms))
print("Medical Questions",100.0*medical_queston/len(lforms))

## medical

## corse

## fine
