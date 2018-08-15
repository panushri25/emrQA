from subprocess import check_call
import sys


## set the file paths in all the files run below##
PYTHON = sys.executable

cmd = "{python} generation/i2b2_medications/medication-answers.py".format(python=PYTHON)
print(cmd)
check_call(cmd, shell=True)

cmd = "{python} generation/i2b2_relations/relations-answers.py".format(python=PYTHON)
print(cmd)
check_call(cmd, shell=True)

cmd = "{python} generation/i2b2_heart_disease_risk/risk-answers.py".format(python=PYTHON)
print(cmd)
check_call(cmd, shell=True)

cmd = "{python} generation/i2b2_smoking/smoking-answers.py".format(python=PYTHON)
print(cmd)
check_call(cmd, shell=True)

cmd = "{python} generation/i2b2_obesity/obesity-answers.py".format(python=PYTHON)
print(cmd)
check_call(cmd, shell=True)


cmd = "{python} generation/combine_data/combine_answers.py".format(python=PYTHON)
print(cmd)
check_call(cmd, shell=True)

cmd = "{python}  evaluation/analysis.py".format(python=PYTHON)
print(cmd)
check_call(cmd, shell=True)
