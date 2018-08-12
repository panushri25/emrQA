import csv
import numpy as np
import collections
import matplotlib
import matplotlib.pyplot as plt
import nltk
from nltk.metrics import *
import json
from matplotlib2tikz import save as tikz_save

file = open("logical_forms_index.csv")
lform_reader = list(csv.reader(file))
import itertools
matplotlib.rcParams.update({'font.size': 22})
file = open("questions_index.csv")
#quest_reader = list(csv.reader(file))

print(quest_reader)
print("Average paraphrases per question", len(quest_reader[1:])/float(len(lform_reader[1:])))
id_2_question = {}
############################################## Average Entities Per Question #######################

def CountEntities(csv_reader):
    total_tokens = 0.0
    total_templates = len(csv_reader)
    Total_entities = 0.0
    for value in csv_reader[1:]:

        question = value[0]
        #tokens = [tok for tok in question.split(" ") if tok != ""]
        #total_tokens += len(tokens)
        #count = question.count("|")
        #if count%2 != 0:
        #    print(question)
        count = set(question.split("|")[1::2])

        num_entites = len(count)
        id_2_question[value[1]] = value[0]
        print(num_entites)
        print(count)
        #print(num_entites)
        Total_entities += num_entites
    #print(total_tokens/len(csv_reader[1:]))
    print(Total_entities/total_templates)
    return [Total_entities,total_templates]

[Total_entities,total_templates] = CountEntities(quest_reader)
Avg_entities_Question = Total_entities/total_templates
print("Average Entities Per Question",Avg_entities_Question)

#[Total_entities,total_templates] = CountEntities(lform_reader)
#Avg_entities_LogicalForm = Total_entities/total_templates
#print("Average Entities Per LForm",Avg_entities_LogicalForm)

############################################################################################################

### Average Entity Type ###

file = open("question-logical-mappping.csv")
csv_reader = list(csv.reader(file))[1:]
dict_map = {}
lform_question = {}
for val in csv_reader:
    dict_map[val[0]]  = val[1]
    if val[1] not in lform_question:
        lform_question[val[1]] = []

    lform_question[val[1]].append(val[0])

 ################################################################## Paraphrase Scoring #######################################################

method = "jaccard_score"
import matplotlib.pyplot as plt

def scoring_method(qtuple,method):

    set1 = set(nltk.word_tokenize(qtuple[0]))
    set2 = set(nltk.word_tokenize(qtuple[1]))

    if method == "jaccard_score":
        score = jaccard_distance(set1,set2)

    return score


total_scores = []
for form in lform_question:
    question_paraphrases = []
    for qid in lform_question[form]:
        question_paraphrases.append(id_2_question[qid])


    question_paraphrases = [question.replace("|", "") for question in question_paraphrases]
    question_tuples = list(itertools.product(question_paraphrases, question_paraphrases))
    scores = []
    for qtuple in question_tuples:
        if qtuple[0] == qtuple[1]:
            continue
        scoring_tuple = scoring_method(qtuple, method)
        scores.append(scoring_tuple)
    if len(scores) != 0:
        min_value = min(scores)
        max_value = max(scores)

        total_scores.append(scores)

#plt.xlabel("Question Templates")
#plt.ylabel("Jaccard Score")

#idx = -1
#for scores in total_scores:#
    #    idx += 1
    #plt.plot([idx] * len(scores), scores, "*", color="blue")
#plt.show()


 ###################################################################################################################################
normalize_concept = [[question,question.replace("|problem|","$$").replace("|test|","$$").replace("|treatment|","$$").strip()] for [question,id] in quest_reader]
normalize_concept = [[value[0]," ".join([val for val in value[1].split(" ") if val != ""])] for value in normalize_concept]

templates = []
[orginals , templates] = zip(*normalize_concept)
templates = np.array(templates)
grouped_index = np.array([])
for value in normalize_concept:
    orginal_quest = value[0]
    norm_quest = value[1]
    index = np.where(templates==norm_quest)[0]
    if len(index) > 1:
        if index not in grouped_index:
           grouped_index = list(grouped_index)
           grouped_index.append(list(index))
           grouped_index = np.array(grouped_index)

orginals = np.array(orginals)

total_non_quniques = 0.0
total_entites = 0.0
for values in grouped_index:
    questions = orginals[values]
    unique = set(questions)
    if len(unique) != 1:
        #print(unique)
        total_entites += len(unique) - 1
        total_non_quniques += 1

num_question_semantics = len(set(templates))

print("Average Entity Type Per Question",num_question_semantics/(num_question_semantics-total_entites))

###################################################################################################

### Logical  Form Vocabulary ##########

