import xmltodict
import csv
import json
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument('--i2b2_dir', default='', help='Directory containing i2b2 obesity challange files')
parser.add_argument('--templates_dir', default='', help='Directory containing template files in the given format')
parser.add_argument('--output_dir', default='', help='Directory to store the output')
args = parser.parse_args()

###################################################### SET FILE PATHS ##################################################################

templates_file = args.templates_dir
obesity_file_path = i2b2_file_paths = args.i2b2_dir

file_names = ["obesity_standoff_annotations_test.xml","obesity_standoff_annotations_training.xml"]
note_names = ["obesity_patient_records_test.xml", "obesity_patient_records_training.xml"]

ql_output = os.path.join(args.output_dir,"obesity-ql.csv")
#print(ql_output)
qa_json_out = os.path.join(args.output_dir,"obesity-qa.json")

######################################################## CODE #########################################################################

def ReadFile():

    file_path = obesity_file_path

    Patient = {} #note_id is the key with a dictionary as value

    for note_name in note_names:
        file = file_path + note_name
        with open(file) as fd:
            XML = xmltodict.parse(fd.read())

            for doc in XML["root"]["docs"]["doc"]:
                doc_id = doc["@id"]
                note_text = doc["text"]


                if doc_id not in Patient:
                    Patient[doc_id] = {}
                Patient[doc_id]["text"] = note_text

    for file_name in file_names:
        file = file_path + file_name
        with open(file) as fd:
            XML = xmltodict.parse(fd.read())

            intuitive = XML["diseaseset"]["diseases"][0]["disease"]
            textual = XML["diseaseset"]["diseases"][1]["disease"]

            #print(intuitive)
            for idx in range(len(intuitive)):

                disease_name = intuitive[idx]["@name"]
                intuitive_docs_list = intuitive[idx]["doc"]

                for pidx in range(len(intuitive_docs_list)):

                    idoc_id = intuitive_docs_list[pidx]["@id"]
                    ijudgment = intuitive_docs_list[pidx]["@judgment"]

                    if idoc_id not in Patient:
                        Patient[idoc_id] = {}
                    if disease_name not in Patient[idoc_id]:
                        Patient[idoc_id][disease_name] = ijudgment

            for idx in range(len(textual)):

                disease_name = textual[idx]["@name"]
                textual_docs_list = textual[idx]["doc"]

                for pidx in range(len(textual_docs_list)):

                    tdoc_id = textual_docs_list[pidx]["@id"]
                    tjudgment = textual_docs_list[pidx]["@judgment"]

                    try:
                        ijudgment  = Patient[tdoc_id][disease_name]
                        if ijudgment != tjudgment and tjudgment != "U" and tjudgment != "Q":
                            print(ijudgment, tjudgment, disease_name, tdoc_id)
                    except:
                        try:
                            Patient[tdoc_id][disease_name] = tjudgment
                        except:
                            Patient[tdoc_id] = {disease_name:tjudgment}
                        continue


    return Patient

def MakeJSONOut(obesity_data,json_out,Patient):


    obesity_out = {"paragraphs": [], "title": "obesity"}

    for note_id in Patient:
        Y_class = []
        U_class = []
        Q_class = []
        N_class = []
        patient_note = Patient[note_id]["text"]
        out = {"note_id": note_id, "context": patient_note, "qas": []}
        unique_questions = []

        for problem in Patient[note_id]:
            if problem == "text":
                continue
            if Patient[note_id][problem] == "Y":
                Y_class.append(problem)
            elif Patient[note_id][problem] == "N":
                N_class.append(problem)
            elif Patient[note_id][problem] == "U":
                U_class.append(problem)
            elif Patient[note_id][problem] == "Q":
                Q_class.append(problem)
            else:
                print(Patient[note_id][problem])

        ######  not doing on all questions #####

        for row in obesity_data:
            question = row[2].strip()

            if question == "":
                continue
            lform = row[3]
            answer_type = row[4]
            question = question.replace("\t", "")
            lform = lform.replace("\t", "")
            orginal = question

            if answer_type == "problems":
                for idx in range(len(Y_class)):
                    problem = Y_class[idx]
                    question = orginal

                    if problem == "Obesity":
                        qwords = question.split("|")
                        qwords[1] = problem
                        lform_new = lform.replace("|problem|",problem)
                        qwords = [word.strip() for word in qwords]
                        final_question = " ".join(qwords)
                        Answer = Y_class[0:idx] + Y_class[idx + 1:]
                    else:
                        question = orginal.replace("|problem|", problem)
                        lform_new = lform.replace("|problem|", problem)
                        filewriter_forlform.writerow([question] + [lform_new] + [question] + [lform])
                        continue

                    ans_list = []
                    for ans in Answer:
                        ans_list.append({"answer_start": "", "text": ans, "evidence": "", "evidence_start": ""})
                    #print(final_question)
                    answer = {"answers": ans_list, "id": [[final_question,final_question],lform], "question": [final_question]}
                    out["qas"].append(answer)

                    filewriter_forlform.writerow([question] + [lform_new] + [question] + [lform])

            elif answer_type == "yes/no" and "|problem|" in question:
                answers = ["yes", "no", "UNK"]
                jdx = -1
                question_template = question.split("##")
                #print(question)
                for temp in [Y_class, N_class, U_class]:
                    jdx += 1
                    for problem in temp:

                        #if problem.lower() != "obesity":
                        #    continue

                        orginal_lform = lform
                        question_lits = question.replace("|problem|",problem).split("##")
                        lform_new = lform.replace("|problem|", problem)
                        #print(question_lits)
                        idx = 0
                        if question_lits not in unique_questions:
                            unique_questions.append(question_lits)

                        for q in question_lits:
                            filewriter_forlform.writerow([q] + [lform_new] + [question_template[idx]] + [orginal_lform])
                            idx += 1

                        Answer = [answers[jdx]]
                        ans_list = []
                        for ans in Answer:
                            ans_list.append({"answer_start": "", "text": ans, "evidence": "", "evidence_start": ""})

                        answer = {"answers": ans_list, "id": [zip(question_lits,question_template),orginal_lform], "question": question_lits}

                        out["qas"].append(answer)
            else:
                print(answer_type)

        obesity_out["paragraphs"].append(out)

    with open(json_out, 'w') as outfile:
        json.dump(obesity_out, outfile)


