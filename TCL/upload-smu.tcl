#!/usr/bin/expect

set hostname 159.50.29.244
set username d83071
set suffixe_unix "l"
set n9k [ string tolower [lindex $argv 0] ]
set unix_username $suffixe_unix$username
set timestamp_file [ clock format [clock seconds] -format {_%Y%m%d_%Hh%Mm%Ss.log} ]
set unix [ exec /home/d83071/CONNEXION/getpass.sh "ldap_old"]
set logfile "LOG/rebond1_$timestamp_file"
set local_username "ld83071"
set local [ exec /home/d83071/CONNEXION/getpass.sh "tac"]
set timeout -1

spawn ssh -o StrictHostKeyChecking=no -l $unix_username $hostname
log_file -noappend $logfile 
expect {
		"yes" { send "yes\r";expect "assword" ; send "$unix\r"}
		"assword" { send "$unix\r"}
		">" { send "\r" }
}
expect ">"
send "\r"

expect ">"
send "scp /home/ld83071/OS/nxos.CSCvw89875-n9k_ALL-1.0.0-9.3.5.lib32_n9000.rpm $local_username@$n9k:\r"

expect {
		"yes" { send "yes\r"; expect "assword" ; send "$local\r"}
		"assword" { send "$local\r"}
}

expect ">"
send "exit\r"

expect ">"
send "exit\r"

expect EOF
log_file
