check_hpadu
===========

A nagios check which runs python-hpadureport-parser

It is currently hard coded to only check "Bus Faults" for all the disks.

The parser (loops through all the disks in ADUReport.xml):
 - https://github.com/martbhell/python-hpadureport

Some ansible roles to configure nagios, cronjobs and HP tools:
 - https://github.com/CSC-IT-Center-for-Science/ansible-role-hp-diag
 - https://github.com/CSC-IT-Center-for-Science/ansible-role-nrpe
 - https://github.com/CSC-IT-Center-for-Science/ansible-role-nrpe-plugins
 - https://github.com/CSC-IT-Center-for-Science/ansible-role-hp-spp
