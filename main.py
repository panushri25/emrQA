from subprocess import check_call
import sys
import os
import csv

PYTHON = sys.executable

#################################### set the full file paths ###############################################

i2b2_relations_challenge_directory = "i2b2/relations/"
i2b2_medications_challenge_directory = "i2b2/medication/"
i2b2_heart_disease_risk_challenge_directory = "i2b2/heart-disease-risk/"
i2b2_obesity_challenge_directory = "i2b2/obesity/"
i2b2_smoking_challenge_directory = "i2b2/smoking/"
i2b2_coreference_challeneg_directory = "i2b2/coreference"

templates_directory = "templates/templates-all.csv"

#################################### make output directory if it does not already exist #########################

cwd = os.getcwd()
model_dir = "output/"
if not os.path.exists(os.path.join(cwd,model_dir)):
    os.makedirs(model_dir)

output_directory = os.path.join(cwd,model_dir)  ## you can modify this to change the output directory path ##

###########################################################################################################

matching_notes = os.path.join("generation/i2b2_relations/", "matching_notes.csv")
match_file = open(matching_notes)
csvreader = csv.reader(match_file)
matching_files = list(csvreader)  #  relation, coreference
new_file = []
new_file.append(matching_files[0])
flag = 0
for file in matching_files[1:]:
    if i2b2_relations_challenge_directory in file[0]:
        flag = 1
        break
    new_file.append([os.path.join(i2b2_relations_challenge_directory,file[0]),os.path.join(i2b2_coreference_challeneg_directory,file[1])])

if flag == 0:
    ofile = open(matching_notes, "w")
    filewriter = csv.writer(ofile, delimiter="\t")

    for val in new_file:
        filewriter.writerow(val)

    ofile.close()

################################### run the generation scripts #######################################


cmd = "{python} generation/i2b2_medications/medication-answers.py --i2b2_dir={i2b2_dir} --templates_dir={templates_dir} --output_dir={output_dir}".format(python=PYTHON, i2b2_dir=i2b2_medications_challenge_directory, templates_dir=templates_directory, output_dir=output_directory)
print(cmd)
check_call(cmd, shell=True)


cmd = "{python} generation/i2b2_relations/relations-answers.py --i2b2_dir={i2b2_dir} --templates_dir={templates_dir} --output_dir={output_dir}".format(python=PYTHON, i2b2_dir=i2b2_relations_challenge_directory, templates_dir=templates_directory, output_dir=output_directory)
print(cmd)
check_call(cmd, shell=True)


cmd = "{python} generation/i2b2_heart_disease_risk/risk-answers.py --i2b2_dir={i2b2_dir} --templates_dir={templates_dir} --output_dir={output_dir}".format(python=PYTHON, i2b2_dir=i2b2_heart_disease_risk_challenge_directory, templates_dir=templates_directory, output_dir=output_directory)
print(cmd)
check_call(cmd, shell=True)


cmd = "{python} generation/i2b2_smoking/smoking-answers.py --i2b2_dir={i2b2_dir} --templates_dir={templates_dir} --output_dir={output_dir}".format(python=PYTHON, i2b2_dir=i2b2_smoking_challenge_directory, templates_dir=templates_directory, output_dir=output_directory)
print(cmd)
check_call(cmd, shell=True)


cmd = "{python} generation/i2b2_obesity/obesity-answers.py --i2b2_dir={i2b2_dir} --templates_dir={templates_dir} --output_dir={output_dir}".format(python=PYTHON, i2b2_dir=i2b2_obesity_challenge_directory, templates_dir=templates_directory, output_dir=output_directory)
print(cmd)
check_call(cmd, shell=True)

##################  combine all the output files and generate the output in normal format ####################

cmd = "{python} generation/combine_data/combine_answers.py --output_dir={output_dir}".format(python=PYTHON, output_dir=output_directory)
print(cmd)
check_call(cmd, shell=True)

#####################  convert normal output to squad format ##################################


######################### basic analysis of the dataset #######################################

'''
cmd = "{python}  evaluation/analysis.py".format(python=PYTHON)
print(cmd)
check_call(cmd, shell=True)
'''