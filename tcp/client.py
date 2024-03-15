
import threading
import socket
import ssl

alias = input('Choose an alias >>> ')
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_ip = '192.168.64.1'  # Replace with the server's IP address
server_port = 59001  # Replace with the server's port

context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
context.check_hostname = False
context.verify_mode = ssl.CERT_REQUIRED

ssl_client = context.wrap_socket(client, server_hostname=server_ip)

ssl_client.connect((server_ip, server_port))

def client_receive():
    while True:
        try:
            message = ssl_client.recv(1024).decode('utf-8')
            if message == "Alias?":
                ssl_client.send(alias.encode('utf-8'))
            elif message.startswith('/file'):
                file_name = message.split()[1]
                receive_file(file_name)
            else:
                print(message)
        except Exception as e:
            print('Error:', e)
            ssl_client.close()
            break

def receive_file(file_name):
    try:
        with open(file_name, 'wb') as file:
            while True:
                data = ssl_client.recv(1024)
                if not data:
                    break
                file.write(data)
        print(f'File {file_name} received successfully.')
    except Exception as e:
        print('Error receiving file:', e)

def client_send():
    while True:
        message = input("")
        if message.startswith('/sendfile'):
            send_file(message)
        elif message.startswith('/request_history'):
            request_history()
        elif message.startswith('/search'):
            search_keyword(message)
        else:
            ssl_client.send(message.encode('utf-8'))

def send_file(message):
    try:
        file_path = message.split()[1]
        with open(file_path, 'rb') as file:
            file_data = file.read()
        ssl_client.send(f'/sendfile {file_path}'.encode('utf-8'))
        ssl_client.send(file_data)
        print(f'File {file_path} sent successfully.')
    except FileNotFoundError:
        print('File not found.')
    except Exception as e:
        print('Error sending file:', e)

def request_history():
    ssl_client.send('/request_history'.encode('utf-8'))

def search_keyword(message):
    ssl_client.send(message.encode('utf-8'))

receive_thread = threading.Thread(target=client_receive)
receive_thread.start()

send_thread = threading.Thread(target=client_send)
send_thread.start()
