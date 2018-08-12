import csv
from os import listdir
from os.path import isfile, join
import itertools
from textblob import TextBlob
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet as wn
import string
import json
import sys
from problem_classfiers import concept_is_CommonNoun, concept_is_PastTense
reload(sys)
sys.setdefaultencoding("ISO-8859-1")
import random

## Resolve the use of medications and treatments
## Resolve id for question-logical froms

class GenerateRelationsQuestions():

    def __init__(self):

        self.similar = []
        val = [wn.synsets('problem'), wn.synsets('test'), wn.synsets('procedure'), wn.synsets('disease'),
               wn.synsets('medication'), wn.synsets('treatment'), wn.synsets('surgery')]
        self.count_corefs = 0
        self.resolved_corefs = 0
        for out in val:
            for ss in out:
                self.similar.extend(ss.lemma_names())

        self.RelationsFilePath = [
            "/home/anusri/Desktop/IBM/i2b2/relations/concept_assertion_relation_training_data/partners/rel/",
            "/home/anusri/Desktop/IBM/i2b2/relations/concept_assertion_relation_training_data/beth/rel/",
            "/home/anusri/Desktop/IBM/i2b2/relations/test_data/rel/"]

        self.NoteFilePath = [
            "/home/anusri/Desktop/IBM/i2b2/relations/concept_assertion_relation_training_data/partners/txt/",
            "/home/anusri/Desktop/IBM/i2b2/relations/concept_assertion_relation_training_data/beth/txt/",
            "/home/anusri/Desktop/IBM/i2b2/relations/test_data/txt/"]

        self.AstFilePath = [ "/home/anusri/Desktop/IBM/i2b2/relations/concept_assertion_relation_training_data/partners/ast/",
            "/home/anusri/Desktop/IBM/i2b2/relations/concept_assertion_relation_training_data/beth/ast/",
            "/home/anusri/Desktop/IBM/i2b2/relations/test_data/ast/"]

        self.ReadRelationsData()
        self.ReadAssertionsData()
        self.ReadTemplates()

    def ReadCoreference(self,coref_path,PatientNote):

        remote_file = open(coref_path.replace("docs","chains") + ".chains")
        coref_concepts = {}
        for line in remote_file:
            line = line.replace("|||", "||")
            words = line.split("||")

            vals = []


            type = words[-1].replace("\"","").split("=")[-1].strip().replace("coref ","")
            if type not in coref_concepts and type != "person":
                coref_concepts[type] = []
            if type == "person":
                continue
            for word in words[0:-1]:
                term = word.split("=")
                full_annotation = "=".join(term[1:])
                index = [pos for pos, char in enumerate(full_annotation) if char == "\""]
                pos1 = int(index[0])
                pos2 = int(index[-1])

                annotation = full_annotation[pos1 + 1:pos2]
                indxs = full_annotation[pos2 + 1:].split(",")

                line_in_note = ""
                start_line = None


                for indx in indxs:
                    indx = indx.strip()
                    out = indx.split(" ")
                    start_line = out[0].split(":")[0]
                    start_token = out[0].split(":")[1]
                    end_line = out[1].split(":")[0]
                    end_token = out[1].split(":")[1]
                    end_token = out[1].split(":")[1]

                line_in_note += ",".join(PatientNote[int(start_line) - 1:int(end_line)])

                vals.append((annotation,line_in_note,start_line,start_token))

            coref_concepts[type].append(vals)

        return coref_concepts

    def SimplePreProcess(self, word):

        if word == "":
            return None

        lemmatizer = WordNetLemmatizer()

        if concept_is_CommonNoun(word) == 1 or concept_is_PastTense(word) == 1:
            return None

        tag = nltk.pos_tag(nltk.word_tokenize(word))
        temp = zip(*tag)
        words = list(temp[0])
        tags = list(temp[1])

        if tags[0] == "DT":
            words[0] = ""
        else:
            pass

        for idx in range(len(tags)):
            if lemmatizer.lemmatize(words[idx].lower()) in ["patient"]:
                words[idx] = ""
            if tags[idx] in ["PRP","PRP$"]:
                if idx != 0 or " ".join(words[0:idx]).strip() != "":
                    words[idx] = "the"
                if idx == 0:
                    words[idx] = ""
            if " ".join(words[0:idx]).strip() != "" and tags[idx] == ["IN", "WDT"]:
                words[idx] = ""

        words = [word for word in words if word != "" and lemmatizer.lemmatize(word) not in self.similar] ## check if its okay to start with "further"
        if len(words) == 0:
            return None


        filter = " ".join(words) ## To make sure it makes sense you can use a parse#
        tag = nltk.pos_tag(nltk.word_tokenize(filter))
        temp = zip(*tag)
        words = list(temp[0])
        tags = list(temp[1])

        if len(set(["NN","NNS","jjR","JJS","JJ","NNP","NNPS","VB","VBG","VBP","VBZ"]).intersection(set(tags))) == 0:
            return None
        #events = word
        #fevent = []
        #out = events.split(" ")
        #for val in out:
        #    if (val.lower().find("patient") == -1):
        #        fevent.append(val)

        #if len(fevent) == 0:
        #    return None

        #events = " ".join(fevent)  # Remove Patient or any other common words

        #exclude = set(string.punctuation)
        #s = ''.join(ch for ch in filter if ch not in exclude)
        #print(filter)
        return filter
    def ReadAssertionsData(self):

        self.problem_status = {}

        for paths in self.AstFilePath:
            files = [f for f in listdir(paths) if isfile(join(paths, f))]
            for file in files:
                remote_file = open(paths + file)
                Noteid = file.split(".")[0]
                PatientNote = self.ClinicalNotes[Noteid]

                if Noteid not in self.problem_status:
                    self.problem_status[Noteid] = {}

                for line in remote_file:
                    line = line.replace("|||", "||")
                    words = line.split("||")

                    vals = []
                    type = words[1].split("=")[1].split("\"")[1]
                    status = words[2].split("=")[1].split("\"")[1]
                    for word in [words[0]]:
                        term = word.split("=")
                        full_annotation = "=".join(term[1:])
                        index = [pos for pos, char in enumerate(full_annotation) if char == "\""]
                        pos1 = int(index[0])
                        pos2 = int(index[-1])

                        annotation = full_annotation[pos1 + 1:pos2]
                        indxs = full_annotation[pos2 + 1:].split(",")

                        line_in_note = ""
                        start_line = None

                        annotation = self.SimplePreProcess(annotation)



                        for indx in indxs:
                            indx = indx.strip()
                            out = indx.split(" ")
                            start_line = out[0].split(":")[0]
                            start_token = out[0].split(":")[1]
                            end_line = out[1].split(":")[0]
                            end_token = out[1].split(":")[1]

                        line_in_note += ",".join(PatientNote[int(start_line) - 1:int(end_line)])

                    if annotation == None:
                        continue
                    if type == "problem":
                        if annotation not in self.problem_status[Noteid]:
                            self.problem_status[Noteid][annotation] = []
                        self.problem_status[Noteid][annotation].append((status,line_in_note,start_line,start_token))
    #the tremendous tumor burden,the cord compression,gait weakness , stress incontinence copd flare a wide based gait shuffling short steps head computerized tomography scan
    def CheckForCoreferences(self,concept, type ,Coreferences):
        self.count_corefs += 1
        valid_list = []
        if type == "problem1" or type == "problem2":
            type= "problem"
        try:
            coref_lists = Coreferences[type]
        except:
            #print(type,Coreferences.keys())
            return None

        #print(coref_lists, concept)
        for coref_list in coref_lists:

            if concept in coref_list:

                #print(concept[0],zip(*coref_list)[0])
                for idx in range(len(zip(*coref_list)[0])):
                    coref_concept = zip(*coref_list)[0][idx]
                    sout = self.SimplePreProcess(coref_concept)
                    #out_list = list(coref_list[idx])
                    #out_list.append(sout) ############################ correct grammar ot not #############
                    if sout != None and  sout not in valid_list:
                        valid_list.append(sout)
                #print(concept[0],valid_list,set(zip(*coref_list)[0]).symmetric_difference(set(valid_list)))

        if len(valid_list) != 0:
            self.resolved_corefs += 1
            return valid_list
        else:
            return None

    def CheckIfConceptValid(self,val, type, Coreferences):

        t1 = self.SimplePreProcess(val[0])
        valid_list = None
        if t1 == None: ## currently only looking for coreference is we orginal word is not valid, can use it to change orginal concepts as well ###
            valid_list = self.CheckForCoreferences(val, type ,Coreferences)
            #print(val[0],valid_list,Coreferences[type])
        else:
            pass
        return (t1,valid_list)

        # If atelast one of the concept is a common noun ignore the relation
        ### Common Noun Check  End###

    def ReadRelationsData(self):


        self.RelationsPerNote = {}

        self.ClinicalNotes = {}

        type = {"TeRP":("test","problem"),"TeCP":("test","problem"),"TrIP":("treatment","problem"),"TrWP":("treatment","problem"),
                "TrCP": ("treatment", "problem"), "TrAP": ("treatment", "problem"), "TrNAP": ("treatment", "problem"),"PIP": ("problem1", "problem2")}

        self.tr_status = {"TrIP":"improves","TrWP":"worsens/not improves","TrAP": "not known status", "TrCP": "causes"}

        for paths in self.NoteFilePath:
            files = [f for f in listdir(paths) if isfile(join(paths, f))]
            for file in files:
                remote_file = open(paths + file)
                Noteid = file.split(".")[0]
                self.ClinicalNotes[Noteid] = remote_file.readlines()

        matching_notes = "/home/anusri/Desktop/IBM/Answers-old/temporal/matching_notes.csv"
        match_file = open(matching_notes)
        csvreader = csv.reader(match_file)
        matching_files = list(csvreader) #temporal, relation, coreference
        Coreference_Note = {}
        self.CoreferenceCluster_to_Entity_map = {}
        self.Entity_to_CoreferenceCluster_map = {}

        ### Create coreference clusters for every type in every note ###
        for file in matching_files[1:]:
            relation_note_id = file[1].split("/")[-1].split(".")[0]
            coreference_path = file[2]
            coreferences = self.ReadCoreference(coreference_path,self.ClinicalNotes[relation_note_id])
            Coreference_Note[relation_note_id] = coreferences
            self.CoreferenceCluster_to_Entity_map[relation_note_id] = {}
            self.Entity_to_CoreferenceCluster_map[relation_note_id] = {}
            for stype in coreferences:
                if stype not in self.CoreferenceCluster_to_Entity_map[relation_note_id]:
                    self.CoreferenceCluster_to_Entity_map[relation_note_id][stype] = {}
                    self.Entity_to_CoreferenceCluster_map[relation_note_id][stype] = {}
                    cluster_id = 0
                    for coref_list in coreferences[stype]:
                        for concept in coref_list:
                            self.CoreferenceCluster_to_Entity_map[relation_note_id][stype][cluster_id] = concept
                            self.Entity_to_CoreferenceCluster_map[relation_note_id][stype][concept] = cluster_id
                        cluster_id += 1
        #############################################################################################################################
        self.map_problems_to_test_revealed = {}
        self.map_tests_to_problem_revealed = {}
        self.map_problems_to_test_investigated = {}
        self.map_tests_to_problem_investigated = {}
        self.map_treatments_to_problem = {}
        self.map_problems_to_treatment = {}
        self.problems_to_badtreatment = {}
        self.allergic_treatments = {}
        self.treatments_status_to_problem = {}
        self.map_problems_to_treatment = {}
        self.badtreatments_to_problem = {}
        self.symptoms_to_problem = {}
        self.problems_to_symptom = {}


        for paths in self.RelationsFilePath:
            files = [f for f in listdir(paths) if isfile(join(paths, f))]
            for file in files:
                remote_file = open(paths + file)
                Noteid = file.split(".")[0]
                PatientNote = self.ClinicalNotes[Noteid]
                try:
                    Coreferences = Coreference_Note[Noteid]
                except:
                    Coreferences = {}
                Relations = {}

                for line in remote_file:
                    line = line.replace("|||", "||")
                    words = line.split("||")

                    vals = []
                    for word in [words[0],words[2]]:
                        term = word.split("=")
                        full_annotation = "=".join(term[1:])
                        index = [pos for pos, char in enumerate(full_annotation) if char == "\""]
                        pos1 = int(index[0])
                        pos2 = int(index[-1])

                        annotation = full_annotation[pos1 + 1:pos2]
                        indxs = full_annotation[pos2 + 1:].split(",")

                        line_in_note = ""
                        start_line = None


                        for indx in indxs:
                            indx = indx.strip()
                            out = indx.split(" ")
                            start_line = out[0].split(":")[0]
                            start_token = out[0].split(":")[1]
                            end_line = out[1].split(":")[0]
                            end_token = out[1].split(":")[1]

                        line_in_note += ",".join(PatientNote[int(start_line) - 1:int(end_line)])

                        vals.append((annotation,line_in_note,start_line,start_token))


                    relate = words[1].split("=")[1].split("\"")[1]

                    ### Common Noun Check Start ###
                    val1 = vals[0]
                    val2 = vals[1]
                    t1 = val1[0]
                    t2 = val2[0]
                    #print(relate)
                    if relate not in Relations:
                        Relations[relate] = []
                    '''
                    t1 = self.SimplePreProcess(val1[0])
                    t2 = self.SimplePreProcess(val2[0])

                    
                        #print("yes")
                        if t1 == None:
                            self.CheckForCoreferences(val1, type[relate][0],Coreferences)
                        if t2 == None:
                            self.CheckForCoreferences(val2, type[relate][0], Coreferences)
                        continue

                    if t1 == None or t2 == None:
                        ## Just use it because we dont want to miss the answers.
                        continue
                    
                    # If atelast one of the concept is a common noun ignore the relation
                    ### Common Noun Check  End###
                    '''
                    val1 = (t1, type[relate][0], val1[1],val1[2],val1[3])
                    val2 = (t2, type[relate][1], val2[1], val2[2],val1[3])

                    if (val1, val2) not in Relations[relate]:
                        Relations[relate].append((val1, val2))

                    self.MakeRelationMappings(val1,val2,relate,Noteid)

                self.RelationsPerNote[Noteid] = [Relations,PatientNote,Coreferences]

                #for cluster_id in self.map_problems_to_test_investigated:
                #    try:
                #        out = self.map_problems_to_test_revealed[cluster_id]
                #        print(self.map_problems_to_test_investigated[cluster_id])
                #        print(out)
                #        print("\n")
                #    except:
                #        continue
                '''
                print(Relations.keys())
                try:
                    relation_investigated = Relations["TeCP"]
                    relation_revealed = Relations["TeRP"]
                except:

                    continue
                values = zip(*relation_revealed)
                for annotations in relation_investigated:
                    try:
                        index_val = list(values[0]).index(annotations[0][0])
                    except:
                        continue

                    for idx in index_val:
                        print(annotations)
                        print(values[2][idx])
                '''

    def MakeRelationMappings(self,val1,val2,relate,Noteid):

        #print(self.Entity_to_CoreferenceCluster_map[Noteid]["problem"])
        #print((val1[0],val1[2],val1[3],val1[4]))
        try:

            concept_cluster_1 = self.Entity_to_CoreferenceCluster_map[Noteid][val1[1].replace("1","")][(val1[0],val1[2],val1[3],val1[4])]
            #print(concept_cluster_1)
        except:
            concept_cluster_1 = val1[0]
        try:

            concept_cluster_2 = self.Entity_to_CoreferenceCluster_map[Noteid][val2[1].replace("2","")][(val2[0],val2[2],val2[3],val2[4])]

            #print(concept_cluster_2)
        except:
            concept_cluster_2 = val2[0]
            #print(concept_cluster_2)

        if Noteid not in self.map_problems_to_test_revealed:
            self.map_problems_to_test_revealed[Noteid] = {}
            self.map_tests_to_problem_revealed[Noteid] = {}
            self.map_problems_to_test_investigated[Noteid] = {}
            self.map_tests_to_problem_investigated[Noteid] = {}
            self.allergic_treatments[Noteid] = []
            self.problems_to_badtreatment[Noteid] = {}
            self.treatments_status_to_problem[Noteid] = {}
            self.map_problems_to_treatment[Noteid] = {}
            self.badtreatments_to_problem[Noteid] = {}
            self.symptoms_to_problem[Noteid] = {}
            self.problems_to_symptom[Noteid] = {}

        if relate == "TeRP":

            ## Coreference Checking is ensuring semantic check ##
            ## Not resolving coreference for answers at this point ###

            ## If val1 belongs to some cluster, map to that if not map, to the concept directly ##
            if concept_cluster_1 not in self.map_problems_to_test_revealed[Noteid]:
                self.map_problems_to_test_revealed[Noteid][concept_cluster_1] = []

            if concept_cluster_2 not in self.map_tests_to_problem_revealed:
                self.map_tests_to_problem_revealed[Noteid][concept_cluster_2] = []

            self.map_problems_to_test_revealed[Noteid][concept_cluster_1].append(val2)
            self.map_tests_to_problem_revealed[Noteid][concept_cluster_2].append(val1)

        if relate == "TeCP":

            ## Simple checking the name, need to check semantically, or normalize with CUI ##

            if concept_cluster_1 not in self.map_problems_to_test_investigated[Noteid]:
                self.map_problems_to_test_investigated[Noteid][concept_cluster_1] = []

            if concept_cluster_2 not in self.map_tests_to_problem_investigated:
                self.map_tests_to_problem_investigated[Noteid][concept_cluster_2] = []

            self.map_problems_to_test_investigated[Noteid][concept_cluster_1].append(val2)
            self.map_tests_to_problem_investigated[Noteid][concept_cluster_2].append(val1)

        if relate == "TrNAP" or relate == "TrCP":

            if val1 not in self.allergic_treatments[Noteid]:
                self.allergic_treatments[Noteid].append(val1)

        if relate == "TrCP":

            if concept_cluster_1 not in self.problems_to_badtreatment[Noteid]:
                self.problems_to_badtreatment[Noteid][concept_cluster_1] = []

            if concept_cluster_2 not in self.badtreatments_to_problem[Noteid]:
                self.badtreatments_to_problem[Noteid][concept_cluster_2] = []

            self.problems_to_badtreatment[Noteid][concept_cluster_1].append(val2)
            self.badtreatments_to_problem[Noteid][concept_cluster_2].append(val1)

            if concept_cluster_1 not in self.map_problems_to_treatment[Noteid]:
                self.map_problems_to_treatment[Noteid][concept_cluster_1] = []

            status = self.tr_status[relate]
            self.map_problems_to_treatment[Noteid][concept_cluster_1].append((val2, status))

        if relate == "TrIP" or relate == "TrWP" or relate == "TrAP":

            if concept_cluster_2 not in self.treatments_status_to_problem[Noteid]:
                self.treatments_status_to_problem[Noteid][concept_cluster_2] = []

            status = self.tr_status[relate]
            self.treatments_status_to_problem[Noteid][concept_cluster_2].append((val1,status)) ## val1 is treatment

            if concept_cluster_1 not in self.map_problems_to_treatment[Noteid]:
                self.map_problems_to_treatment[Noteid][concept_cluster_1] = []

            status = self.tr_status[relate]
            self.map_problems_to_treatment[Noteid][concept_cluster_1].append((val2,status))

        if relate == "PIP":

            if concept_cluster_1 not in self.symptoms_to_problem[Noteid]:
                self.symptoms_to_problem[Noteid][concept_cluster_1] = []

            if concept_cluster_2 not in self.problems_to_symptom[Noteid]:
                self.problems_to_symptom[Noteid][concept_cluster_2] = []

            self.symptoms_to_problem[Noteid][concept_cluster_1].append(val2)
            self.problems_to_symptom[Noteid][concept_cluster_2].append(val1)

    def AnswerSubFunction(self, answertype,val1,val2,Noteid,relate):

        try:
            concept_cluster_1 = self.Entity_to_CoreferenceCluster_map[Noteid][val1[1].replace("1","")][(val1[0],val1[2],val1[3],val1[4])]
        except:
            concept_cluster_1 = val1[0]
        try:
            concept_cluster_2 = self.Entity_to_CoreferenceCluster_map[Noteid][val2[1].replace("2","")][(val2[0],val2[2],val2[3],val2[4])]
        except:
            concept_cluster_2 = val2[0]

        answer = []
        result_start_line = []
        result_start_token = []
        answer_line = []

    ######################## rules for test answers ########################
        if answertype == "yes/no" or answertype == "abnormal" or answertype == "yes":
            answer = ["yes"]
        elif answertype == "tests_investigated":
            tests = self.map_tests_to_problem_investigated[Noteid][concept_cluster_2]
            for test in tests:
                answer += [test[0]]
                answer_line.append(test[2])
                result_start_line.append(int(test[3]))
                result_start_token.append(int(test[4]))
        elif answertype == "tests_revealed":
            tests = self.map_tests_to_problem_revealed[Noteid][concept_cluster_2]
            for test in tests:
                answer += [test[0]]
                answer_line.append(test[2])
                result_start_line.append(int(test[3]))
                result_start_token.append(int(test[4]))
        elif answertype == "conducted_problem_revealed_problem":
            try:
                investigated_problems = self.map_problems_to_test_investigated[concept_cluster_1]
                for problem in investigated_problems:
                    answer += [ problem[0]]
                    #answer += ["conducted " + problem[0]]
                    answer_line.append(problem[2])
                    result_start_line.append(int(problem[3]))
                    result_start_token.append(int(problem[4]))
            except:
                pass
            try:
                revealed_problems = self.map_problems_to_test_revealed[concept_cluster_1]
                for problem in revealed_problems:
                    #answer += ["revealed " + problem[0]]
                    answer += [problem[0]]
                    answer_line.append(problem[2])
                    result_start_line.append(int(problem[3]))
                    result_start_token.append(int(problem[4]))
            except:
                pass
        elif answertype == "revealed_problem":
            try:
                revealed_problems = self.map_problems_to_test_revealed[concept_cluster_1]
                for problem in revealed_problems:
                    answer += [problem[0]]
                    answer_line.append(problem[2])
                    result_start_line.append(int(problem[3]))
                    result_start_token.append(int(problem[4]))
            except:
                answer = ["no"]

        elif answertype == "problems_investigated":
            problems = self.map_problems_to_test_investigated[Noteid][concept_cluster_1]
            #print(problems)
            for problem in problems:
                answer += [problem[0]]
                answer_line.append(problem[2])
                result_start_line.append(int(problem[3]))
                result_start_token.append(int(problem[4]))
 ##########################################################################################################################################
        elif answertype == "allergic_treatments":
            events = self.allergic_treatments[Noteid]

            for event in events:
                answer += [event[0]]
                answer_line.append(event[2])
                result_start_line.append(int(event[3]))
                result_start_token.append(int(event[4]))
        elif answertype == "treatments, status":
            events = self.treatments_status_to_problem[Noteid][concept_cluster_2]

            for temp in events:
                (event, status) = temp
                '''
                stemp = ""
                status = status.strip()
                if val2[0] in self.problem_status[Noteid]:
                    out = self.problem_status[Noteid][val2[0]]
                    if out[1] == question_line and out[2] == line_num:
                        stemp = out[0]
                        status += ", "+stemp
                '''
                #answer += [event[0] + " (" + status + ")"]
                answer += [event[0]]
                answer_line.append(event[2])
                result_start_line.append(int(event[3]))
                result_start_token.append(int(event[4]))
        elif answertype == "problems,status":
            try:
                events =  self.map_problems_to_treatment[Noteid][concept_cluster_1]
                #print(events)
                if "causes" in zip(*events)[1] and "improves" in zip(*events)[1]:
                    print(Noteid)
                for temp in events:
                    (event, status) = temp
                    answer += [event[0] + " (" + status + ")"]
                    #answer += [event[0]]
                    answer_line.append(event[2])
                    result_start_line.append(int(event[3]))
                    result_start_token.append(int(event[4]))
            except:
                caused_problems = self.problems_to_badtreatment[Noteid][concept_cluster_1]

                for event in  caused_problems:
                    answer += [event[0] + " (" + "caused" + ")"]
                    #answer += [event[0]]
                    answer_line.append(event[2])
                    result_start_line.append(int(event[3]))
                    result_start_token.append(int(event[4]))
        elif answertype == "no":
            answer = ["no"]
        elif answertype == "problems_check_conducted":
            events = self.map_problems_to_treatment[Noteid][concept_cluster_1]

            for temp in events:
                (event, status) = temp
                #answer += ["treatment:" + event[0]]
                answer += [event[0]]
                answer_line.append(event[2])
                result_start_line.append(int(event[3]))
                result_start_token.append(int(event[4]))
            try:
                treatment_entities_list = self.CoreferenceCluster_to_Entity_map["treatment"][concept_cluster_1]
                tests = self.map_problems_to_test_investigated[Noteid]
                for test in tests:
                    test_entities_list = self.CoreferenceCluster_to_Entity_map["test"][test]
                    new_set = set(test_entities_list).intersection(set(treatment_entities_list))
                    if len(new_set) != 0:
                        events = self.map_problems_to_test_investigated[Noteid][test]
                        for temp in events:
                            (event, status) = temp
                            #answer += ["tests:" + event[0]]
                            answer += [event[0]]
                            answer_line.append(event[2])
                            result_start_line.append(int(event[3]))
                            result_start_token.append(int(event[4]))
                        break
            except:
                pass
        elif answertype == "problems":

            if relate == "TrCP":
                pass
                #events = self.problems_to_badtreatment[Noteid][concept_cluster_1]

