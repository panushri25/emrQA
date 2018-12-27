import csv
import os
from os import listdir
from os.path import isfile, join
import json
import random
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--i2b2_dir', default='', help='Directory containing i2b2 medications challange files')
parser.add_argument('--templates_dir', default='', help='Directory containing template files in the given format')
parser.add_argument('--output_dir', default='', help='Directory to store the output')

args = parser.parse_args()


###################################################### SET FILE PATHS ##################################################################

## i2b2 file paths ##

DosageFilePath = [ os.path.join(args.i2b2_dir,"annotations_ground_truth/converted.noduplicates.sorted/"), os.path.join(args.i2b2_dir,"training.ground.truth/")]

MedicationClinicalNotes = [os.path.join(args.i2b2_dir,"train.test.released.8.17.09/")]

## template file path ##

template_file_path = args.templates_dir

## output file paths ##

ql_output = os.path.join(args.output_dir,"medication-ql.csv")
medications_qa_output_json = os.path.join(args.output_dir,"medication-qa.json")


######################################################## CODE #########################################################################

class GenerateQA():

    DosageFilePath = DosageFilePath
    MedicationClinicalNotes = MedicationClinicalNotes

    def __init__(self):

        self.ReadMedicationData()
        self.ReadTemplates()

    ######################### Read i2b2 file functions ###################################

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

                            line_in_note += "".join(PatientNote[int(start_line) - 1:int(end_line)])

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
                    if (dictionary, PatientNote) not in self.MedicationData:
                        self.MedicationData.append((dictionary, PatientNote))


                    # print(annotations_span)

    ######################## Main program functions ##########################################

    def ReadTemplates(self):

        self.medications_out = {"paragraphs": [], "title": "medication"}
        self.logical_out = []

        ########################################## Set File Paths ##############################################


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
                    logical_form = line[3].strip()
                    answertype = line[4].split(",")
                    answertype = [type.strip() for type in answertype]


                    #question = question.replace("|problem| or |problem|","|problem|")
                    question = question.replace("|medication| or |medication|", "|medication|")
                    question = question.replace("|problem| or |problem|", "|problem|")
                    question = question.replace("|test| or |test|", "|test|")
                    question = question.replace("|test| |test| |test|", "|test|")
                    question = question.replace("\t", "")
                    logical_form = logical_form.replace("\t", "")

                    if question.strip() == "":
                        continue

                    answer_out = self.MakeMedicationQLA(question,logical_form,answertype,med_list,flag,note_id,PatientNote,question_id)

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
        #   json.dump(self.logical_out, outfile, ensure_ascii=False) ## storage format, question logical_form question_id logicalfrom_id source

    def MakeMedicationQLA(self, question_list, logical_form_template, answertype, med_list, flag, note_id, PatientNote, question_id):

        answer_out = []

        ## save a copy of the orginals ##
        intial_question_list = question_list.split("##")
        intial_template = logical_form_template
        orginal_logical_form_template = logical_form_template.strip()

        ## check for errors in templates and gather all the placeholders in the templates (placeholders stored in rwords) ##
        ## semantic types of placeholders ##

        dup_rwords_list = self.CheckForErrors(intial_question_list, orginal_logical_form_template)
        if dup_rwords_list == None:
            return answer_out

        for med_annotations in med_list:  ## Medlist is a list of dictionaries (each dict is a medication and its attributes)

            flag = 0
            logical_form_template = orginal_logical_form_template
            if len(dup_rwords_list) != 1:  ## sanity check
                print("Check Question_Logical Form Mapping")
                print(dup_rwords_list, intial_question_list)
                print(logical_form_template)
                return answer_out
            else:
                dup_rwords = dup_rwords_list[0]

            rwords = list(dup_rwords)
            line_num = []
            line_token = []
            question_line = []
            quest_list_nar = []

            answer = []

            ### checking if  placeholder values to be used in question is "nm" (not mentioned), if yes set flag to 1  ##

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

            ## Generate question, logical form and answer only if flag is 0 ##

            if flag == 0:
                [paraphrase_questions, tuple_orginal, logical_form] = self.MakeMedicationQL(rwords,
                                                                                            intial_question_list,
                                                                                            logical_form_template,
                                                                                            dup_rwords)
                [answer, answer_line, result_num, result_token, list_nar] = self.MakeAnswer(quest_list_nar, answertype,
                                                                                            med_annotations,
                                                                                            question_line, line_num,
                                                                                            line_token)
            else:
                continue
                # return  answer_out  #### bug fixed ##

            if len(answer) != 0:

                if answertype == ["medication", 'dosage']:
                    entity_type = "complex"
                elif answertype == ["yes"]:
                    entity_type = "empty"
                else:
                    entity_type = "single"

                unique_paras = set(paraphrase_questions)
                if unique_paras not in self.unique_questions:  ## redundancy check: checking if these set of questions are unique for every clinical note ##

                    self.unique_questions.append(unique_paras)
                    question_id += 1
                    ans_list = []
                    for idx in range(len(answer)):

                        start_line = result_num[idx]
                        start_token = result_token[idx]

                        val = {"answer_start": [start_line, start_token], "text": answer[idx],
                               "evidence": answer_line[idx], "evidence_start": result_num[idx], "answer_entity_type": entity_type}

                        if val not in ans_list:
                            ans_list.append(val)

                        ## ""evidence"" in the dictionary above is currently just the answer line in the note. You can also consider question line and answer line from note as evidence in that uncomment below code and use it accordingly #

                        '''

                         ## maximum distance between the question line and answer line ##
                         perms = list(itertools.product(result_num+line_num, result_num+line_num))
                         diffs = [abs(val1 - val2) for (val1, val2) in perms]
                         difference = max(diffs)

                         Note_val = "#".join(answer_line)
                         list_nar = ",".join(list_nar)

                          ## evidence per answer ##
                          evidence_answer = []
                          evidence_start = []
                          evidence_temp_line =  answer_line
                          evidence_temp_start = result_num
                          for pdx in range(len(evidence_temp_line)):
                              if evidence_temp_line[pdx] not in evidence_answer:
                                  evidence_answer.append(evidence_temp_line[pdx])
                                  evidence_start.append(evidence_temp_start[pdx])

                           val = {"answer_start": [start_line, start_token], "text": answer[idx],
                                           "evidence": evidence_answer,
                                           "evidence_start": evidence_start}

                           if qa_csv_write:
                              self.filewriter.writerow(
                                  ["##".join(list(unique_paras))] + [logical_form] + [",".join(set(answer))] + [Note_val] + [note_id + "_MedicationsChallenge"] + [difference] + [list_nar])


                          '''

                    answer_temp = {"answers": ans_list, "id": [tuple_orginal, intial_template],
                                   "question": list(unique_paras)}
                    answer_out.append(answer_temp)

        return answer_out

    ######################## Main Utility Functions ######################################

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
                if med_annotations["dosage"]+med_annotations["list"] not in self.map_meds_to_dosages[med_annotations["medication"][0]]:
                    self.map_meds_to_dosages[med_annotations["medication"][0]].append(med_annotations["dosage"]+med_annotations["list"])
            if med_annotations["problem"][0] != "nm":
                self.map_meds_to_reasons[med_annotations["medication"][0]].append(med_annotations["problem"]+med_annotations["list"])
            if med_annotations["problem"][0] != "nm":
                self.map_reasons_to_meds[med_annotations["problem"][0]].append(med_annotations["medication"]+med_annotations["list"])
            if med_annotations["frequency"][0] != "nm":
                self.map_meds_to_frequency[med_annotations["medication"][0]].append(med_annotations["frequency"]+med_annotations["list"])
            if med_annotations["duration"][0] != "nm":
                self.map_meds_to_durations[med_annotations["medication"][0]].append(med_annotations["duration"]+med_annotations["list"])

    def MakeMedicationQL(self, rwords, question_list, logical_form_template, dup_rwords):

        intial_template = logical_form_template
        paraphrase_questions = []
        tuple_orginal = []

        if rwords == ["time"]:
            time = str(random.randint(2, 5)) + random.choice([" years", " weeks"])
            for question in question_list:
                original = question
                question = question.replace("|time|", time)
            logical_form_template = logical_form_template.replace("|time|", time)
            rwords = []
            dup_rwords = []
            paraphrase_questions.append(question)
            tuple_orginal.append((question, original))
        else:

            ############################ make questions ############################################

            for question in question_list:
                orginal = question
                idx = 0
                done = []
                for types in list(dup_rwords):
                    # temp = qwords
                    index = question.find("|" + types + "|")
                    if index == -1 and types not in done:
                        print(question, "|" + types + "|", done)
                    question = question.replace("|" + types + "|", rwords[idx])
                    done.append(types)
                    idx += 1
                tuple_orginal.append((question, orginal))
                paraphrase_questions.append(question)

                ###################################### Make Logical Form #################################

                ## tab ##
            idx = 0
            done = []
            for types in list(dup_rwords):
                logical_form_template.replace("|treatment|", "|medication")
                index = logical_form_template.find("|" + types + "|")
                if index == -1 and types not in done:
                    print(logical_form_template, "|" + types + "|", done, types)
                done.append(types)

                logical_form_template = logical_form_template.replace("|" + types + "|", rwords[idx])
                idx += 1

        logical_form = logical_form_template

        ### Writing question-logical form ##

        for (question, orginal) in tuple_orginal:
            self.filewriter_forlform.writerow([question] + [logical_form.strip()] + [orginal.strip()] + [intial_template])

        return [paraphrase_questions, tuple_orginal, logical_form]

    def MakeAnswer(self, quest_list_nar, answertype, med_annotations, question_list,line_num,line_token):

        result_num = []
        result_token = []
        answer_line = []
        list_nar = quest_list_nar
        answer = []

        idx = 0
        if answertype[idx] == "yes":

            ### the question line is evidence for yes or no questions ##
            #answer = ["yes"]*len(question_list)
            answer = [""] * len(question_list)
            answer_line.extend(question_list)
            result_num.extend(line_num)
            #result_token.extend(line_token)
            result_token = [""] * len(question_list)
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
                #dos = ",".join([x[0] for x in self.map_meds_to_dosages[med[0]]])
                #answer += ["( " + med[0] + ", " + dos + ")"]

                answer.append([med[0]])
                answer_line.append([med[1]])
                result_num.append([int(med[2])])
                result_token.append([int(med[3])])
                list_nar.append([med[3]])


                for x in self.map_meds_to_dosages[med[0]]:
                    #if x[1] not in answer_line[-1]:
                    answer[-1].extend([x[0]])
                    answer_line[-1].extend([x[1]])
                    result_num[-1].extend([int(x[2])])
                    result_token[-1].extend([int(x[3])])
                    list_nar[-1].extend([x[4]])

                #print("new medicine")
                #print(answer[-1])
                #print(result_num[-1])
                #print(result_token[-1])
                #print(answer_line[-1])
                #result_num[-1].extend([int(x[2]) for x in self.map_meds_to_dosages[med[0]] if int(x[2]) not in result_num[-1]])
                #result_token[-1].extend([int(x[3]) for x in self.map_meds_to_dosages[med[0]]])
                #list_nar.extend([x[3] for x in self.map_meds_to_dosages[med[0]]])

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

    ######################## Supporting Utility Functions ######################################

    def CheckForErrors(self, question_list, logical_form_template):

        ## gather all the placeholders in the templates ##

        dup_rwords_list = []
        unique_templates = []
        qwords_list = []

        ## check if all the questions  paraphrases  have the same placeholders ##

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

        ## Check if the placeholders in logical forms are same as the placeholders in question ##

        lwords = logical_form_template.split("|")
        dup_lrwords = lwords[1:len(lwords):2]
        if set(dup_lrwords) not in dup_rwords_list:
            print("Error Out Of Context Question-Logical Form Pairs:")
            print(question_list, logical_form_template)
            return None

        return dup_rwords_list

if __name__=="__main__":
    GenerateQA()