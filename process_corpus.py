from daniel import process
import glob
import sys
import json
import os
import time
import codecs
from tools import *
from daniel import get_ressource, process_results

class Struct:
  def __init__(self, **entries):
    self.__dict__.update(entries)

def open_utf8(path):
  # f = codecs.open(path,"r", "utf-8")
  # chaine = f.read()
  # f.close()
  with codecs.open(path, "r", "utf-8") as f:
      chaine = f.read()
  return chaine

def  write_output(output_dic, options):
  output_path = "%s.results"%options.corpus
  output_json = json.dumps(output_dic, sort_keys=True, indent=2)
  wfi = open(output_path, "w")
  wfi.write(output_json)
  wfi.close()
  return output_path

def prepare_infos(infos, options):
  infos["is_clean"] = options.is_clean
  infos["ratio"] = options.ratio
  infos["verbose"] = options.verbose
  infos["debug"] = options.debug
  infos["name_out"] = options.name_out
  infos["showrelevant"] = options.showrelevant
  return infos

def  start_detection(options):
  corpus_to_process = json.load(open(options.corpus))
  cpt_proc, cpt_rel = 0, 0
  output_dic, resources = {}, {}
  not_found = []
  has_not_found = False
  abs_path = ""
  print "\n Processing %s documents\n"%str(len(corpus_to_process))
  
  for id_file, infos in corpus_to_process.iteritems():
    if not os.path.exists(infos["document_path"]):
      abs_path = os.path.dirname(os.path.abspath(options.corpus))+"/"
      if not os.path.exists(abs_path + infos["document_path"]):
        not_found.append(infos["document_path"])
        if not has_not_found:
          print "Not found : ",infos["document_path"]
          print "Not found either: ",abs_path+infos["document_path"]
          print "  -> the next not found files will be ignored"
          d = raw_input("Press enter to continue")
          has_not_found = True
        continue
    
    cpt_proc += 1
    
    if abs_path != "":
      infos["document_path"] = abs_path + infos["document_path"]
    
    output_dic[id_file] = infos
    
    if "annotations" in output_dic[id_file]:
      del output_dic[id_file]["annotations"]# for evaluation
    
    infos = prepare_infos(infos, options)
    
    if options.verbose:
      print infos

    #lg = infos["language"] 
    if infos["language"]  not in resources:
      resources[infos["language"] = get_ressource(infos["language"], options)
    
    o = Struct(**infos)
    results = process(o, resources[infos["language"])
    
    if o.verbose or o.showrelevant:
      process_results(results, o)
    
    if "dis_infos" in results:
      cpt_rel += 1
    
    output_dic[id_file]["annotations"] = results["events"]
    output_dic[id_file]["is_clean"] = str(output_dic[id_file]["is_clean"])
    
    if cpt_proc%100 == 0:
      print "%s documents processed, %s relevant"%(str(cpt_proc), str(cpt_rel))
    
    output_path = write_output(output_dic, options)
  
  if len(not_found) > 0:
    path_not_found = "tmp/files_not_found"
    print "--\n %s files not found\n"%str(len(not_found))
    print " list here : %s\n--"%(path_not_found)
    write_utf8(path_not_found, "\n".join(not_found))
  return cpt_proc, cpt_rel, output_path

if __name__=="__main__":
  start = time.clock()
  options = get_args()
  print options
  if options.corpus==None:
    print "Please specify a Json file (-c), see README.txt for more informations about the format. To use the default example :\n -c docs/Indonesian_GL.json"
    exit()
  else:
    options.document_path ="None"
  try:
    os.makedirs("tmp")
  except:
    pass
  cpt_doc, cpt_rel, output_path = start_detection(options)
  end = time.clock()
  print "%s docs proc. in %s seconds"%(str(cpt_doc), str(round(end-start, 4)))
  print "  %s relevant documents"%(str(cpt_rel))
  print "  Results written in %s"%output_path
  if options.evaluate:
    print "\nEvaluation\n :"
    cmd = "python evaluate.py %s %s"%(options.corpus, output_path)
    print "-->",cmd
    os.system(cmd)
