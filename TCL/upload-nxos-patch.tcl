#!/usr/bin/expect

set hostname 159.50.29.244
set username d83071
set suffixe_unix "l"
set n9k [ string tolower [lindex $argv 0] ]
set unix_username $suffixe_unix$username
set timestamp_file [ clock format [clock seconds] -format {_%Y%m%d_%Hh%Mm%Ss.log} ]
set unix [ exec /home/d83071/CONNEXION/getpass.sh "ldap_old"]
set logfile "LOG/rebond1_$timestamp_file"
set local_username "admin"
set local [ exec /home/d83071/CONNEXION/getpass.sh "local"]
set tac [ exec /home/d83071/CONNEXION/getpass.sh "tacacs"]
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

send "scp /apps/data/os_repository/CISCO/NX-OS/N9K/9.3.8/nxos.CSCvz41769-n9k_ALL-1.0.0-9.3.8.lib32_n9000.rpm $unix_username@$n9k:\r"

expect {
		"yes" { send "yes\r"; expect "assword" ; send "$tac\r"}
		"assword" { send "$tac\r"}
}

send "exit\r"

expect ">"
send "exit\r"

expect ">"
send "exit\r"

expect EOF
log_file
