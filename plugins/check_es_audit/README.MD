This is a nagios plugin that can be used to query elasticsearch. The script itself in this case is just searching if anybody has been using the program "shred" on any of the servers that are shipping auditd logs to ES. 
 
  * check_es_audit.py 
    * Python script that calls check_es_audit_util.sh, parses the output. Has a dashboard URL and the location of check_es_audit_util.sh hardcoded. 
  * check_es_audit_util.sh 
    * The CURL command as gotten from a kibana3 term facet. 