if __name__=="__main__":

    ofile = open(ql_output, "w")
    filewriter_forlform = csv.writer(ofile, delimiter="\t")
    filewriter_forlform.writerow(["Question", "Logical Form"])

    ### Read i2b2 files ###

    Patient = ReadFile()

    ### File to read templates ###

    qfile = open(templates_file)
    read_data = list(csv.reader(qfile))

    ## read only templates relevant to obesity challenge ##

    obesity_data = []
    for line in read_data[1:]:
        if line[0] != "obesity":
            continue
        obesity_data.append(line)


    MakeJSONOut(obesity_data,qa_json_out,Patient)
    #MakeQuestion(questions_file,out_file,Patient)


'''
def MakeQuestion(questions_file,out_file,Patient):

    qfile = open(questions_file)
    read_data = list(csv.reader(qfile, delimiter="\t"))

    ofile = open(out_file, "w")
    ofilewriter = csv.writer(ofile)

    values = ["Question", "Answer", "Answer line in note", "Note ID", "Difference in QA lines"]
    ofilewriter.writerow(values)


    for note_id in Patient:
        Y_class = []
        U_class = []
        Q_class = []
        N_class = []
        for problem in Patient[note_id]:
            if Patient[note_id][problem] == "Y":
                Y_class.append(problem)
            elif Patient[note_id][problem] == "N":
                N_class.append(problem)
            elif Patient[note_id][problem] == "U":
                U_class.append(problem)
            elif Patient[note_id][problem] == "Q":
                Q_class.append(problem)
            else:
                print(Patient[note_id][problem])


        for row in read_data[1:4]:
            question = row[1].strip()
            if question == "":
                continue
            #print(row)
            answer_type = row[3]
            question_in = row[0] #question_concept_type

            if answer_type == "problems":
                for idx in range(len(Y_class)):
                    problem = Y_class[idx]
                    qwords = question.split("|")
                    qwords[1] = problem
                    qwords = [word.strip() for word in qwords]
                    final_question = " ".join(qwords)
                    Answer = Y_class[0:idx]+Y_class[idx+1:]
                    ofilewriter.writerow([final_question," ".join(Answer), "", note_id, ""])
            elif answer_type == "yes/no" and question_in == "problem":
                answers = ["yes","no",""]
                jdx = -1
                for temp in [Y_class,N_class,U_class]:
                    jdx += 1
                    for idx in range(len(temp)):
                        problem = temp[idx]
                        qwords = question.split("|")
                        qwords[1] = problem
                        qwords = [word.strip() for word in qwords]
                        final_question = " ".join(qwords)
                        Answer = answers[jdx]
                        ofilewriter.writerow([final_question,Answer, "", note_id, ""])
            elif answer_type == "yes/no" and question_in == "None":
                try:
                    if Patient[note_id]["Obesity"] == "Y":
                        ofilewriter.writerow([question, "yes", "", note_id, ""])
                    if Patient[note_id]["Obesity"] == "N":
                        ofilewriter.writerow([question, "no", "", note_id, ""])
                    if Patient[note_id]["Obesity"] == "U":
                        ofilewriter.writerow([question, "", "", note_id, ""])
                except:
                    print(Patient[note_id].keys())
            else:
                print(answer_type,question_in)
'''