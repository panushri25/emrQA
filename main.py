from subprocess import check_call
import sys


## set the file paths in all the files called below##
PYTHON = sys.executable

cmd = "{python} generation/i2b2_medications/medication-answers.py".format(python=PYTHON)
print(cmd)
check_call(cmd, shell=True)

cmd = "{python} generation/combine_data/combine_answers.py".format(python=PYTHON)
print(cmd)
check_call(cmd, shell=True)

cmd = "{python}  evaluation/analysis.py".format(python=PYTHON)
print(cmd)
check_call(cmd, shell=True)
