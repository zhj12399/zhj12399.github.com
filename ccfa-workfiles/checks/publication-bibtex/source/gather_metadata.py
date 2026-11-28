"""Gather public publisher and Scholar metadata for the website's publications."""
import argparse
import concurrent.futures
import difflib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
import unicodedata
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[4]
WORK = ROOT / 'ccfa-workfiles/checks/publication-bibtex'
CACHE = WORK / 'cache'
REGISTRY = CACHE / 'records.json'
PROFILE = 'https://scholar.google.com/citations?user=Q6bJyiwAAAAJ&hl=en&pagesize=100'

def normalize(text):
    text = unicodedata.normalize('NFKD', html.unescape(text)).casefold()
    return ''.join(c for c in text if c.isalnum())

def read_url(url):
    for attempt in range(4):
        try:
            response = urllib.request.urlopen(url, timeout=20)
            break
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == 3:
                raise
            time.sleep(min(30, int(error.headers.get('Retry-After', 4 * (attempt + 1)))))
    with response:
        raw = response.read()
        encoding = response.headers.get_content_charset()
        if not encoding:
            match = re.search(br'charset\s*=\s*["\']?([\w-]+)', raw[:1200], re.I)
            encoding = match.group(1).decode('ascii') if match else 'utf-8'
        result = raw.decode(encoding)
    time.sleep(1)
    return result

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []
        self.active = None
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a':
            self.active = {'href': attrs.get('href', ''), 'class': attrs.get('class', ''), 'text': ''}
    def handle_data(self, value):
        if self.active is not None:
            self.active['text'] += value
    def handle_endtag(self, tag):
        if tag == 'a' and self.active is not None:
            self.items.append(self.active)
            self.active = None

def plain(markdown):
    markdown = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', markdown)
    return markdown.replace('\\#', '').replace('\\*', '').replace('*', '').replace('_', '')

def load_records():
    if REGISTRY.exists():
        return json.loads(REGISTRY.read_text(encoding='utf-8'))
    records = []
    for kind in ['journal', 'conference']:
        text = (ROOT / 'docs' / (kind + '.md')).read_text(encoding='utf-8-sig')
        for index, match in enumerate(re.finditer(r'^\* ([\s\S]*?)(?=\n\n|\Z)', text, re.M), 1):
            block = re.sub(r' ?\{% include bibtex-button\.html key="[^"]+" %\}', '', match.group(0))
            title_match = re.search(r'"([^\n]+)"', block)
            if not title_match:
                raise ValueError('Missing title: ' + block)
            title_markdown = title_match.group(1)
            links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', title_markdown)
            records.append({'id': kind[0] + str(index).zfill(2), 'kind': kind,
                            'title': plain(title_markdown), 'url': links[0][1].rstrip('#') if links else '',
                            'block': block})
    return records

def save(records):
    CACHE.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def profile(records):
    source = read_url(PROFILE)
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / 'scholar-profile.html').write_text(source, encoding='utf-8')
    parser = Links(); parser.feed(source)
    papers = [p for p in parser.items if p['class'] == 'gsc_a_at']
    for record in records:
        ranked = sorted([(difflib.SequenceMatcher(None, normalize(record['title']), normalize(p['text'])).ratio(), p) for p in papers], key=lambda x:x[0], reverse=True)
        score, paper = ranked[0]
        record['scholar_match_score'] = round(score, 4)
        if score >= 0.88:
            record['scholar_url'] = urllib.parse.urljoin(PROFILE, paper['href'])
            record['scholar_title'] = paper['text']
        print(record['id'], round(score, 4), record['title'], flush=True)
    save(records)

def scholar(record):
    if 'scholar_url' not in record:
        return {'scholar_error': 'No matching profile entry'}
    source = read_url(record['scholar_url'])
    (CACHE / (record['id'] + '-scholar.html')).write_text(source, encoding='utf-8')
    fields = {}
    pattern = r'<div class="gsc_oci_field">([\s\S]*?)</div><div class="gsc_oci_value"[^>]*>([\s\S]*?)</div>'
    for name, value in re.findall(pattern, source):
        fields[html.unescape(re.sub('<[^>]+>', '', name))] = html.unescape(re.sub('<[^>]+>', '', value))
    parser = Links(); parser.feed(source)
    merged = [link for link in parser.items if 'cluster=' in link['href']]
    return {'scholar_fields': fields, 'scholar_cluster_urls': [urllib.parse.urljoin(PROFILE, link['href']) for link in merged]}

def crossref(record):
    doi = ''
    match = re.search(r'(10\.(?:1007|1145)/[^?#]+)', record['url'])
    if match:
        doi = match.group(1)
        url = 'https://api.crossref.org/works/' + urllib.parse.quote(doi, safe='')
        data = json.loads(read_url(url))['message']
        candidates = [data]
    else:
        url = 'https://api.crossref.org/works?' + urllib.parse.urlencode({'query.title':record['title'], 'rows':3})
        candidates = json.loads(read_url(url))['message']['items']
    ranked = sorted([(difflib.SequenceMatcher(None, normalize(record['title']), normalize(candidate.get('title',[''])[0])).ratio(),candidate) for candidate in candidates], key=lambda x:x[0], reverse=True)
    score, metadata = ranked[0]
    result = {'crossref_url':url, 'crossref_match_score':round(score,4),
              'crossref_candidates':[{'title': c.get('title'), 'doi':c.get('DOI'), 'score':round(s,4)} for s,c in ranked]}
    if score >= 0.88:
        selected = ['DOI','title','author','container-title','publisher','volume','issue','page','article-number','published','published-online','published-print','issued','event','type','URL']
        result['crossref'] = {field:metadata[field] for field in selected if field in metadata}
        (CACHE / (record['id'] + '-crossref.json')).write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['profile','scholar','crossref','summary'])
    parser.add_argument('--start',type=int,default=0)
    parser.add_argument('--end',type=int,default=1000)
    args = parser.parse_args()
    records = load_records()
    if args.stage == 'profile':
        profile(records); return
    if args.stage == 'summary':
        for r in records:
            print(json.dumps({k:r[k] for k in ['id','title','scholar_fields','crossref','scholar_error','crossref_error'] if k in r}, ensure_ascii=False), flush=True)
        return
    function = scholar if args.stage == 'scholar' else crossref
    selected = [r for r in records[args.start:args.end] if not r.get('crossref' if args.stage == 'crossref' else 'scholar_fields')]
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        futures = {pool.submit(function, record):record for record in selected}
        for future in concurrent.futures.as_completed(futures):
            record = futures[future]
            try:
                record.update(future.result())
                print(record['id'], args.stage, 'OK', record.get('crossref_match_score',''), flush=True)
            except Exception as error:
                record[args.stage + '_error'] = str(error)
                print(record['id'], args.stage, 'ERROR', str(error), flush=True)
            save(records)

if __name__ == '__main__':
    main()
