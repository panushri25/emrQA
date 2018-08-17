# emrQA: A Large Corpus for Question Answering on Electronic Medical Records

- This repo contains code for the paper
Anusri Pampari, Preethi Raghavan, Jennifer Liang and Jian Peng,  
emrQA: A Large Corpus for Question Answering on Electronic Medical Records,  
In Conference on Empirical Methods in Natural Language Processing (EMNLP) 2018, Brussels, Belgium.

- The data can be generated using the NLP Datasets from the [i2b2 Challenges][i2b2-datasets], which are accessible by everyone subject to a license agreement. 
- Please contact [Anusri Pampari][anusri-home] (\<last-name\>2@illinois.edu)  for suggestions and comments.

(under construction)


In our work, we have currently made use of all the challenge datasets except the 2012 Temporal Relations Challenge. Our future extensions of the dataset to include this challenge dataset  will soon be available. 


Some statistics of the generated data:

| Datasets | QA pairs | QL pairs | #Notes | 
| i2b2 relations | 141,783 | 1,061,710 | 426 |
| i2b2 relations | 141,783 | 1,061,710 | 426 |

## Requirements

### General
- Python 2
- NLP Datasets from [i2b2][i2b2-datasets]

### Python Packages
- nltk
- json


## Generation

To generate emrQA, first [download](#downloading-i2b2) the i2b2 challenge datasets. **Important: Navigate through all the files in the generation folder and set the i2b2 folder paths and the output folder paths as indicated in the script.** 
  
Run `python main.py` to generate the question-answers pairs in a json format and the question-logical form pairs in a csv format.  A thorough discussion of the output format of these files is presented below.

### Question-Answer Format


### Squad Format


### Question-logical form



## Data Analysis

## Baselines

[i2b2-datasets]: https://www.i2b2.org/NLP/DataSets/
[anusri-home]: https://www.linkedin.com/in/anusri-pampari-594bb5126/
