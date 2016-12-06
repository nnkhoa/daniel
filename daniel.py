#!/usr/bin/env python
# -*- coding: utf-8 -*-
import codecs
import sys
import os
import re
import glob
sys.path.append('./rstr_max')
from tools_karkkainen_sanders import *
from rstr_max import *
import os

def exploit_rstr(r,rstr, infos):
  set_id_text = infos["set_id_text"]
  desc = []
  for (offset_end, nb), (l, start_plage) in r.iteritems():
    ss = rstr.global_suffix[offset_end-l:offset_end]
    set_occur = set()
    for o in xrange(start_plage, start_plage+nb) :
      id_str = rstr.idxString[rstr.res[o]]
      set_occur.add(id_str)
    inter = set_occur.intersection(set_id_text)
    if len(inter)>1 and len(set_occur)>len(inter):
      disease_ids = [x-len(set_id_text) for x in set_occur.difference(set_id_text)]
      l_distances = []
      for d in inter:
        l_distances.append(min(d, len(set_id_text)-d-1))
      desc.append([ss, disease_ids, sorted(l_distances)])
  return desc

def get_score(ratio, dist):
  score = pow(ratio, 1+dist[0]*dist[1])
  return score
def filter_desc(desc, l_rsc):
  out = []
  for ss, dis_list, distances in desc:
    for id_dis in dis_list:
      disease_name = l_rsc[id_dis]
      ratio = float(len(ss))/len(disease_name)
      if ratio<0.7:continue
      score = get_score(ratio, distances)
      out.append([score, disease_name, ss, distances])
  return sorted(out,reverse=True)

def get_desc(string, rsc):
  set_id_text = set()
  rstr = Rstr_max()
  cpt = 0
  l_rsc = rsc.keys()
  for s in string:
    rstr.add_str(s)
    set_id_text.add(cpt)
    cpt+=1
  for r in l_rsc:
    rstr.add_str(r)
  r = rstr.go()
  infos ={"set_id_text" : set_id_text}
  desc = exploit_rstr(r,rstr, infos)
  res = filter_desc(desc, l_rsc)
  return res 

def zoning(string):
  z = re.split("<p>", string)
  z = [x for x in z if x!=""]
  return z

def analyze(string, ressource): 
  zones = zoning(string)
  dis_infos = get_desc(zones, ressource["diseases"])
  events = []
  if len(dis_infos)>0:
    loc_infos = get_desc(zones, ressource["locations"])
    if len(loc_infos)==0:
      loc = ressource["locations"]["default_value"]
    else:
      loc = loc_infos[0][1]
    for dis in dis_infos[:1]:
      events.append([dis[1], loc])
  return events

def get_ressource(lg):
  dic = {}
  path_diseases = "ressources/diseases_%s.json"%lg
  path_locations= "ressources/locations_%s.json"%lg
  dic["locations"] = eval(open_utf8(path_locations))
  dic["diseases"] = eval(open_utf8(path_diseases))
  return dic

def open_utf8(path):
  f = codecs.open(path,"r", "utf-8")
  string = f.read()
  f.close()
  return string

def get_clean_html(path, language):
  try:
    tmp = "tmp/out"
    os.system("rm %s"%tmp)
    cmd = "python -m justext -s %s %s >tmp/out"%(language, path)
    os.system(cmd)
    out = open_utf8(tmp)
  except:
    print "Justext is missing"
    out = open_utf8(path)
  return out
  
def process(language, document_path):
  string = get_clean_html(document_path, language)
  ressource = get_ressource(language)
  result = analyze(string, ressource)
  return result

if __name__=="__main__":
  try:
    os.makedirs("tmp")
  except:
    pass
  print "="*20
  print "Usage : argv[1]=language argv[2]=document_path"
  print "example:\n python daniel_v5.py Indonesian some_document_indonesian.html"
  print "="*20
  language = sys.argv[1]
  document_path = sys.argv[2]
  result = process(language, document_path)
  print result
