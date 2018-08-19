# emrQA: A Large Corpus for Question Answering on Electronic Medical Records
(under construction)

- This repo contains code for the paper
Anusri Pampari, Preethi Raghavan, Jennifer Liang and Jian Peng,  
emrQA: A Large Corpus for Question Answering on Electronic Medical Records,  
In Conference on Empirical Methods in Natural Language Processing (EMNLP) 2018, Brussels, Belgium.
- Please contact [Anusri Pampari][anusri-home] (\<last-name\>2@illinois.edu)  for suggestions and comments.

## Quick Links

- [About](#question-answering-on-electronic-medical-records)
- [Requirements](#requirements)
- [Data Generation](#emrqa-generation)
- [Data Analysis](#emrqa-analysis)
- [Baselines](#baselines)

##  Question Answering on Electronic Medical Records

Electronic Medical Records (EMRs) are a longitudinal record of a patient's health information in the form of unstructured clinical notes (progress notes, discharge summaries etc.) and structured vocabularies. Physicians frequently seek answers to questions from unstructured clinical notes in EMRs to support clinical decision-making.

In this work, we address the lack of any publicly available EMR Question Answering (QA) corpus by creating a large-scale dataset, emrQA, using a novel semi-automated generation framework that allows for minimal expert involvement and re-purposes existing annotations available for other clinical NLP tasks. To briefly summarize the  generation process: (1) we collect questions from experts (2) convert them to templates by replacing entities with placeholders (3) expert annotate the templates with logical form templates and then (4) use annotations from existing NLP tasks (based on information in logical forms) to populate placeholders in templates and generate answers. For our purpose, we use existing  NLP task annotations  from the [i2b2 Challenge datasets][i2b2-datasets]. We refer the reader to the paper to get a more detailed overview of the generation framework.

This repository includes the question and logical form templates provided by our experts and the code for generating the emrQA dataset from these templates and the i2b2 challenge datasets. Note that this work is a refactored and extended version of the orginal dataset described in the paper.

Some statistics of the current version of the generated data:

| Datasets | QA pairs | QL pairs | #Clinical Notes | 
| :------: | :------: | :------: | :----: | 
| i2b2 relations (concepts, relations)| 141,243 | 245,486 | 425 |
| i2b2 relations (assertions) | 1,268,029 | 816,224  | 425  |
| i2b2 medications | 255,908 | 198,739 | 261 |
| i2b2 heart disease risk | 30,731 | 36,746 | 119 |
| i2b2 smoking | 4,518 | 6 | 502 |
| i2b2 obesity | 3,72,205) | 352 | 1,118 |
| **emrQA (total)** | **2,072,635** | **1,296,091** | **2,425** |

**UPDATES:**
```
27th August 2018: Extended the i2b2 obesity question-answer pairs to obesity comorbidities. 
20th August 2018: Added QA pairs generated from i2b2 relations (assertions). 
27th Jun 2018: Dataset as decribed in the paper. 
```

## Requirements

To generate emrQA, first download the NLP Datasets from the [i2b2 Challenges][i2b2-datasets] accessible by everyone subject to a license agreement. You will need to download and extract all the datasets corresponding to given a challenge (e.g 2009 Medications Challenge) at a specfic folder location. Once completed, update the path location in `main.py`.  In our work, we have currently made use of all the challenge datasets except the 2012 Temporal Relations Challenge. Our future extensions of the dataset to include this challenge dataset  will soon be available. 

The generation scrpits in the repo require Python 2.7. Run the following commands to clone the repository and install the the requirements for emrQA:

```bash
git clone https://github.com/emrqa/emrQA.git
cd emrQA; pip install -r requirements.txt
```

## emrQA Generation

Run `python main.py` to generate the question-answers pairs in a json format and the question-logical form pairs in a csv format. By default the script creates an `output\` directory and stores all the generated files. You can access the combined question-answer dataset as `data.json` and  question-logical form data as `data.csv`. You can also access the intermediate datasets generated per every i2b2 challenge (e.g. `medications-qa.json` and `medication-ql.csv` generated from the 2009 medications challenge annotations). 

A thorough discussion of the output format of these files is presented below.

#### Question-Answer (JSON) Format

The json files in `output\` directory have the following format:

```
data.json
├── "data"
   └── [i]
       ├── "paragraphs"
       │   └── [j]
       │       ├── "note_id": "clinical note id"
       │       ├── "context": "clinical note text"
       │       └── "qas"
       │           └── [k]
       │               ├── "answers"
       │               │   └── [l]
       │               │       ├── "answer_start"
       │               │       │             └── [m]
       │               │       │                 ├── "start_line" : N
       │               │       │                 └── "start_token": N
       │               │       │ 
       │               │       ├──"text": "answer as a concept"
       │               │       │
       │               │       ├──"evidence": "answer line"
       │               │       │     
       │               │       └── "evidence_start": "line start" 
       │               │ 
       │               ├── "id": "<uuid>"              |
       │               │ 
       │               │   
       │               └── "question": "paragraph question?"
       │ 
       └── "title": "i2b2 challenge name"

```

Scripts provided in `generation/combine_data/squad_format.py` convert the given format into squad format where line in the clinical note which holds the answer is used as answer text as described in the paper.
`
#### Question-Logical Form (CSV) Format



## emrQA Analysis

## Baselines

[i2b2-datasets]: https://www.i2b2.org/NLP/DataSets/
[anusri-home]: https://www.linkedin.com/in/anusri-pampari-594bb5126/
