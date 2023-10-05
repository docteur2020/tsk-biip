#!/usr/bin/expect

set hostname 159.50.66.10
set username d83071
set suffixe_unix "l"
set asr [ string tolower [lindex $argv 0] ]
set type_connexion [ exec /home/d83071/CONNEXION/get_connexion.sh $asr]
set unix_username $suffixe_unix$username
set timestamp_file [ clock format [clock seconds] -format {_%Y%m%d_%Hh%Mm%Ss.log} ]
set unix [ exec /home/d83071/CONNEXION/getpass.sh "rebond_old"]
set logfile "LOG/rebond1_$timestamp_file"
set local_username "admin"
set local [ exec /home/d83071/CONNEXION/getpass.sh "local"]
set tac [ exec /home/d83071/CONNEXION/getpass.sh "tacacs"]
set timeout -1

switch $type_connexion {
	LOCAL0 {
		set username_cur $local_username
		set password_cur $local
	}
	TSK {
		set type [ string tolower [ exec /home/d83071/CONNEXION/get_param.sh $asr "3" ] ]
		set password_cur  [ exec /home/d83071/CONNEXION/getpass.sh $type ]
		set username_cur  [ exec /home/d83071/CONNEXION/getlogin.sh $type ]
	}
	default {
		set username_cur $unix_username
		set password_cur $tac
	}
}

puts "CONNEXION $type_connexion"
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


send "scp /apps/data/os_repository/CISCO/IOS-XR/ACDC/7.5.2-GISO/asr9k-goldenk9-x64-7.5.2-ASR9K752.iso $username_cur@$asr:/misc/disk1/asr9k-goldenk9-x64-7.5.2-ASR9K752.iso\r"

expect {
		"yes" { send "yes\r"; expect "assword" ; send "$password_cur\r"}
		"assword" { send "$password_cur\r"}
}

send "exit\r"

expect "\\$"
send "exit\r"

expect "\\$"
send "exit\r"

expect EOF
log_file
