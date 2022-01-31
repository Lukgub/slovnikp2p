import socket
import re
import sys


class Client:

    # Zpracovani konfiguracniho souboru

    def parsuj_config(self):
        config = []
        with open('config.ini', 'r') as file_reader:
            for line in file_reader:
                config.append(re.sub('[^0-9.\\-/]+', '', line))
        return config

    def start(self):
        buffer = 64
        config = self.parsuj_config()
        try:
            # Kontrola hodnot v konfiguracnim souboru
            assert re.fullmatch('([0-9]{1,3}\.){3}[0-9]{1,3}', config[0]) and \
                   re.fullmatch('([0-9]{1,3}\.){3}[0-9]{1,3}/[0-9]{1,2}', config[1]) and \
                   re.fullmatch('[0-9]{5}', config[2]) and re.fullmatch('[0-9]{5}-[0-9]{5}', config[3]) and \
                   int(config[3][:config[3].index('-')]) <= int(config[2]) <= int(config[3][config[3].index('-') + 1:])
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
                connection.connect((config[0], int(config[2])))
                with connection:
                    connected = True

                    while connected:

                        vstup = input()
                        if vstup == '':
                            vstup = 's'
                        elif vstup.__eq__('stop'):
                            connected = False
                        socket.timeout(3)
                        connection.send(bytes(vstup, 'utf-8'))
                        connection.recv(buffer).decode('utf-8')
        except:
            pass


client = Client()
client.start()
