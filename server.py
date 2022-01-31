import threading
import re
import ipaddress
import subprocess
import platform
import socket
from concurrent.futures.thread import ThreadPoolExecutor


class Server:

    # Pingovani na adresy v subnetu

    def hledej_aplikace(self, host):
        if platform.system().lower() == 'windows':
            prikaz = '-n'
        else:
            prikaz = '-c'

        prikaz = ['ping', prikaz, '1', str(host)]
        return subprocess.call(prikaz) == 0

    # Zpracovani konfiguracniho souboru

    def parsuj_config(self):
        config = []
        with open('config.ini', 'r') as file_reader:
            for line in file_reader:
                config.append(re.sub('[^0-9.-/]+', '', line))
        subnet = config[1].split('/')
        return config

    # Metoda pro interakci s klientem

    def klient(self, connection):
        slovnik = {'team': 'tým', 'fortress': 'pevnost', 'two': 'dva', 'half': 'půlka', 'life': 'žívot'}
        connected = True
        vystup = ''
        config = self.parsuj_config()
        while connected:
            vstup = connection.recv(64).decode('UTF-8').strip()

            with open('log.txt', 'a') as log_writer:
                log_writer.write('->' + vstup)
                log_writer.write('\n')

            if not vstup or vstup.strip().isspace():
                break

            elif vstup == 'stop':
                connected = False

            elif re.fullmatch('TRANSLATELOC".+"', vstup):
                slovo = vstup[13:-1].lower()
                if slovnik.keys().__contains__(slovo):
                    vystup = f'TRANSLATESUC"{slovnik[slovo]}"'
                else:
                    vystup = f'TRANSLATEERR"{slovo} nelze prelozit."'

            elif re.fullmatch('TRANSLATEANY".+"', vstup):
                slovo = vstup[13:-1].lower()
                if slovnik.keys().__contains__(slovo):
                    vystup = f'TRANSLATESUC"{slovnik[slovo]}"'
                else:
                    adresy = list(ipaddress.ip_network(config[1]).hosts())
                    vysledky = {}

                    # Hledani vhodnych peeru pro komunikaci
                    with ThreadPoolExecutor(max_workers=254) as executor:
                        index = 0
                        for thread in executor.map(self.hledej_aplikace, adresy):
                            vysledky[adresy[index]] = thread
                            index += 1

                    # Pokus o navazani komunikace s ostatnimi peery
                    for adresa in adresy:
                        try:
                            if vysledky[adresa] is True:
                                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as rem_connection:
                                    rem_connection.settimeout(0.4)
                                    rem_connection.connect(("192.168.64.143", 65532))
                                    rem_connection.send(('TRANSLATELOC"' + slovo + '"').encode('UTF-8'))
                                    rem_connection.close()

                                    if re.fullmatch('TRANSLATESUC".+"', vystup):
                                        vystup = rem_connection.recv(64).decode('UTF-8')
                                    rem_connection.close()
                        except:
                            vystup = f'TRANSLATEERR"{slovo} nelze prelozit."'

            elif re.fullmatch('TRANSLATEREM".+"', vstup):
                slovo = vstup[13:-1].lower()

                adresy = list(ipaddress.ip_network(config[1]).hosts())
                vysledky = {}
                # Hledani vhodnych peeru pro komunikaci

                # with ThreadPoolExecutor(max_workers=254) as executor:
                #     index = 0
                #     for thread in executor.map(self.hledej_aplikace, adresy):
                #         vysledky[adresy[index]] = thread
                #         index += 1

                # Pokus o navazani komunikace s ostatnimi peery
                for adresa in adresy:
                    try:
                        if True: # vysledky[adresa] is True and not vysledky[config[0]]:
                            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as rem_connection:
                                rem_connection.settimeout(3)
                                rem_connection.connect((str(adresa), 65525))
                                rem_connection.send(('TRANSLATELOC"' + slovo + '"').encode())
                                vystup_rem = rem_connection.recv(1024).decode('UTF-8')
                                if re.fullmatch('TRANSLATESUC".+"', vystup_rem):
                                    vystup = vystup_rem
                        print(vysledky)
                    except:
                        pass
            else:
                vystup = 'TRANSLATEERR"Chyba s prekladem"'
            connection.send(vystup.encode('UTF-8'))
            with open('log.txt', 'a') as log_writer:
                log_writer.write('<-' + vystup)
                log_writer.write('\n')

    # Metoda se zavola pri startu aplikace v mainu a z ni se volaji ostatni tridy

    def start(self):
        config = self.parsuj_config()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((config[0], int(config[2])))

        while True:
            s.listen(5)
            connection, adresa = s.accept()
            t = threading.Thread(target=self.klient, args=(connection, ))
            t.start()


server = Server()
server.start()

