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

Electronic Medical Records (EMRs) are a longitudinal record of a patient's health information in the form of unstructured clinical notes (progress notes, discharge summaries etc.) and structured vocabularies. Physicians frequently seek answers to questions from unstructured EMRs to support clinical decision-making. 
In this work, we address the lack of any publicly available EMR QA corpus by creating a large-scale dataset, emrQA, using a novel generation framework that allows for minimal expert involvement and re-purposes existing annotations available for other clinical NLP tasks (here the i2b2 challenge datasets).

This repository includes code for generating and analyzing the emrQA dataset as described in the paper. Note that this work is a refactored and extended version of the orginal dataset described in the paper.

Some statistics of the generated data:

| Datasets | QA pairs | QL pairs | #Clinical Notes | 
| :------: | :------: | :------: | :----: | 
| i2b2 relations (concepts, relations)| 141,243 | 245,486 | 425 |
| i2b2 relations (assertions) | 1,268,029 | 816,224  | 425  |
| i2b2 medications | 255,908 | 198,739 | 261 |
| i2b2 heart disease risk | 30,731 | 36,746 | 119 |
| i2b2 smoking | 4,518 | 6 | 502 |
| i2b2 obesity | 55,346 | 280 | 1,118 |
| **emrQA (total)** | **479,304** | **1,265,283** | **3,431** |


## Requirements

The data can be generated using the NLP Datasets from the [i2b2 Challenges][i2b2-datasets], which are accessible by everyone subject to a license agreement.  
In our work, we have currently made use of all the challenge datasets except the 2012 Temporal Relations Challenge. Our future extensions of the dataset to include this challenge dataset  will soon be available. 

The following scrpits require Python 2.7. 
Run the following commands to clone the repository and install emrQA:

```bash
git clone https://github.com/emrqa/emrQA.git
cd emrQA; pip install -r requirements.txt
```
To generate emrQA, first [download](#downloading-i2b2) the i2b2 challenge datasets. 

**Important: Navigate through all the files in the generation folder and set the i2b2 folder paths and the output folder paths as indicated in the script.** 

## emrQA Generation

 Run `python main.py` to generate the question-answers pairs in a json format and the question-logical form pairs in a csv format.  A thorough discussion of the output format of these files is presented below.

#### Question-Answer Format


#### Squad Format

The `reader` directory scripts expect the datasets as a `.json` file where the data is arranged like SQuAD:

```
file.json
├── "data"
│   └── [i]
│       ├── "paragraphs"
│       │   └── [j]
│       │       ├── "context": "paragraph text"
│       │       └── "qas"
│       │           └── [k]
│       │               ├── "answers"
│       │               │   └── [l]
│       │               │       ├── "answer_start": N
│       │               │       └── "text": "answer"
│       │               ├── "id": "<uuid>"
│       │               └── "question": "paragraph question?"
│       └── "title": "document id"
└── "version": 1.1
```

#### Question-logical form



## emrQA Analysis

## Baselines

[i2b2-datasets]: https://www.i2b2.org/NLP/DataSets/
[anusri-home]: https://www.linkedin.com/in/anusri-pampari-594bb5126/
