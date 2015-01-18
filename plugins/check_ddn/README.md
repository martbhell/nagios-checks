A nagios check that does some health checking of a DDN SFA12k. 
Depends on the python API libraries/egg from DDN which can 
be found on:  
http://www.ddn.com/support/product-downloads-and-documentation 
 
It basically does many health checks in serial. 

Health checks:

  * overall controller health
  * enclosures
  * UPS
  * unassigned pool
  * internal disks
  * jobs on RAID pools
  * hosts
  * presentations
  * pools
  * temperature sensors

Roadmap: 

  * refactor (some health checks are just copy-pasted to be run if the system is in health_critical or health_non_critical) 
  * Move username/password out of the check (stored in a separate file perhaps) 
  * Don't assume so much, for example it assumes two controllers and 10 disk shelves per SFA12k. 
