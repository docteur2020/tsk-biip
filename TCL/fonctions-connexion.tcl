proc connexion_expert {username password} {
		set expert [ exec /home/d83071/CONNEXION/getpass.sh "tac"]
		expect  {
			"assword" { send "$password\r";}
			"yes/no"  { send "yes\r"; expect "assword";  send "$password\r";}
		}
		expect  {

 			-re {[a-zA-Z0-9]>} { send "lock database override\r" ;}

 		}
		expect  {
 			-re {[a-zA-Z0-9]>} { send "tacacs_enable TACP-15\r" ;}

 		}
		puts 'toto'
		expect  {
			"assword" { send "$password\r";}
		}
		puts 'titi'
		sleep 1
		send "\r"
		expect {
			"\>" { send "\r" ;}
			continue
		}
		expect {
			-re {[a-zA-Z0-9]>} { send "expert\r" ;}
			continue
		}
		expect  {
			"assword" { send "$expert\r";}
			continue
		}
		sleep 1
		send "\r"
		
}

proc getlog {fichier fichier_commandes} {
	log_file -a $fichier
	
	expect {
					-re {[a-zA-Z0-9]#}  {
						puts "Coucou4.11"
						set OUTPUT $expect_out(buffer)
						
						# puts "\n\nOUTPUT\n\n"
						set FIN [ string  map -nocase { \r "" \n "" " " ""} $OUTPUT]
						
						# puts "!$OUTPUT!"
						# puts "!$output!"
						puts "\n\n!FIN:$FIN\n\n"
						
						send "terminal length 0 \r"
						
						puts "Coucou4"
						
						
					}
					-re {[a-zA-Z0-9]\S+>#}  {
						puts "Coucou4.33"
						set OUTPUT $expect_out(buffer)
						
						# puts "\n\nOUTPUT\n\n"
						set FIN [ string  map -nocase { \r "" \n "" " " ""} $OUTPUT]
						
						# puts "!$OUTPUT!"
						# puts "!$output!"
						puts "\n\n!FIN:$FIN\n\n"
						
						send "terminal length 0 \r"
						
						puts "Coucou4"
						
						
					}
					-re {[a-zA-Z0-9]\S+#}  {
					    puts "Coucou4.22"
						set OUTPUT $expect_out(buffer)
						
						puts "\n\nOUTPUT\n\n"
						set FIN [ string  map -nocase { \r "" \n "" " " ""} $OUTPUT]
						set FIN "d83071"
						puts "\n\DEB FIN\n\n"
						puts "FIN:!$FIN!"
						puts "\n\nFIN OUTPUT\n\n"
						
						send "\r"
						
						puts "Coucou4.8"
						
						
					}


			}

					
	while {[gets $fichier_commandes ligne] >= 0} {
	puts "Coucou4.55"
	expect $FIN
    	send "${ligne}\r"
		puts "Coucou boucle"
	}

	expect $FIN
	send "\r"
	
	puts "Coucou5"

	expect -re {[a-zA-Z0-9]#|[a-zA-Z0-9]\S+#}
	send "\r"
	
	puts "Coucou6"
	
	puts "\n\n == FIN DE PRISE DE TRACE == \n\n"
	
	log_file

	expect -re {[a-zA-Z0-9]#|[a-zA-Z0-9]\S+#}
	send "\r"
	
	return
}
proc conflog {fichier fichier_commandes} {
	log_file -a $fichier
	
	expect -re {[a-zA-Z0-9]#}
	
	set OUTPUT $expect_out(buffer)

    # puts "\n\nOUTPUT\n\n"
	set FIN [ string trim $OUTPUT "\n\r"]
    # puts "!$OUTPUT!"
	# puts "!$output!"
    # puts "\n\nFIN OUTPUT\n\n"

	send "terminal length 0 \r"

	puts "Coucou4"
	
	expect "#"
	send "conf t\r"
	
	while {[gets $fichier_commandes ligne] >= 0} {
		expect {
			"to continue connecting" { 	send "yes\r"  ;  }
			"Cannot overwrite" { exp_continue ;   }
			-re {Continue.*yes} { 	send "yes\r" ;  }
			-re {\(config.*\)#} {  send "$ligne\r"  }
			"Enter TEXT message" {  send "$ligne\r"  }
			expect -re {[a-zA-Z0-9]#} { 	send $\r;   }
		}
	}

	expect "#"
	send "\r"
	
    expect "#"
	send "end\r"
	
	puts "Coucou5"

	expect -re {[a-zA-Z0-9]#}
	send "\r"
	
	puts "Coucou6"
	
	puts "\n\n == FIN DE CONFIGURATION == \n\n"
	
	log_file

	expect -re {[a-zA-Z0-9]#}
	send "\r"
	
	puts "Coucou7"
	
	return
}
proc getlog_vpx {fichier fichier_commandes} {
	log_file -a $fichier
	
 
	puts "Coucou4"
	
	while {[gets $fichier_commandes ligne] >= 0} {
	puts "Coucou4.5"
	expect ">"
    	send "${ligne}\r"
		puts "Coucou boucle"
	}

	expect ">"
	send "\r"
	
	puts "Coucou5"

	expect ">"
	send "\r"
	
	puts "Coucou6"
	
	puts "\n\n == FIN DE PRISE DE TRACE == \n\n"
	
	log_file

	expect ">"
	send "\r"
	
	return
}
proc getlog_time {fichier fichier_commandes} {
	log_file -a $fichier
	
	expect -re {[a-zA-Z0-9]#}
	send "terminal length 0 \r"


	while {[gets $fichier_commandes ligne] >= 0} {
	expect -re {[a-zA-Z0-9]#}
		set timestamp [ exec date +Timestamp:%d%m%y_%Hh%Mm%Ss ]
		exp_send_log "\r\n$timestamp\r\n"
    	send "${ligne}\r"
	}

	expect -re {[a-zA-Z0-9]#}
	send "\r"
	


	expect -re {[a-zA-Z0-9]#}
	send "\r"
	

	
	puts "\n\n == FIN DE PRISE DE TRACE == \n\n"
	
	log_file

	expect -re {[a-zA-Z0-9]#}
	send "\r"
	
	return
}

proc config {fichier fichier_commandes} {
	log_file -a $fichier
	
	expect -re {[a-zA-Z0-9]#}
	send "terminal length 0 \r"

	expect -re {[a-zA-Z0-9]#}
	send "conf t\r"
	

	while {[gets $fichier_commandes ligne] >= 0} {
		expect {
			"to continue connecting" { 	send "yes\r"  ;  }
			"Cannot overwrite" { exp_continue ;   }
			-re {Continue.*yes} { 	send "yes\r" ;  }
			">" { 	send $ligne\r ;   }
			-re {\(config.*\)#} {  send "$ligne\r"  }
			expect -re {[a-zA-Z0-9]#} { 	send $\r;   }
			expect -re '{.*}' { 	send yes\r; puts  }
		}
	}
	
	expect {
			"to continue connecting" { 	send "yes\r" ; puts "\n\n1\n\n" ;  }
			"Cannot overwrite" { exp_continue ; puts "\n\n10\n\n" ;  }
			"(y/n)" { 	send "y\r" ; puts "\n\n3\n\n" ; expect "password" ; send "B2rn1s12345!\r" }
			"password" { 	send "B2rn1s12345!\r" ; puts "\n\n2\n\n" ;}
			-re {Continue.*yes} { 	send "yes\r" ; puts "\n\n5\n\n" ; }
			">" { 	send $ligne\r ;  }
			-re {\(config.*\)#} { puts "\n\n4\n\n";	sleep 3; send "$ligne\r" ; sleep 3; puts "\n\n40\n\n" }
			expect -re {[a-zA-Z0-9]#} { 	send $\r; puts "\n\n7\n\n"  }
			expect -re '{.*}' { 	send yes\r; puts "\n\n8\n\n"  }
		}
	

	expect #
	send "end\r"
	
	puts "\n\n == FIN DE CONFIGURATION== \n\n"
	
	log_file

	expect -re {[a-zA-Z0-9]#}
	send "\r"
	
	expect {	
		-re {[a-zA-Z0-9]#} {send "\r"}
		"startup" {send "\r"}
	}

	puts "cucou7"
	expect {	
	-re {[a-zA-Z0-9]#} {send "\r"}
	"Continue" {send "yes\r"}
	}
	

}

proc configure_iou {fichier fichier_commandes} {
	log_file -a $fichier
	
	expect -re {[a-zA-Z0-9]#}
	send "terminal length 0 \r"

	expect -re {[a-zA-Z0-9]#}
	send "conf t\r"
	
	expect "#"
	send "service compress-config\r"
	
	while {[gets $fichier_commandes ligne] >= 0} {
	expect "#"
    	send $ligne\r
	}

	expect "#"
	send "end\r"

	expect -re {[a-zA-Z0-9]#}
	send "\r"
	
	puts "\n\n == FIN DE CONFIGURATION== \n\n"
	
	log_file

	expect -re {[a-zA-Z0-9]#}
	send "copy run start\r"
	
	expect {	
		-re {[a-zA-Z0-9]#} {send "\r"}
		"startup" {send "\r"}
	}

	
	expect {	
	-re {[a-zA-Z0-9]#} {send "\r"}
	"Continue" {send "yes\r"}
	}
}


proc getlog_alteon {fichier fichier_commandes} {
	log_file -a $fichier
	
			expect "#"
			send "lines 0\r"

	while {[gets $fichier_commandes ligne] >= 0} {
	
			expect "#"
			send "\r"
			
			expect "#"
			send "$ligne\r"
			
		   	expect "#"
			puts "\n\n COMMANDE FINI \n\n"
			send "\r"

	}
	expect "#"
	send "\r"

	expect "#"
	send "\r"
	
	puts "\n\n == FIN DE PRISE DE TRACE == \n\n"
	
	log_file

	expect "#"
	send "\r"
	
	
	
	return
}
proc deconnexion { } {
expect -re {[a-zA-Z0-9]#}
send "exit\r"

expect "\\$"
send "exit\r"

expect eof


}

proc deconnexion_spectrum { } {
expect -re {[a-zA-Z0-9]#}
send "exit\r"

expect "Spectrum"
send "exit\r"

expect eof


}
proc deconnexion_direct { } {
expect -re {[a-zA-Z0-9]#}
send "exit\r"

expect eof


}

proc deconnexion_linux { } {
expect "\\\$"
send "exit\r"

expect "\\$"
send "exit\r"

expect eof

}
proc deconnexion_alteon_exp { } {

expect "#"
send "exit\r"

expect {
		"\\$" { send "exit\r"}
		"Enter password" { 
					send "\035"
					expect "telnet>"
					send "quit\r"
					expect "\\$"
					send "exit\r" 
		}
		"Enter" { 
					send "\035"
					expect "telnet>"
					send "quit\r"
					expect "\\$"
					send "exit\r" 
		}
		"con0" { 
					send "\035"
					expect "telnet>"
					send "quit\r"
					expect "\\$"
					send "exit\r" 
		}
}

send "exit\r"

expect eof


}



proc deconnexion_console { } {
expect -re {[a-zA-Z0-9]#}
send "exit\r"

expect "RETURN"
send "\035"


expect "telnet"
send "quit\r"

puts "\n\ndeconnexion reverse telnet \n\n"

expect { 
		"\\$" {send "exit\r"}
		timeout {exec ../pkillssh}
}
expect  {
			eof {puts "\n\ndeconnexion propre\n\n"}
			timeout {exec ../pkillssh}
		}

}

proc deconnexion_console_nexus { } {
expect -re {[a-zA-Z0-9]#}
send "exit\r"

expect "login"
send "\035"


expect "telnet"
send "quit\r"

puts "\n\ndeconnexion reverse telnet \n\n"

expect { 
		"\\$" {send "exit\r"}
		timeout {exec ../pkillssh}
}
expect  {
			eof {puts "\n\ndeconnexion propre\n\n"}
			timeout {exec ../pkillssh}
		}

}
proc init_console {} {

	expect {
			"Escape" {send "\r"}
			"TigCtx" { sleep 2 ; puts "\nCoucCou\n" ; send "\r"}
	}
	
	expect {
		"Press Enter" {send "\r";}
		exp_continue
		
	}
}
proc init_console2 {} {

	expect {
			"Escape" {send "\r"}
			"TigCtx" { sleep 1 ; puts "\nCoucCou\n" ; send "\r"}
	}
	
}


proc connexion {username password enable passphrase} {
		
		#puts "\n\n\n30\n\n\n"
		#sleep 2
		#puts "\n\n\n31\n\n\n"
		#sleep 2
		expect  {
		    "passphrase" {send "$passphrase\r" ; puts "0000"}
			#"Escape character is"  {send "\r" ; puts "2345"; exp_continue}
			#"rname" { send "$username\r" ; expect "assword" ; send "$password\r" ; puts "0001"}
			#"login" { send "$username\r" ; expect "assword" ; send "$password\r" ; puts "0002"} 
			"yes/no" {send "yes\r"}
			"assword" { send "$password\r";}
			-re {\n[a-zA-Z0-9]\S+#} {send "\r" ;  puts "0001"}
			#"\\)>"  { send "\r" ;}
		}
		#puts "\n\n\n32\n\n\n"
		#sleep 2	
		expect  {
		    "passphrase" {send "$passphrase\r"}
			"rname" { send "$username\r" ; expect "assword" ; send "$password\r" ; puts "1111"}
			#"login" { send "$username\r" ; expect "assword" ; send "$password\r" ;puts "2222" }
			"assword" { send "$password\r"}
			"yes" {send "yes\r"}
			-re {[0-9[a-zA-Z]>} {send "en\r" ; }
 			"\\)>"  { send "\r" ;}
			-re {[a-zA-Z0-9]#} { send "ter mon\r" ; 
								}
									
			-re {[a-zA-Z0-9] #} { send "\r" ; 
								}
			-re {[a-zA-Z0-9]>} {send "\r" ; }
			
			
 		}
		#puts "\n\n\n33\n\n\n"
		#sleep 2
		expect {
        	"assword" {send "$password\r"}
        	"sername" { send "$username\r" ; expect "assword" ; send "$password\r" }
			"\\)>"  { send "\r" ;}
        	-re {[a-zA-Z0-9]#} {send "\r" ; }
			-re {[a-zA-Z0-9]\s+\\$} { send "\r" ;}
			-re {[a-zA-Z0-9]\s#} { send "\r" ;}
		}

		#puts "\n\n\n34\n\n\n"
		#sleep 2
		
		return
} 
proc connexion_wo_monitor {username password enable passphrase} {
		
		#puts "\n\n\n30\n\n\n"
		#sleep 2
		#puts "\n\n\n31\n\n\n"
		#sleep 2
		expect  {
		    "passphrase" {send "$passphrase\r" ; puts "0000"}
			#"Escape character is"  {send "\r" ; puts "2345"; exp_continue}
			#"rname" { send "$username\r" ; expect "assword" ; send "$password\r" ; puts "0001"}
			#"login" { send "$username\r" ; expect "assword" ; send "$password\r" ; puts "0002"} 
			"yes/no" {send "yes\r"}
			"assword" { send "$password\r";}
			-re {\n[a-zA-Z0-9]\S+#} {send "\r" ;  puts "0001"}
			#"\\)>"  { send "\r" ;}
		}
		#puts "\n\n\n32\n\n\n"
		#sleep 2	
		expect  {
		    "passphrase" {send "$passphrase\r"}
			"rname" { send "$username\r" ; expect "assword" ; send "$password\r" ; puts "1111"}
			#"login" { send "$username\r" ; expect "assword" ; send "$password\r" ;puts "2222" }
			"assword" { send "$password\r"}
			"yes" {send "yes\r"}
			-re {[0-9[a-zA-Z]>} {send "en\r" ; }
 			"\\)>"  { send "\r" ;}
			-re {[a-zA-Z0-9]#} { send "\r" ; 
								}
									
			-re {[a-zA-Z0-9] #} { send "\r" ; 
								}
			-re {[a-zA-Z0-9]>} {send "\r" ; }
			
			
 		}
		#puts "\n\n\n33\n\n\n"
		#sleep 2
		expect {
        	"assword" {send "$password\r"}
        	"sername" { send "$username\r" ; expect "assword" ; send "$password\r" }
			"\\)>"  { send "\r" ;}
        	-re {[a-zA-Z0-9]#} {send "\r" ; }
			-re {[a-zA-Z0-9]\s+\\$} { send "\r" ;}
			-re {[a-zA-Z0-9]\s#} { send "\r" ;}
		}

		#puts "\n\n\n34\n\n\n"
		#sleep 2
		
		return
} 
proc connexion_enable {username password enable passphrase} {

		expect  {
			"name" { send "$username\r" ; expect "assword" ; send "$password\r" }
			"login" { send "$username\r" ; expect "assword" ; send "$password\r" } 
			"yes" {send "yes\r"}
			"assword" { send "$password\r"}
			"passphrase" {send "$passphrase\r"}
		}
		expect  {
			name" { send "$username\r" ; expect "assword" ; send "$password\r" }
			login" { send "$username\r" ; expect "assword" ; send "$password\r" }
			"assword" { send "$password\r"}
			"passphrase" {send "$passphrase\r"}
			"yes" {send "yes\r"}
 			">" { send "en\r" ;}
			-re {[a-zA-Z0-9]#} {send "\r" ; }
 		}
		expect {
 			"assword" {send "$enable\r"}
 			"sername" { send "$username\r" ; expect "assword" ; send "$password\r" }
 			-re {[a-zA-Z0-9]#} {send "\r" ; }
			">" { send "en\r" ;}
		}
		expect {
        	"assword" {send "$enable\r"}
        	"sername" { send "$username\r" ; expect "assword" ; send "$password\r" }
        	-re {[a-zA-Z0-9]#} {send "\r" ; }
        	">" { send "en\r" ;}
		}
		
		expect -re {[a-zA-Z0-9]#|[a-zA-Z0-9]>}
		send "en\r"
	
		expect {
			"assword" {send "$enable\r"}
			-re {[a-zA-Z0-9]#|[a-zA-Z0-9]>}  {send "\r"}
		}

		return
} 
proc connexion_bigip {username password enable passphrase} {

		expect  {
			"name" { send "$username\r" ; expect "assword" ; send "$password\r" }
			"login" { send "$username\r" ; expect "assword" ; send "$password\r" } 
			"yes" {send "yes\r"}
			"assword" { send "$password\r"; puts "test1 $password\n\n" }
			"passphrase" {send "$passphrase\r"}
			-re {[a-zA-Z0-9]#} { send "\r" ;}
			" #" { send "\r" ;}
		}
		expect  {
			name" { send "$username\r" ; expect "assword" ; send "$password\r" }
			login" { send "$username\r" ; expect "assword" ; send "$password\r" }
			"assword" { send "$password\r"}
			"passphrase" {send "$passphrase\r"}
			"yes" {send "yes\r"}
 			-re {[a-zA-Z0-9]#} { send "\r" ;}
			" #" { send "\r" ;}
 		}
		expect {
 			"assword" {send "$enable\r"}
 			"sername" { send "$username\r" ; expect "assword" ; send "$password\r" }
			-re {[a-zA-Z0-9]#} { send "\r" ;}
			" #" { send "\r" ;}
		}
		return
} 

proc connexion2 {hostname prefixe prefixe_pass1 prefixe_pass2 prefixe_pass3} {
	set suffixe_pass [lindex [split $hostname "-"] 1]
	set position [ expr { [string length $hostname] -1 }  ]
	set suffixe_pass_autre [string index $hostname $position ]
	set password1 "${prefixe}${prefixe_pass1}-${suffixe_pass}"
	set password2 "${prefixe}${prefixe_pass2}-${suffixe_pass}"
	set password3 "${prefixe}${prefixe_pass3}-${suffixe_pass}"
	set enable1 "M${prefixe_pass1}-${suffixe_pass}"
	set enable2 "M${prefixe_pass2}-${suffixe_pass}"
	set enable3 "M${prefixe_pass3}-${suffixe_pass}"
	puts "\nConnexion en reverse Telnet"
	puts "\n$password1 $password2 $password3\n"

	expect "Escape"
	send "\r"
			
	expect {
				"assword" {send "$password1\r" }
				-re {[a-zA-Z0-9]#} {send "\r" ; }
	}
				
	expect {
			">" { send "en\r" ; expect "assword" ; send "$enable1\r";puts "pass 1 OK "}
			"assword"  { send "$password2\r"  }
			-re {[a-zA-Z0-9]#} {send "\r" ; }
	}

	expect  {
			">" { send "en\r" ; expect "assword" ; send "$enable2\r"; puts "pass 2 OK "}
			"assword"  { send "$password3\r"  }
			-re {[a-zA-Z0-9]#} {send "\r" ; }
	}

	expect  {
			">" { send "en\r" ; expect "assword" ; send "$enable3\r"; puts "pass 3 OK "}
			-re {[a-zA-Z0-9]#} {send "\r" ; }
	}

	expect -re {[a-zA-Z0-9]#}
	send "\r"

   	return
}

proc connexion_reverse_custom {username password enable} {
	puts "\nConnexion en reverse"

	expect "Escape"
	send "\r"
			
	expect  {
			"name" { send "$username\r" ; expect "assword" ; send "$password\r" }
			"login" { send "$username\r" ; expect "assword" ; send "$password\r" } 
			"yes" {send "yes\r"}
			"assword" { send "$password\r"}
			"passphrase" {send "$passphrase\r"}
		}
		expect  {
			name" { send "$username\r" ; expect "assword" ; send "$password\r" }
			login" { send "$username\r" ; expect "assword" ; send "$password\r" }
			"assword" { send "$password\r"}
			"passphrase" {send "$passphrase\r"}
			"yes" {send "yes\r"}
 			">" { send "en\r" ;}
			-re {[a-zA-Z0-9]#} {send "\r" ; }
 		}
		expect {
 			"assword" {send "$enable\r"}
 			"sername" { send "$username\r" ; expect "assword" ; send "$password\r" }
 			-re {[a-zA-Z0-9]#} {send "\r" ; }
			">" { send "en\r" ;}
		}
		expect {
        	"assword" {send "$enable\r"}
        	"sername" { send "$username\r" ; expect "assword" ; send "$password\r" }
        	-re {[a-zA-Z0-9]#} {send "\r" ; }
        	">" { send "en\r" ;}
		}
		
		expect -re {[a-zA-Z0-9]#}
		send "en\r"
	
		expect {
			"assword" {send "$enable\r"}
			-re {[a-zA-Z0-9]#}  {send "\r"}
		}

   	return
}

proc connexion2_nexus {hostname prefixe prefixe_pass1 prefixe_pass2 prefixe_pass3} {
	set suffixe_pass [lindex [split $hostname "-"] 1]
	set position [ expr { [string length $hostname] -1 }  ]
	set suffixe_pass_autre [string index $hostname $position ]
	set password1 "${prefixe}${prefixe_pass1}-${suffixe_pass}"
	set password2 "${prefixe}${prefixe_pass2}-${suffixe_pass}"
	set password3 "${prefixe}${prefixe_pass3}-${suffixe_pass}"
	set enable1 "M${prefixe_pass1}-${suffixe_pass}"
	set enable2 "M${prefixe_pass2}-${suffixe_pass}"
	set enable3 "M${prefixe_pass3}-${suffixe_pass}"
	puts "\nConnexion en reverse Telnet NEXUS - Console"
	puts "\n$password1 $password2 $password3\n"

	expect "Escape"
	send "\r"
	
	expect {
				"login" {send "admin\r" }
				-re {[a-zA-Z0-9]#} {send "\r" ; }
	}	
	
			
	expect {
				"assword" {send "$password1\r" }
				-re {[a-zA-Z0-9]#} {send "\r" ; }
	}
				
	expect {
			">" { send "en\r" ; expect "assword" ; send "$enable1\r";puts "pass 1 OK "}
			-re {[a-zA-Z0-9]#} {send "\r" ; }
			"login"  { send "admin\r" ; expect "assword"; send "$password2\r"  }
			-re {[a-zA-Z0-9]#} {send "\r" ; }
	}

	expect  {
			">" { send "en\r" ; expect "assword" ; send "$enable2\r"; puts "pass 2 OK "}
			-re {[a-zA-Z0-9]#} {send "\r" ; }
				"login"  { send "admin\r" ;  expect "assword"; send "$password3\r"  }
			-re {[a-zA-Z0-9]#} {send "\r" ; }
	}

	expect  {
			">" { send "en\r" ; expect "assword" ; send "$enable3\r"; puts "pass 3 OK "}
			-re {[a-zA-Z0-9]#} {send "\r" ; }
	}

	expect -re {[a-zA-Z0-9]#}
	send "\r"

   	return
}

proc connexion2_admin_nexus {hostname} {
	set password "admin"
	puts "\nConnexion en reverse Telnet NEXUS - Console SPEC"

	expect "Escape"
	send "\r"
	
	expect {
				"login" {send "admin\r" }
				-re {[a-zA-Z0-9]#} {send "\r" ; }
	}	
	
			
	expect {
				"assword" {send "$password\r" }
				-re {[a-zA-Z0-9]#} {send "\r" ; }
	}
				

	expect -re {[a-zA-Z0-9]#}
	send "\r"

   	return
}
proc connexion3 {hostname prefixe passphrase prefixe_pass1 prefixe_pass2 prefixe_pass3} {
    set suffixe_pass [lindex [split $hostname "-"] 1]
    set position [ expr { [string length $hostname] -1 }  ]
	set suffixe_pass_autre [string index $hostname $position ]
	set password1 "${prefixe}${prefixe_pass1}-${suffixe_pass}"
	set password2 "${prefixe}${prefixe_pass2}-${suffixe_pass}"
	set password3 "${prefixe}${prefixe_pass3}-${suffixe_pass}"
	set enable1 "M${prefixe_pass1}-${suffixe_pass}"
	set enable2 "M${prefixe_pass2}-${suffixe_pass}"
    set enable3 "M${prefixe_pass3}-${suffixe_pass}"

    expect  "passphrase" 
	send "$passphrase\r"

	expect "Escape"
	send "\r"

	puts "\n$password1"
	
 
	expect  {
		"assword"  { send "$password1\r"  }
		"name" { send "$username\r" ; expect "assword" ; send "$password1\r" }
		">" { send "en\r" ; expect "assword" ; send "$enable1\r"}
	}
	puts "test1\n"
	expect  {
		"assword"  { send "$password2\r"  }
		">" { send "en\r" ; expect "assword" ; send "$enable1\r"}
		-re {[a-zA-Z0-9]#} {send "\r" ; }
	}
	puts "test12\n"
	expect  {
		"assword"  { send "$password3\r"  }
		">" { send "en\r" ; expect "assword" ; send "$enable2\r"}
		-re {[a-zA-Z0-9]#} {send "\r" ; }
	}
	puts "test3\n"
	expect  {
		">" { send "en\r" ; expect "assword" ; send "$enable3\r"}
		-re {[a-zA-Z0-9]#} {send "\r" ; }
	}
	
	puts "test4\n"
	
	expect -re {[a-zA-Z0-9]#}
	send "\r"

	return
}

proc connexion4 {hostname prefixe passphrase prefixe_pass1 prefixe_pass2 prefixe_pass3} {
    set suffixe_pass [lindex [split $hostname "-"] 1]
    set position [ expr { [string length $hostname] -1 }  ]
	set suffixe_pass_autre [string index $hostname $position ]
	set password1 "${prefixe}${prefixe_pass1}-${suffixe_pass}"
	set password2 "${prefixe}${prefixe_pass2}-${suffixe_pass}"
	set password3 "${prefixe}${prefixe_pass3}-${suffixe_pass}"
	set enable1 "M${prefixe_pass1}-${suffixe_pass}"
	set enable2 "M${prefixe_pass2}-${suffixe_pass}"
    set enable3 "M${prefixe_pass3}-${suffixe_pass}"

    expect  "passphrase" 
	send "$passphrase\r"

	puts "\n$password1"
	
 
	expect  {
		"assword"  { send "$password1\r"  }
		"name" { send "$username\r" ; expect "assword" ; send "$password1\r" }
		">" { send "en\r" ; expect "assword" ; send "$enable1\r"}
	}
	puts "test1\n"
	expect  {
		"assword"  { send "$password2\r"  }
		">" { send "en\r" ; expect "assword" ; send "$enable1\r"}
		-re {[a-zA-Z0-9]#} {send "\r" ; }
	}
	puts "test12\n"
	expect  {
		"assword"  { send "$password3\r"  }
		">" { send "en\r" ; expect "assword" ; send "$enable2\r"}
		-re {[a-zA-Z0-9]#} {send "\r" ; }
	}
	puts "test3\n"
	expect  {
		">" { send "en\r" ; expect "assword" ; send "$enable3\r"}
		-re {[a-zA-Z0-9]#} {send "\r" ; }
	}
	
	puts "test4\n"
	
	expect -re {[a-zA-Z0-9]#}
	send "\r"

	return
}

proc connexion5 {hostname prefixe passphrase prefixe_pass1 prefixe_pass2 prefixe_pass3} {
    set suffixe_pass [lindex [split $hostname "-"] 1]
    set position [ expr { [string length $hostname] -1 }  ]
	set suffixe_pass_autre [string index $hostname $position ]
	set password1 "${prefixe}${prefixe_pass1}-${suffixe_pass}"
	set password2 "${prefixe}${prefixe_pass2}-${suffixe_pass}"
	set password3 "${prefixe}${prefixe_pass3}-${suffixe_pass}"
	set enable1 "M${prefixe_pass1}-${suffixe_pass}"
	set enable2 "M${prefixe_pass2}-${suffixe_pass}"
    set enable3 "M${prefixe_pass3}-${suffixe_pass}"

 
	expect  {
		"assword"  { send "$password1\r"  }
		"name" { send "$username\r" ; expect "assword" ; send "$password1\r" }
		">" { send "en\r" ; expect "assword" ; send "$enable1\r"}
	}
	puts "test1\n"
	expect  {
		"assword"  { send "$password2\r"  }
		">" { send "en\r" ; expect "assword" ; send "$enable1\r"}
		-re {[a-zA-Z0-9]#} {send "\r" ; }
	}
	puts "test12\n"
	expect  {
		"assword"  { send "$password3\r"  }
		">" { send "en\r" ; expect "assword" ; send "$enable2\r"}
		-re {[a-zA-Z0-9]#} {send "\r" ; }
	}
	puts "test3\n"
	expect  {
		">" { send "en\r" ; expect "assword" ; send "$enable3\r"}
		-re {[a-zA-Z0-9]#} {send "\r" ; }
	}
	
	puts "test4\n"
	
	expect -re {[a-zA-Z0-9]#}
	send "\r"
	
	return
}

proc connexion_default { hostname } {

	set test_expose [ exec ./test_exp.sh $hostname]
	if {$test_expose!=1} {
	puts "\nEquipement non expose\n"
	set username "d83071"
	set password "Oclo0hvr!"
	set enable "Oclo0hvr!"
	set fichier "${hostname}_shrun.log"
	set prefixe_pass1 "ayril"
	set prefixe_pass2 "yraje"
	set prefixe_pass3 "acxes"
	set suffixe_pass [lindex [split $hostname "-"] 1]
	set position [ expr { [string length $hostname] -1 }  ]
	set suffixe_pass_autre [string index $hostname $position ]
	set password1 "T${prefixe_pass1}-${suffixe_pass}"
	set password2 "T${prefixe_pass2}-${suffixe_pass}"
	set password3 "T${prefixe_pass3}-${suffixe_pass}"
	set enable1 "M${prefixe_pass1}-${suffixe_pass}"
	set enable2 "M${prefixe_pass2}-${suffixe_pass}"
	set enable3 "M${prefixe_pass3}-${suffixe_pass}"

	send "telnet $hostname\r"

	expect  {
		"refused" { send "ssh -l ciscoworks $hostname\r" ;} 
		"timeout" { send "ssh -l ciscoworks $hostname\r" ;} 
		-re {[a-zA-Z0-9]#}  {send "\r" ; }
		"assword"  { 
				send "$password1\r" 
				expect {
						"name" { send "$username\r" ; expect "assword" ; send "$password\r" }
						">" { send "en\r" ; expect "assword" ; send "$enable1\r"}
						-re {[a-zA-Z0-9]#}  {send "\r" ; }
						"assword"  { send "$password2\r"  }
						}
				#puts "\n test0 \n"
				expect  {
						">" { send "en\r" ; expect "assword" ; send "$enable2\r"}
						-re {[a-zA-Z0-9]#}  {send "\r" ; }
						"assword"  { send "$password3\r"  }
						}
						
				#puts "\n test1 \n"
				expect  {
						">" { send "en\r" ; expect "assword" ; send "$enable3\r"}
						-re {[a-zA-Z0-9]#}  {send "\r" ; }
						}
		
				#puts "\n test3 \n"
				expect -re {[a-zA-Z0-9]#}
				send "\r"
				}
	 
		"name" { send "ciscoworks\r" ; expect "assword" ; send "d0n'tYze1t\r" }
		"login" { send "admin\r" ; expect "assword" ; send "cisco\r" }
		"not known" {
					puts "\nConnexion en reverse Telnet"
					set IP_rebond [exec ./get_IP $hostname ]
					set Port_reverse [exec ./get_Port $hostname]
					puts "$IP_rebond $Port_reverse"
					send "telnet $IP_rebond $Port_reverse\r\r\r"
					expect "Escape"
					send "\r"
					set cons_prefixe_pass1 "ayril"
					set cons_prefixe_pass2 "euzan"
					set cons_prefixe_pass3 "yraje"
					set cons_suffixe_pass [lindex [split $hostname "-"] 1]
					set cons_position [ expr { [string length $hostname] -1 }  ]
					set cons_suffixe_pass_autre [string index $hostname $position ]
					set cons_password1 "P${cons_prefixe_pass1}-${cons_suffixe_pass}"
					set cons_password2 "P${cons_prefixe_pass2}-${cons_suffixe_pass}"
					set cons_password3 "P${cons_prefixe_pass3}-${cons_suffixe_pass}"
					set cons_enable1 "M${cons_prefixe_pass1}-${cons_suffixe_pass}"
					set cons_enable2 "M${cons_prefixe_pass2}-${cons_suffixe_pass}"
					set cons_enable3 "M${cons_prefixe_pass3}-${cons_suffixe_pass}"
					puts "$cons_password1 $cons_enable1\n"
					puts "$cons_password2 $cons_enable2\n"
					puts "$cons_password3 $cons_enable3\n"
					expect {
					
							"refused" { send "ssh -l ciscoworks $hostname\r" ;} 
							"assword"  { 
										send "$cons_password1\r" 
										expect {
											"name" { send "$username\r" ; expect "assword" ; send "$password\r" }
											">" { send "en\r" ; expect "assword" ; send "$enable1\r";puts "pass 1 OK "}
											-re {[a-zA-Z0-9]#}  {send "\r" ; }
											"assword"  { send "$cons_password2\r"  }
										}
										#puts "\n test0 \n"
										expect  {
											">" { send "en\r" ; expect "assword" ; send "$cons_enable2\r"; puts "pass 2 OK "}
											-re {[a-zA-Z0-9]#}  {send "\r" ; }
										puts "$cons_password1   $cons_enable1 "
											"assword"  { send "$cons_password3\r"  }
										}
						
									#puts "\n test1 \n"
									expect  {
									">" { send "en\r" ; expect "assword" ; send "$cons_enable3\r"; puts "pass 3 OK "}
									-re {[a-zA-Z0-9]#}  {send "\r" ; }
									}
		
									#puts "\n test3 \n"
									expect -re {[a-zA-Z0-9]#}
									send "\r"
							}
	 
							"name" { send "ciscoworks\r" ; expect "assword" ; send "d0n'tYze1t\r" }
					}
					
		}
		"\\$" { send "ssh -l ciscoworks $hostname\r" ;} 
	}
	
	expect  {
		"assword" { send "d0n'tYze1t\r"}
		"yes" {send "yes\r"}
		">" { send "en\r" ;}
		-re {[a-zA-Z0-9]#} {send "\r" ; }
		"login" { send "$username\r" ; expect "assword" ; send "$password\r"}
		}

	expect  {
		-re {[a-zA-Z0-9]#} {send "\r" ; }
		"assword" {send "d0n'tYze1t\r"}
		"sername" { send "ciscoworks\r" ; expect "assword" ; send "d0n'tYze1t\r" }
		">" { send "en\r" } 
		
		}
	
	expect {
	 "assword" {send "d0n'tYze1t\r"}
	 "sername" { send "ciscoworks\r" ; expect "assword" ; send "d0n'tYze1t\r" }
	 -re {[a-zA-Z0-9]#} {send "\r" ; }
	}
	expect -re {[a-zA-Z0-9]#}
	send "\r"

	} else {
	puts "\nEquipement expose\n"
	set username "d83071"
	set prefixe_pass1 "arkhy"
	set prefixe_pass2 "euzan"
	set prefixe_pass3 "ymone"
	set suffixe_pass [lindex [split $hostname "-"] 1]
	set password1 "P${prefixe_pass1}-${suffixe_pass}"
	set password2 "P${prefixe_pass2}-${suffixe_pass}"
	set password3 "P${prefixe_pass3}-${suffixe_pass}"
	set enable1 "M${prefixe_pass1}-${suffixe_pass}"
	set enable2 "M${prefixe_pass2}-${suffixe_pass}"
	set enable3 "M${prefixe_pass3}-${suffixe_pass}"
	set fichier "${hostname}_shrun.log"

	set passphrase "D1mension!!!"

	puts $password1

	send "\r"

	expect "\\$"
	send "ssh $hostname@172.16.16.210\r"

	expect  "passphrase" 
	send "$passphrase\r"

	#sleep 2

	expect "Escape"
	send "\r"

	expect  {
		"assword"  { send "$password1\r"  }
		"name" { send "$username\r" ; expect "assword" ; send "$password1\r" }
		">" { send "en\r" ; expect "assword" ; send "$enable1\r"}
		-re {[a-zA-Z0-9]#} {send "\r" ; }
		}
	puts "test1\n"
	expect  {
		"assword"  { send "$password2\r"  }
		">" { send "en\r" ; expect "assword" ; send "$enable1\r"}
		-re {[a-zA-Z0-9]#} {send "\r" ; }
		}
		puts "test12\n"
	expect  {
		"assword"  { send "$password3\r"  }
		">" { send "en\r" ; expect "assword" ; send "$enable2\r"}
		-re {[a-zA-Z0-9]#} {send "\r" ; }
		}
		puts "test3\n"
	expect  {
		">" { send "en\r" ; expect "assword" ; send "$enable3\r"}
		-re {[a-zA-Z0-9]#} {send "\r" ; }
		}
		
		puts "test4\n"
		

	expect -re {[a-zA-Z0-9]#}
	send "\r"
	
	puts "Ne te deconnecte pas"
	return

	}

}

proc connexion_default_console { hostname } {

	set test_expose [ exec ./test_exp.sh $hostname]
	if {$test_expose!=1} {
	puts "\nEquipement non expose\n"
	set username "d83071"
	set password "Oclo0hvr!"
	set enable "Oclo0hvr!"
	set fichier "${hostname}_shrun.log"
	set prefixe_pass1 "ayril"
	set prefixe_pass2 "yraje"
	set prefixe_pass3 "acxes"
	set suffixe_pass [lindex [split $hostname "-"] 1]
	set position [ expr { [string length $hostname] -1 }  ]
	set suffixe_pass_autre [string index $hostname $position ]
	set password1 "P${prefixe_pass1}-${suffixe_pass}"
	set password2 "P${prefixe_pass2}-${suffixe_pass}"
	set password3 "P${prefixe_pass3}-${suffixe_pass}"
	set enable1 "M${prefixe_pass1}-${suffixe_pass}"
	set enable2 "M${prefixe_pass2}-${suffixe_pass}"
	set enable3 "M${prefixe_pass3}-${suffixe_pass}"


	expect  {
		-re {[a-zA-Z0-9]#}  {send "\r" ; }
		"assword"  { 
				send "$password1\r" 
				expect {
						"name" { send "$username\r" ; expect "assword" ; send "$password\r" }
						">" { send "en\r" ; expect "assword" ; send "$enable1\r"}
						-re {[a-zA-Z0-9]#}  {send "\r" ; }
						"assword"  { send "$password2\r"  }
						}
				#puts "\n test0 \n"
				expect  {
						">" { send "en\r" ; expect "assword" ; send "$enable2\r"}
						-re {[a-zA-Z0-9]#}  {send "\r" ; }
						"assword"  { send "$password3\r"  }
						}
						
				#puts "\n test1 \n"
				expect  {
						">" { send "en\r" ; expect "assword" ; send "$enable3\r"}
						-re {[a-zA-Z0-9]#}  {send "\r" ; }
						}
		
				#puts "\n test3 \n"
				expect -re {[a-zA-Z0-9]#}
				send "\r"
				}
	 

	}
	
	expect  {
		"assword" { send "d0n'tYze1t\r"}
		"yes" {send "yes\r"}
		">" { send "en\r" ;}
		-re {[a-zA-Z0-9]#} {send "\r" ; }
		"login" { send "$username\r" ; expect "assword" ; send "$password\r"}
		}

	expect  {
		-re {[a-zA-Z0-9]#} {send "\r" ; }
		"assword" {send "d0n'tYze1t\r"}
		"sername" { send "ciscoworks\r" ; expect "assword" ; send "d0n'tYze1t\r" }
		">" { send "en\r" } 
		
		}
	
	expect {
	 "assword" {send "d0n'tYze1t\r"}
	 "sername" { send "ciscoworks\r" ; expect "assword" ; send "d0n'tYze1t\r" }
	 -re {[a-zA-Z0-9]#} {send "\r" ; }
	}
	expect -re {[a-zA-Z0-9]#}
	send "\r"

	} else {
	puts "\nEquipement expose\n"
	set username "d83071"
	set prefixe_pass1 "arkhy"
	set prefixe_pass2 "euzan"
	set prefixe_pass3 "ymone"
	set suffixe_pass [lindex [split $hostname "-"] 1]
	set password1 "P${prefixe_pass1}-${suffixe_pass}"
	set password2 "P${prefixe_pass2}-${suffixe_pass}"
	set password3 "P${prefixe_pass3}-${suffixe_pass}"
	set enable1 "M${prefixe_pass1}-${suffixe_pass}"
	set enable2 "M${prefixe_pass2}-${suffixe_pass}"
	set enable3 "M${prefixe_pass3}-${suffixe_pass}"
	set fichier "${hostname}_shrun.log"

	set passphrase "D1mension!!!"

	puts $password1

	send "\r"

	expect "\\$"
	send "ssh $hostname@172.16.16.210\r"

	expect  "passphrase" 
	send "$passphrase\r"

	#sleep 2

	expect "Escape"
	send "\r"

	expect  {
		"assword"  { send "$password1\r"  }
		"name" { send "$username\r" ; expect "assword" ; send "$password1\r" }
		">" { send "en\r" ; expect "assword" ; send "$enable1\r"}
		-re {[a-zA-Z0-9]#} {send "\r" ; }
		}
	puts "test1\n"
	expect  {
		"assword"  { send "$password2\r"  }
		">" { send "en\r" ; expect "assword" ; send "$enable1\r"}
		-re {[a-zA-Z0-9]#} {send "\r" ; }
		}
		puts "test12\n"
	expect  {
		"assword"  { send "$password3\r"  }
		">" { send "en\r" ; expect "assword" ; send "$enable2\r"}
		-re {[a-zA-Z0-9]#} {send "\r" ; }
		}
		puts "test3\n"
	expect  {
		">" { send "en\r" ; expect "assword" ; send "$enable3\r"}
		-re {[a-zA-Z0-9]#} {send "\r" ; }
		}
		
		puts "test4\n"
		

	expect -re {[a-zA-Z0-9]#}
	send "\r"
	
	puts "Ne te deconnecte pas"
	return

	}

}
proc connexion_expose1 { hostname } {

	puts "\nEquipement type expose T en reverse\n"
	set username "d83071"
	set prefixe_pass1 "arkhy"
	set prefixe_pass2 "euzan"
	set prefixe_pass3 "acxes"
	set suffixe_pass [lindex [split $hostname "-"] 1]
	set password1 "T${prefixe_pass1}-${suffixe_pass}"
	set password2 "T${prefixe_pass2}-${suffixe_pass}"
	set password3 "T${prefixe_pass3}-${suffixe_pass}"
	set enable1 "M${prefixe_pass1}-${suffixe_pass}"
	set enable2 "M${prefixe_pass2}-${suffixe_pass}"
	set enable3 "M${prefixe_pass3}-${suffixe_pass}"
	set fichier "${hostname}_shrun.log"

	set passphrase "D1mension!!!"

	puts $password1

	send "\r"

	expect "\\$"
	send "ssh $hostname@172.16.16.210\r"

	expect  "passphrase" 
	send "$passphrase\r"

	#sleep 2

	# expect "Escape"
	# send "\r"
	
	puts "\n\n$password1"
	expect  {
		"assword"  { send "$password1\r"  }
		"name" { send "$username\r" ; expect "assword" ; send "$password1\r" }
		">" { send "en\r" ; expect "assword" ; send "$enable1\r";puts "\n999999\n"}
		-re {[a-zA-Z0-9]#} {send "\r" ; }
		}
	puts "test1\n"
	expect  {
		">" { send "en\r" ; expect "assword" ; send "$enable1\r"; puts "\nAAAAA\n"}
		"assword"  { send "$password2\r"  }
		-re {[a-zA-Z0-9]#} {send "\r" ; }
		}
		puts "\ntest12\n"
	expect  {
		">" { send "en\r" ; expect "assword" ; send "$enable2\r"}
		"assword"  { send "$password3\r"  }
		-re {[a-zA-Z0-9]#} {send "\r" ; }
		}
		puts "test3\n"
	expect  {
		">" { send "en\r" ; expect "assword" ; send "$enable3\r"}
		-re {[a-zA-Z0-9]#} {send "\r" ; }
		
		}
		
		puts "test4\n"
		

	expect -re {[a-zA-Z0-9]#}
	send "\r"
	
	puts "Ne te deconnecte pas"
	return

}
proc connexion_expose2 { hostname } {

	puts "\nEquipement type expose T\n"
	set username "d83071"
	set prefixe_pass1 "arkhy"
	set prefixe_pass2 "euzan"
	set prefixe_pass3 "acxes"
	set suffixe_pass [lindex [split $hostname "-"] 1]
	set password1 "T${prefixe_pass1}-${suffixe_pass}"
	set password2 "T${prefixe_pass2}-${suffixe_pass}"
	set password3 "T${prefixe_pass3}-${suffixe_pass}"
	set enable1 "M${prefixe_pass1}-${suffixe_pass}"
	set enable2 "M${prefixe_pass2}-${suffixe_pass}"
	set enable3 "M${prefixe_pass3}-${suffixe_pass}"
	set fichier "${hostname}_shrun.log"

	set passphrase "D1mension!!!"

	puts $password1

	send "\r"

	expect "\\$"
	send "telnet $hostname\r"

	# expect  "passphrase" 
	# send "$passphrase\r"

	#sleep 2

	# expect "Escape"
	# send "\r"
	
	# puts "\n\n$password1"
	expect  {
		"assword"  { send "$password1\r"  }
		"name" { send "$username\r" ; expect "assword" ; send "$password1\r" }
		">" { send "en\r" ; expect "assword" ; send "$enable1\r"}
		-re {[a-zA-Z0-9]#} {send "\r" ; }
		}
	puts "test1\n"
	expect  {
		">" { send "en\r" ; expect "assword" ; send "$enable1\r"}
		"assword"  { send "$password2\r"  }
		-re {[a-zA-Z0-9]#} {send "\r" ; }
		}
		puts "test12\n"
	expect  {
		">" { send "en\r" ; expect "assword" ; send "$enable2\r"}
		"assword"  { send "$password3\r"  }
		-re {[a-zA-Z0-9]#} {send "\r" ; }
		}
		puts "test3\n"
	expect  {
		">" { send "en\r" ; expect "assword" ; send "$enable3\r"}
		-re {[a-zA-Z0-9]#} {send "\r" ; }
		
		}
		
		puts "test4\n"
		

	expect -re {[a-zA-Z0-9]#}
	send "\r"
	
	puts "Ne te deconnecte pas"
	return

}
proc connexion_expose_vpx { hostname } {

	puts "\nEquipement type expose M\n"
	set username "admin"
	set prefixe_pass1 "arkhy"
	set prefixe_pass2 "euzan"
	set prefixe_pass3 "acxes"
	set suffixe_pass [lindex [split $hostname "-"] 1]
	set password1 "T${prefixe_pass1}-${suffixe_pass}"
	set password2 "T${prefixe_pass2}-${suffixe_pass}"
	set password3 "T${prefixe_pass3}-${suffixe_pass}"
	set enable1 "M${prefixe_pass1}-${suffixe_pass}"
	set enable2 "M${prefixe_pass2}-${suffixe_pass}"
	set enable3 "M${prefixe_pass3}-${suffixe_pass}"
	set fichier "${hostname}_shrun.log"

	set passphrase "D1mension!!!"

	puts $password1

	send "\r"

	expect "\\$"
	send "ssh -l $username $hostname\r"

	# expect  "passphrase" 
	# send "$passphrase\r"

	#sleep 2

	# expect "Escape"
	# send "\r"
	
	# puts "\n\n$password1"
	expect  {
		"assword"  { send "$enable1\r"  }
		"name" { send "$username\r" ; expect "assword" ; send "$enable1\r" }
		">" { send "\r" ;}

		}
	puts "test1\n"
	expect  {
		">" { send "\r" ;}
		"assword"  { send "$enable2\r"  }

		}
		puts "test12\n"
	expect  {
		">" { send "\r" ; }
		"assword"  { send "$enable3\r"  }

		}
		puts "test3\n"
	expect  {
		">" { send "\r" ;}
		
		}
		
		puts "test4\n"
		

	expect ">"
	send "\r"
	
	puts "Ne te deconnecte pas"
	return

}
proc connexion_custom_vpx { hostname username password enable} {



	send "\r"

	expect "\\$"
	send "ssh -l $username $hostname\r"

	# expect  "passphrase" 
	# send "$passphrase\r"

	#sleep 2

	# expect "Escape"
	# send "\r"
	
	# puts "\n\n$password1"
	expect  {
		"assword"  { send "$enable\r"  }
		"name" { send "$username\r" ; expect "assword" ; send "$enable\r" }
		">" { send "\r" ;}
		"yes" {send "yes\r" ;  expect "assword" ; send "$enable\r" }

		}
	expect  {
		">" { send "\r" ;}
		"assword"  { send "$enable\r"  }

		}
	expect  {
		">" { send "\r" ; }
		"assword"  { send "$enable\r"  }

		}

	expect  {
		">" { send "\r" ;}
		
		}
		

	expect ">"
	send "\r"
	
	puts "Ne te deconnecte pas"
	return

}
proc connexion_cw {hostname ip} {

	send "telnet $ip\r"
	set password "d0n'tYze1t"
	
	puts "\n\n CONNEXION CW $hostname\n\n"
	expect  {
		"refused" { send "ssh -l ciscoworks $ip\r" ;} 
		"timeout" { send "ssh -l ciscoworks $ip\r" ;} 
		-re {[a-zA-Z0-9]#}  {send "\r" ; }
		"name" { send "ciscoworks\r" ; } 
		}
	expect {
				"yes" { send "yes\r" ; exp_continue}
				"assword" { send "$password\r"}
				"expire" {exp_continue}
				-re {[a-zA-Z0-9]#}  {send "\r" ; }
				-re {[a-zA-Z0-9]>}  {
							send "en\r" ; 
							expect {
										"name" { send "ciscoworks\r"; expect "assword" ; send "$password\r"}
										"assword" { send "$password\r"}
							}
						}
		}
	expect {
				-re {[a-zA-Z0-9]#}  {send "\r" ; }
				-re {[a-zA-Z0-9]>}  {
							send "en\r" ; 
							expect {
										"name" { send "ciscoworks\r"; expect "assword" ; send "$password\r"}
										"assword" { send "$password\r"}
							}
						}
	}
	
	expect {
				-re {[a-zA-Z0-9]#}  {send "\r" ; }
				-re {[a-zA-Z0-9]>}  {
							send "en\r" ; 
							expect {
										"name" { send "ciscoworks\r"; expect "assword" ; send "$password\r"}
										"assword" { send "$password\r"}
							}
						}
	}
		return
}

proc connexion_cw2 {hostname ip} {

	send "telnet $ip\r"
	set password "d0n'tYze1t"
	
	puts "\n\n CONNEXION CW $hostname sans diese\n\n"
	expect  {
		"refused" { send "ssh -l ciscoworks $ip\r" ;} 
		"timeout" { send "ssh -l ciscoworks $ip\r" ;} 
		"#"  {send "\r" ; }
		"name" { send "ciscoworks\r" ; expect "assword" ; send "d0n'tYze1t\r" }
		}
	expect {
				"assword" { send "$password\r"}
				"#" {send "\r" ; }
				">" {
							send "en\r" ; 
							expect {
										"name" { send "ciscoworks\r"; expect "assword" ; send "$password\r"}
										"assword" { send "$password\r"}
							}
					}
		}
	expect "#"  {send "\r" ; }
				
		return
}
proc connexion_cw_telnet {hostname} {

	send "telnet $hostname\r"
	set password "d0n'tYze1t"
	
	puts "\n\n CONNEXION CW $hostname\n\n"
	expect  {
		"refused" { send "ssh -l ciscoworks $ip\r" ;} 
		"timeout" { send "ssh -l ciscoworks $ip\r" ;} 
		-re {[a-zA-Z0-9]#}  {send "\r" ; }
		-re "name|login" { send "ciscoworks\r" ; expect "assword" ; send "d0n'tYze1t\r" }
		}
	expect {
				"assword" { send "$password\r"}
				"#" {send "\r" ; }
				">" {
							send "en\r" ; 
							expect {
										"name" { send "ciscoworks\r"; expect "assword" ; send "$password\r"}
										"assword" { send "$password\r"}
							}
					}
		}
	expect "#"  {send "\r" ; }
				
		return
}
proc connexion_cw_ssh {hostname ip} {
	
	
	puts "\n\n CONNEXION CW SSH $hostname\n\n"
	
	set password "d0n'tYze1t"
	send "ssh -l ciscoworks $ip\r"

	expect {
				"yes" { send "yes\r" ; exp_continue}
				"passphrase" { send "D1mension!!!\r" ;  exp_continue}
				"assword" { send "$password\r"}
				-re {[a-zA-Z0-9]#}  {send "\r" ; }
				-re {[a-zA-Z0-9]>}   {
							send "en\r" ; 
							expect {
										"name" { send "ciscoworks\r"; expect "assword" ; send "$password\r"}
										"assword" { send "$password\r"}
							}
						}
		}
		
	expect {
				"yes" { send "yes\r" ; exp_continue}
				"passphrase" { send "D1mension!!!\r" ;  exp_continue}
				"assword" { send "$password\r"}
				-re {[a-zA-Z0-9]#}  {send "\r" ; }
				-re {[a-zA-Z0-9]>}   {
							send "en\r" ; 
							expect {
										"name" { send "ciscoworks\r"; expect "assword" ; send "$password\r"}
										"assword" { send "$password\r"}
										-re {[a-zA-Z0-9]#}  {send "\r" ; }
							}
						}
		}
		
	expect -re {[a-zA-Z0-9]#}  {send "\r" ; }
				
	return
}

proc connexion_cw_host {hostname} {
	
	
	puts "\n\n CONNEXION CW SSH $hostname\n\n"
	
	set password "d0n'tYze1t"
	send "ssh -l ciscoworks $hostname\r"

	expect {
				"yes" { send "yes\r" ; exp_continue}
				"passphrase" { send "D1mension!!!\r" ;  exp_continue}
				"assword" { send "$password\r"}
				-re {[a-zA-Z0-9]#}  {send "\r" ; }
				-re {[a-zA-Z].*[0-9]>}  {
							send "en\r" ; 
							expect {
										"name" { send "ciscoworks\r"; expect "assword" ; send "$password\r"}
										"assword" { send "$password\r"}
							}
						}
		}
	expect -re {[a-zA-Z0-9]#}  {send "\r" ; }
				
	return
}

proc connexion_alt_exp {hostname prefixe passphrase prefixe_pass1 prefixe_pass2 prefixe_pass3} {
	set suffixe_pass [lindex [split $hostname "-"] 1]
	set position [ expr { [string length $hostname] -1 }  ]
	set username "noradius"
	set suffixe_pass_autre [string index $hostname $position ]
	set password1 "${prefixe}${prefixe_pass1}-${suffixe_pass}"
	set password2 "${prefixe}${prefixe_pass2}-${suffixe_pass}"
	set password3 "${prefixe}${prefixe_pass3}-${suffixe_pass}"
	puts "\nConnexion via Proxy - Alteon"
	puts "\n$password1 $password2 $password3\n"

	expect  {
		"passphrase"  {	send "$passphrase\r"}
		"Escape" {send "\r"}
		"seeing above note" { send "y\r"}
		"n to skip it" { send "n\r"}
		"password" {send "$password1\r" }
	}

	#sleep 2

	expect {
		"Escape" {send "\r"}
		"seeing above note" { send "y\r"}
		"n to skip it" { send "n\r"}
		"password" {send "$password2}"
	}
	

	expect  {
		"username" {send "$username\r" ; expect "assword" { send "$password1\r"  } }
		"assword"  { send "$password3\r"  }
		"seeing above note" { send "y\r"}
		"#" {send "\r" ; }
		}
	puts "test1\n"
	expect  {
		"incorrect" {
					expect {
							"username" { send "$username\r" ; expect "assword" { send "$password2\r"  } }
							"assword"  { send "$password2\r"  }
							}
					}
		"assword"  { send "$password2\r"  }
		"username" {send "$username\r" ; expect "assword" { send "$password2\r"  } }
		"seeing above note" { send "y\r"}
		"#" {send "\r" ; }
		}
	puts "test2\n"
	expect  {
		"username" {send "$username\r" ; expect "assword" { send "$password3\r"  } }
		"username" {send "$username\r" ; expect "assword" { send "$password2\r"  } }
		"incorrect" {send "\r" }
		"assword"  { send "$password3\r"  }
		"seeing above note" { send "y\r"}
		"#" {send "\r" ; }
		}
			

	expect {
		"#" {send "\r"}
			"seeing above note" { send "y\r"}
			"n to skip it" { send "n\r"}
	}
	
	expect {
			"#" {send "\r"}
			seeing above note" { send "y\r"}
			"n to skip it" { send "n\r"}
	}
	
	expect {
		"#" {send "\r"}
		seeing above note" { send "y\r"}
		"n to skip it" { send "n\r"}
	}
	
	puts "Ne te deconnecte pas"
	return
}

proc connexion_alt_nonexp {hostname prefixe passphrase prefixe_pass1 prefixe_pass2 prefixe_pass3} {
	set suffixe_pass [lindex [split $hostname "-"] 1]
	set position [ expr { [string length $hostname] -1 }  ]
	set suffixe_pass_autre [string index $hostname $position ]
	set password1 "${prefixe}${prefixe_pass1}-${suffixe_pass}"
	set password2 "${prefixe}${prefixe_pass2}-${suffixe_pass}"
	set password3 "${prefixe}${prefixe_pass3}-${suffixe_pass}"
	puts "\nConnexion Console - Alteon non expose"
	puts "\n$password1 $password2 $password3\n"



	expect "Escape"
	send "\r"

	expect  {
		"assword"  { send "$password1\r"  }
		"#" {send "\r" ; }
		}
	puts "test1\n"
	expect  {
		"assword"  { send "$password2\r"  }
		"#" {send "\r" ; }
		}
	puts "test2\n"
	expect  {
		"assword"  { send "$password3\r"  }
		"#" {send "\r" ; }
		}
			

	expect "#"
	send "\r"
	
	puts "Ne te deconnecte pas"
	return
}
proc connexion_alt_custom {hostname username password} {

	puts "\nConnexion Telnet - Alteon Radius"


	expect  {
		"username"  { send "$username\r"  }
		"assword"  { send "$password\r"  }
		"#" {send "\r" ; }
		}
		
	expect  {
		"assword"  { send "$password\r"  }
		"#" {send "\r" ; }
		}
	puts "test1\n"
	expect  {
		"assword"  { send "$password\r"  }
		"#" {send "\r" ; }
		}
	puts "test2\n"
	expect  {
		"assword"  { send "$password\r"  }
		"#" {send "\r" ; }
		}
			

	expect "#"
	send "\r"
	
	puts "Ne te deconnecte pas"
	return
}



proc rebond { ip } {

	if { $ip == "159.50.29.244" || $ip == "159.50.29.208" } {
		set unix [ exec /home/d83071/CONNEXION/getpass.sh "rebond_old"]
	} else {
		set unix [ exec /home/d83071/CONNEXION/getpass.sh "adm"]
	}
	expect {
		"yes" { send "yes\r";expect "assword" ; send "$unix\r"}
		"assword" { send "$unix\r"}
		"\\$"  {send "\r"}
		">"  {puts 'toto';send "\r"}
	}
	


	expect { 
		">" ; 	send "\r"
		"#" ; 	send "\r" 
		"\\$" ; 	send "\r" 
	}
	
	expect { 
		">" ; 	send "\r"
		"#" ; 	send "\r" 
		"\\$" ; 	send "\r" 
	}
	
	expect { 
		">" ; 	send "\r"
		"#" ; 	send "\r" 
		"\\$" ; 	send "\r" 
	}
}

proc spectrum {} {
	expect {
		"yes" { send "yes\r";expect "assword" ; send "Oclo0hvr\r"}
		"assword" { send "Oclo0hvr!\r"}
		"\\$" {	send "\r" }
	}

	expect "\\$"
	send "\r"
	
	expect "\\$"
	send "\r"
	
	expect "\\$"
	
	puts "\n\FIN\n\n"
	
}

proc oob_pwd { login mdp} {
	expect "login"
	send "$login\r"
	
	expect "Password"
	send "$mdp\r\r"
	
	# puts "\n2 secondes !!!\n\n"
	# sleep 2
	# send "\r"

}
proc rebond_cdn {} {

	set passphrase "Tek3pmac!"
	set password "Tek3pmac!"

	expect {
					"yes" { send "yes\r";expect "assword" ; send "B2rn1s12345!\r"}
					"assword" { send "B2rn1s12345!\r"}
	}

	expect "\\$"
	send "ssh -l d83071 111.64.216.100\r"


	expect "password"
	send "$password\r"

	expect "\\$"
	send "bash\r"

	expect "\\$"

}
proc deconnexion_cdn { } {
expect -re {[a-zA-Z0-9]#}
send "exit\r"

expect {
		"\\$" { send "exit\r"}
		"con0" { 
					send "\035"
					expect "telnet>"
					send "quit\r"
					expect "\\$"
					send "exit\r" 
		}
}
expect {
		"\\$" { send "exit\r"}
		"con0" { 
					send "\035"
					expect "telnet>"
					send "quit\r"
					expect "\\$"
					send "exit\r" 
		}
}

expect {
		"\\$" { send "exit\r"}
		"con0" { 
					send "\035"
					expect "telnet>"
					send "quit\r"
					expect "\\$"
					send "exit\r" 
		}
}
send "exit\r"

expect eof

}

proc deconnexion_vpx { } {
expect ">"
send "exit\r"

expect {
		"\\$" { send "exit\r"}
		"con0" { 
					send "\035"
					expect "telnet>"
					send "quit\r"
					expect "\\$"
					send "exit\r" 
		}
}

send "exit\r"

expect eof

}

proc deconnexion_default { } {

puts "coucou  deb decom"

expect {
			-re {[a-zA-Z0-9]#} { send "end\r" }
			-re {[a-zA-Z0-9]\S+#} { send "end\r" }
		}

expect {
			-re {[a-zA-Z0-9]#} { send "exit\r" }
			-re {[a-zA-Z0-9]\S+#} { send "exit\r" }
			-re {[a-zA-Z0-9]\S+\>} { send "exit\r" }
		}

puts "coucou  decom"
expect {
		eof {puts "END" }
		"\\$" { send "exit\r"}
		"con0" { 
					send "\035"
					expect "telnet>" 
					send "quit\r"
					expect "\\$"
					send "exit\r" 
		}
		-re {[a-zA-Z0-9]>} { send "exit\r"  ; expect "\\>" ; send "exit\r" }
		"login" { send "\x1A" ; expect ">" ; send "exit\r" ; expect "\\$"}
		"\$" { send "exit\r"}
					-re {[a-zA-Z0-9]\S+\>} { send "exit\r" }
}


}

proc iou_connect {_id _password _path _nb_ethernet} {

	expect "password"
	send "$_password\r"
	
	expect "\\\$"
	send "cd $_path\r"
	
	expect "\\\$"
	send "./i86bi_linuxl2-upk9-ms -e$_nb_ethernet -n64 $_id\r"
	
	expect {
		"initial" {send "no\r"}
		"terminate" {send "yes\r" }
		"RETURN" {send "\r"}
		">" { send "en\r"}
		"#" { send "\r"}
	}	
	
	expect {
		"initial" {send "no\r"}
		"terminate" {send "yes\r" }
		"RETURN" {send "\r"}
		">" { send "en\r"}
		"#" { send "\r"}
	}	

	expect {
		"initial" {send "no\r"}
		"terminate" {send "yes\r" }
		"RETURN" {send "\r"}
		">" { send "en\r"}
		"#" { send "\r"}
	}	
	
		expect {
		"initial" {send "no\r"}
		"terminate" {send "yes\r" }
		"RETURN" {send "\r"}
		">" { send "en\r"}
		"#" { send "\r"}
	}	
} 

proc iou_disconnect {} {
    expect -re {[a-zA-Z0-9]#}
    send "exit\r"
	
	expect "RETURN"
	send "\003"
		
	expect "\\\$"
	send "exit"
	
} 

proc rebond_pfhr {passphrase_} {
	set ip_rebond "184.5.1.149"
	set login_rebond "netprd06"
	set password_rebond "Frites.59"

	
	send "ssh -l $login_rebond $ip_rebond\r"
	
	expect "passphrase"
	send "$passphrase_\r"
	
	expect "password"
	send "$password_rebond\r"
	
}

proc oob_cb3_test3 {} {
	set ip_oob "184.3.32.8"
	set login_oob "local"
	set password_oob "cisco"
	
	expect -re {[a-zA-Z0-9]#}
	send "telnet $ip_oob\r"

	expect "sername"
	send "$login_oob\r"
	
	expect "assword"
	send "$password_oob\r"
	
	expect -re {[a-zA-Z0-9]#}
	send "\r"
}

proc oob_cb3_test4 {} {
	set ip_oob "184.3.32.9"
	set login_oob "local"
	set password_oob "cisco"
	
	expect -re {[a-zA-Z0-9]#}
	send "telnet $ip_oob\r"

	expect "sername"
	send "$login_oob\r"
	
	expect "assword"
	send "$password_oob\r"
	
	expect -re {[a-zA-Z0-9]#}
	send "\r"
}
proc init_hpov_def_c2 {} {
	set password_oob "Yol9Kxm"
	
	expect "assword"
	send "$password_oob\r"
	
	expect -re {[a-zA-Z0-9]#}
	send "minicom cisco\r"
	
	sleep 4
}