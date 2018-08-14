import csv
from os import listdir
from os.path import isfile, join
import itertools
import json
import random

### Fix start_token ##
#check for uniqness of questions
#check for uniqness of answers

## i2b2 file paths ##

DosageFilePath = [
    "/home/anusri/Desktop/IBM/i2b2/medication/annotations_ground_truth/converted.noduplicates.sorted/",
        "/home/anusri/Desktop/IBM/i2b2/medication/training.ground.truth/"]

MedicationClinicalNotes = ["/home/anusri/Desktop/IBM/i2b2/medication/train.test.released.8.17.09/"]

## template file path ##

template_file_path = "/home/anusri/Desktop/emrQA/templates/templates-all.csv"

## output file paths ##

qa_output = "/home/anusri/Desktop/emrQA/output/medication-qa.csv"
ql_output = "/home/anusri/Desktop/emrQA/output/medication-ql.csv"
medications_qa_output_json = "/home/anusri/Desktop/emrQA/output/medication-qa.json"
medications_ql_output_json = "/home/anusri/Desktop/emrQA/output/medication-ql.json"

class GenerateQA():


    DosageFilePath = DosageFilePath
    MedicationClinicalNotes = MedicationClinicalNotes


    def __init__(self):

        self.ReadMedicationData()
        self.ReadTemplates()

    def ReadMedicationData(self):

        ## based on format of the i2b2 files. please refer to the i2b2 medications challenge documentation for details ###

        abbs = {"m": "medication", "do": "dosage", "mo": "mode", "f": "frequency", "du": "duration", "r": "problem",
                "e": "event", "t": "temporal", "c": "certainty", "ln": "list"}
        exception = ["list", "event", "temporal",
                     "certainty"]  ## very few annotations are tagged with these, hence we willl ignore them.

        self.MedicationData = []
        ClinicalNotes = {}

        ## read the clinical notes ##
        for paths in self.MedicationClinicalNotes:
            files = [f for f in listdir(paths) if isfile(join(paths, f))]
            for file in files:
                remote_file = open(paths + file)
                ClinicalNotes[file.strip()] = remote_file.readlines()

        ## read the annotations per clinical note (parse the files) ##

        annotations_span = []
        for paths in self.DosageFilePath:
            files = [f for f in listdir(paths) if isfile(join(paths, f))]
            for file in files:
                remote_file = open(paths + file)

                note_id = file.split(".")[0]
                note_id = note_id.split("_")[0]
                # print(file)
                dictionary = {note_id: []}
                PatientNote = ClinicalNotes[note_id]  ## access the corresponding clinical note.
                flag = 0
                for line in remote_file:
                    med_list = {}
                    line = line.replace("|||", "||")
                    words = line.split("||")

                    for word in words:
                        term = word.split("=")
                        try:
                            type = abbs[term[0].strip()]  ## check if all of them lie within the given annotation list
                        except:
                            print(paths + file)
                            flag = 1
                            break

                        full_annotation = "=".join(term[1:])
                        index = [pos for pos, char in enumerate(full_annotation) if char == "\""]
                        pos1 = int(index[0])
                        pos2 = int(index[-1])

                        annotation = full_annotation[pos1 + 1:pos2]
                        indxs = full_annotation[pos2 + 1:].split(",")

                        line_in_note = ""
                        start_line = None
                        if annotation == "nm" or type in exception:
                            med_list[type] = [annotation, line_in_note, start_line]
                            continue

                        # print(word,annotation,indxs)
                        # print(indxs)
                        for indx in indxs:
                            indx = indx.strip()
                            out = indx.split(" ")

                            start_line = out[0].split(":")[0]
                            start_token = out[0].split(":")[1]
                            end_line = out[1].split(":")[0]
                            end_token = out[1].split(":")[1]

                            line_in_note += ",".join(PatientNote[int(start_line) - 1:int(end_line)])

                            # if int(end_line) > int(start_line):
                            #    print(type)
                            #    print(line)
                            #    print(end_line,start_line)

                            ## some end line number are greater than start line numbers. annotation line_in_note can span upto 3 lines
                            ## annotation  can be discontinous set of tokens

                        med_list[type] = [annotation, line_in_note, start_line, start_token]

                        # if start_line != end_line:
                        #   print(int(end_line)-int(start_line))
                        #    print(line_in_note)

                    dictionary[note_id].append(med_list)

                remote_file.close()

                if flag == 0:
                    self.MedicationData.append((dictionary, PatientNote))


                    # print(annotations_span)

    def ReadTemplates(self):

        self.medications_out = {"paragraphs": [], "title": "medication"}
        self.logical_out = []

        ########################################## Set File Paths ##############################################


        ### File to write Question-Answers ##

        ofile = open(qa_output,"w")
        self.filewriter = csv.writer(ofile, delimiter="\t")
        self.filewriter.writerow(["Question", "Logical Form" ,"Answer", "Answer line in note",  "Note ID", "Difference in QA lines"])

        ### File to write Question-Logical Forms ##

        ofile = open(ql_output, "w")
        self.filewriter_forlform = csv.writer(ofile, delimiter="\t")
        self.filewriter_forlform.writerow(["Question", "Logical Form"])

        ### File to read templates ###

        file = open(template_file_path)
        filereader = list(csv.reader(file))

        ## read only templates relevant to medications challenge ##

        med_lines = []
        for line in filereader[1:]:
            if line[0] != "medication" and line[0] != "medications":
                continue
            med_lines.append(line)

        ########################################## Main Function Call ##############################################

        for (dictionary,PatientNote) in self.MedicationData:
            for note_id in dictionary:
                out_patient = {"note_id": note_id, "context": PatientNote, "qas": []}

                med_list = dictionary[note_id] ## extract all the annotations given per note ##

                ## create one to many mappings, to use them for QA. Coreference not resolved ##

                self.MakeMedicationRelationMappings(med_list)

                flag = 0
                self.unique_questions = []
                question_id = 0
                for line in med_lines:
                    ## do +1 for the new format ##
                    question = line[2].strip()
                    answertype = line[4].split(",")
                    answertype = [type.strip() for type in answertype]
                    logical_form = line[3].strip()

                    #question = question.replace("|problem| or |problem|","|problem|")
                    question = question.replace("|medication| or |medication|", "|medication|")
                    question = question.replace("|problem| or |problem|", "|problem|")
                    question = question.replace("|test| or |test|", "|test|")
                    question = question.replace("|test| |test| |test|", "|test|")
                    question = question.replace("\t", "")
                    logical_form = logical_form.replace("\t", "")

                    if question.strip() == "":
                        continue

                    answer_out = self.MakeMedicationQA(question,logical_form,answertype,med_list,flag,note_id,PatientNote,question_id)

                    if len(answer_out) != 0:
                        #for answer in answer_out:
                            #print(answer["id"])
                        out_patient["qas"].extend(answer_out)
            self.medications_out["paragraphs"].append(out_patient)

        ################################################################# Dump JSON ###########################################

        json_out = medications_qa_output_json
        with open(json_out, 'w') as outfile:
            json.dump(self.medications_out, outfile, ensure_ascii=False) ## storage format same as SQUAD

        #json_out = medications_ql_output_json
        #with open(json_out, 'w') as outfile:
        #    json.dump(self.logical_out, outfile, ensure_ascii=False) ## storage format, question logical_form question_id logicalfrom_id source

    def MakeMedicationRelationMappings(self,med_list):

        self.map_meds_to_reasons = {}
        self.map_meds_to_dosages = {}
        self.map_meds_to_frequency = {}
        self.map_reasons_to_meds = {}
        self.map_meds_to_durations = {}
        self.medications_all = {}


        for med_annotations in med_list:

            if med_annotations["medication"][0] not in self.medications_all:
                self.medications_all[med_annotations["medication"][0]] = [med_annotations["medication"]]
                #print(med_annotations["medication"])

            if med_annotations["medication"][0] not in self.map_meds_to_dosages:
                self.map_meds_to_dosages[med_annotations["medication"][0]] = []

            if med_annotations["medication"][0] not in self.map_meds_to_frequency:
                self.map_meds_to_frequency[med_annotations["medication"][0]] = []

            if med_annotations["medication"][0] not in self.map_meds_to_reasons:
                self.map_meds_to_reasons[med_annotations["medication"][0]] = []

            if med_annotations["problem"][0] != "nm":
                if med_annotations["problem"][0] not in self.map_reasons_to_meds:
                    self.map_reasons_to_meds[med_annotations["problem"][0]] = []

            if med_annotations["medication"][0] not in self.map_meds_to_durations:
                self.map_meds_to_durations[med_annotations["medication"][0]] = []

            if med_annotations["dosage"][0] != "nm":
                #if med_annotations["event"] == ""
                self.map_meds_to_dosages[med_annotations["medication"][0]].append(med_annotations["dosage"]+med_annotations["list"])
            if med_annotations["problem"][0] != "nm":
                self.map_meds_to_reasons[med_annotations["medication"][0]].append(med_annotations["problem"]+med_annotations["list"])
            if med_annotations["problem"][0] != "nm":
                self.map_reasons_to_meds[med_annotations["problem"][0]].append(med_annotations["medication"]+med_annotations["list"])
            if med_annotations["frequency"][0] != "nm":
                self.map_meds_to_frequency[med_annotations["medication"][0]].append(med_annotations["frequency"]+med_annotations["list"])
            if med_annotations["duration"][0] != "nm":
                self.map_meds_to_durations[med_annotations["medication"][0]].append(med_annotations["duration"]+med_annotations["list"])

    def MakeAnswer(self, quest_list_nar, answertype, med_annotations, question_list,line_num,line_token):

        result_num = []
        result_token = []
        answer_line = []
        list_nar = quest_list_nar
        answer = []

        idx = 0
        if answertype[idx] == "yes":
            answer = ["yes"]*len(question_list)
            answer_line.extend(question_list)
            result_num.extend(line_num)
            result_token.extend(line_token)
            list_nar.extend(quest_list_nar)
        elif answertype == ["problem"]:
            for listr in self.map_meds_to_reasons[med_annotations["medication"][0]]:
                answer += [listr[0]]
                answer_line.append(listr[1])
                result_num.append(int(listr[2]))
                result_token.append(int(listr[3]))
                list_nar.append(listr[3])
        elif answertype == ["frequency"]:
            # print("frequency")
            for listr in self.map_meds_to_frequency[med_annotations["medication"][0]]:
                answer += [listr[0]]
                answer_line.append(listr[1])
                result_num.append(int(listr[2]))
                result_token.append(int(listr[3]))
                list_nar.append(listr[3])
        elif answertype == ["dosage"]:
            for med in [med_annotations["medication"][0]]:
                for listr in self.map_meds_to_dosages[med]:
                    answer += [listr[0]]
                    answer_line.append(listr[1])
                    result_num.append(int(listr[2]))
                    result_token.append(int(listr[3]))
                    list_nar.append(listr[3])
        elif answertype == ["medication"]:
            for listr in self.map_reasons_to_meds[med_annotations["problem"][0]]:
                answer += [listr[0]]
                answer_line.append(listr[1])
                result_num.append(int(listr[2]))
                result_token.append(int(listr[3]))
                list_nar.append(listr[3])
        elif answertype == ["medication", 'dosage']:
            meds = self.map_reasons_to_meds[med_annotations["problem"][0]]
            for med in meds:
                dos = ",".join([x[0] for x in self.map_meds_to_dosages[med[0]]])
                answer += ["( " + med[0] + ", " + dos + ")"]
                #answer += [dos]
                answer_line.append(med[1])
                answer_line.extend([x[1] for x in self.map_meds_to_dosages[med[0]]])
                result_num.extend([int(med[2])])
                result_token.extend([int(med[3])])
                result_num.extend([int(x[2]) for x in self.map_meds_to_dosages[med[0]]])
                result_token.extend([int(x[3]) for x in self.map_meds_to_dosages[med[0]]])
                list_nar.extend([x[3] for x in self.map_meds_to_dosages[med[0]]])
                list_nar.append(med[3])
        elif answertype == ["duration"]:
            for listr in self.map_meds_to_durations[med_annotations["medication"][0]]:
                answer += [listr[0]]
                answer_line.append(listr[1])
                result_num.append(int(listr[2]))
                result_token.append(int(listr[3]))
                list_nar.append(listr[3])
        elif answertype == ["medications_all"]:
            for medication_name in self.medications_all:
                listr = self.medications_all[medication_name][0]
                answer += [listr[0]]
                answer_line.append(listr[1])
                result_num.append(int(listr[2]))
                result_token.append(int(listr[3]))
                list_nar.append(listr[3])
        elif answertype == ["none"]:
            pass
        else:
            print(answertype)
            answer = []

        return [answer,answer_line, result_num, result_token, list_nar]

    def CheckForErrors(self, question_list,logical_form_template):
        dup_rwords_list = []
        unique_templates = []
        qwords_list = []
        for question in question_list:
                if question.strip() == "":
                    continue
                question = question.replace("|medication| or |medication|", "|medication|")
                question = question.replace("|problem| or |problem|", "|problem|")
                question = question.replace("|test| or |test|", "|test|")
                question = question.replace("|test| |test| |test|", "|test|")
                question = question.strip()

                if question not in unique_templates:
                    unique_templates.append(question)
                else:
                    continue
                qwords = question.split("|")
                dup_rwords = qwords[1:len(qwords):2]
                qwords_list.append(qwords)

                if len(dup_rwords_list) == 0:
                    dup_rwords_list = [set(dup_rwords)]
                else:
                    if set(dup_rwords) not in dup_rwords_list:
                        print("Error Out Of Context Question:")
                        print(question, logical_form_template, question_list)
                        return None


        lwords = logical_form_template.split("|")
        dup_lrwords = lwords[1:len(lwords):2]
        if set(dup_lrwords) not in dup_rwords_list:
            print("Error Out Of Context Question-Logical Form Pairs:")
            print(question_list, logical_form_template)
            return None

        return dup_rwords_list

    #def MakeMedicationQL(self):

    def MakeMedicationQA(self,question_list,logical_form_template, answertype,med_list,flag,note_id,PatientNote,question_id):

        print(question_list)
        print(logical_form_template)

        answer_out = []
        intial_question_list = question_list.split("##")
        intial_template = logical_form_template

        #orginal_questions_list = question_list
        orginal_logical_form_template = logical_form_template.strip()

        question_list = question_list.split("##")
        logical_form_template = logical_form_template.strip()

        if self.CheckForErrors(question_list,logical_form_template) == None:
            return answer_out
        else:
            dup_rwords_list = self.CheckForErrors(question_list,logical_form_template) ## type of words to replace ##

        ##### make questions #####

        for med_annotations in med_list: ## Medlist is a list of dictionaries (each dict is a medication and its attributes)

            logical_form_template = orginal_logical_form_template
            if len(dup_rwords_list) != 1:
                print("Check Question_Logical Form Mapping")
                print(dup_rwords_list,question_list)
                print(logical_form_template)
                return answer_out
            else:
                dup_rwords = dup_rwords_list[0]

            rwords = list(dup_rwords)
            line_num = []
            line_token = []
            question_line = []
            quest_list_nar = []
            paraphrase_questions = []
            tuple_orginal = []
            answer = []

            if rwords != ["time"]:
                for idx in range(len(rwords)):
                    if rwords[idx] == "treatment":
                        rwords[idx] = "medication"
                    if med_annotations[rwords[idx]][0] == "nm":
                        flag = 1
                        break
                    else:
                        line_num.append(int(med_annotations[rwords[idx]][2]))
                        line_token.append(int(med_annotations[rwords[idx]][3]))
                        question_line.append(med_annotations[rwords[idx]][1])
                        rwords[idx] = med_annotations[rwords[idx]][0]
                        quest_list_nar.append(med_annotations["list"][0])

            ### checking if no question annotation is nm and make question ##
            if flag == 0:

                if rwords == ["time"]:
                    time = str(random.randint(2, 5)) + random.choice([" years", " weeks"])
                    for question in question_list:
                        original = question
                        question = question.replace("|time|", time)
                    logical_form_template = logical_form_template.replace("|time|", time)
                    rwords = []
                    dup_rwords = []
                    paraphrase_questions.append(question)
                    tuple_orginal.append((question,original))
                else:
                    for question in question_list:

                        orginal = question
                        idx = 0
                        done = []
                        for types in list(dup_rwords):
                            #temp = qwords
                            index = question.find("|"+types+"|")
                            if index == -1 and types not in done:
                                print(question,"|" + types + "|",done)
                            question = question.replace("|"+types+"|",rwords[idx])
                            done.append(types)
                            idx += 1
                        tuple_orginal.append((question,orginal))
                        paraphrase_questions.append(question)
                #print(paraphrase_questions)

          ### Make Logical Form ####

                idx = 0
                done = []
                for types in list(dup_rwords):
                    logical_form_template.replace("|treatment|","|medication")
                    index = logical_form_template.find("|" + types + "|")
                    if index == -1 and types not in done:
                        print(logical_form_template, "|" + types + "|", done,types)
                    done.append(types)

                    logical_form_template = logical_form_template.replace("|" + types + "|", rwords[idx])
                    idx += 1

                logical_form = logical_form_template

                ##### Make answers for the succesful questions ####
                [answer, answer_line, result_num, result_token, list_nar] = self.MakeAnswer( quest_list_nar, answertype, med_annotations, question_line, line_num,line_token)

            else:
                return  answer_out

            if len(answer) != 0:
                perms = list(itertools.product(result_num+line_num, result_num+line_num))
                diffs = [abs(val1 - val2) for (val1, val2) in perms]
                difference = max(diffs)

                Note_val = "#".join(answer_line)
                list_nar = ",".join(list_nar)

                print(len(paraphrase_questions))
                unique_paras = set(paraphrase_questions)
                print(len(unique_paras))
                if unique_paras not in self.unique_questions:
                    #print(unique_paras)
                    tuple_id = []
                    #question_templates = orginal_questions_list.split("##")
                    unique_tup = list(set(zip(paraphrase_questions, intial_question_list)))
                    # print(unique_tup)

                    for (question,orginal) in tuple_orginal:
                        self.filewriter_forlform.writerow([question] + [logical_form.strip()] + [orginal.strip()] + [intial_template])

                    #l_id = self.logicalform_id[intial_template]
                    #for qidx in range(len(unique_tup)):
                    #    q_id = self.question_id[unique_tup[qidx][1]]
                    #    #print(unique_tup[qidx][1],q_id,orginal_logical_form_template,l_id,unique_tup[qidx][0])
                    #    self.filewriter_forlform.writerow([unique_tup[qidx][0]] + [logical_form] + [q_id] + [l_id])
                    #    tuple_id.append([q_id,unique_tup[qidx][0]])
                    #tuple_id_update = tuple_id
                    #l_id_update = l_id
                    self.unique_questions.append(unique_paras)
                    question_id += 1
                    ans_list = []
                    for idx in range(len(answer)):
                        ## evidence per answer ##
                        evidence_answer = []
                        evidence_start = []
                        evidence_temp_line =  answer_line
                        evidence_temp_start = result_num
                        for pdx in range(len(evidence_temp_line)):
                            if evidence_temp_line[pdx] not in evidence_answer:
                                evidence_answer.append(evidence_temp_line[pdx])
                                evidence_start.append(evidence_temp_start[pdx])

                        ### even the question line is evidence ##
                        if answer[idx] == "yes" or answer[idx] == "no":
                            start_line = ""
                            start_token = ""
                            self.filewriter.writerow(
                                ["##".join(list(unique_paras))] + [logical_form] + [",".join(answer)] + ["#".join(evidence_answer)] + [
                                    note_id + "_MedicationsChallenge"] + [difference] + [list_nar])

                            start_line = result_num[idx]  ## only result
                            start_token = result_token[idx]
                            #print(start_line)
                            #print(start_token)
                            #print(unique_paras)
                            #print(evidence_answer)
                            #print(PatientNote[result_num[idx]-1])

                        else:
                            self.filewriter.writerow(
                                ["##".join(list(unique_paras))] + [logical_form] + [",".join(set(answer))] + [Note_val] + [
                                    note_id + "_MedicationsChallenge"] + [difference] + [list_nar])

                            start_line = result_num[idx] ## only result
                            start_token = result_token[idx]
                            #print(evidence_answer)
                            #print(PatientNote[result_num[idx] - 1])

                        # evidence will have q_line_answer_line

                        val = {"answer_start": [start_line, start_token], "text": answer[idx],
                                         "evidence": evidence_answer,
                                         "evidence_start": evidence_start}
                        if val not in ans_list:
                            ans_list.append(val)
                    #print("\n")
                    #print(l_id,tuple_id)
                    answer_temp = {"answers": ans_list, "id": [tuple_orginal,intial_template], "question": list(unique_paras), "orginal_template": intial_template}
                    answer_out.append(answer_temp)

            else:
                ### Writing only question - logical form ##
                #question_templates = orginal_questions_list.replace("|medication|", "|treatment|").split("##")

                for (question, orginal) in tuple_orginal:
                    self.filewriter_forlform.writerow(
                        [question] + [logical_form.strip()] + [orginal.strip()] + [intial_template])

        return answer_out


#if __name__=="__main":
GenerateQA()