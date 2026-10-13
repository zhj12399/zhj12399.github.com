"""Build the website bibliography from verified publication records."""
import html
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[4]
WORK = ROOT / 'ccfa-workfiles/checks/publication-bibtex'
RECORDS = json.loads((WORK / 'cache/records.json').read_text(encoding='utf-8'))
BY_ID = {r['id']:r for r in RECORDS}
DATE = '2026-10-13'

def clean(value):
    for _ in range(3):
        value = html.unescape(value)
    return re.sub(r'\s+', ' ', value).strip()

def strip_marks(value):
    return re.sub(r'[†‡#*]', '', clean(value))

def ascii_words(value):
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii').lower()
    return re.findall('[a-z0-9]+', value)

EXTRA = {
 'j01': {'omit_pages':True, 'note':'Early access', 'sources':['https://ieeexplore.ieee.org/abstract/document/11701489/'], 'verification_note':'Publisher and Crossref show placeholder pages 1-1; omit pages rather than export a placeholder or unverified manuscript pagination.'},
 'j03': {'omit_pages':True, 'note':'Online first', 'verification_note':'Publisher has no final volume/issue/pages; Scholar manuscript pages are not treated as final pagination.'},
 'j13': {'verification_note':'Use publisher-registered pages 1-20; Scholar lists article number 4018620 in its pages field.'},
 'j14': {'title':'Toward Practical Colorectal Cancer Diagnosis: A Bowel-Sound-Based System With Portable Sensor and On-Board Lightweight AI Model', 'volume':'12','number':'21','pages':'45722--45736', 'sources':['https://ieeexplore.ieee.org/abstract/document/11131175'], 'verification_note':'Use the final IEEE title, volume, issue and pages; Crossref is still showing early-access metadata.'},
 'c01': {'title':'Similarity as Evidence: An Explainable Siamese Framework for Snore Sound Classification', 'booktitle':'Interspeech 2026 [Long Track]', 'author':'Meng, Boyang and Sun, Mengkai and Zhang, Haojie and Qian, Kun and Xue, Wei and Hu, Bin and Schuller, Bjoern', 'year':'2026','pages':'2790--2798','doi':'10.21437/Interspeech.2026-2153','publisher':'ISCA', 'location':'Sydney, Australia','sources':['https://www.isca-archive.org/interspeech_2026/meng26f_interspeech.html','https://www.isca-archive.org/interspeech_2026/index.html']},
 'c02': {'location':'Chongqing, China', 'omit_pages':True, 'sources':['https://www.ic-cea.org/iccea2026'], 'verification_note':'Title/authors/conference/year verified in the author Scholar record; venue verified on conference website. No matching publisher paper record or final pages/DOI found; omit unknown fields.'},
 'c06': {'location':'Hohhot, China', 'omit_pages':True, 'sources':['https://www.csmcw-csmt.org.cn/news/info/47?Nid=654'], 'verification_note':'Title/authors verified in the author Scholar record; event verified with the organizer. A final paper DOI and proceedings pagination were not found; omit these fields. Correct lsing to Ising.'},
 'c09': {'location':'Rotterdam, The Netherlands','sources':['https://www.isca-archive.org/interspeech_2025/index.html']},
 'c10': {'location':'Rotterdam, The Netherlands','sources':['https://www.isca-archive.org/interspeech_2025/index.html','https://www.isca-archive.org/interspeech_2025/yang25b_interspeech.html']},
 'c12': {'verification_note':'IEEE publisher registration puts this paper in the 2024 IEEE Smart World Congress proceedings, with location Nadi, Fiji; UIC is a co-located conference and Denarau is the venue area.'},
 'c13': {'location':'Wuhan, China', 'booktitle':'Proceedings of the 11th Conference on Sound and Music Technology', 'sources':['https://link.springer.com/chapter/10.1007/978-981-96-4783-5_3','https://www.csmcw-csmt.org.cn/news/info/47?Nid=629'], 'verification_note':'Conference held in 2024; publisher year is 2025. Keep Scholar-style key year 2024 and use year=2025 in the citation.'},
 'c16': {'type':'techreport', 'institution':'DCASE 2024 Challenge', 'title':'LIF-ProtoNet: Prototypical Network with Leaky Integrate-and-Fire Neuron and Squeeze-and-Excitation Blocks for Bioacoustic Event Detection', 'pages':'1--4','location':'Tokyo, Japan', 'note':'Technical report submitted to the DCASE 2024 Challenge; location refers to the associated DCASE 2024 Workshop', 'sources':['https://dcase.community/documents/challenge2024/technical_reports/DCASE2024_QianHu_92_5.pdf','https://dcase.community/workshop2024/'], 'verification_note':'Official report has four pages. Challenge report is not relabeled as a workshop proceedings paper; qualify the workshop location.'},
 'c17': {'title':'面向心音识别的自监督联邦学习 (Self-Supervised Federated Learning for Heart Sound Recognition)', 'location':'Urumqi, China', 'omit_pages':True, 'sources':['https://www.ncmmsc.org.cn/2024/news/show.asp?id=28','https://www.ncmmsc.org.cn/2024/UploadFile/file/20240813/20240813215056965696.pdf','https://www.ncmmsc.org.cn/2024/dhrc/'], 'verification_note':'Official acceptance list and program verify the paper and all six authors; event website verifies Urumqi. Final proceedings pages/DOI were not retrievable; omit unknown fields.'},
 'c18': {'location':'Kos, Greece','sources':['https://www.isca-archive.org/interspeech_2024/index.html']},
 'c19': {'location':'Kos, Greece','sources':['https://www.isca-archive.org/interspeech_2024/index.html']},
 'c21': {'location':'Seoul, Republic of Korea'},
 'c23': {'type':'techreport', 'institution':'DCASE 2023 Challenge', 'pages':'1--4','location':'Tampere, Finland', 'note':'Technical report submitted to the DCASE 2023 Challenge; location refers to the associated DCASE 2023 Workshop', 'sources':['https://dcase.community/documents/challenge2023/technical_reports/DCASE2023_QianXu_86_t7.pdf','https://dcase.community/workshop2023/index'], 'verification_note':'Official four-page technical report. The workshop location is explicitly qualified.'},
}