lform_vocab = []
for value in lform_reader[1:]:
    lform = value[0]
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
arthemetic = []
punctuations = []
attribute_values = []
Functions = []
Event_Combination = []
Relations_COmbination = []
brackets = []
arguments = []


relations = ["reveals", "relates","causes","given","conducted","improves","worsens"]
Functions = ["CheckRange","CheckIfNull","sortBy"]
attributes = ["date","result","onsetdate","startdate","QuitDate","PackPerDay","status","abnormalResultFlag","adherence","enddate","IsTobaccoUser","sig",
              "YearsOfUse","diagnosisdate","dosage"]
attribute_values_defined = ["pending","currentDate"]


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
        print(vocab)

    #print(vocab)
print(attribute_values)

##################################### Relation Distribution #########################################

relations_used = []
for value in lform_reader[1:]:
    lform = value[0]
    lform = lform.replace("-", " - ").replace("1", "").replace("2", "").replace("/", " / ").replace("<", " < ").replace(">",
                                                                                                                    " > ").replace(
    "(", " ( ").replace(")", " ) ").replace("[", " [ ").replace("]", " ] ").replace("{", " { ").replace("}",
                                                                                                        " } ").replace(
    "=", " = ").replace(",", " , ")
    tokens = [tok for tok in lform.split(" ") if tok != ""]

    rel = set(tokens).intersection(set(relations))
    if len(rel) != 0:
        relations_used.append("/".join(list(rel)))
    else:
        relations_used.append("None")



#print(relations_used)
relations_dict = collections.Counter(relations_used)
#print(relations_dict)

