#!/usr/bin/expect

set hostname 159.50.66.10
set username d83071
set suffixe_unix "l"
set n9k [ string tolower [lindex $argv 0] ]
set type_connexion [ exec /home/d83071/CONNEXION/get_connexion.sh $n9k]
set unix_username $suffixe_unix$username
set timestamp_file [ clock format [clock seconds] -format {_%Y%m%d_%Hh%Mm%Ss.log} ]
set unix [ exec /home/d83071/CONNEXION/getpass.sh "rebond_old"]
set logfile "LOG/rebond1_$timestamp_file"
set local_username "admin"
set local [ exec /home/d83071/CONNEXION/getpass.sh "LOCAL0"]
set tac [ exec /home/d83071/CONNEXION/getpass.sh "tacacs"]
set timeout -1

switch $type_connexion {
    LOCAL0 {
            set username_cur $local_username
            set password_cur $local
    }

	TSK {
		set username_cur $local_username
		set password_cur $local
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

send "scp /apps/data/os_repository/CISCO/NX-OS/N9K/9.3.9/nxos.9.3.9.bin $username_cur@$n9k:\r"

expect {
		"yes" { send "yes\r"; expect "assword" ; send "$password_cur\r"}
		"assword" { send "$password_cur\r"}
}

expect "\\$"
send "\r"

expect "\\$"
send "scp /apps/data/os_repository/CISCO/NX-OS/N9K/9.3.9/nxos.CSCwa91783-n9k_ALL-1.0.0-9.3.9.lib32_n9000.rpm $username_cur@$n9k:\r"

expect {
		"yes" { send "yes\r"; expect "assword" ; send "$password_cur\r"}
		"assword" { send "$password_cur\r"}
}

expect "\\$"
send "scp /apps/data/os_repository/CISCO/NX-OS/N9K/9.3.9/nxos.CSCwb70210-n9k_ALL-1.0.0-9.3.9.lib32_n9000.rpm $username_cur@$n9k:\r"

expect {
		"yes" { send "yes\r"; expect "assword" ; send "$password_cur\r"}
		"assword" { send "$password_cur\r"}
}

expect "\\$"
send "\r"

expect "\\$"
send "scp /apps/data/os_repository/CISCO/NX-OS/N9K/9.3.9/n9000-epld.9.3.9.img $username_cur@$n9k:\r"

expect {
		"yes" { send "yes\r"; expect "assword" ; send "$password_cur\r"}
		"assword" { send "$password_cur\r"}
}
expect "\\$"
send "\r"

expect "\\$"
send "scp /apps/data/os_repository/CISCO/NX-OS/N9K/9.3.9/nxos.CSCwe09300-n9k_ALL-1.0.0-9.3.9.lib32_n9000.rpm $username_cur@$n9k:\r"

expect {
                "yes" { send "yes\r"; expect "assword" ; send "$password_cur\r"}
                "assword" { send "$password_cur\r"}
}



expect "\\$"
send "\r"

expect "\\$"
send "exit\r"

expect "\\$"
send "exit\r"

expect "\\$"
send "exit\r"

expect EOF
log_file