def author_field(record):
    metadata = record.get('crossref', {})
    scholar = record['scholar_fields']
    public_names = [strip_marks(n) for n in scholar['Authors'].split(', ')]
    authors = metadata.get('author')
    if not authors:
        return ' and '.join(n.rsplit(' ',1)[1] + ', ' + n.rsplit(' ',1)[0] for n in public_names)
    result = []
    for author in authors:
        family, given = author['family'], author.get('given','')
        if family == 'Chen Xu' and not given:
            family, given = 'Xu', 'Chen'
        canonical = ' '.join(ascii_words(given + ' ' + family))
        for name in public_names:
            if ' '.join(ascii_words(name)) == canonical:
                given, family = name.rsplit(' ',1)
                break
        result.append(strip_marks(family) + (', ' + strip_marks(given) if given else ''))
    return ' and '.join(result)

def make_key(record):
    first = strip_marks(record['scholar_fields']['Authors'].split(', ')[0]).rsplit(' ',1)[-1]
    year = record['scholar_fields']['Publication date'][:4]
    words = ascii_words(record['scholar_title'])
    if record['id']=='c17': words=ascii_words('Self-Supervised Federated Learning for Heart Sound Recognition')
    while words and words[0] in ['a','an','the']: words.pop(0)
    return ''.join(ascii_words(first)) + year + words[0]

