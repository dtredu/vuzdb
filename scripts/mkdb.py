#!/usr/bin/env python3
import sqlite3
import sys,json
import traceback

TRANSACTION_INIT = '''
CREATE TABLE IF NOT EXISTS universities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid VARCHAR UNIQUE NOT NULL CHECK(uid IN ('mephi', 'misis')),
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS programs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid VARCHAR UNIQUE NOT NULL,
    university_id INTEGER NOT NULL,
    code_id INTEGER NOT NULL,
    name_id INTEGER NOT NULL,
    qual VARCHAR NOT NULL CHECK(qual IN ('B', 'M', 'A', 'S', '1', '2', '_')),
    FOREIGN KEY (university_id) REFERENCES universities(id),
    FOREIGN KEY (code_id) REFERENCES program_codes(id),
    FOREIGN KEY (name_id) REFERENCES program_names(id)
);

CREATE TABLE IF NOT EXISTS program_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    desc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS program_names (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS programs_eduformats (
    program_id INTEGER NOT NULL,
    eduformat_id INTEGER NOT NULL,
    PRIMARY KEY (program_id, eduformat_id),
    FOREIGN KEY (program_id) REFERENCES programs(id),
    FOREIGN KEY (eduformat_id) REFERENCES eduformats(id)
);

CREATE TABLE IF NOT EXISTS eduformats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    duration INTEGER NOT NULL CHECK(duration > 0),
    eduform VARCHAR NOT NULL CHECK(eduform IN ('V', 'O', 'Z', '_')),
    UNIQUE (duration, eduform)
);

CREATE TABLE IF NOT EXISTS plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid VARCHAR UNIQUE NOT NULL,
    program_id INTEGER NOT NULL,
    year INTEGER NOT NULL CHECK(year >= 2000 AND year <= 2100),
    pdf_url TEXT NOT NULL,
    FOREIGN KEY (program_id) REFERENCES programs(id)
);

CREATE TABLE IF NOT EXISTS disciplines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL,
    code_id INTEGER NOT NULL,
    name_id INTEGER NOT NULL,
    semester INTEGER NOT NULL CHECK(semester > 0),
    hours INTEGER NOT NULL CHECK(hours > 0),
    FOREIGN KEY (plan_id) REFERENCES plans(id),
    FOREIGN KEY (code_id) REFERENCES discipline_codes(id),
    FOREIGN KEY (name_id) REFERENCES discipline_names(id),
    UNIQUE (plan_id, code_id, semester)
);

CREATE TABLE IF NOT EXISTS discipline_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS discipline_names (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);
'''
universities = (
  ('misis','НИТУ МИСИС'),
  ('mephi','НИЯУ МИФИ'),
)


TRANSACTION_INSERT_UNIVERSITY = '''
INSERT INTO universities (uid, name) 
VALUES (?, ?) 
ON CONFLICT(uid) 
DO UPDATE SET name = excluded.name;
'''

TRANSACTION_INSERT_PROGRAM_CODE = '''
INSERT INTO program_codes (code, desc)
VALUES (?, ?)
ON CONFLICT(code) DO UPDATE SET desc = excluded.desc;
'''
TRANSACTION_INSERT_PROGRAM_NAME = '''
INSERT OR IGNORE INTO program_names (name) VALUES (?)
'''
TRANSACTION_INSERT_PROGRAM = '''
WITH 
univ AS (
    SELECT id FROM universities WHERE uid = ?
),
code AS (
    SELECT id FROM program_codes WHERE code = ?
),
name AS (
    SELECT id FROM program_names WHERE name = ?
)
INSERT INTO programs (uid, university_id, code_id, name_id, qual)
VALUES (?, (SELECT id FROM univ), (SELECT id FROM code), (SELECT id FROM name), ?)
ON CONFLICT(uid) DO UPDATE SET 
    university_id = excluded.university_id,
    code_id = excluded.code_id,
    name_id = excluded.name_id,
    qual = excluded.qual;
'''
TRANSACTION_INSERT_EDUFORMAT = '''
INSERT INTO eduformats (duration, eduform) VALUES (?, ?)
ON CONFLICT (duration, eduform) DO NOTHING;
'''
TRANSACTION_INSERT_PROGRAM_EDUFORMAT_LINK = '''
WITH 
program AS (
    SELECT id FROM programs WHERE uid = ?
),
eduformat AS (
    SELECT id FROM eduformats WHERE duration = ? AND eduform = ?
)
INSERT INTO programs_eduformats (program_id, eduformat_id)
VALUES ((SELECT id FROM program), (SELECT id FROM eduformat))
ON CONFLICT (program_id, eduformat_id) DO NOTHING;
'''

