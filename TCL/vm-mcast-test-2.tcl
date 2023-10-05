#!/usr/bin/expect

set hostname 10.253.106.56
set unix_username "momo"
set timestamp_file [ clock format [clock seconds] -format {_%Y%m%d_%Hh%Mm%Ss.log} ]
set unix "momo"
set logfile "LOG/rebond_multicast_1_$timestamp_file"



spawn ssh -o StrictHostKeyChecking=no -l $unix_username $hostname
log_file -noappend $logfile 
expect {
		"yes" { send "yes\r";expect "assword" ; send "$unix\r"}
		"assword" { send "$unix\r"}
		"\\\$" { send "\r" }
}
expect "\\\$"
send "\r"

interact

log_file
