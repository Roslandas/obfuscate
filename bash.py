#!/bin/bash

IFS=$'\t\n'

openssl_install=$(dpkg -l | egrep "openssl")		# Dependencies 

# find the current user.
whoami=$(whoami)
ubuntu1="/home/$whoami/Ubuntu One"

# Check to make sure openssl is installed.
if [ -z "$openssl_install" ]
then
	zenity --warning --text="The package \"openssl\" is required and currently is not installed. \n\nRun \"sudo apt-get install openssl\" in a terminal and then re-run this script."
	exit 0
fi

# Ask whether to encrypt or to decrypt...
method=$(gdialog --title "Encrypt -or- Decrypt?" --radiolist "" 60 100 110 1 Encrypt off 2 Decrypt off 2>&1)
if [ $method = "1" ] # start the encryption process...
then
	# Make sure the Ubuntu One folder exists.
	if [ -d "$ubuntu1" ]
	then
		echo
	else
		zenity --warning --text="The \"Ubuntu One\" directory was expected at \"/home/$whoami/Ubuntu One/\", and was not found."
		exit 0
	fi

	# Get the passphrase to be used for encrypting the data...
	# Confirm the entry and require a passphrase to be used...
	while [[ "$match" = "" ]]
	do
		pass=`zenity --entry --hide-text --text="Enter a strong passphrase" --title="Encryption Passphrase Required"`
		pass_conf=`zenity --entry --hide-text --text="Confirm passphrase" --title="Confirmation"`
		if [[ "$pass" = "" ]]
		then
			zenity --warning --text="Sorry, a passphrase is required.\n\nThe program will now exit."
			exit 0
		elif [[ "$pass" = "$pass_conf" ]]
		then
			match='1'
			continue
		else
			zenity --warning --text="Sorry, your passwords didn't match.\n\nPress \"OK\" to retry."		
		fi
	done

	for each in `echo "$NAUTILUS_SCRIPT_SELECTED_FILE_PATHS"`
	do
		if [ -d "$each" ]
		then
			dirname=$(echo $each | sed 's/\/$//g;s/.*\///g')
			cd $NAUTILUS_SCRIPT_CURRENT_URI
			#tar -czf $dirname.gzip $each
			tar -czf `basename $each`.gzip `basename $each`
			openssl des3 -salt -pass pass:$pass -in `basename $each`.gzip -out $ubuntu1/`basename $each`.gzip.des3
			rm $dirname.gzip
		else
			filename=$(echo $each | sed 's/.*\///g')
			openssl des3 -salt -pass pass:$pass -in $each -out $ubuntu1/$filename.des3
		fi
	done
elif [ $method = "2" ] # start the decryption process...
then
	for each in `echo "$NAUTILUS_SCRIPT_SELECTED_FILE_PATHS"`
	do
		decrypt_loc=$(echo "$NAUTILUS_SCRIPT_CURRENT_URI" | sed 's/file\:\/\///g;s/\%20/ /g')
		if [[ "$ubuntu1" = "$decrypt_loc" ]]
		then
			zenity --warning --text="Sorry, this script won't allow decryption of data\nfrom within $ubuntu1.\n\nThis will prevent accidental decryption of data within the Ubuntu One Cloud.\n\nFirst copy your encrypted data to another directory\nand then re-run this script.\n\nThe program will now exit."
			exit 0
		fi

		# start decrypting data...
		# Get the passphrase to be used to decrypt...
		pass=`zenity --entry --hide-text --text="Enter the passphrase needed for decryption:" --title="Decryption Passphrase Required"`
		if [[ "$pass" = "" ]]
		then
			zenity --warning --text="Sorry, a passphrase is required\nto decrypt data.\n\nThe program will now exit."
			exit 0
		fi
		
		if [[ "$each" =~ \.gzip ]]
		then
			filename=$(echo $each | sed 's/\.des3//g')
			openssl des3 -d -salt -pass pass:$pass -in $each -out $filename
			tar -xzf $filename
			rm $filename
		else
			filename=$(echo $each | sed 's/\.des3//g')
			openssl des3 -d -salt -pass pass:$pass -in $each -out $filename
		fi
	done
fi
