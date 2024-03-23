from io import StringIO
import socket
import threading
import time
from startrak.sessionutils import set_session, get_session
import asyncio
from startrak.types.exporters import BytesExporter
from startrak.types.importers import JSONImporter, TextImporter

_is_server = False

def connect(host : str = 'localhost', port : int = 8080, timeout : float = None):
	if _is_server:
		raise ConnectionResetError('Server used as client')
	client = SocketClient(host, port, timeout)
	client.connect()

def start_server(host : str = 'localhost', port : int = 8080):
	global _is_server
	server = SocketServer(host, port)
	_is_server = True
	server.start()

class SocketClient:
	def __init__(self, host: str = 'localhost', port: int = 8080, timeout: float = None) -> None:
		self.host = host
		self.port = port
		self.timeout = timeout
		self.session_hash = hash(get_session())
		self.stop_event = threading.Event()

	def connect(self):
		try:
			self.socket = socket.create_connection((self.host, self.port), timeout=self.timeout)
			print(f'Connected to {self.host}:{self.port}')
			threading.Thread(target=self.write_loop, daemon=True).start()
			threading.Thread(target=self.receive_loop, daemon=True).start()
		except Exception as e:
			print(f'Error connecting to {self.host}:{self.port}: {e}')

	def write_loop(self):
		while not self.stop_event.is_set():
			if self.session_hash != (newhash := hash(get_session())):
				try:
					with BytesExporter() as exp:
						exp.write(get_session())

					self.socket.sendall(exp.data())
					self.session_hash = newhash
				except Exception as e:
					print(f'Error sending data: {e}')
			time.sleep(0.1)  # Adjust sleep time as needed

	def receive_loop(self):
		while not self.stop_event.is_set():
			try:
				data = self.socket.recv(1024)  # Adjust buffer size as needed
				if not data:
					continue
				try:
					with JSONImporter(data) as imp:
						obj = imp.read()
						set_session(obj)
						self.session_hash = hash(get_session())
				except:
					raise
			except Exception as e:
				raise
				print(f'Error receiving data: {e}')
			time.sleep(0.1)  # Adjust sleep time as needed

	def stop(self):
		self.stop_event.set()
		self.socket.close()

class SocketServer:
	def __init__(self, host='localhost', port=8080):
		self.host = host
		self.port = port
		self.clients = []
		self.server_socket = None
		self.server_thread = None

	def handle_client(self, client_socket, address):
		print(f"Client connected: {address}")
		self.clients.append(client_socket)
		try:
			while True:
				data = client_socket.recv(1024)
				if not data:
					break
				with JSONImporter(data) as imp:
					obj = imp.read()
					set_session(obj)
					print('Session changed in one of the clients')

		except Exception as e:
			print(f"Error handling client: {e}")
		finally:
			self.clients.remove(client_socket)
			client_socket.close()
			print(f"Client disconnected: {address}")

	def broadcast(self):
		while True:
			for client_socket in self.clients:
				try:
					with BytesExporter() as exp:
						exp.write(get_session())
					client_socket.sendall(exp.data())
				except Exception as e:
					print(f"Error broadcasting data to client: {e}")
			time.sleep(1)

	def listen(self):
		self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server_socket.bind((self.host, self.port))
		self.server_socket.listen()
		threading.Thread(target=self.broadcast).start()
		print(f"Server listening on {self.host}:{self.port}")
		while True:
			client_socket, address = self.server_socket.accept()
			# client_socket.settimeout(0)  # Set timeout here (5 seconds)
			client_thread = threading.Thread(target=self.handle_client, args=(client_socket, address))
			client_thread.start()

	def start(self, block : bool = False):
		if block:
			self.listen()
		else:
			self.server_thread = threading.Thread(target=self.listen)
			self.server_thread.start()

	def join_server_thread(self):
		self.server_thread.join()