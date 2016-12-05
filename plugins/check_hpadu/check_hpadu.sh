#!/bin/bash

# A script written by Johan Guldmyr @ CSC 2016 to:
# extract and compare Bus Faults bweteen two HP ADU Reports
# and return an appropriate nagiosy code if it's 
# increasing too much
#####

# requirements: unzip, python, https://github.com/martbhell/python-hpadureport

#########
hpssacli_dir="/var/lib/hpssacli_diags/"
python_hpadureport_parser_path="/usr/local/bin/python-hpadureport-parser.py"
tempdir_second_last="/var/lib/hpssacli_diags/temp_second_last"
tempdir_last="/var/lib/hpssacli_diags/temp_last"

OK=0
WARNING=1
CRITICAL=2
UNKNOWN=3

if [ ! -f "/bin/unzip" ]; then
	echo "UNKNOWN: /bin/unzip is not available, install"
	exit $UNKNOWN
fi
if [ ! -f "$python_hpadureport_parser_path" ]; then
	echo "UNKNOWN: $python_hpadureport_parser_path is not available, install"
	exit $UNKNOWN
fi

dircleanup() {

  if [ -d "$tempdir_second_last" ]; then
    if [ "$(ls -A $tempdir_second_last)" ]; then
        #echo "Take action $tempdir_second_last is not Empty"
        rm $tempdir_second_last/ADUReport.xml
    fi
    rmdir $tempdir_second_last
  fi
  
  if [ -d "$tempdir_last" ]; then
    if [ "$(ls -A $tempdir_last)" ]; then
        #echo "Take action $tempdir_last is not Empty"
        rm $tempdir_last/ADUReport.xml
    fi
    rmdir $tempdir_last
  fi

}

dircleanup
cd "$hpssacli_dir"
second_last_file="$(ls -Art "$hpssacli_dir"|tail -n2|head -n1)"
last_file="$(ls -Art "$hpssacli_dir"|tail -n1)"
if [ "x$second_last_file" == "x" ] || [ "x$last_file" == "x" ]; then
  echo "WARNING: Not enough reports generated"
  exit $WARNING
elif [ "$second_last_file" == "$last_file" ]; then
  echo "WARNING: Both reports are the same - generate more reports"
  exit $WARNING
fi
mkdir -p "$tempdir_second_last"
mkdir -p "$tempdir_last"

#unzip quietly, exclude all except .xml file
/bin/unzip -q "$second_last_file" -x ADUReport.txt ADUReport.htm report.checksum -d "$tempdir_second_last"
/bin/unzip -q "$last_file" -x ADUReport.txt ADUReport.htm report.checksum -d "$tempdir_last"
python $python_hpadureport_parser_path -1 "$tempdir_second_last/ADUReport.xml" -2 "$tempdir_last/ADUReport.xml" -e "Bus Faults"
aduparserreturncode=$?

exit $aduparserreturncode

dircleanup
