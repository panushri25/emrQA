import json
import csv
import random
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument('--output_dir', default='/home/anusri/Desktop/emrQA/output/', help='Directory of output files')

args = parser.parse_args()

###################################################### SET FILE PATHS ##################################################################

medications = json.load(open(os.path.join(args.output_dir,"medication-qa.json")))
relations = json.load(open(os.path.join(args.output_dir,"relations-qa.json")), encoding="latin-1")
risk = json.load(open(os.path.join(args.output_dir,"risk-qa.json")))
smoking = json.load(open(os.path.join(args.output_dir,"smoking-qa.json")))
obesity = json.load(open(os.path.join(args.output_dir,"obesity-qa.json")))


######################################################## CODE #########################################################################

data = [medications, relations, risk, smoking, obesity]
#data = [relations]
data_out = {"data": data}
json_out = os.path.join(args.output_dir,"data.json")
with open(json_out, 'w') as outfile:
    json.dump(data_out, outfile,  encoding="latin-1")

total_clinical_notes = 0
all_questions = []
all_clinical_notes = []
for dataset in data:

    for note in dataset["paragraphs"]:
        total_clinical_notes += 1
        if " ".join(note["context"]) not in all_clinical_notes:
            all_clinical_notes.extend([" ".join(note["context"])])
        else:
           #print("repeat")
           continue

        for questions in note["qas"]:
            #print(questions["question"])
            all_questions.append(list(set(questions["question"])))  # all questions

out = []
count = {}
print("Total Clinical Notes", len(all_clinical_notes))
total_question = len(all_questions)
totals = 0
questions_list = []
for value in all_questions:
    #print(value)
    if type(value) != list:
        print("error")
    if len(value[0]) == 1:
        print(value)
    #out.append([len(value[0]),len(value),"\t".join(value)])
    #if len(value) not in count:
    #    count[len(value)] = []
    totals += len(value)
    questions_list.extend(value)

'''
print(len(count))
new_list = sorted(out, key=lambda x: x[1], reverse=True)

ofile = open("testing","w")
for val in new_list:
    ofile.write("\t".join(map(str,val)))
    ofile.write("\n")

ofile.close()
'''
## Average Question Length ##

print("Total Number  Of Questions", totals)
print("Total number of question types", total_question)

##################################################################################################################################

medications = os.path.join(args.output_dir,"medication-ql.csv")
relations = os.path.join(args.output_dir,"relations-ql.csv")
risk = os.path.join(args.output_dir,"risk-ql.csv")
smoking = os.path.join(args.output_dir,"smoking-ql.csv")
obesity = os.path.join(args.output_dir,"obesity-ql.csv")

data = [medications, relations, risk, smoking, obesity]

unique = set()


for file_path in data:
    file = open(file_path)
    filereader = list(csv.reader(file))

    for line in filereader[1:]:
        unique.add(tuple(line))
        #if random.randint(1,100) < 10:
            #print(line)

values = list(unique)

print("Total number of QL forms", len(values))

final_out = os.path.join(args.output_dir,"data-ql.csv")
ofile = open(final_out, "w")
writer = csv.writer(ofile, delimiter="\t")
writer.writerow(["Question", "Logical Form", "QTemplate", "LTemplate"])

for val in values:
    writer.writerow(val)

ofile.close()


'''

datasets = json.load(open("data.json"))
for dataset in datasets:
    print(dataset["title"])

    for ClinicalNote in dataset["paragraphs"]:

        NoteText = "\n".join(ClinicalNote["context"])

        for questions in ClinicalNote["qas"]:

            paraphrase_questions = questions["question"]
            print(paraphrase_questions)
            for answer in  questions["answers"]:

                answer_text = answer["text"]
                answer_start = answer["answer_start"] ## [start_line,start_token] from NoteText
                evidence = answer["evidence"] ## The evidence here is question line + answer line (the evidence we use as ground truth is start_line from answer_start)

                print(answer_text,answer_start,evidence)

'''
'''
use_evidence_model = "True"

paras = []
idx = 0
for note in medications["paragraphs"]:

    if medications["title"] == "risk-dataset":

        text = "\n".join(note["context"])
        para = {"context": text, "qas": []}

        for questions in note["qas"]:
            idx += 1  ## Take care of this
            question = {"question": questions["question"], "answers": [], "id": idx}

        if use_evidence_model == "True":
            for answer in questions["answers"]:
                question["answers"].append({"text": answer["evidence"], "answer_start": answer["answer_start"][0]}) ## the answer line
        else:
            for answer in questions["answers"]:
                question["answers"].append({"text": answer["text"], "answer_start": answer["answer_start"][1]}) ## the answer text
    else:

        text = "".join(note["context"])
        line_lenth = [len(line) for line in note["context"]]
        para = {"context": text, "qas": []}

        for questions in note["qas"]:
            idx += 1
            print(questions["id"])
            question = {"question": questions["question"], "answers": [], "id": idx}
            for answer in questions["answers"]:

                if use_evidence_model == "True":
                    try: ## evidence and evidence start token
                        question["answers"].append({"text":note["context"][answer["answer_start"][0]-1],"answer_start":sum(line_lenth[answer[:answer["answer_start"][0]-1]])})
                    except:
                        unique = []
                        for num in list(map(lambda x: x - 1, answer["evidence_start"])):
                            if num not in unique:
                                unique.append(num)
                                question["answers"].append({"text":note["context"][num],"answer_start":sum(line_lenth[:num])})
                else:
                    try: ## answer and answer start token
                        question["answers"].append({"text": answer["text"],
                                                    "answer_start": sum(
                                                        line_lenth[answer[:answer["answer_start"][0] - 1]])+answer["answer_start"][1]})
                    except:
                        unique = []
                        for num in list(map(lambda x: x - 1, answer["evidence_start"])):
                            if num not in unique:
                                unique.append(num)
                                question["answers"].append(
                                    {"text": note["context"][num], "answer_start": sum(line_lenth[:num])})


        para["qas"].append(question)

    paras.append(para)

medications_new = {"paragraphs": paras, "title": "medications"}

#file = open("file.json", "w")
data = {}
data["data"] = [medications_new]
output = {'qids': [], 'questions': [], 'answers': [],
              'contexts': [], 'qid2cid': []}
for article in data["data"]:
        for paragraph in article['paragraphs']:
            output['contexts'].append(paragraph['context'])
            for qa in paragraph['qas']:
                output['qids'].append(qa['id'])
                #print(qa["question"])
                output['questions'].append(qa['question'])
                output['qid2cid'].append(len(output['contexts']) - 1)
                if 'answers' in qa:
                    output['answers'].append(qa['answers'])
                    #print(qa['answers'])
                    
json_out = "data_squad_format.json"
with open(json_out, 'w') as outfile:
    json.dump(data, outfile,  encoding="utf-8")

'''