labels = relations_dict.keys()
sizes = [relations_dict[key] for key in labels]
#colors = ['yellowgreen', 'gold', 'lightskyblue', 'lightcoral']
colors = ['C0', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9']


plt.figure(1)
patches, texts = plt.pie(sizes, colors=colors, labels=labels)
#texts[0].set_fontsize(10)
plt.axis('equal')
plt.tight_layout()
#plt.show()
tikz_save("pie-relations.tex")
# Average Relations per questions
#################################### Answer Type Distribution #######################################

attribute_question = []
event_question = []
event_confirmation = []

#for value in lform_reader[1:]:
#    lform = value[0]
forms = json.load(open('/home/anusri/Desktop/codes_submission/evaluation/ql_lforms.json'))
for lform in forms:
    lform = lform.replace("-", " - ").replace("1", "").replace("2", "").replace("/", " / ").replace("<", " < ").replace(">",
                                                                                                                    " > ").replace(
    "(", " ( ").replace(")", " ) ").replace("[", " [ ").replace("]", " ] ").replace("{", " { ").replace("}",
                                                                                                        " } ").replace(
    "=", " = ").replace(",", " , ")

    tokens = [tok for tok in lform.split(" ") if tok != ""]

    if "x" not in lform:
        event_confirmation.append(lform)
    if "( x )" in lform:
        event_question.append(lform)
    else:
        attribute_question.append(lform)

print("\n")
print("Event Confirmation Questions",len(event_confirmation)*100.0/len(lform_reader[1:]))
print("Event Questions",len(event_question)*100.0/len(lform_reader[1:]))
print("Attribute Questions",len(attribute_question)*100.0/len(lform_reader[1:]))




################################## Question categories ####################################

relations = ["reveals", "relates","causes","given","conducted","improves","worsens"]
Functions = ["CheckRange","CheckIfNull","sortBy"]
attributes = ["date","result","onsetdate","startdate","QuitDate","PackPerDay","status","abnormalResultFlag","adherence","enddate","IsTobaccoUser","sig",
              "YearsOfUse","diagnosisdate","dosage"]
attribute_values_defined = ["pending","currentDate"]

medical_domain_qs = []
date_questions = []
time_questions = []
trend_question = []
multiple_events = []
Lab_Questions = []
arthmetic_questions = []
indefinite_evidence = []
event_confirmation = []
current = []
past = []
for event in Events:
    events_used[event] = 0

relation_questions = 0.0
property = 0.0
question_with_relation = []
for value in lform_reader[1:]:
    lform = value[0]
    lform = lform.replace("-", " - ").replace("1", "").replace("2", "").replace("/", " / ").replace("<", " < ").replace(">",
                                                                                                                    " > ").replace(
    "(", " ( ").replace(")", " ) ").replace("[", " [ ").replace("]", " ] ").replace("{", " { ").replace("}",
                                                                                                        " } ").replace(
    "=", " = ").replace(",", " , ")
    tokens = [tok for tok in lform.split(" ") if tok != ""]

    rel = set(tokens).intersection(set(relations))

    #############################################################################################################

## part 1 analysis
    ## Indefinite Evidence -- no spcfic attribute - no relations, no "["
    if len(rel) == 0:
        if "[" not in tokens:
            indefinite_evidence.append(lform)
        else:
            out = list((set(Events)).intersection(set(tokens)))     ## Event Property Questions
            for e in out:
                events_used[e] += 1
            property += 1
    else:
        question_with_relation.append(lform)





######################################################################################################
    ## Event Confirmation -- relations with no x
    if "x" not in tokens:
        event_confirmation.append(lform)


    if len(rel) !=0:
        relation_questions += 1
    # Number of questions which will need medical_knowledge to answer (question with "." in it)
    if len(set(attribute_values+["abnormalResultFlag"]).intersection(tokens)) != 0:
        medical_domain_qs.append(lform)

    if len(set(["abnormalResultFlag", "CheckRange", ">" ,"<", ]).intersection(tokens)) != 0:
        arthmetic_questions.append(lform)
    ## Arthemetic Evidence -- only lab events

    event_tokens = set(tokens).intersection(Events)
    if len(event_tokens) == 1:
        if "LabEvent" in list(event_tokens) or "VitalEvent" in list(event_tokens):
            Lab_Questions.append(lform)

    if len(event_tokens) == 2:

        if set(["LabEvent","VitalEvent"]) == event_tokens:
            Lab_Questions.append(lform)

    #1) Trend Questions -- lab results - sortby
    # 2) Dpecfic date questions -- lab results - no sorty by

    if "|date|" in tokens:
        date_questions.append(lform)
    elif "|time|" in tokens:
        time_questions.append(lform)
    elif "currentDate" in tokens:
        current.append(lform)
    elif "sortBy" in tokens:
        trend_question.append(lform)
    else:
        past.append(lform)


    # 1) Related Event Entity Question
    # 2) Related Event and property Question
    # 3) Related Event Property Questions


    ## avergae number of events in relation to questions

    if "AND" in tokens:
        multiple_events.append(lform)

print("Indefinte Evidence", 100.0 * len(indefinite_evidence) / len(lform_reader[1:]))
print("More than one relations", 100.0 * len(question_with_relation) / len(lform_reader[1:]))
print("More than one relations", 100.0 * len(question_with_relation) / len(lform_reader[1:]))

##################### Type Of Answers Needed ####################

print("Arthemetic Reasoning Questions",len(arthmetic_questions)*100.0/len(lform_reader[1:]))


print("Lab Questions", len(Lab_Questions)*100.0/len(lform_reader[1:]))
print(Lab_Questions)
print("\n")

print(relation_questions*100/len(lform_reader[1:]))
'''
########### Time Classfication ###

## spedfic date questions
print("\n")
print("Specfic dated questions",100.0*len(date_questions)/len(lform_reader[1:]))
print(date_questions)
print("\n")

print("definte past",100.0*len(time_questions)/len(lform_reader[1:]))
print(time_questions)
print("\n")

print("Trend Questions",100.0*len(trend_question)/len(lform_reader[1:]))
print(trend_question)
print("\n")

print("Current Questions",100.0*len(current)/len(lform_reader[1:]))
print("Past Questions", 100.0*len(past)/len(lform_reader[1:]))

print((100.0*len(past)/len(lform_reader[1:]))+(100.0*len(trend_question)/len(lform_reader[1:])))

print("\n")
print("Medical Knowledge Question Templates",100.0*len(medical_domain_qs)/len(lform_reader[1:]))
print(medical_domain_qs)
print("\n")


print("Event Property Questions",100.0*property/len(lform_reader[1:]))
print(events_used)
print("\n")



print("Multiple Events", len(multiple_events)*100.0/len(lform_reader[1:]))
print(multiple_events)
print("\n")

'''

#########################################################################################################################

length = []
for value in lform_reader[1:]:
    lform = value[0]
    lform = lform.replace("-", " - ").replace("1", "").replace("2", "").replace("/", " / ").replace("<", " < ").replace(">",
                                                                                                                    " > ").replace(
    "(", " ( ").replace(")", " ) ").replace("[", " [ ").replace("]", " ] ").replace("{", " { ").replace("}",
                                                                                                        " } ").replace(
    "=", " = ").replace(",", " , ")
    tokens = [tok for tok in lform.split(" ") if tok != ""]

    length.append(len(tokens))

print("Average Lenght OF Logical FOrm",sum(length)/len(length))

plt.figure(2)
plt.xlabel("Formula Size")
plt.ylabel("Frequency")
plt.title("Formula Size Bins")
plt.hist(length, bins=30)
tikz_save('hist-formulasize.tex')