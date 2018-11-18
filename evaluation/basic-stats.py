import json
from nltk.tokenize.stanford import StanfordTokenizer
import os
import numpy as np
import matplotlib.pyplot as plt
import nltk
from random import *
from nltk import sent_tokenize
from nltk import word_tokenize
import random
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--output_dir', default='/home/anusri/Desktop/emrQA/output/', help='Directory to store the output')

args = parser.parse_args()

#os.environ['STANFORD_PARSER'] = '/home/anusri/Desktop/codes_submission/packages/stanford-jars/'
#os.environ['STANFORD_MODELS'] = '/home/anusri/Desktop/codes_submission/packages/stanford-jars'
#tokenizer = StanfordTokenizer("/home/anusri/Desktop/codes_submission/packages/stanford-jars/stanford-postagger.jar")
#from matplotlib2tikz import save as tikz_save

def LengthStatistics(list_values):

    metrics = {}
    Total_values= len(list_values)
    Total_Tokens = 0.0
    #print(Total_values)
    for question in list_values:
        words = word_tokenize(question.strip())
        words = [word for word in words if word != ""]
        Total_Tokens += len(words)

    Avg_token_length = Total_Tokens / Total_values
    metrics["question_length"] = Total_values
    metrics["avg_question_length"] = Avg_token_length

    return (Total_values, Avg_token_length)


problem = []
treatments = []
tests = []

if __name__ == '__main__':

    data_file = os.path.join(args.output_dir,"data.json")
    datasets = json.load(open(data_file), encoding="latin-1")

    all_questions = []
    all_clinical_notes = []

    total_clinical_notes = 0
    number_of_answers_per_question = {}
    num_classes = 0.0
    classes = []
    total_evidences = []


    for dataset in datasets["data"]:

    

        print("Processing dataset",dataset["title"])

        for note in dataset["paragraphs"]:
            total_clinical_notes += 1

            if " ".join(note["context"]) not in all_clinical_notes:
                all_clinical_notes.extend([" ".join(note["context"])])
            else:
                continue

            for questions in note["qas"]:

                all_answers = []
                evidences = []

                all_questions.append(list(set(questions["question"]))) # all questions

                for answer in questions["answers"]:

                    if dataset["title"] in ["obesity", "smoking"] :
                        #print(answer["text"])
                        classes.append(answer["text"])
                        continue
                        #for txt in answer["text"]:
                        #    if txt not in all_answers:
                        #        all_answers.append(txt)
                    else:
                        if answer["answer_start"][0] != "":
                            if answer["answer_start"] not in all_answers:
                                all_answers.append(answer["answer_start"]) ## all answers
                                #print(questions["question"][0], answer["answer_start"],answer["evidence"])
                                evidences.append(answer["evidence"])

                total_evidences.extend(evidences)

                ## distribution of evidences per question type

                ground_truth = all_answers
                total_answers = len(ground_truth)
                if total_answers not in number_of_answers_per_question:
                    number_of_answers_per_question[total_answers] = 0
                number_of_answers_per_question[total_answers] += 1


    print("Total Clinical Notes", total_clinical_notes, len(all_clinical_notes))
    total_question = len(all_questions)
    totals = 0
    questions_list = []
    for value in all_questions:
        totals += len(value)
        questions_list.extend(value)

    ## Average Question Length ##

    print("Total Number  Of Questions",totals)
    print("Total number of question types", total_question)
    stats_questions = LengthStatistics(questions_list)
    print("Average question length",stats_questions[1])

    ## Average Evidence Length ##

    stats_evidences = LengthStatistics(total_evidences)
    print("Average evidence length",stats_evidences[1])

    ## Average Note Length ##

    stats_evidences = LengthStatistics(all_clinical_notes)
    print("Average clinical note length", stats_evidences[1])

    ## Average number of questions per note ##

    print("Average Number of questions per note", totals/total_clinical_notes)
    print("Average number of question types per note", total_question/total_clinical_notes)

    ## Average number of evidences per question ##

    total__num_answers = 0
    for value in number_of_answers_per_question:
        if value == 0:
            print(number_of_answers_per_question[value])
        else:
            total__num_answers += value*number_of_answers_per_question[value]

    num_classes = len(set(classes))
    print("Average number of evidences", float(total__num_answers) / total_question)
    print("Percentage with one evidences",number_of_answers_per_question[1]*100.0/total_question)
    print("range in number of evidences",min(number_of_answers_per_question.keys()),max(number_of_answers_per_question.keys()))
    print("total number of classes in obesity and smoking datasets", num_classes)

    ################# more stats ignore for now ######################

    # indefinite_evidence_type = []
    # forms_in_data = []

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

