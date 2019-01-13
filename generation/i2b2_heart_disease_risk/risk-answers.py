from os import listdir
import xmltodict
import csv
import sys
import json
import random
import argparse
import os
reload(sys)
sys.setdefaultencoding("ISO-8859-1")

parser = argparse.ArgumentParser()
parser.add_argument('--i2b2_dir', default='', help='Directory containing i2b2 heart disease risk challange files')
parser.add_argument('--templates_dir', default='', help='Directory containing template files in the given format')
parser.add_argument('--output_dir', default='', help='Directory to store the output')
args = parser.parse_args()

###################################################### SET FILE PATHS ##################################################################

## i2b2 file paths ##

RiskFilePath = [os.path.join(args.i2b2_dir,"training-RiskFactors-Complete-Set1/")]

## template file path ##

template_file_path = args.templates_dir

## output file paths ##

qa_output = os.path.join(args.output_dir,"risk-qa.csv")
ql_output = os.path.join(args.output_dir,"risk-ql.csv")
risk_qa_output_json = os.path.join(args.output_dir,"risk-qa.json")


######################################################## CODE #########################################################################

################################################# STANDARD VALUES FROM THE i2b2 heart disease risk paper paper #####################################################################


test_value = {"A1C":"6.5", "glucose": "126", "Cholestrol":"240", "LDL":"100 mg/dl", "blood pressure": "140/90 mm/hg", "BMI": "30"}
dictionary = {}
dictionary = {"high chol.": ("HYPERLIPIDEMIA","Cholestrol"), "A1C": ("DIABETES","A1C"), "high bp": ("HYPERTENSION","blood pressure"),
              "BMI": ("OBESITY","BMI"), "glucose":("DIABETES","glucose"), "high LDL":("HYPERLIPIDEMIA","LDL")}

disease_test = {}
disease_test["HYPERLIPIDEMIA"] = ["high chol.","high LDL"]
disease_test["Diabetes"] = ["A1C","glucose"]
disease_test["HYPERTENSION"] = ["high bp"]
disease_test["OBESE"] = ["BMI"]
disease_test["CAD"] = []

def num_there(s):
    return any(i.isdigit() for i in s)

test_annotations = []
problem_annotations = []

for key in dictionary:
    test_annotations.append([dictionary[key][1]])
    problem_annotations.append(dictionary[key][0])

