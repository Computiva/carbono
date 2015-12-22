#!/bin/bash

#CARBONO INSTALLER                            

clear    
                                                                       
#update
sudo apt-get update

#Instalar dependencias

sudo apt-get install redis-server -y
sudo apt-get install python-pip -y
sudo apt-get install python-webkit -y
sudo pip install tornado redis 

#criar pastas e icons

sudo mkdir /opt/carbono/
sudo cp -R * /opt/carbono/
sudo cp carbono.desktop /usr/share/applications/
sudo chmod +x /usr/share/applications/carbono.desktop
sudo chmod +x /opt/carbono/*
clear

#generate certificate

cd /opt/carbono/
#sudo rm -R certificate/
sudo chmod +x gen_certificate.sh
sudo ./gen_certificate.sh
clear
python create_admin.py

clear
echo "A instalação foi concluída!"
echo "Esse diretório agora pode ser deletado"
echo "Acesse em: Aplicativos > Ferramentas de Sistema > Carbono"
sleep 3

