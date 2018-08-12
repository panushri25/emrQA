'''
This File is to analyze the i2b2_risk files and make answers for questions
'''

from os import listdir
import xml.etree.ElementTree
import xmltodict
import nltk
import numpy as np
import csv

class RiskFileAnalysis():

    def __init__(self):
        self.types = []
        self.ReadFile()
        self.WriteTimeData()
        print(self.types)

    def WriteTimeData(self):
        OutputFile = "TimeSeriesRiskData.csv"

        ofile = open(OutputFile,"w")
        writer = csv.writer(ofile)


        for patient_id in self.Patients:

            for var in ["glucose", "A1C", "mention"]+self.Medications:
                timeline = [patient_id,var]
                heading = ["patient_id", "variable"]
                #print(len(self.Patients[patient_id]))
                for idx in range(len(self.Patients[patient_id])):
                    #looping over the dates
                    #(before,current,after) the date tuple

                    date = self.Patients[patient_id][idx][1]
                    #print(date)

                    heading.extend(["before " + date, date, "after " + date])
                    #print(heading)
                    #print(date)
                    values = [[],[],[]]


                    event_dictionary = self.Patients[patient_id][idx][2]

                    for keys in event_dictionary["Diabetes"][var]:
                        #print(keys)
                        #print(event_dictionary["Diabetes"][var])
                        if "continuing" in event_dictionary["Diabetes"][var][keys]:
                            #values[0] += " # "+keys[0]
                            #values[1] += " # "+keys[0]
                            #values[2] += " # "+keys[0]
                            flag = 0
                            out = zip(*values[0])
                            if len(out) == 0:
                                out = []
                            for word in out[0]:
                                if keys[0] in word:
                                    flag = 1
                                    break
                            if flag == 0:
                                values[0].append((keys[0],keys[1]))
                            else:
                                if keys[1] not in out[1]:
                                    values[0].append((keys[0], keys[1]))

                            flag = 0
                            out = zip(*values[1])
                            if len(out) == 0:
                                out = ["",""]
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
                                out = ["",""]
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
                                #values[2] += " # "+keys[0]
                                flag = 0
                                out = zip(*values[2])
                                if len(out) == 0:
                                    out = ["",""]
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
                                #values[0] += " # "+keys[0]
                                flag = 0
                                out = zip(*values[0])
                                if len(out) == 0:
                                    out = ["",""]
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
                                #values[1] += " # "+keys[0]

                                flag = 0
                                out = zip(*values[1])
                                if len(out) == 0:
                                    out = ["",""]
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
    def ReadFile(self):

        file_path = ["/home/anusri/Desktop/IBM/i2b2/heart-disease-risk/training-RiskFactors-Complete-Set1/"]
        TempFile = "temp_risk.txt"

        self.Patients = {}
        for paths in file_path:
            files = listdir(paths)
            files.sort()


            # print(files)
            for file in files:
                print("Analyzing File:"+file)
                patient_id = file.split("-")[0]

                if patient_id not in self.Patients:
                    self.Patients[patient_id] = []
                ofile = open(TempFile, "w", 0)
                #print(paths + file)
                remote_file = open(paths + file)
                for line in remote_file:
                    try:
                        ofile.write(line)
                    except:
                        print(line)

                ofile.close()
                with open(TempFile) as fd:
                    self.doc = xmltodict.parse(fd.read())

                self.ReadDiabetes(patient_id)
    def ReadDiabetes(self,patient_id):


        Clinical_Notes = self.doc['root']["TEXT"]
        try:
            Record_Date = self.doc['root']["TAGS"]["PHI"][0]["@text"]
        except:
            Record_Date = self.doc['root']["TAGS"]["PHI"]["@text"]
        Dictionary = {}
        Dictionary["Diabetes"] = {}
        Dictionary["Diabetes"]["glucose"] = {}
        Dictionary["Diabetes"]["A1C"] = {}
        Dictionary["Diabetes"]["mention"] = {}


        sentences = Clinical_Notes.split(".")

        CharPos = 0
        indices = []

        for line in sentences:
            indices.append((CharPos,CharPos+len(line),line))
            CharPos = CharPos+1+len(line)

        #print(sentences)
        #print(Record_Date)

        try:
            NumIndoc = len(self.doc['root']["TAGS"]["DIABETES"])
        except:
            #print(Record_Date)
            #self.Patients[patient_id].append((Clinical_Notes, Record_Date, Dictionary))
            self.ReadDiabetesMedication(patient_id, indices, Clinical_Notes, Record_Date, Dictionary)

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

                    start = int(start)-3
                    end = int(end)-3
                    #print(start,end)
                    for tup_id in range(len(indices)):

                        try:
                            if start >= indices[tup_id][0] and end <= indices[tup_id][1]:
                                inline_text = indices[tup_id][2].replace("\n", "")
                                break
                            elif start >= indices[tup_id][0] and end <= indices[tup_id + 1][1]:
                                inline_text = indices[tup_id][2].replace("\n", "") + "." + indices[tup_id + 1][2].replace(
                                    "\n", "")
                            elif start >= indices[tup_id][0] and end <= indices[tup_id + 1][2]:
                                inline_text = indices[tup_id][2].replace("\n", "") + "." + indices[tup_id + 1][2].replace(
                                    "\n", "")
                            else:
                                pass
                        except:
                            print("********************************************************************error")
                            print(text)
                            print(start,end)
                            print(indices[tup_id][0], indices[tup_id][1])

                    inline_text = inline_text.replace("\t","")
                    text = text.replace("\n", "")
                    text = text.replace("\t", "")
                    inline_text = " ".join([word for word in inline_text.split(" ") if word != ""])
                    text = " ".join([word for word in text.split(" ") if word != ""])
                    if (text, inline_text) not in Dictionary["Diabetes"]["mention"]:
                        Dictionary["Diabetes"]["mention"][(text, inline_text)] = []

                    if time not in Dictionary["Diabetes"]["mention"][(text,inline_text)]:
                        Dictionary["Diabetes"]["mention"][(text,inline_text)].append(time)

                elif indicator == "A1C":
                    #print("A1C",text,time)

                    start = int(start)
                    end = int(end)

                    for tup_id in range(len(indices)):
                        #print(indices[tup_id][0],indices[tup_id][1])
                        if start >= indices[tup_id][0] and end <= indices[tup_id][1]:
                            inline_text = indices[tup_id][2].replace("\n", "")
                        elif start >= indices[tup_id][0] and end <= indices[tup_id + 1][1]:
                            inline_text = indices[tup_id][2].replace("\n", "") + "." + indices[tup_id + 1][2].replace("\n", "")
                        elif start >= indices[tup_id][0] and end <= indices[tup_id + 1][2]:
                            inline_text = indices[tup_id][2].replace("\n", "") + "." + indices[tup_id + 1][2].replace("\n", "")
                        else:
                            pass
                    inline_text = inline_text.replace("\t","")
                    text = text.replace("\n", "")
                    text = text.replace("\t", "")
                    inline_text = " ".join([word for word in inline_text.split(" ") if word != ""])
                    text = " ".join([word for word in text.split(" ") if word != ""])
                    if (text, inline_text) not in Dictionary["Diabetes"]["A1C"]:
                        Dictionary["Diabetes"]["A1C"][(text, inline_text)] = []
                    if time not in Dictionary["Diabetes"]["A1C"][(text,inline_text)]:
                        Dictionary["Diabetes"]["A1C"][(text,inline_text)].append(time)

                elif indicator == "glucose":
                    #print("glucose",text,time)
                    start = int(start)
                    end = int(end)

                    for tup_id in range(len(indices)):
                        # print(indices[tup_id][0],indices[tup_id][1])
                        if start >= indices[tup_id][0] and end <= indices[tup_id][1]:
                            inline_text = indices[tup_id][2].replace("\n", "")
                        elif start >= indices[tup_id][0] and end <= indices[tup_id + 1][1]:
                            inline_text = indices[tup_id][2].replace("\n", "") + "." + indices[tup_id + 1][2].replace(
                                "\n", "")
                        elif start >= indices[tup_id][0] and end <= indices[tup_id + 1][2]:
                            inline_text = indices[tup_id][2].replace("\n", "") + "." + indices[tup_id + 1][2].replace(
                                "\n", "")
                        else:
                            pass
                    inline_text = inline_text.replace("\t","")
                    text = text.replace("\n","")
                    text = text.replace("\t", "")
                    inline_text = " ".join([word for word in inline_text.split(" ") if word != ""])
                    text = " ".join([word for word in text.split(" ") if word != ""])
                    if (text, inline_text) not in Dictionary["Diabetes"]["glucose"]:
                        Dictionary["Diabetes"]["glucose"][(text, inline_text)] = []

                    if time not in Dictionary["Diabetes"]["glucose"][(text,inline_text)]:
                        Dictionary["Diabetes"]["glucose"][(text,inline_text)].append(time)

                else:
                    print(indicator)
                    continue
        #print(Record_Date)
        #print(Record_Date)


        self.ReadDiabetesMedication(patient_id,indices,Clinical_Notes,Record_Date,Dictionary)

    def ReadDiabetesMedication(self,patient_id,indices,Clinical_Notes,Record_Date,Dictionary):


        self.Medications = ["metformin", "insulin", "sulfonylureas", "thiazolidinediones", "GLP-1 agonists", "Meglitinides", "DPP4 inhibitors", "Amylin", "anti-diabetes medications"]

        for med in self.Medications:
            Dictionary["Diabetes"][med] = {}

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

                for tup_id in range(len(indices)):
                    # print(indices[tup_id][0],indices[tup_id][1])
                    if start >= indices[tup_id][0] and end <= indices[tup_id][1]:
                        inline_text = indices[tup_id][2].replace("\n", "")
                    elif start >= indices[tup_id][0] and end <= indices[tup_id + 1][1]:
                        inline_text = indices[tup_id][2].replace("\n", "") + "." + indices[tup_id + 1][2].replace(
                            "\n", "")
                    elif start >= indices[tup_id][0] and end <= indices[tup_id + 1][2]:
                        inline_text = indices[tup_id][2].replace("\n", "") + "." + indices[tup_id + 1][2].replace(
                            "\n", "")
                    else:
                        pass
                inline_text = inline_text.replace("\t", "")
                text = text.replace("\n", "")
                text = text.replace("\t", "")
                inline_text = " ".join([word for word in inline_text.split(" ") if word != ""])
                text = " ".join([word for word in text.split(" ") if word != ""])
                if indicator in self.Medications:
                    if (text, inline_text) not in Dictionary["Diabetes"][indicator]:
                        Dictionary["Diabetes"][indicator][(text, inline_text)] = []

                    if time not in Dictionary["Diabetes"][indicator][(text, inline_text)]:
                        Dictionary["Diabetes"][indicator][(text, inline_text)].append(time)
                if indicator2 in self.Medications:
                    if (text, inline_text) not in Dictionary["Diabetes"][indicator2]:
                        Dictionary["Diabetes"][indicator2][(text, inline_text)] = []

                    if time not in Dictionary["Diabetes"][indicator2][(text, inline_text)]:
                        Dictionary["Diabetes"][indicator2][(text, inline_text)].append(time)

        #print(Dictionary["Diabetes"].keys())
        self.Patients[patient_id].append((Clinical_Notes, Record_Date, Dictionary))
RiskFileAnalysis()