def make_entry(record):
    metadata = record.get('crossref', {})
    scholar = record['scholar_fields']
    extra = EXTRA.get(record['id'], {})
    entry_type = extra.get('type', 'article' if record['kind']=='journal' else 'inproceedings')
    title = clean(extra.get('title', metadata.get('title',[record['scholar_title']])[0]))
    key = make_key(record)
    if record['id']=='j11': assert key=='wang2025can'
    fields = {'title':'{' + title + '}', 'author':extra.get('author',author_field(record))}
    if entry_type == 'article':
        fields['journal'] = clean(metadata['container-title'][0])
    elif entry_type == 'techreport':
        fields['institution'] = extra['institution']
        fields['type'] = 'Technical report'
    else:
        containers = metadata.get('container-title', [scholar.get('Conference','')])
        fields['booktitle'] = clean(extra.get('booktitle',containers[-1]))
    year = metadata.get('published',{}).get('date-parts',[[int(scholar['Publication date'][:4])]])[0][0]
    fields['year'] = extra.get('year',str(year))
    for target,source in [('volume','volume'),('number','issue'),('pages','page'),('doi','DOI')]:
        value = extra.get(target,metadata.get(source))
        if target=='pages' and extra.get('omit_pages'): value=None
        if value:
            fields[target] = re.sub(r'\s*[-–]+\s*','--',str(value)) if target=='pages' else str(value)
    if record['kind']=='conference':
        location = extra.get('location', metadata.get('event',{}).get('location'))
        if not location: raise ValueError('Missing verified conference location '+record['id'])
        location = {'Nanchang China':'Nanchang, China','Dongguan China':'Dongguan, China'}.get(location,location)
        fields['location'] = clean(location)
    publisher = extra.get('publisher',metadata.get('publisher'))
    if publisher:
        if 'Institute of Electrical' in publisher: publisher='IEEE'
        if publisher=='Association for Computing Machinery (ACM)':publisher='Association for Computing Machinery'
        fields['publisher'] = clean(publisher)
    url = record['url'] or record['scholar_url']
    if record['id']=='c01': url=extra['sources'][0]
    if 'doi' in fields: url='https://doi.org/'+fields['doi']
    fields['url'] = url
    if extra.get('note'): fields['note']=extra['note']
    bibtex = '@' + entry_type + '{' + key + ',\n' + ',\n'.join('  ' + name + ' = {' + value + '}' for name,value in fields.items()) + '\n}'
    sources = []
    if metadata: sources.append('https://api.crossref.org/works/' + metadata['DOI'])
    sources.append(record['scholar_url'])
    sources.extend(extra.get('sources',[]))
    return key, {'id':record['id'],'title':title,'bibtex':bibtex,'verified_on':DATE,
                'key_source':'Generated in Scholar-style format, as authorized by the user; not a raw Scholar export',
                'sources':list(dict.fromkeys(sources)),
                'verification_note':extra.get('verification_note','Publisher-registered metadata checked against the author Scholar record'),
                'metadata':fields}

def fix_block(record):
    block=record['block']
    changes={
      'j01':[('pp.1-18, 2026.','early access, 2026.')],
      'j11':[('pp.4824-4837, 2025.','pp.4824-4837, 2026.'),('11271376)"','11271376)",')],
      'j12':[('Artificial Intelligence based Music','Artificial Intelligence-Based Music')],
      'j13':[('An On-Board Executable Multitask','An Onboard Executable Multitask')],
      'j14':[('Towards Practical Colorectal Cancer Diagnosis: A Bowel Sound-Based System with','Toward Practical Colorectal Cancer Diagnosis: A Bowel-Sound-Based System With')],
      'c01':[('"Similarity as Evidence: An Explainable Siamese Framework for Snore Sound Classification"','"[Similarity as Evidence: An Explainable Siamese Framework for Snore Sound Classification](https://www.isca-archive.org/interspeech_2026/meng26f_interspeech.html)"'),('pp.1-9','pp.2790-2798'),('September 2026.','September–October 2026.')],
      'c02':[('pp.1-4, ','')],
      'c05':[('pp.1-8','pp.1252-1256')],
      'c06':[('the lsing Model','the Ising Model'),('pp.1-12, ','')],
      'c08':[('Ruolan Huang\\*, Bin Hu\\*','Ruolan Huang\\*, Toru Nakamura, Bin Hu\\*')],
      'c10':[('Zijing Yang','Zijiang Yang'),('MAD-UV: The 1st','MADUV: The 1st')],
      'c12':[('Kun Qian\\*, Yoshiharu Yamamoto, Björn W. Schuller, Bin Hu\\*','Kun Qian\\*, Bin Hu\\*, Yoshiharu Yamamoto, Björn W. Schuller'),('Proceedings of IEEE International Conference on Ubiquitous Intelligence and Computing (UIC)','Proceedings of the 2024 IEEE Smart World Congress (SWC; co-located UIC)'),('Denarau, Fiji','Nadi, Fiji')],
      'c13':[('Advancing Metadata-Convolutional with','Advancing Metadata-Convolutional Neural Networks with')],
      'c15':[('pp.1-6','pp.1-4')],
      'c16':[('pp.1-4, Tokyo, Japan, October 2024.','pp.1-4, 2024. (Associated workshop: Tokyo, Japan, October 2024.)')],
      'c17':[('pp.1-8, ','')],
      'c23':[('pp.1-4, Tampere, Finland, September 2023.','pp.1-4, 2023. (Associated workshop: Tampere, Finland, September 2023.)')],
    }
    for old,new in changes.get(record['id'],[]):
        if old not in block:
            if new in block or new=='': continue
            raise ValueError('Expected replacement missing '+record['id']+' '+old)
        block=block.replace(old,new)
    return block

