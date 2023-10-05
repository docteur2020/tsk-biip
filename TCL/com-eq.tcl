#!/usr/bin/expect -f


set timeout 300
set hostname [ string tolower [lindex $argv 0] ]
set type_connexion [ exec /home/d83071/CONNEXION/get_connexion.sh $hostname]
set tac [ exec /home/d83071/CONNEXION/getpass.sh "tacacs"]
set ldap [ exec /home/d83071/CONNEXION/getpass.sh "tacacs" ]
set passphrase $tac
set username "d83071"
set suffixe_unix "l"
set unix_username $suffixe_unix$username
global unix
set unix [ exec /home/d83071/CONNEXION/getpass.sh "tacacs"]
set password $ldap
set password_ldap $ldap
set password_tacacs $tac
set enable $tac
set date_ [ exec date +%d%m%y_%Hh%Mm%Ss ]
set fichier "LOG/${hostname}_${date_}_commandes.log"
set fichier_commandes [open [lindex $argv 1] r]
set ip_rebond "159.50.29.244"
if { $argc == 3} {
    set ip_rebond "159.50.66.10"
}
source ./fonctions-connexion.tcl

switch $type_connexion {

	TACACS_SSH {
		puts "\nCONNEXION TACACS DIRECT\n"
		set IP  [ exec ./get_IP_direct.sh $hostname ]
		spawn ssh -l $username $IP
		connexion $username $password_tacacs $password_tacacs $passphrase
		puts "\n\nOUTPUT dans LOG/$fichier\n\n"
		getlog $fichier $fichier_commandes
		deconnexion_direct
	}
	TACACS_SSH_SPEC
	{
		puts "\nCONNEXION TACACS INDIRECT\n"
		set IP  [ exec ./get_IP_direct.sh $hostname ]
		spawn ssh vv5347@10.91.32.13
		spectrum
		send "ssh -l $username $hostname\r"
		connexion $username $password_tacacs $password_tacacs $passphrase
		puts "\n\nOUTPUT dans LOG/$fichier\n\n"
		getlog $fichier $fichier_commandes
		deconnexion_spectrum
	}
	TACACS_TELNET {
		puts "\nCONNEXION TACACS DIRECT\n"
		set IP  [ exec ./get_IP_direct.sh $hostname ]
		spawn telnet $IP
		connexion $username $password_tacacs $enable $passphrase
		puts "\n\nOUTPUT dans LOG/$fichier\n\n"
		getlog $fichier $fichier_commandes
		deconnexion_direct
	}
	CUSTOM {
		puts "\nCONNEXION SSH CUSTOMISE\n"
		set username [ exec ./CONNEXION/get_custom_username.sh $hostname ]
		set password [ exec ./CONNEXION/get_custom_password.sh $hostname ]
		set enable   [ exec ./CONNEXION/get_custom_enable.sh $hostname ]
		spawn ssh x112097@192.64.10.129
		paer
		send "ssh -l $username $hostname\r"
		connexion $username $password $enable $passphrase
		getlog $fichier $fichier_commandes
		deconnexion_default
	}
	CUSTOM_IP {
		puts "\nCONNEXION SSH CUSTOMISE IP SANS RESOLUTION\n"
		set username [ exec ./CONNEXION/get_custom_username.sh $hostname ]
		set password [ exec ./CONNEXION/get_custom_password.sh $hostname ]
		set enable   [ exec ./CONNEXION/get_custom_enable.sh $hostname ]
		set ip       [ exec ./CONNEXION/get_custom_ip.sh $hostname ]
		spawn ssh x112097@192.64.10.129
		paer
		send "ssh -l $username $ip\r"
		connexion $username $password $enable $passphrase
		getlog $fichier $fichier_commandes
		deconnexion_default
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
		puts "\n\nOUTPUT dans LOG/$fichier\n\n"
		getlog $fichier $fichier_commandes
		deconnexion_default
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
		puts "\n\nOUTPUT dans LOG/$fichier\n\n"
		getlog $fichier $fichier_commandes
		deconnexion_default
	}
	default {
	    puts "\nConnexion par défaut\n"
		puts "\nCONNEXION TACACS\n"
	    spawn ssh $unix_username@$ip_rebond
		rebond $ip_rebond
		send "ssh -l $unix_username $hostname\r"
		connexion_wo_monitor $unix_username $password_tacacs $password_tacacs $passphrase
		puts "\n\nOUTPUT dans LOG/$fichier\n\n"
		getlog $fichier $fichier_commandes
		deconnexion_default
	}

}
