# Introduction 
Ce projet consiste en un "LoRaWAN Packet forwarder" mais sans passer par les process de rejoindre et identification mis en place par les passerelles par défaut. Donc, cette passerelle n'utilisera ni l'ABP, ni l'OTAA. Elle va justement filtrer les paquets selon des critères (par ex l'header et la taille du paquet). Les paquets admis seront envoyés en HTTPS vers le serveur via 4G (LTE ou LTE-M)

# Préparation
Une grande partie de la documentation est bien expliquée via le [Quick Start Guide de RAK7391](https://docs.rakwireless.com/Product-Categories/WisGate/RAK7391/Quickstart/)
## Raspberry CM4
Après avoir installé la carte sur l'appareil:
1. Mise de la passerelle en mode flash: Mettre un jumper sur la position __eMMC Flash__ (Jumper J39)
2. Connection au PC: Via le port USB C (Libellé Flash)
3. Alimentation: Via le port Ethernet PoE
4. Installation driver: Pour détecter la CM4, il faut installer ce [driver](https://www.raspberrypi.com/documentation/computers/compute-module.html#windows-installer)
5. Affichage de l'eMMC: Pour détecter l'eMMC en tant qu'appareil de stockage, il faut exécuter __RPiBoot.exe__ (typiquement installé dans **C:\Program Files (x86)\Raspberry Pi**)
6. RAK PiOS: A télécharger depuis [leur repo Github](https://github.com/RAKWireless/rakpios/releases) (.zip de la dernière version)
7. Raspberry Pi Imager: Un outil [à télécharger ici](https://www.raspberrypi.com/software/), utilisé pour installer l'image sur la Raspberry.
8. Après avoir téléchargé les deux fichers et après avoir installé l'Imager, suivre les instructions sur ce dernier pour installer l'image téléchargé sur le nouveau disque détecté à l'étape 5
9. A la fin de l'installation, il faut enlever l'alimentation, le jumper et le câble USB C.
10. Premier démarrage: Afin de voir la sortie du système, il faut connecter l'HDMI à un écran et mettre un clavier.
11. Log in: User: rak, Pass: changeme (Il faut faire attention car le layout au début est QWERTY). Vous serez amené à changer le mot de passe.
12. Changez les paramètres de clavier et localisation via la commande:
```shell
sudo raspi-config
```
13. Se connecter au WiFi: Soit via la même commande précédente (Rubrique System options > Wireless LAN), soit en utilisant la commande suivante:
```shell
sudo nmcli device wifi connect <SSID wifi> password <mot de passe>
```
Cette commande fait appel à NetworkManager qui est installé par défaut sur le distro **RAKPiOS**. Pour plus d'information, vérifiez [ce lien](https://developer-old.gnome.org/NetworkManager/stable/nmcli.html)

14. A ce stade là on peut passer de l'écran et du clavier et travailler en SSH, pour trouver l'IP de la raspberry, on peut lancer cette commande
```shell
ifconfig | grep "inet 192"
```
Si un OLED est installé, l'adresse sera affichée dessus.

## Concentrateur SX1303 (RAK 5146)
Au moment de la rédaction de ce document, les modules RAK 5146 (Version USB) ne sont pas détectés automatiquement. Pour tester, lancer cette commande après avoir installé le module dans le slot MiniPCIe N° 3 (Impérativement)
```shell
ls /dev | grep ttyACM
```
Si rien ne s'affiche, dévissez les deux vis et démontez le module. Il faut masquer le pin 13, à côté du pin marqué 15, avec un isolant comme montré dans la photo ci dessous:
![Pin masqué du RAK5146](./docs/RAK5146.jpg "Pin masqué avec un bout de ruban adhésif")

**Il faut couper un tout petit bout qui couvre seulmenet ce pin, en plus il faut que ça colle bien afin qu'il glisse pas en insérant le module dans le slot.**

## Module LTE BG96 (RAK8213)
Le module doit être installé dans dans le slot MiniPCIe N° 2 (Impérativement) car il fonctionne pas correctement dans le slot N° 1
Pour vérifier que le module est branché et détecté, il faut trouver au moins 4 **ttyUSB** en lançant cette commande:
```shell
ls /dev | grep ttyUSB
```
Les devs seronts utilisés comme suit:
- ttyUSB0 (qcdm)
- ttyUSB1 (gps)
- ttyUSB2 (at)
- ttyUSB3 (at)

S'ils sont pas détectés, il faut vérifier que l'USB est activé en allant dans le fichier **/boot/config.txt**, il faut que cette ligne soit présente/décommentée:
```
dtoverlay=dwc2,dr_mode=host
```
**En cas de modification, il faut redémarrer!**

Après avoir redémarré, et que le module est maintenant détecté, on passe à la configuration de la connection en utilisant encore NetworkManager et ModemManager.
Pour vérifier que le modem est bien détecté par ModemManager en lançant cette commande:
```shell
mmcli -L
```
Qui doit donner la liste des modems comme suit:
```
/org/freedesktop/ModemManager1/Modem/0 [Quectel] 0
```
Pour avoir les informations d'un modem, on lance cette commande
```shell
mmcli -m 0
```
Avec 0 l'indice du modem (Normalement il y aura qu'un seul donc 0)

Il faut maintenant programmer une interface GSM dans le système et la programmer pour se lancer automatiquement au démarrage, tout en lançant une seule commande:
```shell
nmcli connection add type gsm ifname '*' con-name <nom_connexion> apn <apn_operateur> connection.autoconnect yes gsm.pin <PIN>
```
Avec:
- <nom_connexion>: Un nom choisi, orange ou bouygues par exemple
- <apn_operateur>: L'APN comme défini par l'opérateur. Il faut noter que si c'est une carte M2M, l'APN M2M peut différer de celui utilisé pour le GSM normal.
- <PIN> PIN sur 4 chiffres. Si la carte n'a pas de PIN, il faut omettre le paramètre

Si un message de succès s'affiche, on peut vérifier que l'interface est créée avec cette commande:
```shell
ifconfig | grep wwan
```
Si aucune ligne ne s'affiche, ça peut être à cause d'un problème réseau, la connection peut toujours être lancé manuellement avec cette commande:
```shell
sudo nmcli con up <nom_connexion>
```
Pour voir les connexions paramétrées/actives, on peut lancer cette commande:
```shell
nmcli con show
```
Les connexions en vert représentent celles qui sont actives. On peut faire un redémarrage pour tester si la connexion GSM se lance automatiquement.

# Développement
## Bibliothèque HAL SX1302/1303
Le script python utilise [une bibliothèque partagée](sx1303/libloragw.so) compilé des fichiers sources de la bibliothèque HAL fournie par Semtech. La version présente dans ce projet est la v2.1.0. Si vous voulez utiliser la dernière version, il faut faire ces étapes:
1. lancer ces commandes le repo:
```shell
git clone https://github.com/Lora-net/sx1302_hal.git ~/projects/sx1302_hal
cd ~/projects/sx1302_hal
make all
```
2. Ouvrir le fichier Makefile dans [ce dossier](~/projects/sx1302_hal/libloragw/Makefile):
```shell
cd ~/projects/sx1302_hal/libloragw/
sudo nano Makefile
```
et remplacer le contenu par celui-ci:
```make
### get external defined data

LIBLORAGW_VERSION := `cat ../VERSION`
include library.cfg
include ../target.cfg

### constant symbols

ARCH ?=
CROSS_COMPILE ?=
CC := $(CROSS_COMPILE)gcc
AR := $(CROSS_COMPILE)ar

CFLAGS := -O2 -Wall -Wextra -fPIC -std=c99 -Iinc -I. -I../libtools/inc

OBJDIR = obj
INCLUDES = $(wildcard inc/*.h) $(wildcard ../libtools/inc/*.h)

### linking options

LIBS := -lloragw -ltinymt32 -lrt -lm

### general build targets

all: 	libloragw.a\
		libloragw.so\
		test_loragw_com \
		test_loragw_i2c \
		test_loragw_reg \
		test_loragw_hal_tx \
		test_loragw_hal_rx \
		test_loragw_cal_sx125x \
		test_loragw_capture_ram \
		test_loragw_com_sx1250 \
		test_loragw_com_sx1261 \
		test_loragw_counter \
		test_loragw_gps \
		test_loragw_toa \
		test_loragw_sx1261_rssi		

clean:
	rm -f libloragw.so
	rm -f libloragw.a
	rm -f test_loragw_*
	rm -f $(OBJDIR)/*.o
	rm -f inc/config.h

install:
ifneq ($(strip $(TARGET_IP)),)
 ifneq ($(strip $(TARGET_DIR)),)
  ifneq ($(strip $(TARGET_USR)),)
	@echo "---- Copying libloragw files to $(TARGET_IP):$(TARGET_DIR)"
	@ssh $(TARGET_USR)@$(TARGET_IP) "mkdir -p $(TARGET_DIR)"
	@scp test_loragw_* $(TARGET_USR)@$(TARGET_IP):$(TARGET_DIR)
	@scp ../tools/reset_lgw.sh $(TARGET_USR)@$(TARGET_IP):$(TARGET_DIR)
  else
	@echo "ERROR: TARGET_USR is not configured in target.cfg"
  endif
 else
	@echo "ERROR: TARGET_DIR is not configured in target.cfg"
 endif
else
	@echo "ERROR: TARGET_IP is not configured in target.cfg"
endif

### transpose library.cfg into a C header file : config.h

inc/config.h: ../VERSION library.cfg
	@echo "*** Checking libloragw library configuration ***"
	@rm -f $@
	#File initialization
	@echo "#ifndef _LORAGW_CONFIGURATION_H" >> $@
	@echo "#define _LORAGW_CONFIGURATION_H" >> $@
	# Release version
	@echo "Release version   : $(LIBLORAGW_VERSION)"
	@echo "	#define LIBLORAGW_VERSION	"\"$(LIBLORAGW_VERSION)\""" >> $@
	# Debug options
	@echo "	#define DEBUG_AUX		$(DEBUG_AUX)" >> $@
	@echo "	#define DEBUG_COM		$(DEBUG_COM)" >> $@
	@echo "	#define DEBUG_MCU		$(DEBUG_MCU)" >> $@
	@echo "	#define DEBUG_I2C		$(DEBUG_I2C)" >> $@
	@echo "	#define DEBUG_REG		$(DEBUG_REG)" >> $@
	@echo "	#define DEBUG_HAL		$(DEBUG_HAL)" >> $@
	@echo "	#define DEBUG_GPS		$(DEBUG_GPS)" >> $@
	@echo "	#define DEBUG_GPIO		$(DEBUG_GPIO)" >> $@
	@echo "	#define DEBUG_LBT		$(DEBUG_LBT)" >> $@
	@echo "	#define DEBUG_RAD		$(DEBUG_RAD)" >> $@
	@echo "	#define DEBUG_CAL		$(DEBUG_CAL)" >> $@
	@echo "	#define DEBUG_SX1302	$(DEBUG_SX1302)" >> $@
	@echo "	#define DEBUG_FTIME		$(DEBUG_FTIME)" >> $@
	# end of file
	@echo "#endif" >> $@
	@echo "*** Configuration seems ok ***"

### library module target

$(OBJDIR):
	mkdir -p $(OBJDIR)

$(OBJDIR)/%.o: src/%.c $(INCLUDES) inc/config.h | $(OBJDIR)
	$(CC) -c $(CFLAGS) $< -o $@

### static library
libloragw.so:libloragw.a\
			../libtools/libbase64.a\
			../libtools/libparson.a\
			../libtools/libtinymt32.a
			 $(CC) -shared -o $@ -Wl,--whole-archive $^ -Wl,--no-whole-archive

libloragw.a: $(OBJDIR)/loragw_spi.o \
			 $(OBJDIR)/loragw_usb.o \
			 $(OBJDIR)/loragw_com.o \
			 $(OBJDIR)/loragw_mcu.o \
			 $(OBJDIR)/loragw_i2c.o \
			 $(OBJDIR)/sx125x_spi.o \
			 $(OBJDIR)/sx125x_com.o \
			 $(OBJDIR)/sx1250_spi.o \
			 $(OBJDIR)/sx1250_usb.o \
			 $(OBJDIR)/sx1250_com.o \
			 $(OBJDIR)/sx1261_spi.o \
			 $(OBJDIR)/sx1261_usb.o \
			 $(OBJDIR)/sx1261_com.o \
			 $(OBJDIR)/loragw_aux.o \
			 $(OBJDIR)/loragw_reg.o \
			 $(OBJDIR)/loragw_sx1250.o \
			 $(OBJDIR)/loragw_sx1261.o \
			 $(OBJDIR)/loragw_sx125x.o \
			 $(OBJDIR)/loragw_sx1302.o \
			 $(OBJDIR)/loragw_cal.o \
			 $(OBJDIR)/loragw_debug.o \
			 $(OBJDIR)/loragw_hal.o \
			 $(OBJDIR)/loragw_lbt.o \
			 $(OBJDIR)/loragw_stts751.o \
			 $(OBJDIR)/loragw_gps.o \
			 $(OBJDIR)/loragw_sx1302_timestamp.o \
			 $(OBJDIR)/loragw_sx1302_rx.o \
			 $(OBJDIR)/loragw_ad5338r.o
	$(AR) rcs $@ $^

### test programs

test_loragw_com: tst/test_loragw_com.c libloragw.a
	$(CC) $(CFLAGS) -L. -L../libtools $< -o $@ $(LIBS)

test_loragw_i2c: tst/test_loragw_i2c.c libloragw.a
	$(CC) $(CFLAGS) -L. -L../libtools $< -o $@ $(LIBS)

test_loragw_reg: tst/test_loragw_reg.c libloragw.a
	$(CC) $(CFLAGS) -L. -L../libtools $< -o $@ $(LIBS)

test_loragw_hal_tx: tst/test_loragw_hal_tx.c libloragw.a
	$(CC) $(CFLAGS) -L. -L../libtools $< -o $@ $(LIBS)

test_loragw_hal_rx: tst/test_loragw_hal_rx.c libloragw.a
	$(CC) $(CFLAGS) -L. -L../libtools $< -o $@ $(LIBS)

test_loragw_capture_ram: tst/test_loragw_capture_ram.c libloragw.a
	$(CC) $(CFLAGS) -L. -L../libtools  $< -o $@ $(LIBS)

test_loragw_cal_sx125x: tst/test_loragw_cal_sx125x.c libloragw.a
	$(CC) $(CFLAGS) -L. -L../libtools  $< -o $@ $(LIBS)

test_loragw_com_sx1250: tst/test_loragw_com_sx1250.c libloragw.a
	$(CC) $(CFLAGS) -L. -L../libtools  $< -o $@ $(LIBS)

test_loragw_com_sx1261: tst/test_loragw_com_sx1261.c libloragw.a
	$(CC) $(CFLAGS) -L. -L../libtools  $< -o $@ $(LIBS)

test_loragw_counter: tst/test_loragw_counter.c libloragw.a
	$(CC) $(CFLAGS) -L. -L../libtools  $< -o $@ $(LIBS)

test_loragw_gps: tst/test_loragw_gps.c libloragw.a
	$(CC) $(CFLAGS) -L. -L../libtools  $< -o $@ $(LIBS)

test_loragw_toa: tst/test_loragw_toa.c libloragw.a
	$(CC) $(CFLAGS) -L. -L../libtools  $< -o $@ $(LIBS)

test_loragw_sx1261_rssi: tst/test_loragw_sx1261_rssi.c libloragw.a
	$(CC) $(CFLAGS) -L. -L../libtools  $< -o $@ $(LIBS)

### EOF
```
Puis, dans le même dossier:
```shell
make all
```
On obtient donc un nouveau fichier **libloragw.so**

3. Remplacer [l'ancien libloragw.so](sx1303/libloragw.so) par [le nouveau](~/projects/sx1302_hal/libloragw/libloragw.so) dans le dossier **sx1303** du projet.

Les méthodes de la classe SX1303 utilise plusieurs paramètres par défaut qui fonctionnent correctement dans notre cas, mais il faut penser à les mentionner explicitement ou à les changer pour l'adapter au futur usage.

## Packet forwarder
Pour recevoir correctement et l'envoyer au serveur il faut suivre cet exemple:
```python
from sx1303 import SX1303, RxPacket
from DecodedPayload import DecodedPayload
from requests import post

url = 'https://cff-lora.systel-sa.com/save/'

# Initialisation
gateway = SX1303()
gateway.configure_rx_rf_chains()
gateway.configure_rx_channels()

try:
	# Lancement
    gateway.start()

    while(True):
		# On reçoit un maximum de 10 packets
        nb_packets_received, packets_received = gateway.receive(10)
        if(nb_packets_received == 0):
            sleep(0.01)
        else:
            print(f"received {nb_packets_received} packets")
			# On balaye tous les packets
            for i in range(nb_packets_received):
                rx_packet: RxPacket = packets_received[i]
				# On vérifie si c'est nos packets (Longueur et header)
                if(rx_packet.size == 10 and rx_packet.payload[0]==0xE3):
					# On décode en objet
                    decoded_payload = DecodedPayload(rx_packet.payload)
                    json_data = decoded_payload.get_json()
					# On envoie vers l'URL
                    post(url=url, data=json_data)

except KeyboardInterrupt:
    gateway.stop()
```

