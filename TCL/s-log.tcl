#!/usr/bin/expect -f


set timeout 45
set hostname [ string tolower [lindex $argv 0] ]
set type_connexion [ exec /home/d83071/CONNEXION/get_connexion.sh $hostname]
set tac [ exec /home/d83071/CONNEXION/getpass.sh "tacacs"]
set ldap [ exec /home/d83071/CONNEXION/getpass.sh "rebond_old" ]
set passphrase $tac
set username "d83071"
set suffixe_unix "l"
set unix_username $suffixe_unix$username
global unix
#set unix [ exec /home/d83071/CONNEXION/getpass.sh "unix"]
#set password $ldap
#set password_ldap $ldap
set password_tacacs $tac
set enable $tac
set date_ [ exec date +%d%m%y_%Hh%Mm%Ss ]
set fichier "LOG/${hostname}_${date_}.log"
set ip_rebond "159.50.29.244"
if { $argc == 2} {
    set ip_rebond "159.50.66.10"
}
source ./fonctions-connexion.tcl

switch $type_connexion {

	TACACS_SSH_SPEC
	{
		puts "\nConnexion TACACS ACS wo DNS\n"
		set IP  [ exec CONNEXION/get_IP_direct.sh $hostname ]
	    spawn ssh $unix_username@$ip_rebond
		rebond $ip_rebond
		send "ssh -l $unix_username $IP\r"
		connexion $username $password_tacacs $password_tacacs $passphrase
		puts "\n\nOUTPUT dans LOG/$fichier\n\n"
		log_file -a $fichier
		interact
		log_file
	}
	LOCAL0_IP {
		puts "\nCONNEXION MDP LOCAL NO DNS\n"
	    spawn ssh $unix_username@$ip_rebond
		rebond $ip_rebond
		set IP [exec  /home/d83071/CONNEXION/get_IP.sh $hostname ]
		set local_username "admin"
		set local [ exec /home/d83071/CONNEXION/getpass.sh "local"]
		send "ssh -l $local_username $IP\r"
		connexion $local_username $local $local $passphrase
		log_file -a $fichier
		#puts "[clock format [clock seconds] -format {%Y-%m-%d %H:%M:%S} ]"
		#interact {
		#\r {   send_user "[clock format [clock seconds] -format {%Y-%m-%d %H:%M:%S}]" ;
		#	   send_log  "[clock format [clock seconds] -format {%Y-%m-%d %H:%M:%S}]"; 
		#	   exec echo "[clock format [clock seconds] -format {%Y-%m-%d %H:%M:%S}]" >> $fichier;
		#	   send "\r" }
		#\n { send_user "[clock format [clock seconds] -format {%Y-%m-%d %H:%M:%S}]";
		#       send_log  "[clock format [clock seconds] -format {%Y-%m-%d %H:%M:%S}]"; send "\r" }
		# ~~
		#}
		interact
		log_file
	}
	PFH_IP {
		puts "\nCONNEXION MDP LOCAL NO DNS\n"
	    spawn ssh $unix_username@$ip_rebond
		rebond $ip_rebond
		set IP [exec  /home/d83071/CONNEXION/get_IP.sh $hostname ]
		set local_username "a48907"
		set local [ exec /home/d83071/CONNEXION/getpass.sh "pfh"]
		send "ssh -l $local_username $IP\r"
		connexion $local_username $local $local $passphrase
		log_file -a $fichier
		#puts "[clock format [clock seconds] -format {%Y-%m-%d %H:%M:%S} ]"
		#interact {
		#\r {   send_user "[clock format [clock seconds] -format {%Y-%m-%d %H:%M:%S}]" ;
		#	   send_log  "[clock format [clock seconds] -format {%Y-%m-%d %H:%M:%S}]"; 
		#	   exec echo "[clock format [clock seconds] -format {%Y-%m-%d %H:%M:%S}]" >> $fichier;
		#	   send "\r" }
		#\n { send_user "[clock format [clock seconds] -format {%Y-%m-%d %H:%M:%S}]";
		#       send_log  "[clock format [clock seconds] -format {%Y-%m-%d %H:%M:%S}]"; send "\r" }
		# ~~
		#}
		interact
		log_file
	}
	LOCAL0 {
		puts "\nCONNEXION MDP LOCAL\n"
	    spawn ssh $unix_username@$ip_rebond
		rebond $ip_rebond
		set local_username "admin"
		set local [ exec /home/d83071/CONNEXION/getpass.sh "local"]
		send "ssh -l $local_username $hostname\r"
		connexion $local_username $local $local $passphrase
		log_file -a $fichier
		#puts "[clock format [clock seconds] -format {%Y-%m-%d %H:%M:%S} ]"
		#interact {
		#\r {   send_user "[clock format [clock seconds] -format {%Y-%m-%d %H:%M:%S}]" ;
		#	   send_log  "[clock format [clock seconds] -format {%Y-%m-%d %H:%M:%S}]"; 
		#	   exec echo "[clock format [clock seconds] -format {%Y-%m-%d %H:%M:%S}]" >> $fichier;
		#	   send "\r" }
		#\n { send_user "[clock format [clock seconds] -format {%Y-%m-%d %H:%M:%S}]";
		#       send_log  "[clock format [clock seconds] -format {%Y-%m-%d %H:%M:%S}]"; send "\r" }
		# ~~
		#}
		interact
		log_file
	}
	LOCAL1 {
		puts "\nCONNEXION MDP LOCAL\n"
	    spawn ssh $unix_username@$ip_rebond
		rebond $ip_rebond
		set local_username "admin"
		set local [ exec /home/d83071/CONNEXION/getpass.sh "local1"]
		send "ssh -l $local_username $hostname\r"
		connexion $local_username $local $local $passphrase
		log_file -a $fichier
		#puts "[clock format [clock seconds] -format {%Y-%m-%d %H:%M:%S} ]"
		#interact {
		#\r {   send_user "[clock format [clock seconds] -format {%Y-%m-%d %H:%M:%S}]" ;
		#	   send_log  "[clock format [clock seconds] -format {%Y-%m-%d %H:%M:%S}]"; 
		#	   exec echo "[clock format [clock seconds] -format {%Y-%m-%d %H:%M:%S}]" >> $fichier;
		#	   send "\r" }
		#\n { send_user "[clock format [clock seconds] -format {%Y-%m-%d %H:%M:%S}]";
		#       send_log  "[clock format [clock seconds] -format {%Y-%m-%d %H:%M:%S}]"; send "\r" }
		# ~~
		#}
		interact
		log_file
	}
	DOMAN {
	    puts "\nConnexion DOMAN"
		set doman [ exec /home/d83071/CONNEXION/getpass.sh "doman" ]
	    spawn ssh $unix_username@$ip_rebond
		rebond $ip_rebond
		send "ssh -l $username $hostname\r"
		connexion $username $doman $doman $passphrase
		puts "\n\nOUTPUT dans LOG/$fichier\n\n"
		log_file -a $fichier
		interact
		log_file
	}
	TSK {
	    puts "\nConnexion TSK"
		set type [ string tolower [ exec /home/d83071/CONNEXION/get_param.sh $hostname "3" ] ]
		set tsk  [ exec /home/d83071/CONNEXION/getpass.sh $type ]
		set username_tsk  [ exec /home/d83071/CONNEXION/getlogin.sh $type ]
	    spawn ssh $unix_username@$ip_rebond
		rebond $ip_rebond
		send "ssh -l $username_tsk $hostname\r"
		connexion $username_tsk $tsk $tsk $passphrase
		puts "\n\nOUTPUT dans LOG/$fichier\n\n"
		log_file -a $fichier
		interact
		log_file
	}
	CKP {
	    puts "\nConnexion Checkpoint"
	    spawn ssh $unix_username@$ip_rebond
		rebond $ip_rebond
		send "ssh -l $unix_username $hostname\r"
		connexion_expert $unix_username $password_tacacs
		puts "\n\nOUTPUT dans LOG/$fichier\n\n"
		log_file -a $fichier
		interact
		log_file
	}
	default {
	    puts "\nConnexion par défaut\n"
		puts "\nCONNEXION TACACS\n"
	    spawn ssh $unix_username@$ip_rebond
		rebond $ip_rebond
		send "ssh -l $unix_username $hostname\r"
		connexion $unix_username $password_tacacs $password_tacacs $passphrase
		puts "\n\nOUTPUT dans LOG/$fichier\n\n"
		log_file -a $fichier
		interact
		#interact
		log_file
	}

}
