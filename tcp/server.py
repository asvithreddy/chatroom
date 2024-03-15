import threading
import socket
import os
import ssl

server_cert = 'server.crt'  
server_key = 'server.key'   

host = '192.168.64.1'
port = 59001
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(certfile="server.crt", keyfile="server.key" )



clients = {}
aliases = {}

def broadcast(message, sender_alias):
    full_message = f'{sender_alias}: {message}'
    for client in clients.values():
        try:
            client.send(full_message.encode('utf-8'))
        except Exception as e:
            print(f"Error broadcasting message to {client}: {e}")

def handle_client(client, alias):
    while True:
        try:
            message = client.recv(1024)
            if not message:
                break
            sender_alias = aliases[client].decode('utf-8')
            if message.decode('utf-8').startswith('/sendfile'):
                file_path = message.decode('utf-8').split(' ')[1]
                send_file(client, file_path)
            elif message.decode('utf-8').startswith('/request_history'):
                send_chat_history(client)
            elif message.decode('utf-8').startswith('/search'):
                search_keyword = message.decode('utf-8').split(' ')[1]
                search_chat_history(client, search_keyword)
            elif message.decode('utf-8').startswith('/msg'):
                recipient_alias, private_message = message.decode('utf-8').split(' ', 2)[1:]
                send_private_message(sender_alias, recipient_alias, private_message)
            else:
                broadcast(message.decode('utf-8'), sender_alias)
                save_message(sender_alias + ">> " + message.decode('utf-8'))
        except Exception as e:
            print(f"Error handling client {client}: {e}")
            break

    client.close()
    aliases.pop(client)

def search_chat_history(client, keyword):
    try:
        with open("chat_history.txt", "r") as file:
            messages = file.readlines()
            result_messages = [message.strip() for message in messages if keyword in message]
            result = "\n".join(result_messages)
        client.send(result.encode('utf-8'))
    except FileNotFoundError:
        client.send("No chat history available.".encode('utf-8'))

def send_file(client, file_path):
    try:
        with open(file_path, 'rb') as file:
            file_data = file.read()
            file_name = os.path.basename(file_path)
            client.send(f'/file {file_name}'.encode('utf-8'))
            client.send(file_data)
    except FileNotFoundError:
        client.send('File not found.'.encode('utf-8'))

def accept_connections():
    while True:
        print('Server is running and listening ...')
        conn, client_address = server.accept()
        client_ssl_socket=context.wrap_socket(conn,server_side=True)
        print(f'Connection is established with {str(client_address)}')

        client_ssl_socket.send('Alias?'.encode('utf-8'))
        alias = client_ssl_socket.recv(1024)
        aliases[client_ssl_socket] = alias

        print(f'The alias of this client is {alias.decode("utf-8")}')
        
        
        clients[alias] = client_ssl_socket
        threading.Thread(target=handle_client, args=(client_ssl_socket, alias)).start()

def save_message(message):
    with open("chat_history.txt", "a") as file:
        file.write(message + "\n")

def send_chat_history(client):
    try:
        with open("chat_history.txt", "r") as file:
            history = file.read()
        client.send(history.encode('utf-8'))
    except FileNotFoundError:
        client.send("No chat history available.".encode('utf-8'))

def send_private_message(sender_alias, recipient_alias, private_message):
    recipient_socket = clients.get(recipient_alias)
    if recipient_socket:
        sender_socket = clients.get(sender_alias)
        sender_socket.send(f'Private message sent to {recipient_alias}: {private_message}'.encode('utf-8'))
        recipient_socket.send(f'Private message from {sender_alias}: {private_message}'.encode('utf-8'))
    else:
        sender_socket = clients.get(sender_alias)
        sender_socket.send(f'Error: User {recipient_alias} not found.'.encode('utf-8'))



if __name__ == "__main__":
    accept_connections()
