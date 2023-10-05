#!/usr/bin/expect

set hostname 159.50.29.208
set username d83071
set suffixe_unix "l"
set unix_username $suffixe_unix$username
set timestamp_file [ clock format [clock seconds] -format {_%Y%m%d_%Hh%Mm%Ss.log} ]
set unix [ exec /home/d83071/CONNEXION/getpass.sh "ldap"]
set logfile "LOG/rebond1_$timestamp_file"

puts "\n$unix:\n"

spawn ssh -o StrictHostKeyChecking=no -l $unix_username $hostname
log_file -noappend $logfile 
expect {
		"yes/no" { send "yes\r";expect "assword" ; send "$unix\r"}
		"assword" { send "$unix\r"}
		"\\$" { send "\r" }
}
expect "\\$"
send "bash\r"

interact

log_file
