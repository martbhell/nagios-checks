This is a nagios plugin can be used to count number of occurences of a string in the output of lspci

Sample output:

<pre>
$ bash check_count_lspci.sh  -w 0 -c 8 -d NVIDIA
OK - 8 NVIDIA devices found | NVIDIAdevices=8
</pre>
