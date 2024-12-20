import hashlib
import json
import requests
import copy
import logging
from urllib.parse import urljoin,urlparse,urlsplit,urlunsplit,unquote,parse_qs,urlencode
from bs4 import BeautifulSoup
from lxml import html
import re
from tqdm import tqdm


FOUT_JSON = "misis.json"
FOUT_SH = "misis.sh"

MISIS = "https://misis.ru/sveden/education/eduaccred/"
MISIS_BASE = 'https://misis.ru'

RE_YEAR = re.compile(r'([0-9]{4})')

XPATH_PROGRAMS_ROW   = '//tr[@itemprop="eduAccred"]'
XPATH_PLANS_ROW_YEAR = '//div[contains(text(), "Учебный план")]/..//div[contains(text(), "год начала подготовки:")]'
XPATH_PLANS_ROW_PDF  = XPATH_PLANS_ROW_YEAR + '/..//*[@href and contains(text(), "план")]'
XPATHS_SUB = {
    "CODE" : './/td[@itemprop="eduCode"]//*[@id]',
    "NAME" : './/td[@itemprop="eduName"]',
    "PROF" : './/td[@itemprop="eduProf"]//a[@href]',
    "LEVEL": './/td[@itemprop="eduLevel"]',
    "FORM" :'.//td[@itemprop="eduForm"]',
    "DURATION" : './/td[@itemprop="learningTerm"]'
}

DURATIONS = {
    "1 год / 2 года": [12, 24],
    "2 года": [24],
    "2 года 6 месяцев": [30],
    "3 года": [36],
    "4 год": [48],
    "4 года": [48],
    "4 года 6 месяцев": [54],
    "5 лет": [60],
    "5 лет 5 месяцев": [65],
    "5 лет 6 месяцев": [66],
    "6 лет": [72],
    "6 лет 5 месяцев": [77],
    "6 лет 6 месяцев": [78],
}

EDUFORMS = {
    "Заочная": "Z",
    "Очная": "O",
    "Очно-заочная": "V",
}

LEVELS = {
    "Высшее образование - бакалавриат": "B",
    "Высшее образование - магистратура": "M",
    "Высшее образование - специалитет": "S",

    "Высшее образование - подготовка кадров высшей квалификации": "A",

    "Высшее образование - базовое высшее образование": "1",
    "Высшее образование - специализированное высшее образование": "2",
}

parse_eduform  = lambda st: EDUFORMS[st]
parse_durations = lambda st: DURATIONS[st]
parse_level = lambda st: LEVELS[st]


try:
    response = requests.get(MISIS)
    response.raise_for_status()  # Check if the request was successful
except requests.exceptions.RequestException as e:
    print(f"Error fetching the URL: {e}")

dom = html.fromstring(response.content.decode('utf-8'))
k = 0
pdf_download_cmds = list()
data = list()
prof_url = ''
members = {}


def parse_url(url): 
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check if the request was successful
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    dom = html.fromstring(response.content.decode('utf-8'))
    plans = list()
    for el_year,el_pdf in zip(dom.xpath(XPATH_PLANS_ROW_YEAR),dom.xpath(XPATH_PLANS_ROW_PDF)):
        year = RE_YEAR.findall(el_year.text)[0]
        pdf = urljoin(base_url, el_pdf.attrib['href'])
        if urlparse(pdf).hostname == "files.misis.ru":
            scheme, netloc, path, query_string, fragment = urlsplit(pdf)
            query_string = urlencode(parse_qs(query_string) | {'dl':1},doseq = True)
            #print(scheme, netloc, path, query_string, fragment)
            #pdf = f'{scheme}://{netloc}{path}{query_string}{fragment}'
            pdf = unquote(urlunsplit((scheme, netloc, path, query_string, fragment)))
        sha1_hash = hashlib.sha1() 
        sha1_hash.update(pdf.encode('utf-8')) 
        plans.append({
            "uid": sha1_hash.hexdigest(),
            "year": int(year), 
            "pdf": pdf,
        })
    return plans
