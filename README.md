# emrQA: A Large Corpus for Question Answering on Electronic Medical Records
                  The page and codes are still under construction. Please check back in December. 
                  We are excited to announce that this data will now be hosted directly under the 
                  i2b2 license !! So you can directly download the dataset from the i2b2 website 
                  instead of generating it from the scripts. We are setting this up for you, kindly
                  stay tuned. Believe me it takes some iterations to draw consensus on a usable format. 
                  But we are almost there. :) 

- This repo contains code for the paper
Anusri Pampari, Preethi Raghavan, Jennifer Liang and Jian Peng,  
[emrQA: A Large Corpus for Question Answering on Electronic Medical Records][paper-link],  
In Conference on Empirical Methods in Natural Language Processing (EMNLP) 2018, Brussels, Belgium.
- General queries/thoughts have been addressed in the discussion section below.
- Please contact [Anusri Pampari][anusri-home] (\<last-name\>2@illinois.edu)  for suggestions and comments.

## Quick Links

- [About](#question-answering-on-electronic-medical-records)
- [Requirements](#requirements)
- [Data Generation](#emrqa-generation)
- [Data Analysis](#emrqa-analysis)
- [Baselines](#baselines)
- [Discussion](#discussion)

##  Question Answering on Electronic Medical Records (EMR)

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
| i2b2 obesity | 372,205 | 352 | 1,118 |
| **emrQA (total)** | **2,072,635** | **1,296,091** | **2,425** |

**UPDATES:**
```
29th Novemebr 2018: We are excited to announce that this data will now be hosted directly under the i2b2 license !! So you can directly download the dataset from the i2b2 website instead of generating it from the scripts. We are setting this up, kindly stay tuned. Expected date of setup: Mid december !
27th August 2018: Extended the i2b2 obesity question-answer pairs to obesity comorbidities. 
20th August 2018: Added QA pairs generated from i2b2 relations (assertions). 
27th Jun 2018: Dataset as decribed in the paper. 
```

## Requirements

To generate emrQA, first download the NLP Datasets from the [i2b2 Challenges][i2b2-datasets] accessible by everyone subject to a license agreement. You will need to download and extract all the datasets corresponding to given a challenge (e.g 2009 Medications Challenge) at a specfic folder location (the contains of the folder location are eloborated below in the discussion section for your reference). Once completed, update the path location in `main.py`.  In our work, we have currently made use of all the challenge datasets except the 2012 Temporal Relations Challenge. Our future extensions of the dataset to include this challenge dataset  will soon be available. 

The generation scrpits in the repo require Python 2.7. Run the following commands to clone the repository and install the requirements for emrQA:

```bash
git clone https://github.com/emrqa/emrQA.git
cd emrQA; pip install -r requirements.txt
```


## emrQA Generation

Run `python main.py` to generate the question-answers pairs in a json format and the question-logical form pairs in a csv format. The input to these scripts is a csv file (`templates-all.csv`) located in `templates\` directory. By default the script creates an `output\` directory to store all the generated files. You can access the combined question-answer dataset as `data.json` and  question-logical form data as `data-ql.csv`. You can also access the intermediate datasets generated per every i2b2 challenge (e.g. `medications-qa.json` and `medication-ql.csv` generated from the 2009 medications challenge annotations). 


A thorough discussion of the output format of these files is presented below.

#### Input: Templates (CSV) Format

Each row in the csv file has the following format:

```
"dataset"  \t  "question templates"  \t  "logical form templates"  \t  "answer type" \t "sub-answer-type"
```

A brief explantion how following fields are used in `main.py`,

```
dataset: The i2b2 challenge dataset annotations to be used for the templates in that row. This field should be one of the following values, medications, relations, risk, smoking or obesity.
 
question templates: All the question paraphrase templates are provided as a string seperated by ##.

logical form templates: The logical form template expert annotated for the question templates.

answer type: The output type

sub-answer-type:
```
#### Output: Question-Answer (JSON) Format

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
       │               │       │                 ├── integer (line number in clinical note to find the answer entity)
       │               │       │                 └── integer (token position in line to find the answer entity)
       │               │       │ 
       │               │       ├──"text": "answer entity"
       │               │       │
       │               │       ├──"evidence": "evidence line to support the answer entity "
       │               │       │
       │               │       └── "evidence_start": integer (line number in clinical note to find the evidence line) 
       │               │ 
       │               ├── "id" 
       │               │    └─ [n]
       │               │       ├──[o] 
       │               │       │  ├── "paraphrase question"
       │               │       │  └── "paraphrase question-template"
       │               │       │ 
       │               │       └── "logical-form-template"
       │               │ 
       │               └── "question"
       │                    └──[p]
       │                       └──"paraphrase question"
       │ 
       └── "title": "i2b2 challenge name"

```

To generate the data in the SQUAD format (input format for the [DrQA][drqa] baseline in the paper) run,

```bash
python generation/combine_data/squad_format.py --output_dir output/
```
#### Output: Question-Logical Form (CSV) Format

Each row in the csv file has the following format,

```
"question"  \t  "logical-form"  \t  "question-template"  \t  "logical-form-template"
```

## emrQA Analysis

#### Basic statistics

To run the scripts that finds the basic statistics of the dataset, such as average question length etc, do.

```bash
python evaluation/basic-stats.py --output_dir output/
```

#### Paraphrase analysis

To run the scripts that finds (1) the average number of paraphrase templates (2) Jaccard and BLEU Score of parapharase templates

```bash
python evaluation/paraphrase-analysis --templates_dir templates/
```

#### Logical form template analysis

To run the scripts that filter logical form templates with specific properties,

```bash
python evaluation/template-analysis.py --templates_dir templates/
```
## Discussion

##### i2b2 datasets directory structure

The i2b2 challenge datasets used to generate the current emrQA version was downloaded in August, 2017. Since the structure of these i2b2 datasets itself could change, we thought it might be useful to discuss our i2b2  repository structure. 

The scipts in this repository are used to parse the following i2b2 directory structure,

```

├── "i2b2 (download the datsets in single folder)"
       ├── "smoking" (download 2006 smoking challenge datasets here)
       │       │ 
       │       ├── "smokers_surrogate_test_all_groundtruth_version2.xml"
       │       └── "smokers_surrogate_train_all_version2.xml"
       │ 
       ├── "obesity" (download 2008 obesity challenge datasets here)
       │       │ 
       │       ├── "obesity_standoff_annotations_test.xml"
       │       ├── "obesity_standoff_annotations_training.xml"
       │       ├── "obesity_patient_records_test.xml"
       │       └── "obesity_patient_records_training.xml"
       │       
       ├── "medication" (download 2009 medication challenge datasets here)
       │       │ 
       │       ├── "train.test.released.8.17.09/" (folder containing all clinical notes)
       │       ├── "annotations_ground_truth/converted.noduplicates.sorted/" (folder path with medication annotations
       │       └── "training.ground.truth/" (folder path with medication annotations)
       │       
       ├── "relations" (download 2010 relation challenge datasets here)
       │       │ 
       │       ├── "concept_assertion_relation_training_data/partners/txt/" (folder path containing clinical notes)
       │       ├── "concept_assertion_relation_training_data/beth/txt/" (folder path containing clinical notes)
       │       ├── "test_data/txt/" (folder path containing clinical notes)
       │       ├── "concept_assertion_relation_training_data/partners/rel/" (folder path with relation annotations)
       │       ├── "concept_assertion_relation_training_data/beth/rel/" (folder path with relation annotations)
       │       ├── "test_data/rel/" (folder path with relation annotations)
       │       ├── "concept_assertion_relation_training_data/partners/ast/" (folder path with assertion annotations)
       │       ├── "concept_assertion_relation_training_data/beth/ast/" (folder path with assertion annotations)
       │       └── "test_data/ast/" (folder path with assertion annotations)
       │       
       ├── "coreference" (download 2011 coreference challenge datasets here)
       │       │ 
       │       ├── "Beth_Train"  (folder with the following subfolders "chains", "concepts", "docs", "pairs")
       │       ├── "Partners_Train" (folder with the following subfolders "chains", "concepts", "docs", "pairs")
       │       └── "i2b2_Test" (folder with "i2b2_Beth_Test" and "i2b2_Partners_Test" containing "chains" and "concepts" subfolders)
       │       
       └── "heart-disease-risk" (download 2014 heart disease risk factprs challenge datasets here)
               │ 
               └── "training-RiskFactors-Complete-Set1/" (folder path with files containing annotations and clinical notes)
       

``` 


##### The answer evidence is not a complete sentence. Why ?

The annotations used from the i2b2 datasets (except heart disease risk) have both token span and line number annotations. Clinical notes in these datasets are split at the newline character and assigned a line number. Our evidence line is simply the line in the clinical note corresponsing to a particular i2b2 annotation's line number. Since i2b2 heart disease risk annotations has only token span annotations without any  line number annotations, we break the clinical notes at newline character and the line containing the token span is considered as our evidence line. 
 
- When clinical notes are split at newline character, start/stop of the evidence line may not overlap with a complete sentence in a clinical note. To avoid this we tried to use a sentence splitter instead of newline character to determine our evidence lines. But existing sentence splitter's such as NLTK sentence splitter do even worse in breaking a clinical notes sentence because of its noisy, ungrammatical structure.
- Clinical notes are noisy, so some of the evidence lines may not have complete context or may not be grammatically correct.

[i2b2-datasets]: https://www.i2b2.org/NLP/DataSets/
[anusri-home]: https://www.linkedin.com/in/anusri-pampari-594bb5126/
[drqa]: https://github.com/facebookresearch/DrQA
[paper-link]: http://aclweb.org/anthology/D18-1258



