#!/usr/bin/expect -f

dict set folders "cisco" ".confg"
dict set folders "fortinet" ".confg"
dict set folders "paloalto" ".xml"
dict set folders "F5" ".scf"
set timeout 120
set unix [ exec /home/d83071/CONNEXION/getpass.sh "rebond_old"]

foreach item [dict keys $folders] {

	set folder $item  
	set FOLDER  [string toupper $folder]
	set extension [dict get $folders $item]
	
	spawn scp  -r ld83071@159.50.29.244:/apps/data/backup_telecom/$folder/running/*$extension CONFIG/$FOLDER
	
	expect {
		"yes" { send "yes\r";expect "assword" ; send "$unix\r"}
		"assword" { send "$unix\r"}
		">" { send "\r" }
	}
	
	
	expect eof
}
