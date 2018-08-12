import json
import random

random.seed(1213)
medications = json.load(open("/home/anusri/Desktop/codes_submission/Answers/medication/medications-QA-updated.json"))
relations = json.load(open("/home/anusri/Desktop/codes_submission/Answers/relations/relations.json"), encoding="latin-1")
risk = json.load(open("/home/anusri/Desktop/codes_submission/Answers/longitudnal-test/risk-QA.json"))

use_evidence_model = "True"
descriptive_check = ["yes",'no',"yes/no","(improves)","(caused)" , "(worsens)", "(not known status)"]
span = 20
evidences_percent = 0.0
total_questions = 0.0
length_evidence = 0.0
sample = 0
sample_200 = []
train_paras = []
test_paras = []
map_id_to_question = {}
idx = 0
datasets = [medications, relations, risk]
#datasets = [risk]
max_ans_length = 0
temp = []
for dataset in datasets:

    medications = dataset
    for note in medications["paragraphs"]:

        if medications["title"] == "risk-dataset":

            text = "\n".join(note["context"])
            #print(len(text))
            para = {"context": text, "qas": []}
            #print(para["context"])
            for questions in note["qas"]:
                idx += 1  ## Take care of this
                question = {"question": questions["question"][random.randrange(len(questions["question"]))], "answers": [], "id": idx}
                #print(questions["id"])
                short_answers = []
            #print(questions["question"])
                if use_evidence_model == "True":
                    for answer in questions["answers"]:


                        val = {"text": answer["evidence"], "answer_start": answer["answer_start"][0]}
                        short_answers.append([answer["text"], val["answer_start"],
                                              val["answer_start"] + len(val["text"]), text[val["answer_start"]-span:val["answer_start"] + len(val["text"])+span]])
                        #print(type(answer["text"]))
                        #print(val["text"])
                        #print(text[val["answer_start"]:val["answer_start"]+len(val["text"])])
                        #print("\n")
                        if val not in question["answers"]:
                            question["answers"].append(val) ## the answer line

                else:
                    for answer in questions["answers"]:
                        question["answers"].append({"text": answer["text"], "answer_start": answer["answer_start"][1]-1}) ## the answer text
                        if len(question["answers"][-1]["text"].strip().split()) > max_ans_length:
                            max_ans_length = len(question["answers"][-1]["text"].strip().split())
                #if question in para["qas"]:
                    #print(question)
                map_id_to_question[idx] = [questions["id"],short_answers]
                para["qas"].append(question)
                #if len(sample_200) <= 200:


                if len(question["answers"]) > 1:
                    evidences_percent += 1
                length_evidence += len(question["answers"])

        else:

            text = "".join(note["context"])
            line_lenth = [len(line) for line in note["context"]]
            para = {"context": text, "qas": []}

            for questions in note["qas"]:
                idx += 1
                #print(questions["id"])
                question = {"question": questions["question"][random.randrange(len(questions["question"]))], "answers": [], "id": idx}
                short_answers = []

                for answer in questions["answers"]:

                    if use_evidence_model == "True":
                        try: ## evidence and evidence start token
                            val = {"text":note["context"][answer["answer_start"][0]-1],"answer_start":sum(line_lenth[answer[:answer["answer_start"][0]-1]])}
                            print(val["text"])
                            #print(answer["text"])
                            #short_answers.append(answer["text"])
                            short_answers.append([answer["text"], val["answer_start"],
                                                  val["answer_start"] + len(val["text"]), text[
                                                                                          val["answer_start"] - span:val[
                                                                                                                      "answer_start"] + len(
                                                                                              val["text"]) + span]])
                            if val not in question["answers"]:
                                question["answers"].append(val)
                            if len(question["answers"][-1]["text"].strip().split()) > max_ans_length:
                                max_ans_length = len(question["answers"][-1]["text"].strip().split())

                        except:
                            unique = []
                            print(answer["text"])
                            #short_answers.append(answer["text"])
                            #short_answers.append(answer["text"], val["answer_start"],
                                                 #val["answer_start"] + len(val["text"]))
                            for num in list(map(lambda x: x - 1, answer["evidence_start"])):
                                if num not in unique:
                                    unique.append(num)
                                    val = {"text":note["context"][num],"answer_start":sum(line_lenth[:num])}
                                    short_answers.append([answer["text"], val["answer_start"],
                                                          val["answer_start"] + len(val["text"]), text[val[
                                                                                                           "answer_start"] - span:
                                        val["answer_start"] + len(val["text"]) + span]])
                                    if type(note["context"][num]) == 'unicode':
                                        print(type(note["context"][num]))
                                    if val not in question["answers"]:
                                        question["answers"].append(val)
                                    if len(question["answers"][-1]["text"].strip().split()) > max_ans_length:
                                        max_ans_length = len(question["answers"][-1]["text"].strip().split())


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
                                    if len(question["answers"][-1]["text"].strip().split()) > max_ans_length:
                                        max_ans_length = len(question["answers"][-1]["text"].strip().split())

                if question in para["qas"]:
                    print(question)
                map_id_to_question[idx] = [questions["id"],short_answers]
                para["qas"].append(question)
                if len(question["answers"]) > 1:
                    evidences_percent += 1
                length_evidence += len(question["answers"])
        if random.randint(1,100) < 20:
            test_paras.append(para)

        else:
            train_paras.append(para)

        if random.randint(1,100) < 10:
            sample_200.append(para)



print(max_ans_length)
print(evidences_percent*100/idx)
print(length_evidence/idx)
outfile_dict = open("/home/anusri/Desktop/codes_submission/DrQA-predictions/dict.json","w")
json.dump(map_id_to_question,outfile_dict)

medications_train = {"paragraphs": train_paras, "title": "medications"}
medications_test = {"paragraphs": test_paras, "title": "medications"}

data = {}
data["data"] = [medications_train]
with open("med-train.json", 'w') as outfile:
    json.dump(data, outfile,  encoding="utf-8")

#print(data)
data = {}
data["data"] = [medications_test]
with open("med-test.json", 'w') as outfile:
    json.dump(data, outfile,  encoding="utf-8")

with open("sample_2.json", 'w') as outfile:
    json.dump(sample_200, outfile,  encoding="utf-8")

print(len(sample_200))