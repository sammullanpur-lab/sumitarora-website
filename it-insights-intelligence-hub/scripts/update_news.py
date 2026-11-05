#!/usr/bin/env python3
"""Publish original-source technology headlines and CISA KEV records; stdlib only."""
import datetime as dt
import email.utils
import html
import json
import pathlib
import re
import urllib.request
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEST = ROOT / 'content' / 'news.json'
SOURCES = [
    ('Microsoft', 'Microsoft', 'https://devblogs.microsoft.com/microsoft365dev/feed/'),
    ('Microsoft', 'Microsoft', 'https://devblogs.microsoft.com/identity/feed/'),
    ('Fortinet', 'Fortinet', 'https://filestore.fortinet.com/fortiguard/rss/ir.xml'),
    ('Infrastructure', 'Microsoft Azure', 'https://azure.microsoft.com/en-us/blog/feed/'),
]
CISA_URL = 'https://raw.githubusercontent.com/cisagov/kev-data/develop/known_exploited_vulnerabilities.json'


def clean(value, limit=400):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]*>', ' ', value or ''))).strip()[:limit]


def childtext(node, name):
    for child in node:
        if child.tag.split('}')[-1] == name:
            return ''.join(child.itertext()).strip()
    return ''


def parse_date(value):
    try:
        return email.utils.parsedate_to_datetime(value).astimezone(dt.timezone.utc).isoformat()
    except (TypeError, ValueError, IndexError):
        pass
    try:
        parsed = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed.astimezone(dt.timezone.utc).isoformat()
    except (AttributeError, TypeError, ValueError):
        return ''


def download(url, accept):
    request = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; SumitAroraTechnologyBriefing/1.1)',
        'Accept': accept,
    })
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read(4_000_000)


def fetch_rss(category, source, url):
    root = ET.fromstring(download(url, 'application/rss+xml, application/atom+xml, application/xml, text/xml'))
    entries = [node for node in root.iter() if node.tag.split('}')[-1] in ('item', 'entry')]
    results = []
    for node in entries[:45]:
        title = clean(childtext(node, 'title'), 180)
        link = childtext(node, 'link')
        if not link:
            for child in node:
                if child.tag.split('}')[-1] == 'link' and child.attrib.get('href') and child.attrib.get('rel', 'alternate') == 'alternate':
                    link = child.attrib['href']
                    break
        date = parse_date(childtext(node, 'pubDate') or childtext(node, 'published') or childtext(node, 'updated'))
        summary = clean(childtext(node, 'description') or childtext(node, 'summary') or childtext(node, 'content'), 260)
        if title and date and link.startswith('https://') and urlparse(link).hostname:
            results.append({'title': title, 'url': link, 'summary': summary, 'published': date, 'source': source, 'category': category})
        if len(results) == 10:
            break
    return results


def fetch_cisa():
    catalog = json.loads(download(CISA_URL, 'application/json'))
    records = sorted(catalog['vulnerabilities'], key=lambda item: item.get('dateAdded', ''), reverse=True)
    results = []
    for entry in records[:10]:
        cve = entry.get('cveID', '')
        date = parse_date(entry.get('dateAdded', ''))
        if not re.fullmatch(r'CVE-\d{4}-\d{4,}', cve) or not date:
            continue
        title = clean(cve + ': ' + entry.get('vulnerabilityName', ''), 180)
        results.append({
            'title': title,
            'url': 'https://nvd.nist.gov/vuln/detail/' + cve,
            'summary': clean(entry.get('shortDescription', ''), 260),
            'published': date,
            'source': 'CISA KEV',
            'category': 'Cybersecurity',
        })
    return results


def main():
    try:
        previous = json.loads(DEST.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        previous = {'items': [], 'updated_at': None}
    fresh = []
    successes = 0
    for category, source, url in SOURCES:
        try:
            rows = fetch_rss(category, source, url)
            if not rows:
                raise ValueError('Feed contained no usable dated entries')
            fresh.extend(rows)
            successes += 1
            print(source, len(rows), 'items')
        except Exception as exc:
            print('Skipping', source, type(exc).__name__, str(exc)[:150])
    try:
        rows = fetch_cisa()
        if not rows:
            raise ValueError('No valid CISA KEV records')
        fresh.extend(rows)
        successes += 1
        print('CISA KEV', len(rows), 'items')
    except Exception as exc:
        print('Skipping CISA KEV', type(exc).__name__, str(exc)[:150])
    if not successes:
        print('No sources available; preserving previous snapshot')
        return
    seen = set()
    combined = []
    for item in sorted(fresh + previous.get('items', []), key=lambda item: item.get('published', ''), reverse=True):
        url = item.get('url', '')
        key = url.rstrip('/').lower()
        if key and key not in seen and url.startswith('https://'):
            seen.add(key)
            combined.append(item)
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps({'updated_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'items': combined[:60]}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Saved', len(combined[:60]), 'articles')


if __name__ == '__main__':
    main()
