from os import listdir
from os.path import isfile, join
import xmltodict
import csv
import json

def ReadFile():
    file_path = "/home/anusri/Desktop/IBM/i2b2/smoking/"
    file_names = ["smokers_surrogate_test_all_groundtruth_version2.xml","smokers_surrogate_train_all_version2.xml"]

    status = []
    for file_name in file_names:
        file = file_path + file_name
        with open(file) as fd:
            XML = xmltodict.parse(fd.read())
            idx = 0
            for key in XML["ROOT"]["RECORD"]:
                idx += 1

                patient_id = key["@ID"]
                answer_class = key["SMOKING"]["@STATUS"]
                patient_note = key["TEXT"]

                status.append([patient_id,answer_class,patient_note])

    return status


def MakeQuestion(smoking_data,out_file,status):

    ofile = open(out_file,"w")
    ofilewriter = csv.writer(ofile)

    values = ["Question", "Answer" , "Answer line in note",	"Note ID", "Difference in QA lines"]
    ofilewriter.writerow(values)

    for row in smoking_data:
        #print(row)
        question = row[1].strip()
        #print(row)
        answer_type = row[3]

        if answer_type == "smoke_class":
            for state in status:
                values = [question, state[1],"",state[0],""]
                patient_id = status[0]
                patient_note = status[2]

                ofilewriter.writerow(values)
        elif answer_type == "None":
            #return []
            pass
        else:
            print(answer_type)



def MakeJSONOutput(smoking_data, json_out, status):

    smoking_out = {"paragraphs": [], "title": "smoking"}


    for row in smoking_data:
        question = row[2].strip()
        form = row[3].strip()
        if question == "":
            continue
        #print(row)
        answer_type = row[4]

        tuple_id = []
        question_list = question.split("##")
        for q in question_list:
            q_id = question_id[q]
            tuple_id.append([q_id,q])
        l_id = logicalform_id[form]
        if answer_type == "smoke_class":
            for state in status:
                # values = [question, state[1],"",state[0],""]
                patient_id = state[0]
                patient_note = state[2]
                out = {"note_id": patient_id, "context": patient_note, "qas": [
                    {"answers": [{"answer_start": "", "text": state[1], "evidence": "", "evidence_start": ""}],
                     "id": [tuple_id,form], "question": question_list}]}

                smoking_out["paragraphs"].append(out)

    with open(json_out, 'w') as outfile:
        json.dump(smoking_out, outfile)


question_id = {}
logicalform_id = {}

csvreader = (csv.reader(open("/home/anusri/Desktop/codes_submission/dataset_indexing/questions_index.csv")))
for listi in csvreader:
    question_id[listi[0]] = listi[1]

csvreader = (csv.reader(open("/home/anusri/Desktop/codes_submission/dataset_indexing/logical_forms_index.csv")))
for listi in csvreader:
    logicalform_id[listi[0]] = listi[1]


questions_file = "templates-all.csv"
out_file = "smoking-question-answers.csv"
json_out = "smoking.json"
status = ReadFile()

filereader = list(csv.reader(open(questions_file)))
smoking_lines = []
for line in filereader[1:]:
    if line[0] != "smoking" and line[0] != "smoking":
        continue
    smoking_lines.append(line)

MakeQuestion(smoking_lines,out_file,status)
MakeJSONOutput(smoking_lines,json_out,status)


