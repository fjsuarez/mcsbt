import socket
import threading
import signal
import sys

class ChatClient(threading.Thread):
    def __init__(self, conn, address, server):
        super().__init__()
        self.conn = conn
        self.address = address
        self.server = server
        self.connection_alive = True
        self.name = None

    def run(self):
        self.name = self.conn.recv(1024).decode('utf-8')
        print(f"[SERVER] New client connected: {self.name} from {self.address}")
        self.server.broadcast(f"{self.name} has joined the chat.")
        self.conn.sendall(f"Welcome to the chat server, {self.name}!\n".encode('utf-8'))
        if not self.server.clients:
            self.conn.sendall("You are the first user in the chat.\n".encode('utf-8'))
        else:
            self.conn.sendall(f"Current chat members: {', '.join([client.name for client in self.server.clients])}\n".encode('utf-8'))
        self.server.clients.append(self)
        self.conn.settimeout(1)
        while self.connection_alive:
            try:
                message = self.conn.recv(1024).decode('utf-8')
                if message:
                    self.server.broadcast(message, self.name)
                else:
                    self.connection_alive = False
                    break
            except socket.timeout:
                # print(f"Checking if thread {self.name} running...")
                continue
            except Exception as e:
                if self.server.running:
                    print(f"\nError receiving message: {e}")
                self.connection_alive = False
                break
        if self.server.running:
            self.server.remove_client(self)
        # else:
            # print(f"Thread {self.name} execution ended.")


class ChatServer:
    def __init__(self, host, port):
        self.clients = []
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(5)
        self.running = True
        self.client_semaphore = threading.Semaphore(1)

    def signal_handler(self, sig, frame):
        print("\nClosing server...")
        self.running = False

    def start(self):
        signal.signal(signal.SIGINT, self.signal_handler)
        print(f"[SERVER] Server started on {self.server.getsockname()}")
        while self.running:
            try:
                self.server.settimeout(1)
                conn, address = self.server.accept()
                self.add_client(conn, address, self)
            except socket.timeout:
                # print(f"{self.running} Checking if running... active users: {threading.active_count() - 1}")
                continue
        self.cleanup()

    def add_client(self, client, address, server):
        new_client = ChatClient(client, address, server)
        new_client.start()
        print(f"[SERVER] Current active threads: {threading.active_count() - 1}")
    
    def remove_client(self, client):
        self.client_semaphore.acquire()
        if client in self.clients:
            # print(f'[SERVER] Removing client {client.name} from {client.address}...')
            client.connection_alive = False
            try:
                client.conn.sendall("Server closing connection...\n".encode('utf-8'))
            except Exception as e:
                print(f"Exception when sending close message: {e}")
            try:
                client.conn.close()
            except Exception as e:
                print(f"Exception when closing connection: {e}")
            try:
                self.clients.remove(client)
            except Exception as e:
                print(f"Exception when removing client: {e}. Probably already removed.")
            self.broadcast(f"{client.name} has left the chat.")
            print(f'[SERVER] Client {client.name} {client.address} disconnected.')
            del client
        else:
            print(f'[SERVER] Client {client.address} already removed.')
        self.client_semaphore.release()
    
    def broadcast(self, message, sender="[SERVER]"):
        for client in self.clients:
            if sender != client.name:
                try:
                    client.conn.sendall(f"{sender}: {message}\n".encode('utf-8'))
                except Exception as e:
                    print(f"Error sending message to {client.name}: {e}")
                    self.remove_client(client)

    def cleanup(self):
        for client in self.clients:
            client.connection_alive = False
            client.join()
        for client in self.clients[:]:
            self.remove_client(client)
        self.server.close()
        print('[SERVER] Server closed.')
        sys.exit(0)

if __name__ == '__main__':
    HOST = '127.0.0.1'
    PORT = 65432
    server = ChatServer(HOST, PORT)
    server.start()