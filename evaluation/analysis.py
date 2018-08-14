import json
from nltk.tokenize.stanford import StanfordTokenizer
import os
import numpy as np
import matplotlib.pyplot as plt
import nltk
from random import *
from nltk import sent_tokenize
from nltk import word_tokenize
#os.environ['STANFORD_PARSER'] = '/home/anusri/Desktop/codes_submission/packages/stanford-jars/'
#os.environ['STANFORD_MODELS'] = '/home/anusri/Desktop/codes_submission/packages/stanford-jars'
#tokenizer = StanfordTokenizer("/home/anusri/Desktop/codes_submission/packages/stanford-jars/stanford-postagger.jar")
#from matplotlib2tikz import save as tikz_save

#["medications","relations","risk-dataset"]
## Medications QA: 25070
## Relations QA: 32157
## Risk dataset QA: 3313
## Obesity QA:
## Smoking QA: 1506
## title : medication, risk-dataset, relations, obesity, smokin


def QuestionStatistics(questions):

    metrics = {}
    Total_questions = len(questions)
    Total_Tokens = 0
    for question in questions:
        #print(question)
        #words = tokenizer.tokenize(question.strip())
        words = sent_tokenize(question)
        print(words)
        Total_Tokens += len(words)

    Avg_token_length = Total_Tokens / Total_questions
    metrics["question_length"] = Total_questions
    metrics["avg_question_length"] = Avg_token_length

    return metrics

def LengthStatistics(list_values):

    metrics = {}
    Total_values= len(list_values)
    Total_Tokens = 0
    print(Total_values)
    for question in list_values:
        #words = tokenizer.tokenize(question.strip())
        words = word_tokenize(question.strip())
        words = [word for word in words if word != ""]
        #print(words)
        Total_Tokens += len(words)
        #print(Total_Tokens)

    Avg_token_length = Total_Tokens / Total_values
    metrics["question_length"] = Total_values
    metrics["avg_question_length"] = Avg_token_length

    return (Total_values, Avg_token_length)

def AnswerStatistics():

    ## 1) FRom Logical Forms infer the concept sbeing asked, high level and specfic from
    pass

problem = []
treatments = []
tests = []

if __name__ == '__main__':

    ten_evidences = 0
    data_file = "/home/anusri/Desktop/emrQA/output/data.json"
    datasets = json.load(open(data_file), encoding="latin-1")
    all_questions = []
    all_clinical_notes = []
    num_answers = []
    total_evidences = []
    total_clinical_notes = 0
    number_of_answers_per_question = {}
    total_question_char = 0.0
    indefinite_evidence_type = []
    forms_in_data = []
    for dataset in datasets:
        #if dataset["title"] in ["obesity","smoking"]:
        #    continue
        print("Processing dataset",dataset["title"])
        for note in dataset["paragraphs"]:
            total_clinical_notes += 1

            all_clinical_notes.extend([" ".join(note["context"])])

            for questions in note["qas"]:

                all_answers = []
                evidences = []

                all_questions.append(questions["question"]) # all questions

                for answer in questions["answers"]:
                    if dataset["title"] == "obesity":
                        for txt in answer["text"]:
                            if txt not in all_answers:
                                all_answers.append(txt)
                    else:
                        if answer["answer_start"][0] != "":
                            if answer["answer_start"] not in all_answers:
                                all_answers.append(answer["answer_start"]) ## all answers
                                if dataset["title"] == "risk-dataset":
                                    index = int(answer["answer_start"][0])
                                    evidences.append(note["context"][index])
                                else:
                                    index = int(answer["answer_start"][0]) - 1
                                    evidences.append(note["context"][index])
                        else:
                            if answer["evidence_start"] not in all_answers:
                                all_answers.append(answer["evidence_start"])  ## all answers
                                index = int(answer["evidence_start"][0]) - 1
                                evidences.append(note["context"][index])

                ground_truth = all_answers
                total_answers = len(ground_truth) ## distribution of evidences per question type
                if total_answers not in number_of_answers_per_question:
                    number_of_answers_per_question[total_answers] = 0
                number_of_answers_per_question[total_answers] += 1

                lform = questions["id"][1]
                if (lform,questions["id"][0])  not in forms_in_data:
                    forms_in_data.append((lform,questions["id"][0]) )

    with open('ql_lforms.json', 'w') as outfile:
        json.dump(forms_in_data, outfile)

    total_question = len(all_questions)
    totals = 0
    questions_list = []
    for value in all_questions:
        print(value)
        print(len(value))
        totals += len(value)
        questions_list.extend(value)

    #print(indefinite_evidence_type)
    #print("indefinite",len(num_answers)*100.0/total_question)
    #print(min(num_answers),max(num_answers))
    #plt.figure(2)
    #plt.xlabel("Number of evidences greater than 1")
    #plt.ylabel("Frequency")
    #plt.title("Formula Size Bins")
    #plt.hist(num_answers, bins=3)
    #plt.show()
    #tikz_save('evidences-hist.tex')

    print("Total Number  Of Questions",totals)

    print("Total number of question types", total_question)

    #stats_questions = LengthStatistics(questions_list)
    #print("Average question length",stats_questions[1])

    print(total_evidences)
    stats_evidences = LengthStatistics(total_evidences)
    print("Average evidence length",stats_evidences[1])


    total__num_answers = 0
    for value in number_of_answers_per_question:
        if value == 0:
            print(number_of_answers_per_question[value])
        else:
            total__num_answers += value*number_of_answers_per_question[value]

    print("Percentage with one evidences",number_of_answers_per_question[1]*100.0/total_question)
    print(number_of_answers_per_question)
    #print("Percentage with ten evidence",ten_evidences*100.0/total_question)
    print("Average number of evidences",float(total__num_answers)/total_question)
    #print(number_of_answers_per_question)

    #stats_clinincal_notes = LengthStatistics(all_clinical_notes)
    #print("Total Clinincal Notes",stats_clinincal_notes[0])
    #print("Average Clinincal Note length", stats_clinincal_notes[1])

    #print(number_of_answers_per_question[0])
    #print(number_of_answers_per_question[1])
    #print(number_of_answers_per_question)
    ## Plot the distribution of number of answer
    #print(number_of_answers_per_question)

    #x = np.arange(len(number_of_answers_per_question)-1)
    #plt.bar(x,list(np.array(number_of_answers_per_question.values().remove(number_of_answers_per_question[1]))))
    #plt.xticks(x, number_of_answers_per_question.keys().remove(1))
    #plt.show()

    ### Question Metrics ###
    #question_metrics = QuestionStatistics(all_questions)

    #### Answer Metrics ####

    #answer_metrics = AnswerStatistics(all_answers)
    #print(question_metrics)