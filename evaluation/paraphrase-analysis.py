import csv
import os
import nltk
from nltk.metrics import *
from nltk.translate.bleu_score import sentence_bleu
import argparse
import itertools
import random
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('--templates_dir', default='/home/anusri/Desktop/emrQA/templates', help='Directory containing template files in the given format')

args = parser.parse_args()
csv_reader = list(csv.reader(open(os.path.join(args.templates_dir,"templates-all.csv"))))

def scoring_method(qtuple,method):

    if method == "jaccard_score":
        set1 = set(nltk.word_tokenize(qtuple[0]))
        set2 = set(nltk.word_tokenize(qtuple[1]))
        score = jaccard_distance(set1,set2)

    if method == "blue_score":
        (reference, candidate) = qtuple
        score = sentence_bleu(reference, candidate)

    return score

if __name__=="__main__":

    method = "blue_score"
    #method = "jaccard_score"
    unique_logical_forms = []
    total_questions = []
    total_scores = []

    for line in csv_reader[1:]:

        question = line[2].strip()
        logical_form = line[3].strip()

        question = question.replace("|medication| or |medication|", "|medication|")
        question = question.replace("|problem| or |problem|", "|problem|")
        question = question.replace("|test| or |test|", "|test|")
        question = question.replace("|test| |test| |test|", "|test|")
        question = question.replace("\t", "")
        logical_form = logical_form.replace("\t", "").replace("|medication|","|treatment|")
        if logical_form not in unique_logical_forms:
            unique_logical_forms.append(logical_form)

        paraphrase_questions = question.split("##")
        random.shuffle(paraphrase_questions)
        total_questions.extend(list(set(paraphrase_questions)))

        question_tuples = list(itertools.product([paraphrase_questions[0]], paraphrase_questions[1:]))
        scores = []
        for qtuple in question_tuples:
            if qtuple[0] == qtuple[1]:
                continue
            scoring_tuple = scoring_method(qtuple, method)
            scores.append(scoring_tuple)

        if len(scores) != 0:
            min_value = min(scores)
            max_value = max(scores)

            total_scores.extend(scores)

    ## total questions by total question types

    print("Average paraphrases per question", len(total_questions)*1.0/len(unique_logical_forms))
    print("Average of "+ method+ " of paraphrases", np.mean(np.array(total_scores)))
    print("Standard deviation of " + method + " of paraphrases", np.std(np.array(total_scores)))

