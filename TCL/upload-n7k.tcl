#!/usr/bin/expect

set hostname 159.50.29.244
set username d83071
set suffixe_unix "l"
set n7k [ string tolower [lindex $argv 0] ]
set unix_username $suffixe_unix$username
set timestamp_file [ clock format [clock seconds] -format {_%Y%m%d_%Hh%Mm%Ss.log} ]
set unix [ exec /home/d83071/CONNEXION/getpass.sh "ldap_old"]
set logfile "LOG/rebond1_$timestamp_file"
set local_username "admin"
set tacacs [ exec /home/d83071/CONNEXION/getpass.sh "tac"]
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
send "scp /apps/data/os_repository/CISCO/NX-OS/N7K/n7700-s2-kickstart.7.3.4.D1.1.bin $unix_username@$n7k:\r"

expect {
                "yes" { send "yes\r"; expect "assword" ; send "$tacacs\r"}
                "assword" { send "$tacacs\r"}
}
expect ">"
send "\r"

expect ">"
send "scp /apps/data/os_repository/CISCO/NX-OS/N7K/n7700-s2-epld.7.3.4.D1.1.img $unix_username@$n7k:\r"

expect {
                "yes" { send "yes\r"; expect "assword" ; send "$tacacs\r"}
                "assword" { send "$tacacs\r"}
}
expect ">"
send "\r"

expect ">"
send "scp /apps/data/os_repository/CISCO/NX-OS/N7K/n7700-s2-dk9.7.3.4.D1.1.bin $unix_username@$n7k:\r"

expect {
                "yes" { send "yes\r"; expect "assword" ; send "$tacacs\r"}
                "assword" { send "$tacacs\r"}
}
expect ">"
send "exit\r"

expect ">"
send "exit\r"

expect EOF
log_file
