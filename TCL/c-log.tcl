#!/usr/bin/expect -f

set timeout 45
set hostname [ string tolower [lindex $argv 0] ]
set console_info [ exec /home/d83071/CONNEXION/CONSOLE/get_console.sh $hostname]
set console [ split $console_info ":" ]
set CONNEXION [lindex $console 0]
puts $CONNEXION
set REBOND [lindex $console 1]
set PORT [lindex $console 2]
regsub -line {\n} $PORT {} PORT
set username "d83071"
set suffixe_unix "l"
set unix_username $suffixe_unix$username
set date_ [ exec date +%d%m%y_%Hh%Mm%Ss ]
set fichier "LOG/${hostname}_${date_}.log"

set ip_rebond "159.50.29.244"

if { $argc == 2 } { set ip_rebond "159.50.29.208" } 

set secret_local [ exec /home/d83071/CONNEXION/getpass.sh "local"]
set tacacs [ exec /home/d83071/CONNEXION/getpass.sh "tac"]

source ./fonctions-connexion.tcl

switch $CONNEXION {

	LOCAL {
	    puts "\nINTERACT directly\n"
	    spawn ssh $unix_username@$ip_rebond
		rebond $ip_rebond
		send "ssh -l root:$PORT $REBOND\r"
		#connexion $unix_username $password_tacacs $password_tacacs $passphrase
		expect {
			"yes" {send "yes\r"}
			"connection" { 
							puts "ici\n\n"
							send "\r" ;
							#expect	{
							#			"#" send '\r"
							#		}
							
						 }
		}
		interact
		puts "\n\nOUTPUT dans LOG/$fichier\n\n"
		log_file -a $fichier
		interact
		log_file
	}
	OPENGEAR {
	    puts "\nINTERACT directly\n"
	    spawn ssh $unix_username@$ip_rebond
		rebond $ip_rebond
		send "ssh -l $unix_username:port$PORT $REBOND\r"
		#connexion $unix_username $password_tacacs $password_tacacs $passphrase
		expect {
			"yes" {send "yes\r"
					expect "assword"
					send "$tacacs\r"
					}
			"connection" { 
							puts "ici\n\n"
							send "\r" ;
							#expect	{
							#			"#" send '\r"
							#		}
							
						 }
			"assword" { send "$tacacs\r"}
 		}
		interact
		puts "\n\nOUTPUT dans LOG/$fichier\n\n"
		log_file -a $fichier
		interact
		log_file
	}
	default {
	    puts "\nINTERACT directly\n"
	    spawn ssh $unix_username@$ip_rebond
		rebond $ip_rebond
		send "ssh -l root:$PORT $REBOND\r"
		#connexion $unix_username $password_tacacs $password_tacacs $passphrase
		expect {
			"yes" {send "yes\r"}
			"connection" { 
							puts "ici\n\n"
							send "\r" ;
							expect	{
										"#" { send "\r" }
										"\>" { send "\r" }
										"login" { 
													send "admin\r" 
													expect "assword" 
													send "$secret_local\r"
												}
										"assword" { send "$secret_local\r" }
									}
							
						 }
		}
		puts "\n\nOUTPUT dans LOG/$fichier\n\n"
		log_file -a $fichier
		interact 
		log_file
	}

}