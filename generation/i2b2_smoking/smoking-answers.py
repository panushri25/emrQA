import xmltodict
import csv
import json
import argparse
import os
parser = argparse.ArgumentParser()
parser.add_argument('--i2b2_dir', default='', help='Directory containing i2b2 smoking challange files')
parser.add_argument('--templates_dir', default='', help='Directory containing template files in the given format')
parser.add_argument('--output_dir', default='', help='Directory to store the output')
args = parser.parse_args()


###################################################### SET FILE PATHS ##################################################################

templates_file = args.templates_dir
i2b2_file_paths = args.i2b2_dir

ql_output = os.path.join(args.output_dir,"smoking-ql.csv")
qa_output = os.path.join(args.output_dir,"smoking-qa.json")
file_names = ["smokers_surrogate_test_all_groundtruth_version2.xml","smokers_surrogate_train_all_version2.xml"]

######################################################## CODE #########################################################################

def ReadFile():
    file_path = i2b2_file_paths

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


def MakeJSONOutput(smoking_data, json_out, status, filewriter_forlform):

    smoking_out = {"paragraphs": [], "title": "smoking"}

    for state in status:
        patient_id = state[0]
        patient_note = state[2]

        out = {"note_id": patient_id, "context": patient_note, "qas": []}

        for row in smoking_data:
            question = row[2].strip()
            form = row[3].strip()
            answer_type = row[4]

            if question == "":
                continue

            question_list = question.split("##")
            for q in question_list:
                filewriter_forlform.writerow([q, form, q, form])

            if answer_type == "smoke_class":

                out["qas"].append({"answers": [{"answer_start": "", "text": state[1], "evidence": "", "evidence_start": ""}],
                 "id": [zip(question_list, question_list), form], "question": question_list})


        smoking_out["paragraphs"].append(out)


    with open(json_out, 'w') as outfile:
        json.dump(smoking_out, outfile)

if __name__=="__main__":

    ### Read i2b2 files, one status per clinical note ###

    status = ReadFile()

    ### File to read templates ###

    filereader = list(csv.reader(open(templates_file)))

    ## read only templates relevant to smoking challenge ##

    smoking_lines = []
    for line in filereader[1:]:
        if line[0] != "smoking" and line[0] != "smoking":
            continue
        smoking_lines.append(line)

    ofile = open(ql_output, "w")
    filewriter_forlform = csv.writer(ofile, delimiter="\t")
    filewriter_forlform.writerow(["Question", "Logical Form"])

    MakeJSONOutput(smoking_lines, qa_output, status, filewriter_forlform)
    #MakeQuestion(smoking_lines,out_file,status)



'''
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

'''