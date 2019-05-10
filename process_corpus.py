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
  with codecs.open(path, "r", "utf-8") as f:
      chaine = f.read()
  return chaine

# write result
def write_output(output_dic, options):
  output_path = "%s.results"%options.corpus
  output_json = json.dumps(output_dic, sort_keys=True, indent=2)
  with open(output_path, "w") as wfi:
    wfi.write(output_json)
  return output_path

def prepare_infos(infos, options):
  infos["is_clean"] = options.is_clean
  infos["ratio"] = options.ratio
  infos["verbose"] = options.verbose
  infos["debug"] = options.debug
  infos["name_out"] = options.name_out
  infos["showrelevant"] = options.showrelevant
  return infos

# output list of missing docs
def list_docs_not_found(missing_docs): 
    if len(missing_docs) > 0:
        path = "tmp/files_not_found"
        print "--\n %s files not found\n"%str(len(missing_docs))
        print "list here: %s\n--"%(path)
        write_utf8(path, "\n".join(missing_docs))

def skip_missing_doc(is_skipped, abs_path, doc_path):
    if not is_skipped:
        print "Not found: ", doc_path
        print "Not found either: ",  abs_path + doc_path
        print "-> the next not found files will be ignored"
        d = raw_input("Press enter to continue")
        return True
    return False

# look for doc - if missing, put in list to print later
def look_for_doc(doc_path, corpus_path, missing_doc):
    if not os.path.exists(doc_path):
        # check for absolute path also
        if not os.path.exists(os.path.dirname(os.path.abspath(corpus_path)) + "/" + doc_path):
            missing_doc.append(doc_path)
            return False

# return absolute path to document if abs_path exists, otherwise doc_path remain
def check_abs_path(doc_path, corpus_path):
    if os.path.abspath(corpus_path):
        doc_path = os.path.dirname(os.path.abspath(corpus_path)) + "/" + doc_path
    return doc_path

def start_detection(options):
  corpus_to_process = json.load(open(options.corpus))
  cpt_proc, cpt_rel = 0, 0
  output_dic, resources = {}, {}
  missing_docs = []
  is_found = False
  abs_path = ""
  
  print "\n Processing %s documents\n"%str(len(corpus_to_process))
  
  for id_file, infos in corpus_to_process.iteritems(): 
    infos["document_path"] = check_abs_path(infos["document_path"], options.corpus)
    
    if not os.path.exists(infos["document_path"]):
      abs_path = os.path.dirname(os.path.abspath(options.corpus))+"/"
      if not os.path.exists(abs_path + infos["document_path"]):
        missing_docs.append(infos["document_path"])
        is_found = skip_missing_doc(is_found, abs_path, infos["document_path"])
        # ???????
        #if not is_found:
        #  print "Not found : ",infos["document_path"]
        #  print "Not found either: ",abs_path+infos["document_path"]
        #  print "  -> the next not found files will be ignored"
        #  d = raw_input("Press enter to continue")
        #  is_found = True
        # ???????
        continue
    
    cpt_proc += 1
    
    #if abs_path != "":
    #  infos["document_path"] = abs_path + infos["document_path"]
    

    output_dic[id_file] = infos
    
    if "annotations" in output_dic[id_file]:
      del output_dic[id_file]["annotations"]# for evaluation
    
    infos = prepare_infos(infos, options)
    
    if options.verbose:
      print infos

    #lg = infos["language"] 
    if infos["language"]  not in resources:
      resources[infos["language"]] = get_ressource(infos["language"], options)
    
    o = Struct(**infos)
    results = process(o, resources[infos["language"]])
    
    if o.verbose or o.showrelevant:
      process_results(results, o)
    
    if "dis_infos" in results:
      cpt_rel += 1
    
    output_dic[id_file]["annotations"] = results["events"]
    output_dic[id_file]["is_clean"] = str(output_dic[id_file]["is_clean"])
    
    if cpt_proc%100 == 0:
      print "%s documents processed, %s relevant"%(str(cpt_proc), str(cpt_rel))
    
    output_path = write_output(output_dic, options)

  list_docs_not_found(missing_docs) 

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