TRANSACTION_INSERT_PLAN = '''
WITH 
program AS (
    SELECT id FROM programs WHERE uid = ?
)
INSERT INTO plans (uid, program_id, year, pdf_url)
VALUES (?, (SELECT id FROM program), ?, ?)
ON CONFLICT(uid) DO UPDATE SET 
    program_id = excluded.program_id,
    year = excluded.year,
    pdf_url = excluded.pdf_url;
'''


TRANSACTION_INSERT_DISCIPLINE_CODE='''
INSERT OR IGNORE INTO discipline_codes (code) VALUES (?);
'''
TRANSACTION_INSERT_DISCIPLINE_NAME='''
INSERT OR IGNORE INTO discipline_names (name) VALUES (?)
'''
TRANSACTION_INSERT_DISCIPLINE = '''
WITH 
plan AS (
    SELECT id FROM plans WHERE uid = ?
),
code AS (
    SELECT id FROM discipline_codes WHERE code = ?
),
name AS (
    SELECT id FROM discipline_names WHERE name = ?
)
INSERT INTO disciplines (plan_id, code_id, name_id, semester, hours)
VALUES ((SELECT id FROM plan), (SELECT id FROM code), (SELECT id FROM name), ?, ?)
ON CONFLICT (plan_id, code_id, semester) DO UPDATE SET 
    name_id = excluded.name_id,
    hours = excluded.hours;
'''
#TRANSACTION_INSERT_EDUFORMAT = 
#TRANSACTIONS = {
#  'INSERT_PROGRAM': TRANSACTION_INSERT, 
#  'INSERT_PROGRAM_CODE': TRANSACTION_INSERT_PROGRAM_CODE, 
#  'INSERT_PROGRAM_NAME': TRANSACTION_INSERT_PROGRAM_NAME, 
#  'INSERT_DISCIPLINE_CODE': TRANSACTION_INSERT_DISCIPLINE_CODE, 
#  'INSERT_DISCIPLINE_NAME': TRANSACTION_INSERT_DISCIPLINE_NAME, 
#  #'': TRANSACTION_INSERT, 
#  #'': TRANSACTION_INSERT, 
#
#}

#VACUUM;

def parse_uni(filepath):
  file = open(filepath,'r')
  text = file.read()
  file.close()
  data = json.loads(text)
  transactions = list()
  for row in data:
    transactions.append((TRANSACTION_INSERT_PROGRAM_NAME,(row['name'],)))
    transactions.append((TRANSACTION_INSERT_PROGRAM_CODE,(row['code'],row['code-desc'])))
    transactions.append((TRANSACTION_INSERT_PROGRAM,(
      row['university-uid'] ,
      row['code'],
      row['name'],
      row['uid'],
      row['qual'],
    )))
    for eduformat in row['eduformats']:
      transactions.append((TRANSACTION_INSERT_EDUFORMAT,(eduformat['duration'],eduformat['form'])))
      transactions.append((TRANSACTION_INSERT_PROGRAM_EDUFORMAT_LINK,(
        row['uid'],
        eduformat['duration'],
        eduformat['form']
      ),))
    for plan in row['plans']:
      transactions.append((TRANSACTION_INSERT_PLAN,(
        row['uid'],
        plan['uid'],
        plan['year'],
        plan['pdf'],
    ),))
  return transactions

def parse_plan(filepath):
  file = open(filepath,'r')
  text = file.read()
  file.close()
  data = json.loads(text)
  transactions = list()
  for discipline in data['disciplines']:
    transactions.append((TRANSACTION_INSERT_DISCIPLINE_CODE,(discipline['code'],),))
    transactions.append((TRANSACTION_INSERT_DISCIPLINE_NAME,(discipline['name'],),))
    transactions.append((TRANSACTION_INSERT_DISCIPLINE,(
      data['plan-uid'],
      discipline['code'],
      discipline['name'],
      discipline['semester'],
      discipline['hours'],
    ),))
  return transactions

assert len(sys.argv) > 1
dbpath = sys.argv[1]

with sqlite3.connect(dbpath) as conn:

  cur = conn.cursor()

  cur.executescript(TRANSACTION_INIT)

  for university in universities:
    cur.execute(TRANSACTION_INSERT_UNIVERSITY, university)
  conn.commit()


  for line in sys.stdin:
    transactions = None
    print(line.strip(),end=' - ')
    try:
      if line.startswith("uni:"):
        transactions = parse_uni(line.strip()[5:])
      elif line.startswith("plan:"):
        transactions = parse_plan(line.strip()[6:])
      print("OK")
      for transaction in transactions:
        cur.execute(*transaction)
      conn.commit()
    except:
      print("ERROR:")
      traceback.print_exc()
      break; #continue

  cur.execute("VACUUM;")
  conn.commit()
