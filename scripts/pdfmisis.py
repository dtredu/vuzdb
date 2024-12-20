import sys
import os
import re
import pdfplumber
import copy
import json

MUST_BE_TEXT = "Семестр "
#TEST_CELL_IDS = [1]
#                        Б    1       .
RE_SEMESTER = re.compile(r'Семестр ([0-9A-Z])') 
RE_DSID     = re.compile(r'[А-Я0-9]+(?:\.[А-Я0-9]+)+(?:\([А-Я]\))?')
SEMESTERS_IDS = [5, 15]
#RE_DSID = re.compile(r'[А-Я][0-9]?(?:\.(?:[A-Я0-9]+))+')

path_in = sys.argv[1]
path_out = sys.argv[2]

data = {
    'disciplines': list()
}
name, _ = os.path.splitext(os.path.basename(path_in))
data['university-uid'], data['program-uid'], data['plan-uid'] = name.split('-')

print(data,end=" ")

discipline = dict()
pdf = pdfplumber.open(path_in)
for page in pdf.pages:
    text = page.extract_text()
    if text.find(MUST_BE_TEXT) == -1:
        continue
    tables = page.extract_tables()
    assert len(tables) == 1
    table = tables[0]
    semesters = []
    semesters_offsets = []
    for i,cell in enumerate(table[0]):
        if type(cell) == type(None) or (not RE_SEMESTER.fullmatch(cell)):
            continue
        semester = int(RE_SEMESTER.findall(cell)[0])
        semesters.append((semester,i))
    if len(semesters) != 2:
        continue
    assert len(semesters) == 2
    for row in table:
        cell = row[1]
        if type(cell) == type(None) or (not RE_DSID.fullmatch(cell)):
            continue
        discipline['code'] = cell
        discipline['name'] = row[2].replace('\n',' ')
        for sem, i in semesters:
            if not row[i]:
                continue
            discipline['hours']   = int(row[i+1])
            discipline['control'] = row[i]
            discipline['semester'] = sem
            data['disciplines'].append(copy.deepcopy(discipline))
            #print(discipline)
           
if len(data['disciplines']) == 0:
    print("ERROR")
    exit(255)
print("OK")
text = json.dumps(data,indent=2,ensure_ascii=False)

fout = open(path_out,'w')
fout.write(text)
fout.close()