#'//div[contains(text(), "Учебный план")]/..//div[contains(text(), "год начала подготовки:")]/'

dat = {
    "university-uid": "misis",
    "eduformats" : list()
}
notfirst = False
rows = dom.xpath(XPATH_PROGRAMS_ROW)
for row in tqdm(rows):
    #global members
    isnew = len(row.xpath('.//td[@itemprop="eduProf"]//a[@href]')) > 0
    if isnew and notfirst:
        data.append(copy.deepcopy(dat))
        #print(dat)
    if isnew:
        notfirst = True
        dat['eduformats'].clear()
        #members = {key: row.xpath(xpath)[0].text.strip() for key, xpath in XPATHS_SUB.items()}
        prof = row.xpath('.//td[@itemprop="eduProf"]//a[@href]')[0]
        prof_url = urljoin(MISIS_BASE,prof.attrib['href'])
        sha1_hash = hashlib.sha1() 
        sha1_hash.update(prof_url.encode('utf-8')) 
        dat['uid'] = sha1_hash.hexdigest()
        dat['name'] = prof.text.strip()

        code = row.xpath('.//td[@itemprop="eduCode"]//*[@id]')
        code = code[0].text.strip() 
        dat['code'] = code

        name = row.xpath('.//td[@itemprop="eduName"]')
        name = name[0].text.strip() 
        dat['code-desc'] = name

        level = row.xpath('.//td[@itemprop="eduLevel"]')
        level = level[0].text.strip()
        dat['qual'] = parse_level(level)
        
        dat['plans'] = parse_url(prof_url)
        for plan in dat['plans']:
            pdf_download_cmds.append(f'wget "{plan["pdf"]}" -O "{dat["university-uid"]}-{dat["uid"]}-{plan["uid"]}.pdf"\n')
        #dat['name']
        #pdf_urls.append(members['PROFURL'])

    eduform = row.xpath('.//td[@itemprop="eduForm"]')
    eduform = eduform[0].text.strip()
    eduform = parse_eduform(eduform)
    #dat['eduForm'] = eduform
    durations  = row.xpath('.//td[@itemprop="learningTerm"]')
    durations  = durations[0].text.strip()
    durations  = parse_durations(durations)

    for duration in durations:
        dat['eduformats'].append({
            'form': eduform,
            'duration': duration
        })

    #print(members["PROFURL"])
    #print(members['LEVEL'])
else:
    data.append(copy.deepcopy(dat))
    #print(dat)
#print(pdf_urls)
#download_text = ''.join(map(lambda s: f'wget "{s}"\n', pdf_urls))




print("Done, serializing...")

data_text = json.dumps(data,indent=2,ensure_ascii=False)
script_text = ''.join(pdf_download_cmds)

fout = open(FOUT_JSON,'w')
fout.write(data_text)
fout.close()

fout = open(FOUT_SH,'w')
fout.write(script_text)
fout.close()

#[
#  {
#    "uid": "1253", // что угодно, но id-шник уникальный для программы внутри вуза
#    "university-uid": "mephi", // mephi | misis | ...
#    "code": "01.03.02",
#    "code-desc": "Прикладная математика и информатика",
#    "name": "Математика и науки о данных",
#    "qual": "B", // B = бакалавриат, M = магистратура, A = аспирантура
#    "duration" "4",
#    "eduformats": [
#      {
#        "form" : "O",
#        "duration" : 48
#      }
#    ],
#    "plans": [
#      {
#        "uid": "...", // что-угодно, но id-шник уникальный для планов внутри программы
#        "year": "2024",
#        "pdf-url": "https://eis2.mephi.ru/programs/Program/File?fileId=336cb033-36c3-4235-93a1-9881924a85f6"
#      },
#      ... // другие планы, если есть
#    ]
#  }
#]
