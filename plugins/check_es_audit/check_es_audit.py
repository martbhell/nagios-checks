#!/usr/bin/python

# Nagios Script written by Johan Guldmyr @ CSC 2015 to check if anybody has used "shred".

import subprocess # run curler
import json # parse output from curler
import sys # control exit code
import os # check if curler exist
import optparse # parse arguments
import datetime # measure execution time

NAGIOS_UNKNOWN=3
NAGIOS_CRITICAL=2
NAGIOS_WARNING=1
NAGIOS_OK=0

parser = optparse.OptionParser()
parser.add_option('-g', '--good_terms', help='CSV list of approved terms', dest="good_terms")
(opts, args) = parser.parse_args()

if opts.good_terms == None:
  # If it's not set, set it to an empty list == any hits are bad.
  opts.good_terms = []

## We use some lists
seen_terms = []
good_terms = opts.good_terms
bad_terms = []
## Settings
debug = 0
dashboardurl = "https://hostname/urltoadashboardwithmoreinfo"
curler = "/usr/local/nagios/libexec/check_es_audit_util.sh"
## End Settings

def safety():

  if os.path.isfile(curler) == True:
    return
  else:
    print "UNKNOWN: %s does not exist in the same dir as %s." % (curler, os.path.basename(__file__))
    sys.exit(NAGIOS_UNKNOWN)
  

def query():

  # in variable curler we store the curl POST string from a term facet in kibana. Changes to the elasticsearch query is in there.
  proc = subprocess.Popen(["/bin/bash", curler], stdout=subprocess.PIPE)
  (out, err) = proc.communicate()
  # store that json data in json
  json_data = json.loads(out)
  # print the facets term
  for i in json_data["facets"]["terms"]["terms"]:
    # store each seen term in a list
    seen_terms.append(i["term"])
  
  if debug != 0:
    print seen_terms
    print good_terms
  
  for seen in seen_terms:
    if seen not in good_terms:
      # store each seen term that is not in good_terms list
      bad_terms.append(seen)
  
  return([bad_terms, len(bad_terms), len(seen_terms)])

def nagios():
  t1 = datetime.datetime.now() # measure how long it takes to do query()

  query_data = query()
  query_bad_terms = sorted(query_data[0])
  query_perfdata_bad_terms = query_data[1]
  query_perfdata_seen_terms = query_data[2]

  t2 = datetime.datetime.now()
  timeofquery = t2 - t1

  nicer_list_of_bad_terms = ""
  for i in query_bad_terms:
    nicer_list_of_bad_terms+=str(i +",")

  if query_bad_terms != []:
    print "CRIT: UID(s) %s ran shred in the last 1 hour. %s | bad_terms=%s seen_terms=%s query_microseconds=%s" % (nicer_list_of_bad_terms, dashboardurl, query_perfdata_bad_terms, query_perfdata_seen_terms, timeofquery.microseconds)
    sys.exit(NAGIOS_CRITICAL)
  if query_bad_terms == []:
    print "OK: Nobody has run shred in the last 1 hour. %s | bad_terms=%s seen_terms=%s query_microseconds=%s" % (dashboardurl, query_perfdata_bad_terms, query_perfdata_seen_terms, timeofquery.microseconds)
    sys.exit(NAGIOS_OK)

### Run nagios() this file is called directly, not if imported. 

if __name__ == '__main__':
  safety()
  nagios()
