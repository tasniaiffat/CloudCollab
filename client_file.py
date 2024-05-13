import socket 
import tqdm
import os

BUFFER_SIZE = 4096 
host = 'localhost'
FORMAT = 'utf-8'
port = 7071

def file_download(client_socket):
    arr = []

    file_recv = client_socket.recv(1024).decode()
    arr.append(file_recv)
    print(f"{file_recv}")

    selected_file = input("Which file do you want to download? -> ") 
    client_socket.send(selected_file.encode(FORMAT))

    file_size = client_socket.recv(1024).decode()
    print(f"File size: {file_size} bytes")

    downloads_dir = "./Downloads/"
    # if not os.path.exists(downloads_dir):
    #     os.makedirs(downloads_dir)
        
    name = downloads_dir+selected_file
    file = open(name, "wb")

    progress = tqdm.tqdm(unit="B", unit_scale=True, unit_divisor=1000, total=float(file_size))
    data_bytes = b""
    while True:
        data = client_socket.recv(1024)
        if data_bytes[-5:] == b"<END>":
            break
        file.write(data)
        data_bytes += data
        progress.update(len(data))

    file.close()
    print("File received successfully.")
    client_socket.close()

def file_upload(client_socket):
    filename = input("Which file do you want to upload?")
    filesize = str(os.path.getsize(filename))
    print(filename)
    print(filesize)
    client_socket.send(filename.encode(FORMAT))
    client_socket.send(filesize.encode(FORMAT))

    file=open(filename,"rb")
    data=file.read()
    file.close()

    file = open(filename, "rb")
    data = file.read()
    file.close()
    data = data + b"<END>"
    client_socket.sendall(data)

    client_socket.close()

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

print(f"[+] Connecting to {host} : {port}")
client_socket.connect((host, port))
print("[+] Connected.")

option = input("Do you want to download or upload file?")
client_socket.send(option.encode(FORMAT))

if option == "download":
    file_download(client_socket)
else:
    file_upload(client_socket)