#                for event in events:
#                    answer += [event[0]]
#                    answer_line.append(event[2])
#                    result_start_line.append(int(event[3]))
#                    result_start_token.append(int(event[4]))
            else:

                events = self.map_problems_to_treatment[Noteid][concept_cluster_1]

                for temp in events:
                    (event, status) = temp
                    answer += [event[0]]
                    answer_line.append(event[2])
                    result_start_line.append(int(event[3]))
                    result_start_token.append(int(event[4]))

        elif answertype == "treatments":
            events = self.treatments_status_to_problem[Noteid][concept_cluster_2]

            for temp in events:
                (event, status) = temp
                answer += [event[0]]
                answer_line.append(event[2])
                result_start_line.append(int(event[3]))
                result_start_token.append(int(event[4]))
        elif answertype == "problem1, treatment":

            try:
                events = self.badtreatments_to_problem[Noteid][concept_cluster_2]

                for event in events:
                    answer += [event[0]]
                    answer_line.append(event[2])
                    result_start_line.append(int(event[3]))
                    result_start_token.append(int(event[4]))
            except:
                pass
            '''
            try:
                events = self.problems_to_symptom[Noteid][concept_cluster_2]

                for event in events:
                    answer += [event[0]]
                    answer_line.append(event[2])
                    result_start_line.append(int(event[3]))
                    result_start_token.append(int(event[4]))
            except:
                print(relate,answertype)
                pass
            '''
        elif answertype == "problem1":

            events = self.problems_to_symptom[Noteid][concept_cluster_2]

            for event in events:
                answer += [event[0]]
                answer_line.append(event[2])
                result_start_line.append(int(event[3]))
                result_start_token.append(int(event[4]))

        elif answertype == "symptoms":

            events = self.symptoms_to_problem[Noteid][concept_cluster_1]

            for event in events:
                answer += [event[0]]
                answer_line.append(event[2])
                result_start_line.append(int(event[3]))
                result_start_token.append(int(event[4]))
        elif answertype == "none":
            answer = []
        else:
            print(answertype)
            answer = []

        return [answer, answer_line,result_start_line,result_start_token]

    def MakeQuestion_new(self,types_to_replace,annotations,question_list,logical_form_template, Coreferences,Noteid):

        new_question_list = []
        question_start_line = []
        question_line = []

        rwords = list(types_to_replace)
        for idx in range(len(rwords)):
            question_start_line.append(int(annotations[rwords[idx]][2]))
            question_line.append(annotations[rwords[idx]][1])
            # print(annotations[rwords[idx]])
            (t1, valid_list) = self.CheckIfConceptValid(annotations[rwords[idx]], rwords[idx], Coreferences)
            if t1 == None:
                if valid_list != None:
                    replace_annoation = random.choice(valid_list)  ### can be improved forQL forms
                    #print(annotations[rwords[idx]])
                    rwords[idx] = replace_annoation

                    #print(Noteid)
                    #print(valid_list)
                    #print(replace_annoation)
                    #print(question_list)
                else:
                    return None
            else:
                rwords[idx] = t1

        for question in question_list:
            done = []
            idx = 0
            for types in list(types_to_replace):
                # temp = qwords
                index = question.find("|" + types + "|")
                if index == -1 and types not in done:
                    print(question, "|" + types + "|", done)
                question = question.replace("|" + types + "|", rwords[idx])
                done.append(types)
                idx += 1

            new_question_list.append(question)


        idx = 0
        done = []
        for types in list(types_to_replace):
            # temp = qwords
            index = logical_form_template.find("|" + types + "|")
            # print(done, types,idx)
            if index == -1 and types not in done:
                print(logical_form_template, "|" + types + "|", done, types)
            done.append(types)
            logical_form_template = logical_form_template.replace("|" + types + "|", rwords[idx])
            idx += 1

        return [new_question_list,logical_form_template,question_line,question_start_line]

    def MakeQuestion(self,dup_rwords,annotations,qwords,Coreferences):

        if len(set(dup_rwords)) != len(dup_rwords):
            pass
        else:
            rwords = list(dup_rwords)
            question_start_line= []
            question_line = []

            for idx in range(len(rwords)):
                question_start_line.append(int(annotations[rwords[idx]][2]))
                question_line.append(annotations[rwords[idx]][1])
                #print(annotations[rwords[idx]])
                (t1,valid_list) = self.CheckIfConceptValid(annotations[rwords[idx]],rwords[idx], Coreferences)
                if t1 == None:
                    if valid_list != None:
                        replace_annoation = random.choice(valid_list)
                        rwords[idx] = replace_annoation
                        print()
                    else:
                        return None
                else:
                    rwords[idx] = t1

            temp = qwords
            temp[1:len(qwords):2] = rwords
            temp = [word for word in temp if word != ""]
            question = " ".join(temp)  ### Make Question ###

        return [question,question_line,question_start_line]

    def HandleAssertionQA(self,Noteid,dup_rwords, question_list_templates, logical_form_template,Coreferences, answertype):
        types_to_replace = list(dup_rwords)
        answer = []
        result_num = []
        answer_line = []
        result_token = []
        answer_out = []
        if len(dup_rwords) != 0:
            for problem in self.problem_status[Noteid]:
                logical_form = logical_form_template
                status = self.problem_status[Noteid][problem]
                rwords = list(dup_rwords)
                flag = 0
                for idx in range(len(rwords)):
                    #print(problem)
                    (t1,valid_list) = self.CheckIfConceptValid((problem,status[0][1],status[0][2],status[0][3]),rwords[idx], Coreferences )
                    if t1 == None:
                        flag =1
                    else:
                        rwords[idx] = t1

                if flag == 1:
                    continue

                new_question_list = []

                for question in question_list_templates:
                    done = []
                    idx = 0
                    for types in list(types_to_replace):
                        index = question.find("|" + types + "|")
                        if index == -1 and types not in done:
                            print(question, "|" + types + "|", done)
                        question = question.replace("|" + types + "|", rwords[idx])
                        done.append(types)
                        idx += 1
                    #if question not in new_question_list:
                    new_question_list.append(question)

                idx = 0
                done = []
                for types in list(types_to_replace):
                    index = logical_form.find("|" + types + "|")
                    if index == -1 and types not in done:
                        print(logical_form, "|" + types + "|", done, types)
                    done.append(types)
                    logical_form = logical_form.replace("|" + types + "|", rwords[idx])
                    idx += 1

                for val in status:
                    #print(val[0])
                    answer.append(val[0])
                    answer_line.append(val[1])
                    result_num.append(int(val[2]))
                    result_token.append(int(val[3]))

                if answertype == "none":

                    question_templates = question_list_templates
                    unique_tup = list(set(zip(new_question_list, question_templates)))
                    for qidx in range(len(unique_tup)):

                        #q_id = self.question_id[unique_tup[qidx][1]]
                        #l_id = self.logicalform_id[logical_form_template]
                        self.filewriter_forlform.writerow([unique_tup[qidx][0]] + [logical_form] + [unique_tup[qidx][1]] + [logical_form_template])


                else:
                    if len(answer) != 0:
                        perms = list(itertools.product(result_num, result_num))
                        diffs = [abs(val1 - val2) for (val1, val2) in perms]
                        difference = max(diffs)
                        question_templates = question_list_templates
                        if len(new_question_list) != len(question_templates):
                            print(new_question_list)
                            print(question_templates)

                        unique_tup = list(set(zip(new_question_list, question_templates)))
                        tuple_id = []
                        for qidx in range(len(unique_tup)):
                            #q_id = self.question_id[unique_tup[qidx][1]]
                            #l_id = self.logicalform_id[logical_form_template]
                            self.filewriter_forlform.writerow(
                                [unique_tup[qidx][0]] + [logical_form] + [unique_tup[qidx][1]] + [
                                    logical_form_template])
                            #self.filewriter_forlform.writerow([unique_tup[qidx][0]] + [logical_form] + [q_id] + [l_id])
                            #tuple_id.append([q_id,unique_tup[qidx][0]])

                        Note_val = "#".join(answer_line)
                        new_question_list = set(new_question_list)
                        if new_question_list not in self.unique_questions:
                            self.filewriter.writerow(
                                ["##".join(new_question_list)] + [logical_form] + [",".join(answer)] + [Note_val] + [
                                    Noteid + "_RelationsChallenge"] + [
                                    difference])
                            self.unique_questions.append(set(new_question_list))

                            ans_list = []
                            for idx in range(len(answer)):
                                ## evidence per answer ##
                                print(answer[idx])
                                val = {"answer_start": [result_num[idx], result_token[idx]], "text": answer[idx],
                                                 "evidence": "",
                                                 "evidence_start": ""}
                                if val not in ans_list:
                                    ans_list.append(val)

                                # evidence will have q_line_answer_line
                            answer_temp = {"answers": ans_list, "id": [zip(question_templates,new_question_list),logical_form_template], "question": list(set(new_question_list))}
                            answer_out.append(answer_temp)


                    else:

                        question_templates = question_list_templates
                        unique_tup = list(set(zip(new_question_list, question_templates)))

                        for qidx in range(len(unique_tup)):
                            q_id = self.question_id[unique_tup[qidx][1]]
                            l_id = self.logicalform_id[logical_form_template]
                            self.filewriter_forlform.writerow(
                                [unique_tup[qidx][0]] + [logical_form] + [unique_tup[qidx][1]] + [
                                    logical_form_template])

        return answer_out

    def MakeLabTestQA(self, question, logical_form, types_to_replace, answertype, helper,Relations,Noteid,Coreferences):

        question = question.replace("|problem| or |problem|","|problem|")
        orginal_question = question
        logical_form_template = logical_form
        answer_out = []
        #qwords = question.split("|")
        #dup_rwords = qwords[1:len(qwords):2] ## words in question to replace - create a orginal cop ##

        for relate in helper:
            if relate == "ast":
                questions_list = question.strip().split("##")
                self.HandleAssertionQA(Noteid, types_to_replace, questions_list, logical_form_template,Coreferences, answertype)

            else:
                try:
                    relevant_relations = Relations[relate] ## Get relations which satisy the relate criteria
                    #print(relate)
                except:
                    continue

                #print(relate)
                for val1,val2 in relevant_relations:

                    annotations = {val1[1]:(val1[0],val1[2],val1[3],val1[4]),
                                   val2[1]:(val2[0],val2[2],val2[3],val2[4])}

                    #out = self.MakeQuestion(dup_rwords, annotations, qwords, Coreferences)
                    if len(types_to_replace) != 0:
                        questions_list = question.strip().split("##")
                        out = self.MakeQuestion_new(types_to_replace, annotations, questions_list, logical_form_template, Coreferences,Noteid)
                        #print(out)
                        if out == None:
                            continue
                        else:
                            [question_list, logical_form, question_line, question_start_line] = out
                    else:
                        [question_list, logical_form, question_line, question_start_line] = [question.split("##"), logical_form_template, "", ""]

                        #print(question)



                    ##### Make answers for the succesful questions ####

                    [answer, answer_line,answer_start_line,answer_start_token] = self.AnswerSubFunction(answertype, val1, val2, Noteid, relate)
                    #print(answer,answer_line)
                    #print(answer)
                    if len(answer) != 0:
                        result_num = answer_start_line + question_start_line
                        perms = list(itertools.product(result_num, result_num)) ## find different pairs of numbers ##
                        diffs = [abs(val1 - val2) for (val1, val2) in perms]
                        difference = max(diffs)

                        paraphrase_questions = set(question_list)
                        tuple_id = []
                        question_templates = orginal_question.split("##")
                        if len(question_list) != len(question_templates):
                            print(question_list)
                            print(question_templates)
                        unique_tup = list(set(zip(question_list, question_templates)))
                        for qidx in range(len(unique_tup)):
                            #q_id = self.question_id[unique_tup[qidx][1]]
                            #l_id = self.logicalform_id[logical_form_template]
                            self.filewriter_forlform.writerow(
                                [unique_tup[qidx][0]] + [logical_form] + [unique_tup[qidx][1]] + [
                                    logical_form_template])
                            #tuple_id.append([q_id,unique_tup[qidx][0]])
                        if paraphrase_questions not in self.unique_questions:

                            self.unique_questions.append(paraphrase_questions)

                            ans_list = []
                            for idx in range(len(answer)):
                                ## evidence per answer ##
                                evidence_answer = []
                                evidence_start = []
                                evidence_temp_line = question_line + answer_line
                                evidence_temp_start = question_start_line + answer_start_line
                                for pdx in range(len(evidence_temp_line)):
                                    if evidence_temp_line[pdx] not in evidence_answer:
                                        evidence_answer.append(evidence_temp_line[pdx])
                                        evidence_start.append(evidence_temp_start[pdx])
                                if answer[idx] == "yes" or answer[idx] == "no":
                                    start_line = ""
                                    start_token = ""
                                else:
                                    start_line = answer_start_line[idx]
                                    start_token = answer_start_token[idx]

                                val = {"answer_start": [start_line,start_token], "text": answer[idx], "evidence": evidence_answer, "evidence_start": evidence_start} #evidence will have q_line_answer_line
                                if val not in ans_list:
                                    ans_list.append(val)
                            answer_temp = {"answers": ans_list, "id": [zip(question_list, question_templates),logical_form_template], "question":list(paraphrase_questions)}
                            answer_out.append(answer_temp)

                            Note_val = "#".join(list(set(evidence_temp_line)))

                            self.filewriter.writerow(["##".join(paraphrase_questions)] + [logical_form] +[",".join(answer)] + [Note_val] + [Noteid + "_RelationsChallenge"] + [difference])


                    else:
                        ### Writing only question - logical form ##

                        question_templates = orginal_question.split("##")
                        unique_tup = list(set(zip(question_list, question_templates)))
                        for qidx in range(len(unique_tup)):
                            q_id = self.question_id[unique_tup[qidx][1]]
                            l_id = self.logicalform_id[logical_form_template]
                            self.filewriter_forlform.writerow(
                                [unique_tup[qidx][0]] + [logical_form] + [unique_tup[qidx][1]] + [
                                    logical_form_template])
        return answer_out

    def checking_for_errors(self, question_list,logical_form_template):

        question_list = question_list.split("##")
        qwords_list = []
        dup_rwords_list = []
        unique_templates = []

        #logical_form_template = logical_form_template.replace("|treatment|", "|medication|").strip()

        for question in question_list:
            if question.strip() == "":
                continue
            #question = question.replace("|medication| or |medication|", "|medication|")
            #question = question.replace("|treatment|", "|medication|").strip()
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

    def ReadTemplates(self):

        self.question_id = {}
        self.logicalform_id = {}
        self.logical_out = []

        ########################################## Read unique ids ##############################################
        csvreader = (csv.reader(open("/home/anusri/Desktop/codes_submission/dataset_indexing/questions_index.csv")))
        for listi in csvreader:
            self.question_id[listi[0]] = listi[1]

        csvreader = (csv.reader(open("/home/anusri/Desktop/codes_submission/dataset_indexing/logical_forms_index.csv")))
        for listi in csvreader:
            self.logicalform_id[listi[0]] = listi[1]

        ofile = open("final-question-answers.csv", "w")
        self.filewriter = csv.writer(ofile, delimiter="\t")
        self.filewriter.writerow(["Question", "Logical Form",  "Answer", "Answer line in note", "Note ID", "Difference in QA lines"])

        ### File to write Question-Logical Forms ##

        ofile = open("/home/anusri/Desktop/IBM/Answers-old/combine/ql_dataset/relations.csv", "w")
        self.filewriter_forlform = csv.writer(ofile, delimiter="\t")
        self.filewriter_forlform.writerow(["Question", "Logical Form"])

        self.relations_out =  {"paragraphs": [], "title": "relations"}

        file = open("templates-all.csv")
        filereader = list(csv.reader(file))

        med_lines = []
        for line in filereader[1:]:
            if line[0] != "relations":
                continue
            med_lines.append(line)

        total_questions = 0
        for Noteid in self.RelationsPerNote:
            [Relations, PatientNote, Coreferences] = self.RelationsPerNote[Noteid]
            out_patient = {"note_id": Noteid, "context": PatientNote, "qas": []}
            self.unique_questions = []


            for line in med_lines:
                #print(line)
                question = line[2].strip()
                if question == "":
                    continue
                logical_form = line[3].strip()
                question = question.replace("\t", "")
                logical_form = logical_form.replace("\t", "")
                answertype = line[5].strip()
                helper = line[4].split(",")
                helper = [type.strip() for type in helper]
                #dataset = line[3].strip()
                # print(dataset)
                question = question.replace("\t", "")
                logical_form = logical_form.replace("\t", "")
                if question.strip() == "":
                    continue

                types_to_replace = self.checking_for_errors(question,logical_form)
                if len(types_to_replace) != 0:
                    types_to_replace = list(types_to_replace[0])
                else:
                    types_to_replace = []
                answer_out = self.MakeLabTestQA(question, logical_form, types_to_replace , answertype, helper,Relations,Noteid,Coreferences)
                out_patient["qas"].extend(answer_out)
            total_questions += len(self.unique_questions)
            self.relations_out["paragraphs"].append(out_patient)
        json_out= "relations.json"
        print(total_questions)
        with open(json_out, 'w') as outfile:
            json.dump(self.relations_out, outfile, ensure_ascii=False)
        print(self.count_corefs)
        print(self.resolved_corefs)

GenerateRelationsQuestions()