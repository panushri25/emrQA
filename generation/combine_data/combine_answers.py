import json


medications = json.load(open("/home/anusri/Desktop/codes_submission/Answers/medication/medications-QA-updated.json"))
smoking = json.load(open("/home/anusri/Desktop/codes_submission/Answers/smoking/smoking.json"))
obesity = json.load(open("/home/anusri/Desktop/codes_submission/Answers/obesity/obesity.json"))
relations = json.load(open("/home/anusri/Desktop/codes_submission/Answers/relations/relations.json"), encoding="latin-1")
risk = json.load(open("/home/anusri/Desktop/codes_submission/Answers/longitudnal-test/risk-QA.json"))
data = [medications, smoking, obesity, relations, risk]

json_out = "data.json"
with open(json_out, 'w') as outfile:
    json.dump(data, outfile,  encoding="latin-1")

''

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