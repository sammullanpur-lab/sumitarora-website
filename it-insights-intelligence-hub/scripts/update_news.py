#!/usr/bin/env python3
"""Fetch official technology RSS/Atom feeds into a static JSON snapshot. Python stdlib only."""
import datetime as dt, email.utils, json, pathlib, re, urllib.request, xml.etree.ElementTree as ET, html
from urllib.parse import urlparse

ROOT=pathlib.Path(__file__).resolve().parents[1]; DEST=ROOT/'content/news.json'
SOURCES=[
 ('Microsoft','Microsoft','https://devblogs.microsoft.com/microsoft365dev/feed/'),
 ('Microsoft','Microsoft','https://devblogs.microsoft.com/identity/feed/'),
 ('Fortinet','Fortinet','https://www.fortinet.com/blog/rss.xml'),
 ('Cybersecurity','CISA','https://www.cisa.gov/news.xml'),
 ('Infrastructure','Microsoft Azure','https://azure.microsoft.com/en-us/blog/feed/'),
]
def clean(s):return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]*>',' ',s or ''))).strip()[:400]
def childtext(node,name):
 for c in node:
  if c.tag.split('}')[-1]==name:return ''.join(c.itertext()).strip()
 return ''
def parse_date(s):
 try:
  d=email.utils.parsedate_to_datetime(s);return d.astimezone(dt.timezone.utc).isoformat()
 except Exception:pass
 try:return dt.datetime.fromisoformat(s.replace('Z','+00:00')).astimezone(dt.timezone.utc).isoformat()
 except Exception:return ''
def fetch(cat,source,url):
 req=urllib.request.Request(url,headers={'User-Agent':'ITInsightsNewsFetcher/1.0 (+static-site-feed-aggregation)','Accept':'application/rss+xml, application/atom+xml, application/xml, text/xml'})
 with urllib.request.urlopen(req,timeout=14) as r:raw=r.read(3_000_000)
 root=ET.fromstring(raw);entries=[n for n in root.iter() if n.tag.split('}')[-1] in ('item','entry')]
 result=[]
 for node in entries[:35]:
  title=clean(childtext(node,'title'))[:180];link=childtext(node,'link');summary=clean(childtext(node,'description') or childtext(node,'summary') or childtext(node,'content'))[:260]
  if not link:
   for c in node:
    if c.tag.split('}')[-1]=='link' and c.attrib.get('href') and c.attrib.get('rel','alternate')=='alternate':link=c.attrib['href'];break
  date=parse_date(childtext(node,'pubDate') or childtext(node,'published') or childtext(node,'updated'))
  if not title or not date or not link.startswith('https://'):continue
  host=urlparse(link).hostname or ''
  if not host or host.endswith('.invalid'):continue
  result.append(dict(title=title,url=link,summary=summary,published=date,source=source,category=cat))
 return result

def main():
 try:previous=json.loads(DEST.read_text())
 except Exception:previous={'items':[],'updated_at':None}
 items=[];success=0
 for cat,source,url in SOURCES:
  try:
   rows=fetch(cat,source,url);items+=rows;success+=1;print(source,len(rows),'items')
  except Exception as e:print('Skipping',source,type(e).__name__,str(e)[:130])
 if not success:
  print('No feeds available; preserving existing snapshot');return
 # Preserve entries from prior successful fetches if a source fails temporarily.
 items+=previous.get('items',[])
 seen=set();unique=[]
 for item in sorted(items,key=lambda x:x.get('published',''),reverse=True):
  url=item.get('url','');key=url.rstrip('/').lower()
  if key and key not in seen and url.startswith('https://'):
   seen.add(key);unique.append(item)
 DEST.write_text(json.dumps({'updated_at':dt.datetime.now(dt.timezone.utc).isoformat(),'items':unique[:60]},ensure_ascii=False,indent=2)+'\n')
 print('Saved',len(unique[:60]),'articles')
if __name__=='__main__':main()