def main():
    entries={}
    id_keys={}
    for record in RECORDS:
        key,entry=make_entry(record)
        if key in entries: raise ValueError('Duplicate key '+key)
        entries[key]=entry; id_keys[record['id']]=key
    target=ROOT/'docs/_data/publications.json'
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for kind in ['journal','conference']:
        path=ROOT/'docs'/(kind+'.md')
        text=path.read_text(encoding='utf-8-sig')
        for record in RECORDS:
            if record['kind']!=kind:continue
            key=id_keys[record['id']]
            suffix=' {% include bibtex-button.html key="'+key+'" %}'
            if suffix in text: continue
            if record['block'] not in text:
                raise ValueError('Original record missing '+record['id'])
            text=text.replace(record['block'],fix_block(record).rstrip()+suffix,1)
        text=text.replace('\n {% include bibtex-button.html', ' {% include bibtex-button.html')
        text=re.sub(r'(\{% include bibtex-button\.html key="[^"]+" %\})(?:\s+\1)+',r'\1',text)
        if kind=='journal':
            for identifier in ['114388','109795','109449','109302','113165','103745','100085']:
                text=text.replace('pp.'+identifier,'Art. no. '+identifier)
            text=text.replace('vol.74, pp.4018620, 2025.','vol.74, Art. no. 4018620, pp.1-20, 2025.')
        else:
            text=text.replace('pp.25-36, Wuhan, China, October 2024.','pp.25-36, Wuhan, China, October 2024 (proceedings published in 2025).')
        path.write_text(text.rstrip()+'\n',encoding='utf-8')
    report=['# Publication BibTeX verification', '', 'Checked on '+DATE+'.', '',
            '42 entries: 19 journals and 23 conference/technical-report entries.', '',
            'The user authorized Scholar-style keys after the raw export triggered a Google human-verification page. Keys use the first author surname, the year in the author Scholar record, and the first title word (omitting a/an/the). The bilingual Chinese paper uses its English title for the key. Citation year follows the publisher record when available; this may differ from the key year.', '',
            'All author lists are complete; author-role markers are excluded. Publisher-registered author order takes precedence over user-maintained Scholar metadata. Unknown final pagination and DOI values are omitted rather than inferred. DCASE Challenge technical reports retain their type; their location field is explicitly qualified as the associated workshop location.', '',
            '| Key | Entry | Evidence and remaining limits |', '| --- | --- | --- |']
    for key,entry in entries.items():
        links='; '.join('[source '+str(i)+']('+url+')' for i,url in enumerate(entry['sources'],1))
        report.append('| `'+key+'` | '+entry['title'].replace('|','\\|')+' | '+entry['verification_note']+' '+links+' |')
    (WORK/'verification.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    print('Built',len(entries),'verified bibliography entries and updated both publication lists.')
    print(json.dumps(id_keys,ensure_ascii=False))

if __name__=='__main__':main()
