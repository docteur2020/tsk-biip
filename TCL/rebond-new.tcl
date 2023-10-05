#!/usr/bin/expect

set hostname 159.50.66.10
set username d83071
set suffixe_unix "l"
set unix_username $suffixe_unix$username
set timestamp_file [ clock format [clock seconds] -format {_%Y%m%d_%Hh%Mm%Ss.log} ]
set unix [ exec /home/d83071/CONNEXION/getpass.sh "adm" ]
set logfile "LOG/rebondnew_$timestamp_file"



spawn ssh -o StrictHostKeyChecking=no -l $unix_username $hostname
log_file -noappend $logfile 
puts "p:$unix#"
expect {
		"yes" { send "yes\r";expect "assword" ; puts "là"  send "$unix\r"}
		"assword" { puts "ici"; send "$unix\r"}
		">" { send "\r" }
		"\\$" { puts "ici2"; send "\r" }
}
expect {
		">" { send "\r" }
		"#" { send "\r" }
		"\\$" { send "\r" }
}
interact

log_file