class RiskFileAnalysis():

    def __init__(self):
        self.list_medications = []
        self.types = []
        self.ReadFile()
        self.ReadTemplates()
        #self.WriteTimeData()


    ################################ Read the Risk Files #######################################################

    def ReadFile(self):

        file_path = RiskFilePath
        TempFile = "temp_risk.txt"

        self.Patients = {}
        self.RiskAnnotationsPerNote = {}
        for paths in file_path:
            files = listdir(paths)
            files.sort()

            for file in files:

                [patient_id,record] = file.split("-")
                id = record.split(".")[0]

                self.Patients = {}
                if patient_id not in self.Patients:
                    self.Patients[patient_id] = []

                ofile = open(TempFile, "w", 0)
                remote_file = open(paths + file)
                for line in remote_file:
                    try:
                        ofile.write(line)
                    except:
                        print("error writing file")
                ofile.close()
                with open(TempFile) as fd:
                    self.doc = xmltodict.parse(fd.read())

                self.ReadDiabetes(patient_id)
                self.ReadCAD(patient_id)
                self.ReadHyperlipedimia(patient_id)
                self.ReadHYPERTENSION(patient_id)
                self.ReadObesity(patient_id)


                if patient_id not in self.RiskAnnotationsPerNote:
                    self.RiskAnnotationsPerNote[patient_id] = [[],[],[]] ## clinical note, record date, annotations_note

                out = {}
                for tuple in self.Patients[patient_id]:
                    out[tuple[2].keys()[0]] = tuple[2][tuple[2].keys()[0]]

                self.RiskAnnotationsPerNote[patient_id][2].append(out)
                self.RiskAnnotationsPerNote[patient_id][0].append(tuple[0])
                self.RiskAnnotationsPerNote[patient_id][1].append(tuple[1])

    def ReadHYPERTENSION(self, patient_id):

        disease = "HYPERTENSION"
        Medications = ['beta blocker', 'calcium channel blocker', 'thiazolidinedione', 'ARB']
        ## Read Note
        Clinical_Notes = self.doc['root']["TEXT"]
        sentences = Clinical_Notes.split("\n")  ##chnaged from full stop to new linw

        CharPos = 0
        indices = []

        for line in sentences:
            indices.append((CharPos, CharPos + len(line), line))
            CharPos = CharPos + 1 + len(line)  ### +1 to account for the "\n"

        start = ""
        end =  ""
        try:
            Record_Date = ("","","")
            for idx in range(len(self.doc['root']["TAGS"]["PHI"])):
                TYPE = self.doc['root']["TAGS"]["PHI"][idx]["@TYPE"]
                if TYPE == "DATE":
                     ## ist is the date
                    start = self.doc['root']["TAGS"]["PHI"][idx]["@start"]
                    end = self.doc['root']["TAGS"]["PHI"][idx]["@end"]
                    text = self.doc['root']["TAGS"]["PHI"][idx]["@text"]
                    break
                else:
                    continue
        except:
            print(self.doc['root']["TAGS"]["PHI"])
            text = self.doc['root']["TAGS"]["PHI"]["@text"]
            start = self.doc['root']["TAGS"]["PHI"]["@start"]
            end = self.doc['root']["TAGS"]["PHI"]["@end"]

        if start != "" :
            start = int(start)
            end = int(end)

            flag_start = 0
            for tup_id in range(len(indices)):
                if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0 and end <= \
                        indices[tup_id][1]:
                    #start_evidence = tup_id
                    start_evidence = indices[tup_id][0]
                    flag_start = 1
                    inline_text = indices[tup_id][2]
                    break

                if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0:
                    start_evidence = indices[tup_id][0]
                    flag_start = 1
                    inline_text = indices[tup_id][2]
                    continue

                if end <= indices[tup_id][1] and flag_start == 1:
                    end_evidence = indices[tup_id][1]
                    inline_text += "\n" + indices[tup_id][2]
                    break

                if flag_start == 1:
                    inline_text += "\n" + indices[tup_id][2]
                    #print(inline_text)

            start_inline_text = start_evidence
            Record_Date = (text, inline_text, start_inline_text, start)
            #print(Record_Date)

        ### Create Events ##
        Dictionary = {}
        Dictionary[disease] = {}
        Dictionary[disease]["mention"] = {}
        Dictionary[disease]["high bp"] = {}

        # print(sentences)
        # print(Record_Date)

        try:
            NumIndoc = len(self.doc['root']["TAGS"][disease])
        except:
            # print(Record_Date)
            # self.Patients[patient_id].append((Clinical_Notes, Record_Date, Dictionary))
            self.ReadMedication(patient_id, indices, Clinical_Notes, Record_Date, Dictionary, Medications, disease)
            return

        for docid in range(NumIndoc):
            try:
                count = len(self.doc['root']["TAGS"][disease][docid][disease])
                b = 0
            except:
                try:
                    count = len(self.doc['root']["TAGS"][disease][disease])
                    b = 1
                except:
                    count = len(self.doc['root']["TAGS"][disease])
                    b = 3

            for idx in range(count):
                if b == 0:
                    indicator = self.doc['root']["TAGS"][disease][docid][disease][idx]["@indicator"]
                    text = self.doc['root']["TAGS"][disease][docid][disease][idx]["@text"]
                    time = self.doc['root']["TAGS"][disease][docid][disease][idx]["@time"]
                    start = self.doc['root']["TAGS"][disease][docid][disease][idx]["@start"]
                    end = self.doc['root']["TAGS"][disease][docid][disease][idx]["@end"]
                    id = self.doc['root']["TAGS"][disease][docid][disease][idx]["@id"]

                elif b == 1:
                    indicator = self.doc['root']["TAGS"][disease][disease][idx]["@indicator"]
                    text = self.doc['root']["TAGS"][disease][disease][idx]["@text"]
                    time = self.doc['root']["TAGS"][disease][disease][idx]["@time"]
                    start = self.doc['root']["TAGS"][disease][disease][idx]["@start"]
                    end = self.doc['root']["TAGS"][disease][disease][idx]["@end"]
                    id = self.doc['root']["TAGS"][disease][disease][idx]["@id"]

                else:
                    indicator = self.doc['root']["TAGS"][disease][idx]["@indicator"]
                    try:
                        text = self.doc['root']["TAGS"][disease][idx]["@text"]
                        # print(self.doc['root']["TAGS"][disease][idx])
                        time = self.doc['root']["TAGS"][disease][docid][disease][idx]["@time"]
                        start = self.doc['root']["TAGS"][disease][docid][disease][idx]["@start"]
                        end = self.doc['root']["TAGS"][disease][docid][disease][idx]["@end"]
                        id = self.doc['root']["TAGS"][disease][docid][disease][idx]["@id"]
                    except:
                        print("failed")
                        # self.Patients[patient_id].append((Clinical_Notes, Record_Date, Dictionary))

                        continue

                if indicator == "mention":
                    # rint("mention",text,time)

                    # start = int(start) - 3
                    # end = int(end) - 3
                    start = int(start)
                    end = int(end)

                    flag_start = 0
                    for tup_id in range(len(indices)):
                        if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0 and end <= \
                                indices[tup_id][1]:
                            start_evidence = indices[tup_id][0]
                            flag_start = 1
                            inline_text = indices[tup_id][2]
                            break

                        if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0:
                            start_evidence = indices[tup_id][0]
                            flag_start = 1
                            inline_text = indices[tup_id][2]
                            continue

                        if end <= indices[tup_id][1] and flag_start == 1:
                            end_evidence = indices[tup_id][1]
                            inline_text += "\n" + indices[tup_id][2]
                            break

                        if flag_start == 1:
                            inline_text += "\n" + indices[tup_id][2]

                    start_inline_text = start_evidence
                    if (text, inline_text, start_inline_text, start) not in Dictionary[disease]["mention"]:
                        Dictionary[disease]["mention"][(text, inline_text, start_inline_text, start)] = []

                    if time not in Dictionary[disease]["mention"][(text, inline_text, start_inline_text, start)]:
                        Dictionary[disease]["mention"][(text, inline_text, start_inline_text, start)].append(time)

                elif indicator == "high bp":
                    # print("A1C",text,time)

                    start = int(start)
                    end = int(end)

                    flag_start = 0
                    for tup_id in range(len(indices)):
                        if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0 and end <= \
                                indices[tup_id][1]:
                            start_evidence = indices[tup_id][0]
                            flag_start = 1
                            inline_text = indices[tup_id][2]
                            break

                        if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0:
                            start_evidence = indices[tup_id][0]
                            flag_start = 1
                            inline_text = indices[tup_id][2]
                            continue

                        if end <= indices[tup_id][1] and flag_start == 1:
                            end_evidence = indices[tup_id][1]
                            inline_text += "\n" + indices[tup_id][2]
                            break

                        if flag_start == 1:
                            inline_text += "\n" + indices[tup_id][2]

                    start_inline_text = start_evidence

                    if (text, inline_text, start_inline_text, start) not in Dictionary[disease]["high bp"]:
                        Dictionary[disease]["high bp"][(text, inline_text, start_inline_text, start)] = []
                    if time not in Dictionary[disease]["high bp"][(text, inline_text, start_inline_text, start)]:
                        Dictionary[disease]["high bp"][(text, inline_text, start_inline_text, start)].append(time)
                else:
                    print(indicator)
                    continue
        self.ReadMedication(patient_id, indices, Clinical_Notes, Record_Date, Dictionary, Medications, disease)
    def ReadCAD(self, patient_id):

        disease = "CAD"
        Medications = [u'ACE inhibitor', u'thienopyridine', u'beta blocker', u'aspirin', u'calcium channel blocker', u'nitrate' ]

        ## Read Note
        Clinical_Notes = self.doc['root']["TEXT"]
        sentences = Clinical_Notes.split("\n")  ##chnaged from full stop to new linw

        CharPos = 0
        indices = []

        for line in sentences:
            indices.append((CharPos, CharPos + len(line), line))
            CharPos = CharPos + 1 + len(line)  ### +1 to account for the "\n"


        start = ""
        end =  ""
        try:
            Record_Date = ("","","")
            for idx in range(len(self.doc['root']["TAGS"]["PHI"])):
                TYPE = self.doc['root']["TAGS"]["PHI"][idx]["@TYPE"]
                if TYPE == "DATE":
                     ## ist is the date
                    start = self.doc['root']["TAGS"]["PHI"][idx]["@start"]
                    end = self.doc['root']["TAGS"]["PHI"][idx]["@end"]
                    text = self.doc['root']["TAGS"]["PHI"][idx]["@text"]
                    break
                else:
                    continue
        except:
            print(self.doc['root']["TAGS"]["PHI"])
            text = self.doc['root']["TAGS"]["PHI"]["@text"]
            start = self.doc['root']["TAGS"]["PHI"]["@start"]
            end = self.doc['root']["TAGS"]["PHI"]["@end"]

        if start != "" :
            start = int(start)
            end = int(end)

            flag_start = 0
            for tup_id in range(len(indices)):
                if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0 and end <= \
                        indices[tup_id][1]:
                    start_evidence = indices[tup_id][0]
                    flag_start = 1
                    inline_text = indices[tup_id][2]
                    break

                if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0:
                    start_evidence = indices[tup_id][0]
                    flag_start = 1
                    inline_text = indices[tup_id][2]
                    continue

                if end <= indices[tup_id][1] and flag_start == 1:
                    end_evidence = indices[tup_id][1]
                    inline_text += "\n" + indices[tup_id][2]
                    break

                if flag_start == 1:
                   inline_text += "\n" + indices[tup_id][2]

            start_inline_text = start_evidence
            Record_Date = (text, inline_text, start_inline_text, start)

        ### Create Events ##
        Dictionary = {}
        Dictionary[disease] = {}
        Dictionary[disease]["symptom"] = {}
        Dictionary[disease]["test"] = {}
        Dictionary[disease]["mention"] = {}
        Dictionary[disease]["event"] = {}

        # print(sentences)
        # print(Record_Date)

        try:
            NumIndoc = len(self.doc['root']["TAGS"][disease])
        except:
            #print(Record_Date)
            #self.Patients[patient_id].append((Clinical_Notes, Record_Date, Dictionary))
            self.ReadMedication(patient_id, indices, Clinical_Notes, Record_Date, Dictionary, Medications, disease)
            return

        for docid in range(NumIndoc):
            try:
                count = len(self.doc['root']["TAGS"][disease][docid][disease])
                b = 0
            except:
                try:
                    count = len(self.doc['root']["TAGS"][disease][disease])
                    b = 1
                except:
                    count = len(self.doc['root']["TAGS"][disease])
                    b = 3

            for idx in range(count):
                if b == 0:
                    indicator = self.doc['root']["TAGS"][disease][docid][disease][idx]["@indicator"]
                    text = self.doc['root']["TAGS"][disease][docid][disease][idx]["@text"]
                    time = self.doc['root']["TAGS"][disease][docid][disease][idx]["@time"]
                    start = self.doc['root']["TAGS"][disease][docid][disease][idx]["@start"]
                    end = self.doc['root']["TAGS"][disease][docid][disease][idx]["@end"]
                    id = self.doc['root']["TAGS"][disease][docid][disease][idx]["@id"]

                elif b == 1:
                    indicator = self.doc['root']["TAGS"][disease][disease][idx]["@indicator"]
                    text = self.doc['root']["TAGS"][disease][disease][idx]["@text"]
                    time = self.doc['root']["TAGS"][disease][disease][idx]["@time"]
                    start = self.doc['root']["TAGS"][disease][disease][idx]["@start"]
                    end = self.doc['root']["TAGS"][disease][disease][idx]["@end"]
                    id = self.doc['root']["TAGS"][disease][disease][idx]["@id"]

                else:
                    indicator = self.doc['root']["TAGS"][disease][idx]["@indicator"]
                    try:
                        text = self.doc['root']["TAGS"][disease][idx]["@text"]
                        # print(self.doc['root']["TAGS"][disease][idx])
                        time = self.doc['root']["TAGS"][disease][docid][disease][idx]["@time"]
                        start = self.doc['root']["TAGS"][disease][docid][disease][idx]["@start"]
                        end = self.doc['root']["TAGS"][disease][docid][disease][idx]["@end"]
                        id = self.doc['root']["TAGS"][disease][docid][disease][idx]["@id"]
                    except:
                        print("failed")
                        # self.Patients[patient_id].append((Clinical_Notes, Record_Date, Dictionary))

                        continue

                if indicator == "mention":
                    # rint("mention",text,time)

                    #start = int(start) - 3
                    #end = int(end) - 3
                    start = int(start)
                    end = int(end)

                    flag_start = 0
                    for tup_id in range(len(indices)):
                        if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0 and end <= \
                                indices[tup_id][1]:
                            start_evidence = indices[tup_id][0]
                            flag_start = 1
                            inline_text = indices[tup_id][2]
                            break

                        if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0:
                            start_evidence = indices[tup_id][0]
                            flag_start = 1
                            inline_text = indices[tup_id][2]
                            continue

                        if end <= indices[tup_id][1] and flag_start == 1:
                            end_evidence = indices[tup_id][1]
                            inline_text += "\n" + indices[tup_id][2]
                            break

                        if flag_start == 1:
                            inline_text += "\n" + indices[tup_id][2]

                    start_inline_text = start_evidence
                    if (text, inline_text, start_inline_text, start) not in Dictionary[disease]["mention"]:
                        Dictionary[disease]["mention"][(text, inline_text, start_inline_text, start)] = []

                    if time not in Dictionary[disease]["mention"][(text, inline_text, start_inline_text, start)]:
                        Dictionary[disease]["mention"][(text, inline_text, start_inline_text, start)].append(time)

                elif indicator == "event":
                    # print("A1C",text,time)

                    start = int(start)
                    end = int(end)

                    flag_start = 0
                    for tup_id in range(len(indices)):
                        if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0 and end <= \
                                indices[tup_id][1]:
                            start_evidence = indices[tup_id][0]
                            flag_start = 1
                            inline_text = indices[tup_id][2]
                            break

                        if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0:
                            start_evidence = indices[tup_id][0]
                            flag_start = 1
                            inline_text = indices[tup_id][2]
                            continue

                        if end <= indices[tup_id][1] and flag_start == 1:
                            end_evidence = indices[tup_id][1]
                            inline_text += "\n" + indices[tup_id][2]
                            break

                        if flag_start == 1:
                            inline_text += "\n" + indices[tup_id][2]

                    start_inline_text = start_evidence

                    if (text, inline_text, start_inline_text, start) not in Dictionary[disease]["event"]:
                        Dictionary[disease]["event"][(text, inline_text, start_inline_text, start)] = []
                    if time not in Dictionary[disease]["event"][(text, inline_text, start_inline_text, start)]:
                        Dictionary[disease]["event"][(text, inline_text, start_inline_text, start)].append(time)

                elif indicator == "test":
                    # print("glucose",text,time)
                    start = int(start)
                    end = int(end)

                    flag_start = 0
                    for tup_id in range(len(indices)):
                        if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0 and end <= \
                                indices[tup_id][1]:
                            start_evidence = indices[tup_id][0]
                            flag_start = 1
                            inline_text = indices[tup_id][2]
                            break

                        if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0:
                            start_evidence = indices[tup_id][0]
                            flag_start = 1
                            inline_text = indices[tup_id][2]
                            continue

                        if end <= indices[tup_id][1] and flag_start == 1:
                            end_evidence = indices[tup_id][1]
                            inline_text += "\n" + indices[tup_id][2]
                            break

                        if flag_start == 1:
                            inline_text += "\n" + indices[tup_id][2]

                    start_inline_text = start_evidence

                    if (text, inline_text, start_inline_text, start) not in Dictionary[disease]["test"]:
                        Dictionary[disease]["test"][(text, inline_text, start_inline_text, start)] = []

                    if time not in Dictionary[disease]["test"][(text, inline_text, start_inline_text, start)]:
                        Dictionary[disease]["test"][(text, inline_text, start_inline_text, start)].append(time)

                elif indicator == "symptom":
                    # print("glucose",text,time)
                    start = int(start)
                    end = int(end)

                    flag_start = 0
                    for tup_id in range(len(indices)):
                        if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0 and end <= \
                                indices[tup_id][1]:
                            start_evidence = indices[tup_id][0]
                            flag_start = 1
                            inline_text = indices[tup_id][2]
                            break

                        if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0:
                            start_evidence = indices[tup_id][0]
                            flag_start = 1
                            inline_text = indices[tup_id][2]
                            continue

                        if end <= indices[tup_id][1] and flag_start == 1:
                            end_evidence = indices[tup_id][1]
                            inline_text += "\n" + indices[tup_id][2]
                            break

                        if flag_start == 1:
                            inline_text += "\n" + indices[tup_id][2]

                    start_inline_text = start_evidence

                    if (text, inline_text, start_inline_text, start) not in Dictionary[disease]["symptom"]:
                        Dictionary[disease]["symptom"][(text, inline_text, start_inline_text, start)] = []

                    if time not in Dictionary[disease]["symptom"][(text, inline_text, start_inline_text, start)]:
                        Dictionary[disease]["symptom"][(text, inline_text, start_inline_text, start)].append(time)

                else:
                    print(indicator)
                    continue
        self.ReadMedication(patient_id, indices, Clinical_Notes, Record_Date, Dictionary, Medications, disease)
    def ReadDiabetes(self,patient_id):

        Medications = ["metformin", "insulin", "sulfonylureas", "thiazolidinediones", "GLP-1 agonists",
                       "Meglitinides",
                       "DPP4 inhibitors", "Amylin", "anti-diabetes medications"]

        ## Read Note
        Clinical_Notes = self.doc['root']["TEXT"]
        sentences = Clinical_Notes.split("\n")  ##chnaged from full stop to new linw

        CharPos = 0
        indices = []

        for line in sentences:
            indices.append((CharPos, CharPos + len(line), line))
            CharPos = CharPos + 1 + len(line)  ### +1 to account for the "\n"

        start = ""
        end =  ""
        try:
            Record_Date = ("","","")
            for idx in range(len(self.doc['root']["TAGS"]["PHI"])):
                TYPE = self.doc['root']["TAGS"]["PHI"][idx]["@TYPE"]
                if TYPE == "DATE":
                     ## ist is the date
                    start = self.doc['root']["TAGS"]["PHI"][idx]["@start"]
                    end = self.doc['root']["TAGS"]["PHI"][idx]["@end"]
                    text = self.doc['root']["TAGS"]["PHI"][idx]["@text"]
                    break
                else:
                    continue
        except:
            print(self.doc['root']["TAGS"]["PHI"])
            text = self.doc['root']["TAGS"]["PHI"]["@text"]
            start = self.doc['root']["TAGS"]["PHI"]["@start"]
            end = self.doc['root']["TAGS"]["PHI"]["@end"]

        if start != "" :
            start = int(start)
            end = int(end)

            flag_start = 0
            for tup_id in range(len(indices)):
                if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0 and end <= indices[tup_id][1]:
                    start_evidence = indices[tup_id][0]
                    flag_start = 1
                    inline_text = indices[tup_id][2]
                    break

                if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0:
                    start_evidence = indices[tup_id][0]
                    flag_start = 1
                    inline_text = indices[tup_id][2]
                    continue

                if end <= indices[tup_id][1] and flag_start == 1:
                    end_evidence = indices[tup_id][1]
                    inline_text += "\n" + indices[tup_id][2]
                    break

                if flag_start == 1:
                    inline_text += "\n" + indices[tup_id][2]
            start_inline_text = start_evidence
            Record_Date = (text, inline_text, start_inline_text, start)

        ### Create Events ##
        Dictionary = {}
        Dictionary["Diabetes"] = {}
        Dictionary["Diabetes"]["glucose"] = {}
        Dictionary["Diabetes"]["A1C"] = {}
        Dictionary["Diabetes"]["mention"] = {}


        #print(sentences)
        #print(Record_Date)

        try:
            NumIndoc = len(self.doc['root']["TAGS"]["DIABETES"])
        except:
            #print(Record_Date)
            #self.Patients[patient_id].append((Clinical_Notes, Record_Date, Dictionary))


            self.ReadMedication(patient_id, indices, Clinical_Notes, Record_Date, Dictionary, Medications, "Diabetes")
            return

        for docid in range(NumIndoc):
            try:
                count = len(self.doc['root']["TAGS"]["DIABETES"][docid]["DIABETES"])
                b = 0
            except:
                try:
                    count = len(self.doc['root']["TAGS"]["DIABETES"]["DIABETES"])
                    b = 1
                except:
                    count = len(self.doc['root']["TAGS"]["DIABETES"])
                    b = 3

            for idx in range(count):
                if b == 0:
                    indicator = self.doc['root']["TAGS"]["DIABETES"][docid]["DIABETES"][idx]["@indicator"]
                    text = self.doc['root']["TAGS"]["DIABETES"][docid]["DIABETES"][idx]["@text"]
                    time = self.doc['root']["TAGS"]["DIABETES"][docid]["DIABETES"][idx]["@time"]
                    start = self.doc['root']["TAGS"]["DIABETES"][docid]["DIABETES"][idx]["@start"]
                    end = self.doc['root']["TAGS"]["DIABETES"][docid]["DIABETES"][idx]["@end"]
                    id = self.doc['root']["TAGS"]["DIABETES"][docid]["DIABETES"][idx]["@id"]

                elif b == 1:
                    indicator = self.doc['root']["TAGS"]["DIABETES"]["DIABETES"][idx]["@indicator"]
                    text = self.doc['root']["TAGS"]["DIABETES"]["DIABETES"][idx]["@text"]
                    time = self.doc['root']["TAGS"]["DIABETES"]["DIABETES"][idx]["@time"]
                    start = self.doc['root']["TAGS"]["DIABETES"]["DIABETES"][idx]["@start"]
                    end = self.doc['root']["TAGS"]["DIABETES"]["DIABETES"][idx]["@end"]
                    id = self.doc['root']["TAGS"]["DIABETES"]["DIABETES"][idx]["@id"]

                else:
                    indicator = self.doc['root']["TAGS"]["DIABETES"][idx]["@indicator"]
                    try:
                        text = self.doc['root']["TAGS"]["DIABETES"][idx]["@text"]
                        #print(self.doc['root']["TAGS"]["DIABETES"][idx])
                        time = self.doc['root']["TAGS"]["DIABETES"][docid]["DIABETES"][idx]["@time"]
                        start = self.doc['root']["TAGS"]["DIABETES"][docid]["DIABETES"][idx]["@start"]
                        end = self.doc['root']["TAGS"]["DIABETES"][docid]["DIABETES"][idx]["@end"]
                        id = self.doc['root']["TAGS"]["DIABETES"][docid]["DIABETES"][idx]["@id"]
                    except:
                        print("failed")
                        #self.Patients[patient_id].append((Clinical_Notes, Record_Date, Dictionary))

                        continue

                if indicator == "mention":
                    #rint("mention",text,time)

                    # start = int(start) - 3
                    # end = int(end) - 3
                    start = int(start)
                    end = int(end)

                    flag_start = 0
                    for tup_id in range(len(indices)):

                        if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0 and end <=indices[tup_id][1]:
                                start_evidence = indices[tup_id][0]
                                flag_start = 1
                                inline_text = indices[tup_id][2]
                                break

                        if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0:
                                start_evidence = indices[tup_id][0]
                                flag_start = 1
                                inline_text = indices[tup_id][2]
                                continue

                        if end <= indices[tup_id][1] and flag_start == 1:
                            end_evidence = indices[tup_id][1]
                            inline_text += "\n" + indices[tup_id][2]
                            break

                        if flag_start == 1:
                            inline_text += "\n" + indices[tup_id][2]


                    start_inline_text = start_evidence
                    if (text, inline_text, start_inline_text,start) not in Dictionary["Diabetes"]["mention"]:
                        Dictionary["Diabetes"]["mention"][(text, inline_text, start_inline_text,start)] = []

                    if time not in Dictionary["Diabetes"]["mention"][(text, inline_text, start_inline_text,start)]:
                        Dictionary["Diabetes"]["mention"][(text, inline_text, start_inline_text,start)].append(time)

                elif indicator == "A1C":
                    #print("A1C",text,time)

                    start = int(start)
                    end = int(end)

                    flag_start = 0
                    for tup_id in range(len(indices)):

                        if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0 and end <= \
                                indices[tup_id][1]:
                            start_evidence = indices[tup_id][0]
                            flag_start = 1
                            inline_text = indices[tup_id][2]
                            break

                        if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0:
                            start_evidence = indices[tup_id][0]
                            flag_start = 1
                            inline_text = indices[tup_id][2]
                            continue
                        if end <= indices[tup_id][1] and flag_start == 1:
                            end_evidence = indices[tup_id][1]
                            inline_text += "\n" + indices[tup_id][2]
                            break

                        if flag_start == 1:
                            inline_text += "\n" + indices[tup_id][2]

                    start_inline_text = start_evidence

                    if (text, inline_text, start_inline_text,start) not in Dictionary["Diabetes"]["A1C"]:
                        Dictionary["Diabetes"]["A1C"][(text, inline_text, start_inline_text,start)] = []
                    if time not in Dictionary["Diabetes"]["A1C"][(text, inline_text, start_inline_text,start)]:
                        Dictionary["Diabetes"]["A1C"][(text, inline_text, start_inline_text,start)].append(time)

                elif indicator == "glucose":
                    #print("glucose",text,time)
                    start = int(start)
                    end = int(end)

                    flag_start = 0
                    for tup_id in range(len(indices)):
                        if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0 and end <= \
                                indices[tup_id][1]:
                            start_evidence = indices[tup_id][0]
                            flag_start = 1
                            inline_text = indices[tup_id][2]
                            break

                        if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0:
                            start_evidence = indices[tup_id][0]
                            flag_start = 1
                            inline_text = indices[tup_id][2]
                            continue

                        if end <= indices[tup_id][1] and flag_start == 1:
                            end_evidence = indices[tup_id][1]
                            inline_text += "\n" + indices[tup_id][2]
                            break

                        if flag_start == 1:
                            inline_text += "\n" + indices[tup_id][2]

                    start_inline_text = start_evidence

                    if (text, inline_text, start_inline_text,start) not in Dictionary["Diabetes"]["glucose"]:
                        Dictionary["Diabetes"]["glucose"][(text, inline_text, start_inline_text,start)] = []

                    if time not in Dictionary["Diabetes"]["glucose"][(text, inline_text, start_inline_text,start)]:
                        Dictionary["Diabetes"]["glucose"][(text, inline_text, start_inline_text,start)].append(time)

                else:
                    print(indicator)
                    continue


        self.ReadMedication(patient_id,indices,Clinical_Notes,Record_Date,Dictionary, Medications, "Diabetes")
    def ReadHyperlipedimia(self, patient_id):

        disease = "HYPERLIPIDEMIA"
        Medications = [ "statin", "ezetimibe", "niacin", "fibrate"]

        #        ## Read Note
        Clinical_Notes = self.doc['root']["TEXT"]
        sentences = Clinical_Notes.split("\n")  ##chnaged from full stop to new linw

        CharPos = 0
        indices = []

        for line in sentences:
            indices.append((CharPos, CharPos + len(line), line))
            CharPos = CharPos + 1 + len(line)  ### +1 to account for the "\n"


        start = ""
        end =  ""
        try:
            Record_Date = ("","","")
            for idx in range(len(self.doc['root']["TAGS"]["PHI"])):
                TYPE = self.doc['root']["TAGS"]["PHI"][idx]["@TYPE"]
                if TYPE == "DATE":
                     ## ist is the date
                    start = self.doc['root']["TAGS"]["PHI"][idx]["@start"]
                    end = self.doc['root']["TAGS"]["PHI"][idx]["@end"]
                    text = self.doc['root']["TAGS"]["PHI"][idx]["@text"]
                    break
                else:
                    continue
        except:
            print(self.doc['root']["TAGS"]["PHI"])
            text = self.doc['root']["TAGS"]["PHI"]["@text"]
            start = self.doc['root']["TAGS"]["PHI"]["@start"]
            end = self.doc['root']["TAGS"]["PHI"]["@end"]

        if start != "" :
            start = int(start)
            end = int(end)

            flag_start = 0
            for tup_id in range(len(indices)):
                if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0 and end <= \
                        indices[tup_id][1]:
                    start_evidence = indices[tup_id][0]
                    flag_start = 1
                    inline_text = indices[tup_id][2]
                    break

                if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0:
                    start_evidence = indices[tup_id][0]
                    flag_start = 1
                    inline_text = indices[tup_id][2]
                    continue

                if end <= indices[tup_id][1] and flag_start == 1:
                    end_evidence = indices[tup_id][1]
                    inline_text += "\n" + indices[tup_id][2]
                    break

                if flag_start == 1:
                    inline_text += "\n" + indices[tup_id][2]

            start_inline_text = start_evidence
            Record_Date = (text, inline_text, start_inline_text, start)

        ### Create Events ##
        Dictionary = {}
        Dictionary[disease] = {}
        Dictionary[disease]["high chol."] = {}
        Dictionary[disease]["high LDL"] = {}
        Dictionary[disease]["mention"] = {}


        try:
            NumIndoc = len(self.doc['root']["TAGS"][disease])
        except:
            # print(Record_Date)
            # self.Patients[patient_id].append((Clinical_Notes, Record_Date, Dictionary))
            self.ReadMedication(patient_id, indices, Clinical_Notes, Record_Date, Dictionary, Medications, disease)
            return

        for docid in range(NumIndoc):
            try:
                count = len(self.doc['root']["TAGS"][disease][docid][disease])
                b = 0
            except:
                try:
                    count = len(self.doc['root']["TAGS"][disease][disease])
                    b = 1
                except:
                    count = len(self.doc['root']["TAGS"][disease])
                    b = 3

            for idx in range(count):
                if b == 0:
                    indicator = self.doc['root']["TAGS"][disease][docid][disease][idx]["@indicator"]
                    text = self.doc['root']["TAGS"][disease][docid][disease][idx]["@text"]
                    time = self.doc['root']["TAGS"][disease][docid][disease][idx]["@time"]
                    start = self.doc['root']["TAGS"][disease][docid][disease][idx]["@start"]
                    end = self.doc['root']["TAGS"][disease][docid][disease][idx]["@end"]
                    id = self.doc['root']["TAGS"][disease][docid][disease][idx]["@id"]

                elif b == 1:
                    indicator = self.doc['root']["TAGS"][disease][disease][idx]["@indicator"]
                    text = self.doc['root']["TAGS"][disease][disease][idx]["@text"]
                    time = self.doc['root']["TAGS"][disease][disease][idx]["@time"]
                    start = self.doc['root']["TAGS"][disease][disease][idx]["@start"]
                    end = self.doc['root']["TAGS"][disease][disease][idx]["@end"]
                    id = self.doc['root']["TAGS"][disease][disease][idx]["@id"]

                else:
                    indicator = self.doc['root']["TAGS"][disease][idx]["@indicator"]
                    try:
                        text = self.doc['root']["TAGS"][disease][idx]["@text"]
                        # print(self.doc['root']["TAGS"][disease][idx])
                        time = self.doc['root']["TAGS"][disease][docid][disease][idx]["@time"]
                        start = self.doc['root']["TAGS"][disease][docid][disease][idx]["@start"]
                        end = self.doc['root']["TAGS"][disease][docid][disease][idx]["@end"]
                        id = self.doc['root']["TAGS"][disease][docid][disease][idx]["@id"]
                    except:
                        print("failed")
                        # self.Patients[patient_id].append((Clinical_Notes, Record_Date, Dictionary))

                        continue

                if indicator == "mention":
                    # rint("mention",text,time)

                    # start = int(start) - 3
                    # end = int(end) - 3
                    start = int(start)
                    end = int(end)

                    flag_start = 0
                    for tup_id in range(len(indices)):
                        if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0 and end <= \
                                indices[tup_id][1]:
                            start_evidence = indices[tup_id][0]
                            flag_start = 1
                            inline_text = indices[tup_id][2]
                            break

                        if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0:
                            start_evidence = indices[tup_id][0]
                            flag_start = 1
                            inline_text = indices[tup_id][2]
                            continue

                        if end <= indices[tup_id][1] and flag_start == 1:
                            end_evidence = indices[tup_id][1]
                            inline_text += "\n" + indices[tup_id][2]
                            break

                        if flag_start == 1:
                            inline_text += "\n" + indices[tup_id][2]

                    start_inline_text = start_evidence
                    if (text, inline_text, start_inline_text, start) not in Dictionary[disease]["mention"]:
                        Dictionary[disease]["mention"][(text, inline_text, start_inline_text, start)] = []

                    if time not in Dictionary[disease]["mention"][(text, inline_text, start_inline_text, start)]:
                        Dictionary[disease]["mention"][(text, inline_text, start_inline_text, start)].append(time)

                elif indicator == "high chol.":
                    # print("A1C",text,time)

                    start = int(start)
                    end = int(end)

                    flag_start = 0
                    for tup_id in range(len(indices)):
                        if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0 and end <= \
                                indices[tup_id][1]:
                            start_evidence = indices[tup_id][0]
                            flag_start = 1
                            inline_text = indices[tup_id][2]
                            break

                        if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0:
                            start_evidence = indices[tup_id][0]
                            flag_start = 1
                            inline_text = indices[tup_id][2]
                            continue

                        if end <= indices[tup_id][1] and flag_start == 1:
                            end_evidence = indices[tup_id][1]
                            inline_text += "\n" + indices[tup_id][2]
                            break

                        if flag_start == 1:
                            inline_text += "\n" + indices[tup_id][2]

                    start_inline_text = start_evidence

                    if (text, inline_text, start_inline_text, start) not in Dictionary[disease]["high chol."]:
                        Dictionary[disease]["high chol."][(text, inline_text, start_inline_text, start)] = []
                    if time not in Dictionary[disease]["high chol."][(text, inline_text, start_inline_text, start)]:
                        Dictionary[disease]["high chol."][(text, inline_text, start_inline_text, start)].append(time)

                elif indicator == "high LDL":
                    # print("glucose",text,time)
                    start = int(start)
                    end = int(end)

                    flag_start = 0
                    for tup_id in range(len(indices)):
                        if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0 and end <= \
                                indices[tup_id][1]:
                            start_evidence = indices[tup_id][0]
                            flag_start = 1
                            inline_text = indices[tup_id][2]
                            break

                        if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0:
                            start_evidence = indices[tup_id][0]
                            flag_start = 1
                            inline_text = indices[tup_id][2]
                            continue

                        if end <= indices[tup_id][1] and flag_start == 1:
                            end_evidence = indices[tup_id][1]
                            inline_text += "\n" + indices[tup_id][2]
                            break

                        if flag_start == 1:
                            inline_text += "\n" + indices[tup_id][2]

                    start_inline_text = start_evidence

                    if (text, inline_text, start_inline_text, start) not in Dictionary[disease]["high LDL"]:
                        Dictionary[disease]["high LDL"][(text, inline_text, start_inline_text, start)] = []

                    if time not in Dictionary[disease]["high LDL"][(text, inline_text, start_inline_text, start)]:
                        Dictionary[disease]["high LDL"][(text, inline_text, start_inline_text, start)].append(time)
                else:
                    print(indicator)
                    continue
        self.ReadMedication(patient_id, indices, Clinical_Notes, Record_Date, Dictionary, Medications, disease)
    def ReadObesity(self,patient_id):
        disease = "OBESE"
        Medications = []
        ## Read Note
        Clinical_Notes = self.doc['root']["TEXT"]
        sentences = Clinical_Notes.split("\n")  ##chnaged from full stop to new linw

        CharPos = 0
        indices = []

        for line in sentences:
            indices.append((CharPos, CharPos + len(line), line))
            CharPos = CharPos + 1 + len(line)  ### +1 to account for the "\n"
        start = ""
        end =  ""
        try:
            Record_Date = ("","","")
            for idx in range(len(self.doc['root']["TAGS"]["PHI"])):
                TYPE = self.doc['root']["TAGS"]["PHI"][idx]["@TYPE"]
                if TYPE == "DATE":
                     ## ist is the date
                    start = self.doc['root']["TAGS"]["PHI"][idx]["@start"]
                    end = self.doc['root']["TAGS"]["PHI"][idx]["@end"]
                    text = self.doc['root']["TAGS"]["PHI"][idx]["@text"]
                    break
                else:
                    continue
        except:
            print(self.doc['root']["TAGS"]["PHI"])
            text = self.doc['root']["TAGS"]["PHI"]["@text"]
            start = self.doc['root']["TAGS"]["PHI"]["@start"]
            end = self.doc['root']["TAGS"]["PHI"]["@end"]

        if start != "" :
            start = int(start)
            end = int(end)

            flag_start = 0
            for tup_id in range(len(indices)):
                if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0 and end <= indices[tup_id][1]:
                    start_evidence = indices[tup_id][0]
                    flag_start = 1
                    inline_text = indices[tup_id][2]
                    break

                if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0:
                    start_evidence = indices[tup_id][0]
                    flag_start = 1
                    inline_text = indices[tup_id][2]
                    continue

                if end <= indices[tup_id][1] and flag_start == 1:
                    end_evidence = indices[tup_id][1]
                    inline_text += "\n" + indices[tup_id][2]
                    break

                if flag_start == 1:
                    inline_text += "\n" + indices[tup_id][2]

            start_inline_text = start_evidence
            Record_Date = (text, inline_text, start_inline_text, start)
        ### Create Events ##
        Dictionary = {}
        Dictionary[disease] = {}
        Dictionary[disease]["BMI"] = {}
        Dictionary[disease]["mention"] = {}


        try:
            NumIndoc = len(self.doc['root']["TAGS"][disease])
        except:
            # print(Record_Date)
            # self.Patients[patient_id].append((Clinical_Notes, Record_Date, Dictionary))
            self.ReadMedication(patient_id, indices, Clinical_Notes, Record_Date, Dictionary, Medications, disease)
            return

        for docid in range(NumIndoc):
            try:
                count = len(self.doc['root']["TAGS"][disease][docid][disease])
                b = 0
            except:
                try:
                    count = len(self.doc['root']["TAGS"][disease][disease])
                    b = 1
                except:
                    count = len(self.doc['root']["TAGS"][disease])
                    b = 3

            for idx in range(count):
                if b == 0:
                    indicator = self.doc['root']["TAGS"][disease][docid][disease][idx]["@indicator"]
                    text = self.doc['root']["TAGS"][disease][docid][disease][idx]["@text"]
                    time = self.doc['root']["TAGS"][disease][docid][disease][idx]["@time"]
                    start = self.doc['root']["TAGS"][disease][docid][disease][idx]["@start"]
                    end = self.doc['root']["TAGS"][disease][docid][disease][idx]["@end"]
                    id = self.doc['root']["TAGS"][disease][docid][disease][idx]["@id"]

                elif b == 1:
                    indicator = self.doc['root']["TAGS"][disease][disease][idx]["@indicator"]
                    text = self.doc['root']["TAGS"][disease][disease][idx]["@text"]
                    time = self.doc['root']["TAGS"][disease][disease][idx]["@time"]
                    start = self.doc['root']["TAGS"][disease][disease][idx]["@start"]
                    end = self.doc['root']["TAGS"][disease][disease][idx]["@end"]
                    id = self.doc['root']["TAGS"][disease][disease][idx]["@id"]

                else:
                    indicator = self.doc['root']["TAGS"][disease][idx]["@indicator"]
                    try:
                        text = self.doc['root']["TAGS"][disease][idx]["@text"]
                        # print(self.doc['root']["TAGS"][disease][idx])
                        time = self.doc['root']["TAGS"][disease][docid][disease][idx]["@time"]
                        start = self.doc['root']["TAGS"][disease][docid][disease][idx]["@start"]
                        end = self.doc['root']["TAGS"][disease][docid][disease][idx]["@end"]
                        id = self.doc['root']["TAGS"][disease][docid][disease][idx]["@id"]
                    except:
                        print("failed")
                        # self.Patients[patient_id].append((Clinical_Notes, Record_Date, Dictionary))

                        continue

                if indicator == "mention":
                    # rint("mention",text,time)

                    # start = int(start) - 3
                    # end = int(end) - 3
                    start = int(start)
                    end = int(end)

                    flag_start = 0
                    for tup_id in range(len(indices)):
                        if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0 and end <= \
                                indices[tup_id][1]:
                            start_evidence = indices[tup_id][0]
                            flag_start = 1
                            inline_text = indices[tup_id][2]
                            break

                        if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0:
                            start_evidence = indices[tup_id][0]
                            flag_start = 1
                            inline_text = indices[tup_id][2]
                            continue

                        if end <= indices[tup_id][1] and flag_start == 1:
                            end_evidence = indices[tup_id][1]
                            inline_text += "\n" + indices[tup_id][2]
                            break

                        if flag_start == 1:
                            inline_text += "\n" + indices[tup_id][2]

                    start_inline_text = start_evidence
                    if (text, inline_text, start_inline_text, start) not in Dictionary[disease]["mention"]:
                        Dictionary[disease]["mention"][(text, inline_text, start_inline_text, start)] = []

                    if time not in Dictionary[disease]["mention"][(text, inline_text, start_inline_text, start)]:
                        Dictionary[disease]["mention"][(text, inline_text, start_inline_text, start)].append(time)

                elif indicator == "BMI":
                    # print("A1C",text,time)

                    start = int(start)
                    end = int(end)

                    flag_start = 0
                    for tup_id in range(len(indices)):
                        if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0 and end <= \
                                indices[tup_id][1]:
                            start_evidence = indices[tup_id][0]
                            flag_start = 1
                            inline_text = indices[tup_id][2]
                            break

                        if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0:
                            start_evidence = indices[tup_id][0]
                            flag_start = 1
                            inline_text = indices[tup_id][2]
                            continue

                        if end <= indices[tup_id][1] and flag_start == 1:
                            end_evidence = indices[tup_id][1]
                            inline_text += "\n" + indices[tup_id][2]
                            break

                        if flag_start == 1:
                            inline_text += "\n" + indices[tup_id][2]

                    start_inline_text = start_evidence

                    if (text, inline_text, start_inline_text, start) not in Dictionary[disease]["BMI"]:
                        Dictionary[disease]["BMI"][(text, inline_text, start_inline_text, start)] = []
                    if time not in Dictionary[disease]["BMI"][(text, inline_text, start_inline_text, start)]:
                        Dictionary[disease]["BMI"][(text, inline_text, start_inline_text, start)].append(time)
                else:
                    print(indicator)
                    continue
        self.ReadMedication(patient_id, indices, Clinical_Notes, Record_Date, Dictionary, Medications, disease)
    def ReadMedication(self,patient_id,indices,Clinical_Notes,Record_Date,Dictionary,Medications,disease):


        for med in Medications:
            Dictionary[disease][med] = {}

        try:
            NumIndoc = len(self.doc['root']["TAGS"]["MEDICATION"])
        except:
            self.Patients[patient_id].append((Clinical_Notes, Record_Date, Dictionary))
            return

        for docid in range(NumIndoc):
            try:
                count = len(self.doc['root']["TAGS"]["MEDICATION"][docid]["MEDICATION"])
                b = 0
            except:
                try:
                    count = len(self.doc['root']["TAGS"]["MEDICATION"]["MEDICATION"])
                    b = 1
                except:
                    count = len(self.doc['root']["TAGS"]["MEDICATION"])
                    b = 3

            for idx in range(count):
                if b == 0:
                    indicator = self.doc['root']["TAGS"]["MEDICATION"][docid]["MEDICATION"][idx]["@type1"]
                    indicator2 = self.doc['root']["TAGS"]["MEDICATION"][docid]["MEDICATION"][idx]["@type2"]
                    text = self.doc['root']["TAGS"]["MEDICATION"][docid]["MEDICATION"][idx]["@text"]
                    time = self.doc['root']["TAGS"]["MEDICATION"][docid]["MEDICATION"][idx]["@time"]
                    start = self.doc['root']["TAGS"]["MEDICATION"][docid]["MEDICATION"][idx]["@start"]
                    end = self.doc['root']["TAGS"]["MEDICATION"][docid]["MEDICATION"][idx]["@end"]
                elif b == 1:
                    indicator = self.doc['root']["TAGS"]["MEDICATION"]["MEDICATION"][idx]["@type1"]
                    indicator2 = self.doc['root']["TAGS"]["MEDICATION"]["MEDICATION"][idx]["@type2"]
                    text = self.doc['root']["TAGS"]["MEDICATION"]["MEDICATION"][idx]["@text"]
                    time = self.doc['root']["TAGS"]["MEDICATION"]["MEDICATION"][idx]["@time"]
                    start = self.doc['root']["TAGS"]["MEDICATION"]["MEDICATION"][idx]["@start"]
                    end = self.doc['root']["TAGS"]["MEDICATION"]["MEDICATION"][idx]["@end"]
                else:
                    indicator = self.doc['root']["TAGS"]["MEDICATION"][idx]["@type1"]
                    indicator2 = self.doc['root']["TAGS"]["MEDICATION"][idx]["@type2"]
                    try:
                        text = self.doc['root']["TAGS"]["MEDICATION"][idx]["@text"]
                        time = self.doc['root']["TAGS"]["MEDICATION"][idx]["@time"]
                        start = self.doc['root']["TAGS"]["MEDICATION"][idx]["@start"]
                        end = self.doc['root']["TAGS"]["MEDICATION"][idx]["@end"]
                    except:
                        continue
                #print(indicator,indicator2)
                if indicator not in self.types:
                    self.types.append(indicator)
                if indicator2 not in self.types:
                    self.types.append(indicator2)

                start = int(start)
                end = int(end)
                flag_start = 0
                for tup_id in range(len(indices)):
                    if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0 and end <= indices[tup_id][1]:
                        start_evidence = indices[tup_id][0]
                        flag_start = 1
                        inline_text = indices[tup_id][2]
                        break

                    if start >= indices[tup_id][0] and start <= indices[tup_id][1] and flag_start == 0:
                        start_evidence = indices[tup_id][0]
                        flag_start = 1
                        inline_text = indices[tup_id][2]
                        continue

                    if end <= indices[tup_id][1] and flag_start == 1:
                        end_evidence = indices[tup_id][1]
                        inline_text += "\n" + indices[tup_id][2]
                        break

                    if flag_start == 1:
                        inline_text += "\n" + indices[tup_id][2]

                start_inline_text = start_evidence


                if len(text.split(" ")) <= 1 and num_there(text) == False: ## Some are noisy remove them
                    if text not in self.list_medications:
                        self.list_medications.append(text)

                if indicator in Medications:
                    if (text, inline_text, start_inline_text,start) not in Dictionary[disease][indicator]:
                        Dictionary[disease][indicator][(text, inline_text, start_inline_text,start)] = []

                    if time not in Dictionary[disease][indicator][(text, inline_text, start_inline_text,start)]:
                        Dictionary[disease][indicator][(text, inline_text, start_inline_text,start)].append(time)

                if indicator2 in Medications:
                    if (text, inline_text, start_inline_text,start) not in Dictionary[disease][indicator2]:
                        Dictionary[disease][indicator2][(text, inline_text, start_inline_text,start)] = []

                    if time not in Dictionary[disease][indicator2][(text, inline_text, start_inline_text,start)]:
                        Dictionary[disease][indicator2][(text, inline_text, start_inline_text,start)].append(time)

        self.Patients[patient_id].append((Clinical_Notes, Record_Date, Dictionary))

    ############################## Main Functions ###########################################################

    def ReadTemplates(self):
        self.logical_out = []

        ### File to write Question-Answers ##

        ofile = open(qa_output, "w")
        self.filewriter = csv.writer(ofile, delimiter="\t")
        self.filewriter.writerow(
            ["Question", "Logical Form", "Answer", "Answer line in note", "Note ID"])

        ### File to write Question-Logical Forms ##

        ofile = open(ql_output, "w")
        self.filewriter_forlform = csv.writer(ofile, delimiter="\t")
        self.filewriter_forlform.writerow(["Question", "Logical Form"])

        self.relations_out = {"paragraphs": [], "title": "risk-dataset"}

        ### File to read templates ###

        file = open(template_file_path)
        filereader = list(csv.reader(file))

        ## read only templates relevant to heart disease risk challenge ##

        risk_lines = []
        for line in filereader[1:]:
            if line[0] != "risk":
                continue
            risk_lines.append(line)

        total_questions = 0

        for Noteid in self.RiskAnnotationsPerNote:
            [PatientNotes, RecordDates, Disease_note] = self.RiskAnnotationsPerNote[Noteid]
            # PatientNote = "\n".join(PatientNotes)
            PatientNote = ""
            print(len(PatientNotes))
            for note in PatientNotes:
                PatientNote += note + "\n"
            offset_notes = [0]
            for note in PatientNotes[0:-1]:
                new_offset = len(note)+1+offset_notes[-1]
                offset_notes.append(new_offset)
            #print(offset_notes)

            out_patient = {"note_id": Noteid, "context": PatientNote.split("\n"), "qas": []}
            self.unique_questions = []

            for line in risk_lines:
                question = line[2].strip()
                answertype = line[4]
                # answertype = [type.strip() for type in answertype]
                logical_form = line[3].strip()
                question = question.replace("\t", "")
                logical_form = logical_form.replace("\t", "")
                question = question.replace("|medication| or |medication|", "|medication|")  ## added ##
                question = question.replace("|problem| or |problem|", "|problem|")  ## added ##
                question = question.replace("|test| or |test|", "|test|")  ## added ##
                question = question.replace("|test| |test| |test|", "|test|")  ## added ##

                if question.strip() == "":
                    continue

                types_to_replace = self.checking_for_errors(question, logical_form)

                if len(types_to_replace) != 0:
                    types_to_replace = list(types_to_replace[0])
                else:
                    types_to_replace = []

                answer_out = self.MakeRiskQLA(PatientNote, question, answertype, logical_form, Disease_note, RecordDates, Noteid, types_to_replace, offset_notes)

                if len(answer_out) != 0:
                    out_patient["qas"].extend(answer_out)

            total_questions += len(self.unique_questions)
            self.relations_out["paragraphs"].append(out_patient)

        with open(risk_qa_output_json, 'w') as outfile:
            json.dump(self.relations_out, outfile, ensure_ascii=False)

    def MakeRiskQLA(self, PatientNote, question, answertype, logical_form, Disease_time_progression, Record_dates, Noteid, types_to_replace, offset_notes):
        answer_out = []
        question_list = question.strip().split("##")
        logical_form_orginal = logical_form

        QLA = self.MakeAnswers(answertype, types_to_replace, question_list, logical_form, Disease_time_progression, Record_dates, Noteid, offset_notes)

        if len(QLA) == 0:
            return []

        for values in QLA:  # question,orginal

            if len(values[2]) == 0:

                paraphrase_questions = values[0]
                unique_tup = list(set(paraphrase_questions))
                #unique_tup = list(set(zip(paraphrase_questions, question_list)))
                for qidx in range(len(unique_tup)):
                    self.filewriter_forlform.writerow([unique_tup[qidx][0]] + [values[1]] + [unique_tup[qidx][1]] + [logical_form_orginal])
            else:

                '''
                answer_text = []
                line_in_note = []
                start_line = []
                for answer in values[2]:
                    (text, inline_text, start_inline_text, start) = answer
                    
                    if inline_text not in line_in_note:
                        answer_text.append(text)
                        line_in_note.append(inline_text)
                        start_line.append(start_inline_text)

                
                Note_val = "#".join(line_in_note)
                self.filewriter.writerow(
                    ["##".join(list(zip(*values[0])[0]))] + [values[1]] + [",".join(answer_text)] + [Note_val] + [
                        Noteid + "_RiskChallenge"])
                '''

                paraphrase_questions = values[0]
                unique_tup = list(set(paraphrase_questions))
                #unique_tup = list(set(zip(paraphrase_questions, question_list)))
                #print("unique_tup",unique_tup)
                for qidx in range(len(unique_tup)):
                    #self.filewriter_forlform.writerow([unique_tup[qidx][0]] + [logical_form] + [unique_tup[qidx][1]] + [logical_form_orginal])
                    #print(unique_tup[qidx][0])
                    self.filewriter_forlform.writerow([unique_tup[qidx][0]] + [values[1]] + [unique_tup[qidx][1]] + [logical_form_orginal])

                if set(list(zip(*values[0])[0])) not in self.unique_questions:

                    self.unique_questions.append(set(list(zip(*values[0])[0])))
                    ans_list = []
                    answers = values[2]

                    for idx in range(len(answers)):
                        (text, inline_text, start_inline_text, start) = answers[idx]
                        entity_type = "single"
                        val = {"answer_start": [start_inline_text, start], "text": text, "evidence": inline_text, "evidence_start": start_inline_text, "answer_entity_type": entity_type}
                        #print("idx \n")\


                        if val not in ans_list:
                            #if val["evidence"] != PatientNote[int(val["evidence_start"]):int(val["evidence_start"]) + len(val["evidence"])]:
                            #    print(val["evidence"])
                            #    print("line in note",PatientNote[int(val["evidence_start"]):int(val["evidence_start"]) + len(val["evidence"])])
                            ans_list.append(val)  # evidence will have q_line_answer_line

                    answer_temp = {"answers": ans_list, "id": [values[0], logical_form_orginal],"question": list(list(zip(*values[0])[0]))}
                    answer_out.append(answer_temp)

        return answer_out

    ######################## Main Utility Functions ########################################################

    def MakeAnswers(self,answertype,types_to_replace,question_list,logical_form, Disease_time_progression, Record_dates,Noteid,offset_notes):
        QLA = []
        non_uniq = []
        logical_form_orginal = logical_form
        if answertype == "none":
            annotations = self.InputMapping(types_to_replace,question_list,logical_form )

            ################# Generate only Question Logical Forms ##################################
            for value in annotations:
                #print(value)
                logical_form_template = logical_form
                new_question_list = []
                paraphrase_questions = []
                for question in question_list:
                    done = []
                    idx = 0
                    for types in list(types_to_replace):
                        # temp = qwords
                        index = question.find("|" + types + "|")
                        if index == -1 and types not in done:
                            if types == "medication":
                                question = question.replace("|treatment|","|medication|")
                                index = question.find("|" + "medication" + "|")
                                if index == -1 and types not in done:
                                    print(question, "|" + types + "|", done)

                            else:
                                print(question, "|" + types + "|", done)
                        question = question.replace("|" + types + "|", value[idx])
                        done.append(types)
                        idx += 1
                    paraphrase_questions.append(question)
                    #print(question)
                    if question not in new_question_list:
                        new_question_list.append(question)


                idx = 0
                done = []
                for types in list(types_to_replace):
                    index = logical_form_template.find("|" + types + "|")
                    if index == -1 and types not in done:
                        print(logical_form_template, "|" + types + "|", done, types)
                    done.append(types)
                    logical_form_template = logical_form_template.replace("|" + types + "|", value[idx])
                    idx += 1
                #print(logical_form_template)
                unique_tup = list(set(zip(paraphrase_questions, question_list)))

                for qidx in range(len(unique_tup)):
                    #print(paraphrase_questions[0],logical_form_template)
                    self.filewriter_forlform.writerow([unique_tup[qidx][0]] + [logical_form_template] + [unique_tup[qidx][1]] + [logical_form_orginal])
            return QLA

        elif answertype == "result_date":
            for (on_date_disease,record_date,note_offset) in zip(Disease_time_progression,Record_dates,offset_notes):
                for Diseases in on_date_disease: ## Diseases has a list of Diseases keys
                     inidcators = on_date_disease[Diseases] ## Get all corresponding indicators for that problem
                     #print(inidcators)
                     test_mentions = disease_test[Diseases]
                     for test in test_mentions: ## on "high bp...
                         #print(test)
                         time = []
                         for annotations in inidcators[test]:
                             time = inidcators[test][annotations][0]

                         test_name = dictionary[test][1]
                         disease_name = dictionary[test][0].lower()

                         logical_form_template = logical_form
                         logical_form_template = logical_form_template.replace("|test|", test_name)
                         logical_form_template = logical_form_template.replace("|date|", record_date[0])

                         answers = []

                         question_paraphrases = []
                         for question in question_list:
                            orginal = question
                            question = question.replace("|test|", test_name)
                            question = question.replace("|date|", record_date[0])
                            if (question, orginal) not in question_paraphrases:
                                question_paraphrases.append((question, orginal))
                            non_uniq.append(question)
                         if "during DCT" in time:
                            annotations = annotations[0:-2] + (annotations[-2]+note_offset, annotations[-1]+note_offset)
                            answers.append(annotations)
                            #print(annotations)

                         QLA.append((question_paraphrases,logical_form_template,answers,non_uniq))
                            #for value in test_annotations:
                             #    test_annotations[]
        elif answertype == "result_value_time":

            year = []
            month = []
            day = []
            for date in Record_dates:
                try:
                    values = date[0].split("-")
                    if int(values[0]) not in year:
                        year.append(int(values[0]))
                    if int(values[1]) not in month:
                        month.append(int(values[1]))
                    if int(values[2]) not in day:
                        day.append(int(values[2]))
                except:
                    values = date[0].split("/")
                    if int(values[2]) not in year:
                        year.append(int(values[2]))
                    if int(values[1]) not in month:
                        month.append(int(values[1]))
                    if int(values[0]) not in day:
                        day.append(int(values[0]))

            if len(year) > 1:
                time_val = str(max(year)-min(year)) + " years"
            elif len(month) > 1:
                time_val = str(max(month)-min(month)) + " months"
            else:
                time_val = str(max(day)-min(day)) + " days"
            for key in disease_test:
                Diseases = key
                test_mentions = disease_test[Diseases]
                for test in test_mentions:  ## on "high bp...

                    test_name = dictionary[test][1]
                    logical_form_template = logical_form
                    logical_form_template = logical_form_template.replace("|test|", test_name)
                    logical_form_template = logical_form_template.replace("|time|", time_val)
                    logical_form_template = logical_form_template.replace("|value|", test_value[test_name])
                    answers = []

                    question_paraphrases = []
                    for question in question_list:
                        orginal = question
                        question = question.replace("|test|", test_name)
                        question = question.replace("|time|", time_val)
                        question = question.replace("|value|", test_value[test_name])
                        if (question, orginal) not in question_paraphrases:
                            question_paraphrases.append((question, orginal))
                        non_uniq.append(question)

                    for (on_date_disease,note_offset) in zip(Disease_time_progression,offset_notes):
                        Diseases = key
                        inidcators = on_date_disease[Diseases]  ## Get all corresponding indicators for that problem
                        time = []
                        for annotations in inidcators[test]:
                            time = inidcators[test][annotations][0]

                        if "before DCT" in time or "during DCT" in time:
                            annotations = annotations[0:-2] + (annotations[-2] + note_offset, annotations[-1] + note_offset)
                            answers.append(annotations)
                            #print(annotations)

                    QLA.append((question_paraphrases, logical_form_template, answers,non_uniq))
                        # for value in test_annotations:
                        #    test_annotations[]
        elif answertype == "results":

            for key in disease_test:
                Diseases = key
                test_mentions = disease_test[Diseases]
                for test in test_mentions:  ## on "high bp...

                    test_name = dictionary[test][1]
                    logical_form_template = logical_form
                    logical_form_template = logical_form_template.replace("|test|", test_name)
                    answers = []

                    question_paraphrases = []
                    for question in question_list:
                        orginal = question
                        question = question.replace("|test|", test_name)
                        if (question, orginal) not in question_paraphrases:
                            question_paraphrases.append((question, orginal))
                        non_uniq.append(question)
                    for (on_date_disease,note_offset) in zip(Disease_time_progression,offset_notes):
                        Diseases = key
                        inidcators = on_date_disease[Diseases]  ## Get all corresponding indicators for that problem
                        time = []
                        for annotations in inidcators[test]:
                            time = inidcators[test][annotations][0]

                        if "before DCT" in time or "during DCT" in time:
                            annotations = annotations[0:-2] + (annotations[-2] + note_offset, annotations[-1] + note_offset)
                            answers.append(annotations)

                    QLA.append((question_paraphrases, logical_form_template, answers,non_uniq))
        elif answertype == "test_problem":

            for key in disease_test:
                Diseases = key
                test_mentions = disease_test[Diseases]
                for test in test_mentions:  ## on "high bp...

                    test_name = dictionary[test][1]
                    logical_form_template = logical_form
                    logical_form_template = logical_form_template.replace("|test|", test_name)
                    logical_form_template = logical_form_template.replace("|problem|",Diseases)
                    answers = []

                    question_paraphrases = []
                    for question in question_list:
                        orginal = question
                        question = question.replace("|test|", test_name)
                        question = question.replace("|problem|", Diseases)
                        if (question, orginal) not in question_paraphrases:
                            question_paraphrases.append((question, orginal))
                        non_uniq.append(question)
                    for (on_date_disease, note_offset) in zip(Disease_time_progression, offset_notes):
                        Diseases = key
                        inidcators = on_date_disease[Diseases]  ## Get all corresponding indicators for that problem
                        time = []
                        for annotations in inidcators[test]:
                            time = inidcators[test][annotations][0]

                        if "before DCT" in time or "during DCT" in time:
                            annotations = annotations[0:-2] + (annotations[-2] + note_offset, annotations[-1] + note_offset)
                            answers.append(annotations)

                    QLA.append((question_paraphrases, logical_form_template, answers,non_uniq))

        elif answertype == "problem_result":

            for key in disease_test:
                Diseases = key
                test_mentions = disease_test[Diseases]
                for test in test_mentions:  ## on "high bp...

                    test_name = dictionary[test][1]
                    logical_form_template = logical_form
                    logical_form_template = logical_form_template.replace("|problem|",Diseases)
                    answers = []

                    question_paraphrases = []
                    for question in question_list:
                        orginal = question
                        question = question.replace("|problem|", Diseases)
                        if (question, orginal) not in question_paraphrases:
                            question_paraphrases.append((question, orginal))
                        non_uniq.append(question)
                    for (on_date_disease, note_offset) in zip(Disease_time_progression, offset_notes):
                        Diseases = key
                        inidcators = on_date_disease[Diseases]  ## Get all corresponding indicators for that problem
                        time = []
                        for annotations in inidcators[test]:
                            time = inidcators[test][annotations][0]

                        if "before DCT" in time or "during DCT" in time:
                            annotations = annotations[0:-2] + (annotations[-2] + note_offset, annotations[-1] + note_offset)
                            answers.append(annotations)

                    QLA.append((question_paraphrases, logical_form_template, answers,non_uniq))

        elif answertype == "test_date":
            for key in disease_test:
                Diseases = key
                test_mentions = disease_test[Diseases]
                for test in test_mentions:  ## on "high bp...

                    test_name = dictionary[test][1]
                    logical_form_template = logical_form
                    logical_form_template = logical_form_template.replace("|test|", test_name)
                    answers = []

                    question_paraphrases = []
                    for question in question_list:
                        orginal = question
                        question = question.replace("|test|", test_name)
                        if (question, orginal) not in question_paraphrases:
                            question_paraphrases.append((question, orginal))
                        non_uniq.append(question)
                    for (on_date_disease,record_date,note_offset) in zip(Disease_time_progression,Record_dates,offset_notes):
                        Diseases = key
                        inidcators = on_date_disease[Diseases]  ## Get all corresponding indicators for that problem
                        time = []
                        for annotations in inidcators[test]:
                            time = inidcators[test][annotations][0]

                        if "during DCT" in time:
                            record_date = record_date[0:-2] + (record_date[-2] + note_offset,record_date[-1]+note_offset)
                            answers.append(record_date)
                            #print(annotations)

                    QLA.append((question_paraphrases, logical_form_template, answers,non_uniq))
        elif answertype == "results_all":
            for key in disease_test:
                Diseases = key
                test_mentions = disease_test[Diseases]
                for test in test_mentions:  ## on "high bp...

                    test_name = dictionary[test][1]

                    answers = []

                    question_paraphrases = []
                    for question in question_list:
                        orginal = question
                        if (question, orginal) not in question_paraphrases:
                            question_paraphrases.append((question, orginal))
                        non_uniq.append(question)
                    for (on_date_disease, note_offset) in zip(Disease_time_progression, offset_notes):
                        Diseases = key
                        inidcators = on_date_disease[Diseases]  ## Get all corresponding indicators for that problem
                        time = []
                        for annotations in inidcators[test]:
                            time = inidcators[test][annotations][0]

                        if "during DCT" in time:
                            annotations = annotations[0:-2] + (annotations[-2] + note_offset, annotations[-1] + note_offset)
                            answers.append(annotations)
                            #print(annotations)

            QLA.append((question_paraphrases, logical_form, answers,non_uniq))
        elif answertype == "test_date":
            for key in disease_test:
                Diseases = key
                test_mentions = disease_test[Diseases]
                for test in test_mentions:  ## on "high bp...

                    test_name = dictionary[test][1]
                    logical_form_template = logical_form
                    logical_form_template = logical_form_template.replace("|test|", test_name)
                    answers = []

                    question_paraphrases = []
                    for question in question_list:
                        orginal = question
                        question = question.replace("|test|", test_name)
                        if (question, orginal) not in question_paraphrases:
                            question_paraphrases.append((question, orginal))
                        non_uniq.append(question)
                    for (on_date_disease, record_date, note_offset) in zip(Disease_time_progression, Record_dates,
                                                                           offset_notes):
                        Diseases = key
                        inidcators = on_date_disease[Diseases]  ## Get all corresponding indicators for that problem
                        time = []
                        for annotations in inidcators[test]:
                            time = inidcators[test][annotations][0]

                        if "during DCT" in time:
                            record_date = record_date[0:-2] + (record_date[-2] + note_offset,record_date[-1]+note_offset)
                            answers.append(record_date)
                            #print(annotations)

                    QLA.append((question_paraphrases, logical_form_template, answers,non_uniq))

        elif answertype == "disease_date":

            for key in disease_test:
                Diseases = key

                logical_form_template = logical_form
                logical_form_template = logical_form_template.replace("|problem|", key.lower())
                answers = []

                question_paraphrases = []
                for question in question_list:
                    orginal = question
                    question = question.replace("|problem|", key.lower())
                    if (question, orginal) not in question_paraphrases:
                        question_paraphrases.append((question, orginal))
                    non_uniq.append(question)
                for (on_date_disease, record_date, note_offset) in zip(Disease_time_progression, Record_dates,offset_notes):
                    Diseases = key
                    inidcators = on_date_disease[Diseases]  ## Get all corresponding indicators for that problem
                    time = []
                    for annotations in inidcators["mention"]:
                        time = inidcators["mention"][annotations][0]

                    if "during DCT" in time and "before DCT" not in time and "after DCT" not in time :
                        record_date = record_date[0:-2] + (record_date[-2] + note_offset,record_date[-1]+note_offset)
                        answers.append(record_date)
                        #print(annotations)

                QLA.append((question_paraphrases, logical_form_template, answers,non_uniq))

        elif answertype == "indicators":
            for key in disease_test:
                Diseases = key

                logical_form_template = logical_form
                logical_form_template = logical_form_template.replace("|problem|", key.lower())
                answers = []

                question_paraphrases = []
                for question in question_list:
                    orginal = question
                    question = question.replace("|problem|", key.lower())
                    if (question, orginal) not in question_paraphrases:
                        question_paraphrases.append((question, orginal))
                    non_uniq.append(question)
                for (on_date_disease, note_offset) in zip(Disease_time_progression, offset_notes):
                    Diseases = key
                    inidcators = on_date_disease[Diseases]  ## Get all corresponding indicators for that problem
                    time = []
                    for annotations in inidcators["mention"]:
                        time = inidcators["mention"][annotations][0]

                    if len(time) != 0:
                        annotations = annotations[0:-2] + (annotations[-2] + note_offset, annotations[-1] + note_offset)
                        answers.append(annotations)
                QLA.append((question_paraphrases, logical_form_template, answers,non_uniq))

        elif answertype == "symptom":
            key = "CAD"
            logical_form_template = logical_form
            logical_form_template = logical_form_template.replace("|problem|", key)
            answers = []

            question_paraphrases = []
            for question in question_list:
                orginal = question
                question = question.replace("|problem|", key)
                if (question,orginal) not in question_paraphrases:
                    question_paraphrases.append((question,orginal))
                non_uniq.append(question)
            for (on_date_disease, note_offset) in zip(Disease_time_progression, offset_notes):
                Diseases = key
                inidcators = on_date_disease[Diseases]  ## Get all corresponding indicators for that problem
                time = []
                for annotations in inidcators["symptom"]:
                    time = inidcators["symptom"][annotations][0]

                if len(time) != 0:
                    annotations = annotations[0:-2] + (annotations[-2] + note_offset, annotations[-1] + note_offset)
                    answers.append(annotations)
                    # print(annotations)

            QLA.append((question_paraphrases, logical_form_template, answers,non_uniq))
        elif answertype == "medications_all":
            for key in disease_test:
                logical_form_template = logical_form

                answers = []

                for (on_date_disease, note_offset) in zip(Disease_time_progression, offset_notes):
                    Diseases = key
                    inidcators = on_date_disease[Diseases]  ## Get all corresponding indicators for that problem
                    time = []
                    for med_type in self.types:
                        try:
                            out = inidcators[med_type]
                        except:
                            continue

                        for annotations in out:
                            time = inidcators[med_type][annotations][0]

                            if len(time) != 0:
                                annotations = annotations[0:-2] + (annotations[-2] + note_offset, annotations[-1] + note_offset)
                                answers.append(annotations)
                                # print(annotations)
            print(question_list[0])
            QLA.append([[(question_list[0],question_list[0])], logical_form_template, answers,question_list])
        else:
            print(answertype)

        return QLA

    def InputMapping(self, types_to_replace, logicalform, question_list):
        annotations = []
        if types_to_replace == ["test"]:
            annotations = test_annotations
            return annotations
        elif types_to_replace == ["test", "date"]:
            annotations = []
            for test in test_annotations:
                date = str(2000 + random.randint(0, 100)) + "-" + str(random.randint(1, 12)) + "-" + str(
                    random.randint(1, 28))
                annotations.append([test[0], date])
        elif types_to_replace == ["test", "time"]:
            annotations = []
            for test in test_annotations:
                time = random.choice(["years ", "weeks "]) + str(random.randint(2, 5))
                annotations.append([test[0], time])
        elif types_to_replace == ["test", "time", "value"]:
            annotations = []
            for test in test_annotations:
                time = random.choice(["years ", "weeks "]) + str(random.randint(2, 5))
                annotations.append([test[0], time, test_value[test[0]]])
        elif types_to_replace == ["medication"] or types_to_replace == ["treatment"]:
            annotations = [[meds] for meds in self.list_medications]
        elif types_to_replace == ["problem"]:
            annotations = [[prob] for prob in problem_annotations]
        elif types_to_replace == ["test", "problem"]:
            annotations = []
            for problem in disease_test:
                for test in disease_test[problem]:
                    annotations.append([dictionary[test][1], problem])
        elif types_to_replace == ["time"]:
            time = random.choice(["years ", "weeks "]) + str(random.randint(2, 5))
            annotations.append([time])
        elif types_to_replace == ["none"]:
            pass
        else:
            print(types_to_replace)

        return annotations

    ###################################### Supporting Utility Functions #######################################

    def checking_for_errors(self, question_list, logical_form_template):
        question_list = question_list.split("##")
        qwords_list = []
        dup_rwords_list = []
        unique_templates = []

        # logical_form_template = logical_form_template.replace("|treatment|", "|medication|").strip()

        for question in question_list:
            if question.strip() == "":
                continue
            # question = question.replace("|medication| or |medication|", "|medication|")
            # question = question.replace("|treatment|", "|medication|").strip()
            # logical_form_template.replace()
            if question not in unique_templates:
                unique_templates.append(question)
            else:
                continue

            qtemplate = question
            qwords = question.split("|")
            dup_rwords = qwords[1:len(qwords):2]

            qwords_list.append(qwords)

            if len(dup_rwords_list) == 0:
                dup_rwords_list = [set(dup_rwords)]
            else:
                if set(dup_rwords) not in dup_rwords_list:

                    question = question.replace("|treatment|", "|medication|").strip()
                    qwords = question.split("|")
                    dup_rwords = qwords[1:len(qwords):2]
                    if set(dup_rwords) not in dup_rwords_list:
                        print("Error Out Of Context Question:")
                        print(question, logical_form_template, question_list)
                        return []

        lwords = logical_form_template.split("|")
        dup_lrwords = lwords[1:len(lwords):2]
        if set(dup_lrwords) not in dup_rwords_list:
            print("Error Out Of Context Question-Logical Form Pairs:")
            print(question_list, logical_form_template)
            return []

        if len(dup_rwords_list) != 1:
            print("Check Question_Logical Form Mapping")
            print(dup_rwords_list, question_list)
            print(logical_form_template)
            return []

        return dup_rwords_list

    ## viz function ##
    def WriteTimeData(self):
        OutputFile = "TimeSeriesRiskData.csv"

        ofile = open(OutputFile, "w")
        writer = csv.writer(ofile)

        for patient_id in self.Patients:

            for var in ["glucose", "A1C", "mention"] + self.Medications:
                timeline = [patient_id, var]
                heading = ["patient_id", "variable"]
                # print(len(self.Patients[patient_id]))
                for idx in range(len(self.Patients[patient_id])):
                    # looping over the dates
                    # (before,current,after) the date tuple

                    date = self.Patients[patient_id][idx][1]
                    # print(date)

                    heading.extend(["before " + date, date, "after " + date])
                    # print(heading)
                    # print(date)
                    values = [[], [], []]

                    event_dictionary = self.Patients[patient_id][idx][2]

                    for keys in event_dictionary["Diabetes"][var]:
                        # print(keys)
                        # print(event_dictionary["Diabetes"][var])
                        if "continuing" in event_dictionary["Diabetes"][var][keys]:
                            # values[0] += " # "+keys[0]
                            # values[1] += " # "+keys[0]
                            # values[2] += " # "+keys[0]
                            flag = 0
                            out = zip(*values[0])
                            if len(out) == 0:
                                out = []
                            for word in out[0]:
                                if keys[0] in word:
                                    flag = 1
                                    break
                            if flag == 0:
                                values[0].append((keys[0], keys[1]))
                            else:
                                if keys[1] not in out[1]:
                                    values[0].append((keys[0], keys[1]))

                            flag = 0
                            out = zip(*values[1])
                            if len(out) == 0:
                                out = ["", ""]
                            for word in out[0]:
                                if keys[0] in word:
                                    flag = 1
                                    break
                            if flag == 0:
                                values[1].append((keys[0], keys[1]))
                            else:
                                if keys[1] not in out[1]:
                                    values[1].append((keys[0], keys[1]))

                            flag = 0
                            out = zip(*values[2])
                            if len(out) == 0:
                                out = ["", ""]
                            for word in out[0]:
                                if keys[0] in word:
                                    flag = 1
                                    break
                            if flag == 0:
                                values[2].append((keys[0], keys[1]))
                            else:
                                if keys[1] not in out[1]:
                                    values[2].append((keys[0], keys[1]))
                        else:
                            if "after DCT" in event_dictionary["Diabetes"][var][keys]:
                                # values[2] += " # "+keys[0]
                                flag = 0
                                out = zip(*values[2])
                                if len(out) == 0:
                                    out = ["", ""]
                                for word in out[0]:
                                    if keys[0] in word:
                                        flag = 1
                                        break
                                if flag == 0:
                                    values[2].append((keys[0], keys[1]))
                                else:
                                    if keys[1] not in out[1]:
                                        values[2].append((keys[0], keys[1]))

                            if "before DCT" in event_dictionary["Diabetes"][var][keys]:
                                # values[0] += " # "+keys[0]
                                flag = 0
                                out = zip(*values[0])
                                if len(out) == 0:
                                    out = ["", ""]
                                for word in out[0]:
                                    if keys[0] in word:
                                        flag = 1
                                        break
                                if flag == 0:
                                    values[0].append((keys[0], keys[1]))
                                else:
                                    if keys[1] not in out[1]:
                                        values[0].append((keys[0], keys[1]))
                            if "during DCT" in event_dictionary["Diabetes"][var][keys]:
                                # values[1] += " # "+keys[0]

                                flag = 0
                                out = zip(*values[1])
                                if len(out) == 0:
                                    out = ["", ""]
                                for word in out[0]:
                                    if keys[0] in word:
                                        flag = 1
                                        break
                                if flag == 0:
                                    values[1].append((keys[0], keys[1]))
                                else:
                                    if keys[1] not in out[1]:
                                        values[1].append((keys[0], keys[1]))

                        if "not mentioned" in event_dictionary["Diabetes"][var][keys]:
                            print("not mentioned occurence")

                    timeline.extend(values)

                if var == "glucose":
                    writer.writerow(heading)

                writer.writerow(timeline)

            writer.writerow([""])

RiskFileAnalysis()