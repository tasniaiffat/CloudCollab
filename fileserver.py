import socket
import threading
import os
import tqdm
import time

HOST = 'localhost'
PORT = 7071
SIZE = 1024
FORMAT = 'utf-8'
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST,PORT))

def file_download(conn):

    arr = []

    arr=os.listdir("./Server")
    # conn.send(str(len(arr)).encode(FORMAT))
    send_data = ""

    for ob in arr:
        ob=ob+"\n"
        send_data = send_data+ob
        # conn.send(ob.encode())
    conn.send(send_data.encode(FORMAT))

    filename = conn.recv(SIZE).decode()
    # print(filename)
    print(filename)
    
    if filename == "quit": 
        connected = False
        # break
    filename = "./Server/" + filename  

    filesize = os.path.getsize(filename)
    
    conn.send(str(filesize).encode())
    
    file=open(filename,"rb")
    data=file.read()
    file.close()
    
    data = data + b"<END>"
    # print(data)
    conn.sendall(data)
        
    # conn.close()

def file_upload(conn):
    
    selectedFile = conn.recv(1024).decode()
    print(selectedFile)
    # filesize = os.path.getsize(filename)
    file_size = conn.recv(1024).decode("utf-8")
    # print(file_size)
    name = "./Server/"+selectedFile
    print(name)
    file = open(name, "wb")

    progress = tqdm.tqdm(unit="B", unit_scale=True, unit_divisor=1000, total=float(file_size))
    data_bytes=b""
    while True:
        data = conn.recv(1024)
        if data_bytes[-5:]==b"<END>":
            break
        file.write(data)
        data_bytes += data
        progress.update(len(data))

    file.close()
    print("File received successfully.")
    # conn.close()


def handle_client(conn,address):
    print(f"[NEW CONNECTION] Connected to {address}")
    time.sleep(2)
    option = conn.recv(1024).decode()
    print(option)
    if option == "download":
        file_download(conn) 
    else :
        file_upload(conn)           
        
    conn.close()

def start():
    while True:
        server.listen()
        print(f"[LISTENING] Server is listening on {HOST}:{PORT}")    
        while True:
            client_conn, address = server.accept()
            thread = threading.Thread(target=handle_client, args=(client_conn, address))
            thread.start()
            print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

print("[STARTING] Server is starting...")
start()

    
    