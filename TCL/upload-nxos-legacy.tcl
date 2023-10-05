#!/usr/bin/expect

set hostname 159.50.66.10
set username d83071
set suffixe_unix "l"
set n5k [ string tolower [lindex $argv 0] ]
set type_connexion [ exec /home/d83071/CONNEXION/get_connexion.sh $n5k]
set unix_username $suffixe_unix$username
set timestamp_file [ clock format [clock seconds] -format {_%Y%m%d_%Hh%Mm%Ss.log} ]
set unix [ exec /home/d83071/CONNEXION/getpass.sh "ldap_old"]
set logfile "LOG/rebond1_$timestamp_file"
#set IP [exec  /home/d83071/CONNEXION/get_IP.sh $n5k]
set local_username "admin"
set local [ exec /home/d83071/CONNEXION/getpass.sh "local"]
set timeout -1
set tac [ exec /home/d83071/CONNEXION/getpass.sh "tacacs"]

switch $type_connexion {
	LOCAL0 {
		set username_cur $local_username
		set password_cur $local
	}
	TSK {
		set type [ string tolower [ exec /home/d83071/CONNEXION/get_param.sh $n5k "3" ] ]
		set password_cur  [ exec /home/d83071/CONNEXION/getpass.sh $type ]
		set username_cur  [ exec /home/d83071/CONNEXION/getlogin.sh $type ]
	}
	default {
		set username_cur $unix_username
		set password_cur $tac
	}
}

puts "$password_cur"

spawn ssh -o StrictHostKeyChecking=no -l $unix_username $hostname
log_file -noappend $logfile 
expect {
		"yes" { send "yes\r";expect "assword" ; send "$unix\r"}
		"assword" { send "$unix\r"}
		">" { send "\r" }
}
expect "\\$"
send "\r"

expect "\\$"
send "scp /apps/data/os_repository/CISCO/NX-OS/n6000-uk9-kickstart.7.3.8.N1.1.bin $username_cur@$n5k:\r"

expect "assword"
send "$password_cur\r"

expect "\\$"
send "\r"

expect "\\$"
send "\r"

send "scp /apps/data/os_repository/CISCO/NX-OS/n6000-uk9.7.3.8.N1.1.bin $username_cur@$n5k:\r"

expect "assword"
send "$password_cur\r"

expect "\\$"
send "exit\r"

expect "\\$"
send "exit\r"

expect EOF
log_file
