import sys
import socket
import json
import logging
import xmltodict
import ssl
import os
import time
import datetime
import threading
import random
import concurrent.futures

server_address = ('172.16.16.101', 12000)
banyak_request = 100
banyakresp = 0
latensi = 0

def make_socket(destination_address='localhost',port=12000):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (destination_address, port)
        #logging.warning(f"connecting to {server_address}")
        sock.connect(server_address)
        return sock
    except Exception as ee:
        logging.warning(f"error {str(ee)}")

def make_secure_socket(destination_address='localhost',port=10000):
    try:
        #get it from https://curl.se/docs/caextract.html

        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.verify_mode=ssl.CERT_OPTIONAL
        context.load_verify_locations(os.getcwd() + '/domain.crt')

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (destination_address, port)
        logging.warning(f"connecting to {server_address}")
        sock.connect(server_address)
        secure_socket = context.wrap_socket(sock,server_hostname=destination_address)
        logging.warning(secure_socket.getpeercert())
        return secure_socket
    except Exception as ee:
        logging.warning(f"error {str(ee)}")

def deserialisasi(s):
    logging.warning(f"deserialisasi {s.strip()}")
    return json.loads(s)
    

def send_command(command_str,is_secure=False):
    alamat_server = server_address[0]
    port_server = server_address[1]
#    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# gunakan fungsi diatas
    if is_secure == True:
        sock = make_secure_socket(alamat_server,port_server)
    else:
        sock = make_socket(alamat_server,port_server)

    logging.warning(f"connecting to {server_address}")
    try:
        logging.warning(f"sending message ")
        sock.sendall(command_str.encode())
        # Look for the response, waiting until socket is done (no more data)
        data_received="" #empty string
        while True:
            #socket does not receive all data at once, data comes in part, need to be concatenated at the end of process
            data = sock.recv(16)
            if data:
                #data is not empty, concat with previous content
                data_received += data.decode()
                if "\r\n\r\n" in data_received:
                    break
            else:
                # no more data, stop the process by break
                break
        # at this point, data_received (string) will contain all data coming from the socket
        # to be able to use the data_received as a dict, need to load it using json.loads()
        hasil = deserialisasi(data_received)
        logging.warning("data received from server:")
        return hasil
    except Exception as ee:
        logging.warning(f"error during data receiving {str(ee)}")
        return False


def getdatapemain(nomor=0):
    cmd=f"{nomor}\r\n\r\n"
    hasil = send_command(cmd)
    return hasil

def ambildatapemain(index, mainres):
    time_request_start = time.perf_counter()

    result = getdatapemain(random.randint(1, 20))
    if (result):
        latency = time.perf_counter() - time_request_start
        print(result['nomor'], result['nama'], result['posisi'])
        mainres[index] = latency
    else:
        print('Ada kesalahan saat transfer')
        mainres[index] = -1

if __name__ == '__main__':
    worker = 1
    #worker = 5
    #worker = 10
    #worker = 20

    tugas = {}
    hasil = {}

    time_start = time.perf_counter()
    loop = banyak_request
    while loop > 0:
        loop_dalam =  worker if loop >= worker else loop

        for i in range(loop_dalam):
            tugas[i] = threading.Thread(target=ambildatapemain, args=(i, hasil))
            tugas[i].start()

        for i in range(loop_dalam):
            tugas[i].join()
            # print(hasil)
            if (hasil[i] != -1):
                banyakresp+= 1
                latensi += hasil[i]

        loop -= loop_dalam
    
    print(f'Dengan {worker} thread')
    print(f'Request: {banyak_request}')
    print(f'Response: {banyakresp}')
    print(f'Latency: {(latensi / banyakresp) * 1000:.3f} ms')
    print(f'Waktu Eksekusi: {(time.perf_counter() - time_start) * 1000:.3f} ms')
