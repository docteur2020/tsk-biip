#!/usr/bin/expect -f


set timeout 45
set hostname [ string tolower [lindex $argv 0] ]
set type_connexion [ exec /home/d83071/CONNEXION/get_connexion.sh $hostname]
set tac [ exec /home/d83071/CONNEXION/getpass.sh "tacacs"]
#set ldap [ exec /home/d83071/CONNEXION/getpass.sh "ldap" ]
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

source ./fonctions-connexion.tcl

switch $type_connexion {

	TACACS_SSH_SPEC
	{
		puts "\nConnexion TACACS ACS wo DNS\n"
		set IP  [ exec CONNEXION/get_IP_direct.sh $hostname ]
	    spawn ssh $unix_username@$ip_rebond
		rebond
		send "ssh -l $unix_username $IP\r"
		connexion $username $password_tacacs $password_tacacs $passphrase
		puts "\n\nOUTPUT dans LOG/$fichier\n\n"
		log_file -a $fichier
		interact
		log_file
	}
	TACACS_SSH {
	puts "\nCONNEXION TACACS DIRECT\n"
	set IP  [ exec ./get_IP_direct.sh $hostname ]
	spawn ssh -l $unix_username $IP
	connexion $username $password $enable $passphrase
	puts "\n\nOUTPUT dans LOG/$fichier\n\n"
	log_file -a $fichier
	interact
	log_file
	}
	TACACS_TELNET {
	puts "\nCONNEXION TACACS DIRECT\n"
	set IP  [ exec ./get_IP_direct.sh $hostname ]
	spawn telnet $IP
	connexion $username $password $enable $passphrase
	puts "\n\nOUTPUT dans LOG/$fichier\n\n"
	log_file -a $fichier
	interact
	log_file
	}
	CUSTOM {
		puts "\nCONNEXION SSH CUSTOMISE\n"
		set username [ exec ./CONNEXION/get_custom_username.sh $hostname ]
		set password [ exec ./CONNEXION/get_custom_password.sh $hostname ]
		set enable   [ exec ./CONNEXION/get_custom_enable.sh $hostname ]
		spawn ssh d83071@$ip_rebond
		rebond
		send "ssh -l $unix_username $hostname\r"
		connexion $username $password $enable $passphrase
		log_file -a $fichier
		interact
		log_file
	}
	CUSTOM_IP {
		puts "\nCONNEXION SSH CUSTOMISE IP SANS RESOLUTION\n"
		set username [ exec ./CONNEXION/get_custom_username.sh $hostname ]
		set password [ exec ./CONNEXION/get_custom_password.sh $hostname ]
		set enable   [ exec ./CONNEXION/get_custom_enable.sh $hostname ]
		set ip       [ exec ./CONNEXION/get_custom_ip.sh $hostname ]
		spawn ssh d83071@$ip_rebond
		rebond
		send "ssh -l $unix_username $ip\r"
		connexion $username $password $enable $passphrase
		log_file -a $fichier
		interact
		log_file
	}
	CUSTOM_TELNET {
		puts "\nCONNEXION TELNET CUSTOMISE\n"
		spawn ssh d83071@$ip_rebond
		rebond
		set username [ exec ./CONNEXION/get_custom_username.sh $hostname ]
		set password [ exec ./CONNEXION/get_custom_password.sh $hostname ]
		set enable   [ exec ./CONNEXION/get_custom_enable.sh $hostname ]
		send "telnet $hostname\r"
		connexion $username $password $enable $passphrase
		log_file -a $fichier
		interact
		log_file
	}
	REVERSE {
		puts "\nCONNEXION CONSOLE EN REVERSE TELNET\n"
		spawn ssh d83071@$ip_rebond
		rebond
		set prefixe_pass1 "ayril"
		set prefixe_pass2 "arkhy"
		set prefixe_pass3 "euzan"
		set IP_rebond [exec ./get_IP.sh $hostname ]
		set Port_reverse [exec ./get_Port.sh $hostname]
		send "telnet $IP_rebond $Port_reverse\r"
		connexion2 $hostname "P" $prefixe_pass1 $prefixe_pass2 $prefixe_pass3
		log_file -a $fichier
		interact
		log_file
	}
	REVERSE2 {
		puts "\nCONNEXION CONSOLE EN REVERSE TELNET\n"
		spawn ssh d83071@$ip_rebond
		rebond
		set prefixe_pass1 "ayril"
		set prefixe_pass2 "yraje"
		set prefixe_pass3 "euzan"
		set IP_rebond [exec ./get_IP.sh $hostname ]
		set Port_reverse [exec ./get_Port.sh $hostname]
		send "telnet $IP_rebond $Port_reverse\r"
		connexion2 $hostname "T" $prefixe_pass1 $prefixe_pass2 $prefixe_pass3
		log_file -a $fichier
		interact
		log_file
	}
	REVERSE3 {
		puts "\nCONNEXION CONSOLE EN REVERSE TELNET\n"
		spawn ssh d83071@$ip_rebond
		rebond
		set prefixe_pass1 "arkhy"
		set prefixe_pass2 "yraje"
		set prefixe_pass3 "euzan"
		set IP_rebond [exec ./get_IP.sh $hostname ]
		set Port_reverse [exec ./get_Port.sh $hostname]
		send "telnet $IP_rebond $Port_reverse\r"
		connexion2 $hostname "P" $prefixe_pass1 $prefixe_pass2 $prefixe_pass3
		log_file -a $fichier
		interact
		log_file
	}
	REVERSE_NEXUS {
		puts "\nCONNEXION CONSOLE EN REVERSE TELNET - NEXUS\n"
		spawn ssh d83071@$ip_rebond
		rebond
		set prefixe_pass1 "arkhy"
		set prefixe_pass2 "ayril"
		set prefixe_pass3 "euzan"
		set IP_rebond [exec ./get_IP.sh $hostname ]
		set Port_reverse [exec ./get_Port.sh $hostname]
		send "telnet $IP_rebond $Port_reverse\r"
		connexion2_nexus $hostname "P" $prefixe_pass1 $prefixe_pass2 $prefixe_pass3
		log_file -a $fichier
		interact
		log_file
	}
	REVERSE_NEXUS_SPEC {
		puts "\nCONNEXION CONSOLE EN REVERSE TELNET- NEXUS SPEC\n"
		spawn ssh d83071@$ip_rebond
		rebond
		set IP_rebond [exec ./get_IP.sh $hostname ]
		set Port_reverse [exec ./get_Port.sh $hostname]
		send "telnet $IP_rebond $Port_reverse\r"
		connexion2_admin_nexus $hostname
		log_file -a $fichier
		interact
		log_file
	}
	PROXY {
		puts "\nCONNEXION VIA PSTERM P\n"
		spawn ssh d83071@$ip_rebond
		rebond
		set prefixe_pass1 "euzan"
		set prefixe_pass2 "arkhy"
		set prefixe_pass3 "yraje"
		send "ssh $hostname@172.16.16.210\r"
		connexion3 $hostname "P" $passphrase $prefixe_pass1 $prefixe_pass2 $prefixe_pass3
		log_file -a $fichier
		interact
		log_file
	}
	PROXY2 {
		puts "\nCONNEXION VIA PSTERM T\n"
		spawn ssh d83071@$ip_rebond
		rebond
		set prefixe_pass1 "euzan"
		set prefixe_pass2 "ymone"
		set prefixe_pass3 "yraje"
		send "ssh $hostname@172.16.16.210\r"
		connexion3 $hostname "T" $passphrase $prefixe_pass1 $prefixe_pass2 $prefixe_pass3
		log_file -a $fichier
		interact
		log_file
	}
	PROXY3 {
		puts "\nCONNEXION VIA PSTERM T W/0 Escape\n"
		spawn ssh d83071@$ip_rebond
		rebond
		set prefixe_pass1 "euzan"
		set prefixe_pass2 "ymone"
		set prefixe_pass3 "yraje"
		send "ssh $hostname@172.16.16.210\r"
		connexion4 $hostname "T" $passphrase $prefixe_pass1 $prefixe_pass2 $prefixe_pass3
		log_file -a $fichier
		interact
		log_file
	}
	PROXY4 {
		puts "\nCONNEXION VIA PSTERM T W/0 Escape\n"
		spawn ssh d83071@$ip_rebond
		rebond
		set prefixe_pass1 "euzan"
		set prefixe_pass2 "ymone"
		set prefixe_pass3 "yraje"
		send "ssh $hostname@172.16.16.210\r"
		connexion4 $hostname "P" $passphrase $prefixe_pass1 $prefixe_pass2 $prefixe_pass3
		log_file -a $fichier
		interact
		log_file
	}
	EXPOSE_1 {
		puts "\nCONNEXION PAR DEFAUT\n"
		spawn ssh d83071@$ip_rebond
		rebond
		connexion_expose1 $hostname
		log_file -a $fichier
		interact
		log_file
	}
	EXPOSE_2 {
		puts "\nCONNEXION EXPOSE TELNET\n"
		spawn ssh d83071@$ip_rebond
		rebond
		connexion_expose2 $hostname
		log_file -a $fichier
		interact
		log_file
	}
	EXPOSE_VPX {
		puts "\nCONNEXION SSH VPX\n"
		spawn ssh d83071@$ip_rebond
		rebond
		connexion_expose_vpx $hostname
		log_file -a $fichier
		interact
		log_file
	}
	CUSTOM_VPX {
		puts "\nCONNEXION SSH VPX CUSTOM\n"
		spawn ssh d83071@$ip_rebond
		rebond
		set username [ exec /home/d83071/CONNEXION/get_custom_username.sh $hostname ]
		set password [ exec /home/d83071/CONNEXION/get_custom_password.sh $hostname ]
		set enable   [ exec /home/d83071/CONNEXION/get_custom_enable.sh $hostname ]
		connexion_custom_vpx $hostname $username $password $enable
		log_file -a $fichier
		interact
		log_file
	}
	ALTEON_PROXY_EXP {
		puts "\nCONNEXION ALTEON VIA PSTERM\n"
		spawn ssh d83071@$ip_rebond
		rebond
		set prefixe_pass1 "arkhy"
		set prefixe_pass2 "euzan"
		set prefixe_pass3 "yraje"
		send "ssh $hostname@172.16.16.210\r"
		connexion_alt_exp $hostname "M" $passphrase $prefixe_pass1 $prefixe_pass2 $prefixe_pass3
		log_file -a $fichier
		interact
		log_file
		
	}
	ALTEON_PROXY_CUSTOM {
		puts "\nCONNEXION ALTEON VIA PSTERM CUSTOM\n"
		spawn ssh d83071@$ip_rebond
		rebond
		set username [ exec ./get_custom_username.sh $hostname ]
		set password [ exec ./get_custom_password.sh $hostname ]
		set enable   [ exec ./get_custom_enable.sh $hostname ]
		set IP_rebond [exec ./get_IP.sh $hostname ]
		set Port_reverse [exec ./get_Port.sh $hostname]
		send "telnet $IP_rebond $Port_reverse\r"
		connexion_alt $hostname $passphrase $username $password $enable
		log_file -a $fichier
		interact
		log_file
		
	}
	ALTEON_EXP_CUSTOM {
		puts "\nCONNEXION ALTEON VIA PSTERM CUSTOM\n"
		spawn ssh d83071@$ip_rebond
		rebond
		set username [ exec ./get_custom_username.sh $hostname ]
		set password [ exec ./get_custom_password.sh $hostname ]
		set enable   [ exec ./get_custom_enable.sh $hostname ]
		set IP_rebond [exec ./get_IP.sh $hostname ]
		set Port_reverse [exec ./get_Port.sh $hostname]
		send "ssh $hostname@172.16.16.210\r"
		connexion_alt_exp_custom  $hostname $passphrase $username $password $enable
		log_file -a $fichier
		interact
		log_file
		
	}
	ALTEON_REVERSE_EXP {
		puts "\nCONNEXION ALTEON VIA PSTERM\n"
		spawn ssh d83071@$ip_rebond
		rebond
		set prefixe_pass1 "euzan"
		set prefixe_pass2 "ymone"
		set prefixe_pass3 "yraje"
		set IP_rebond [exec ./get_IP.sh $hostname ]
		set Port_reverse [exec ./get_Port.sh $hostname]
		send "telnet $IP_rebond $Port_reverse\r"
		connexion_alt_exp2 $hostname "M" $passphrase $prefixe_pass1 $prefixe_pass2 $prefixe_pass3
		log_file -a $fichier
		interact
		log_file		
	}
	ALTEON_REVERSE_EXP_BSJ {
		puts "\nCONNEXION ALTEON VIA PSTERM SUFFIXE BEAUSEJOUR\n"
		spawn ssh d83071@$ip_rebond
		rebond
		set prefixe_pass1 "euzan"
		set prefixe_pass2 "ymone"
		set prefixe_pass3 "yraje"
		set IP_rebond [exec ./get_IP.sh $hostname ]
		set Port_reverse [exec ./get_Port.sh $hostname]
		send "telnet $IP_rebond $Port_reverse\r"
		connexion_alt_exp3 $hostname "M" $passphrase $prefixe_pass1 $prefixe_pass2 $prefixe_pass3
		log_file -a $fichier
		interact
		log_file		
	}
	ALTEON_TELNET {
		puts "\nCONNEXION ALTEON TELNET\n"
		spawn ssh d83071@$ip_rebond
		rebond
		set prefixe_pass1 "euzan"
		set prefixe_pass2 "ymone"
		set prefixe_pass3 "yraje"
		send "telnet $hostname\r"
		connexion_alt_exp2 $hostname "M" $passphrase $prefixe_pass1 $prefixe_pass2 $prefixe_pass3
		log_file -a $fichier
		interact
		log_file		
	}
	CISCOWORKS {
		puts "\nCONNEXION CISCOW\n"
		spawn ssh d83071@$ip_rebond
		set ip [ exec ./get_IP_CW.sh $hostname ]
		rebond
		connexion_cw $hostname $ip
		log_file -a $fichier
		interact
		log_file
	}
	CW_NODIESE {
		puts "\nCONNEXION CISCOW\n"
		spawn ssh d83071@$ip_rebond
		set ip [ exec ./get_IP_CW.sh $hostname ]
		rebond
		connexion_cw2 $hostname $ip
		log_file -a $fichier
		interact
		log_file
	}
	CW_SSH {
		puts "\nCONNEXION CISCOW SSH\n"
		spawn ssh d83071@$ip_rebond
		set ip [ exec ./get_IP_CW.sh $hostname ]
		rebond
		connexion_cw_ssh $hostname $ip
		log_file -a $fichier
		interact
		log_file
	}
	CW_TELNET {
		puts "\nCONNEXION CISCOW\n"
		spawn ssh d83071@$ip_rebond
		rebond
		connexion_cw_telnet $hostname
		log_file -a $fichier
		interact
		log_file
	}
	CW_SSH_HOST {
		puts "\nCONNEXION CISCOW\n"
		spawn ssh d83071@$ip_rebond
		rebond
		connexion_cw_host $hostname
		log_file -a $fichier
		interact
		log_file
	}
	LOGIN_ACS_SSH {
		spawn ssh d83071@$ip_rebond
		rebond
		connexion_acs_ssh $hostname $username $password_ldap $passphrase
		log_file -a $fichier
		interact
		log_file
	}
	LOGIN_ACS_SSH2 {
		spawn ssh d83071@$ip_rebond
		rebond
		connexion_acs_ssh $hostname $username $password $passphrase
		log_file -a $fichier
		interact
		log_file
	}
	MAIA_ANC {
		puts "\nCONNEXION MAIA ANCIEN\n"
		spawn ssh d83071@$ip_rebond
		rebond
		set prefixe_pass1 "aikel"
		set prefixe_pass2 "ymone"
		set prefixe_pass3 "yraje"
		send "telnet $hostname\r"
		connexion5 $hostname "T" $passphrase $prefixe_pass1 $prefixe_pass2 $prefixe_pass3
		log_file -a $fichier
		interact
		log_file
	}
	AVAYA {
		puts "\nCONNEXION MAIA AVAYA\n"
		spawn ssh d83071@$ip_rebond
		rebond
		connexion_avaya $hostname $username $password_ldap $passphrase
		log_file -a $fichier
		interact
		log_file
	}
	ALTEON {
		puts "\nCONNEXION ALTEON\n"
		spawn ssh d83071@$ip_rebond
		rebond
		send "telnet $hostname\r"
		set username [ exec /home/d83071/CONNEXION/get_custom_username.sh $hostname ]
		set password [ exec /home/d83071/CONNEXION/get_custom_password.sh $hostname ]
		set enable   [ exec /home/d83071/CONNEXION/get_custom_enable.sh $hostname ]
		connexion_alt_custom $hostname $username $password
		log_file -a $fichier
		interact
		log_file		
	}
	LOGIN_ACS_TELNET {
		spawn ssh d83071@$ip_rebond
		rebond
		connexion_acs_telnet $hostname $username $password_ldap
		log_file -a $fichier
		interact
		log_file	
	}
	LOGIN_ACS_TELNET2 {
		spawn ssh d83071@$ip_rebond
		rebond
		connexion_acs_telnet $hostname $username $password_ldap
		log_file -a $fichier
		interact
		log_file	
	}

	BIGIP {
		puts "\nCONNEXION VIA CDN BIG IP\n"
		spawn ssh d83071@$ip_rebond
		rebond
		set username [ exec ./get_custom_username.sh $hostname ]
		set password [ exec ./get_custom_password.sh $hostname ]
		set enable [ exec ./get_custom_enable.sh $hostname ]
		send "ssh -l $unix_username $hostname\r"
		connexion_bigip $username $password $password $passphrase
		log_file -a $fichier
		interact
		log_file	
	}
	REVERSE_SESAME {
		puts "\nCONNEXION CONSOLE EN REVERSE SESAME\n"
		spawn ssh d83071@$ip_rebond
		rebond
		set IP_rebond [exec ./get_IP.sh $hostname ]
		set Port_reverse [exec ./get_Port.sh $hostname]
		send "telnet $IP_rebond $Port_reverse\r"
		connexion_reverse_custom $username $password_sesame $password_sesame
		log_file -a $fichier
		interact
		log_file
	}
	LOCAL0_IP {
		puts "\nCONNEXION MDP LOCAL NO DNS\n"
	    spawn ssh $unix_username@$ip_rebond
		rebond
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

	DOMAN {
	    puts "\nConnexion DOMAN"
		set doman [ exec /home/d83071/CONNEXION/getpass.sh "doman" ]
	    spawn ssh $unix_username@$ip_rebond
		rebond
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
		rebond
		send "ssh -l $username_tsk $hostname\r"
		connexion $username_tsk $tsk $tsk $passphrase
		puts "\n\nOUTPUT dans LOG/$fichier\n\n"
		log_file -a $fichier
		interact
		log_file
	}
	default {
	    puts "\nConnexion par défaut\n"
		puts "\nCONNEXION TACACS\n"
	    spawn ssh $unix_username@$ip_rebond
		rebond
		send "ssh -l $unix_username $hostname\r"
		connexion $unix_username $password_tacacs $password_tacacs $passphrase
		puts "\n\nOUTPUT dans LOG/$fichier\n\n"
		log_file -a $fichier
		interact -o "\n" { send_log [timestamp -format %c\n] }
		log_file
	}

}
