from __future__ import annotations
from enum import IntEnum
from io import BytesIO, StringIO
import socket as sockets
import threading
import time
from startrak.internals.exceptions import InstantiationError
from startrak.sessionutils import set_session, get_session
from startrak.types.exporters import BytesExporter
from startrak.types.importers import BytesImporter

_CLIENT = None
_SERVER = None
__all__ = ['connect', 'start_server', 'socket_log', 'ServerFlags', 'ClientFlags']

class ServerFlags(IntEnum):
	ALLOW_RECIEVE = 		1 << 0
	ALLOW_BROADCAST =	1 << 1

class ClientFlags(IntEnum):
	ALLOW_READ =		1 << 0
	ALLOW_WRITE =		1 << 1

def connect(host : str = 'localhost', port : int = 8080, flags : ClientFlags = ClientFlags.ALLOW_READ | ClientFlags.ALLOW_WRITE,
				timeout : float = None, quiet = True):
	if _SERVER:
		raise ConnectionError('Server used as client')
	global _CLIENT

	client = SocketClient(host, port, flags, quiet= quiet, timeout= timeout)
	client.connect()
	_CLIENT = client

def start_server(host : str = 'localhost', port : int = 8080, flags : ServerFlags = ServerFlags.ALLOW_BROADCAST | ServerFlags.ALLOW_RECIEVE,
					quiet = True, block = False):
	if _CLIENT:
		raise ConnectionError('Client used as server')
	global _SERVER

	server = SocketServer(host, port, flags, quiet= quiet)
	server.start(block)
	_SERVER = server

def get_socket() -> SocketObject | None:
	if _CLIENT:
		return _CLIENT
	elif _SERVER:
		return _SERVER
	else:
		return None

def socket_log():
	socket = get_socket()
	if socket:
		print(socket.out.getvalue())


class SocketObject:
	host : str
	port : int
	flags : int
	out : StringIO
	session_hash : int
	socket : sockets.socket | None

	def __init__(self, host: str, port: int, flags : int, quiet : bool = True):
		if type(self) is SocketObject:
			raise InstantiationError(self)
		if not flags:
			raise ValueError('Invalid flags')
		self.host = host
		self.port = port
		self.flags = flags
		self.socket = None
		self.out = StringIO()

		self._quiet = quiet
		self.session_hash = self.get_hash()

	def get_hash(self):
		return hash(get_session())
	
	def print(self, message : str):
		self.out.write(message + '\n')
		if not self._quiet:
			print(message)
	

class SocketClient(SocketObject):
	def __init__(self, host: str, port: int, flags : int, quiet: bool = True, timeout: float = None):
		super().__init__(host, port, flags, quiet)
		self.timeout = timeout
		self.stop_event = threading.Event()

	def connect(self):
		if self.socket:
			raise ConnectionError('Client already connected')
		self.socket = sockets.create_connection((self.host, self.port), timeout=self.timeout)

		if self.flags & ClientFlags.ALLOW_READ:
			threading.Thread(target=self.receive_loop, daemon=True).start()
		if self.flags & ClientFlags.ALLOW_WRITE:
			threading.Thread(target=self.write_loop, daemon=True).start()
		print(f'Connected to {self.host}:{self.port}')

	def write_loop(self):
		time.sleep(0.05)
		while not self.stop_event.is_set():
			session_hash = self.get_hash()
			if self.session_hash == session_hash:
				continue
			self.print('Session is changed in client')
			try:
				with BytesExporter() as exp:
					exp.write(get_session())

				self.socket.sendall(exp.data() + b'\n')
				self.session_hash = session_hash
			except Exception as e:
				self.print(f'Error sending data: {e}')
			time.sleep(0.1)

	def receive_loop(self):
		while not self.stop_event.is_set():
			try:
				buffer = BytesIO()
				while True:
					data = self.socket.recv(1024)
					if data:
						buffer.write(data)
						if b'\n' not in data:
							continue

					buffer.seek(0)
					with BytesImporter(buffer.read().rstrip(b'\n')) as imp:
						obj = imp.read()
					set_session(obj)
					self.session_hash = self.get_hash()
					buffer.truncate(0)
					self.print('Session changed in the server')

			except OSError:
				raise
			except Exception as e:
				self.print(f'Error receiving data: {type(e).__name__}: {e}')
			time.sleep(0.1)

	def stop(self):
		self.stop_event.set()
		self.socket.close()

class SocketServer(SocketObject):
	clients : list[sockets.socket]
	def __init__(self, host: str, port: int, flags : int, quiet: bool = True):
		super().__init__(host, port, flags, quiet)
		self.clients = []

	def handle_client(self, client_socket : sockets.socket, address):
		self.clients.append(client_socket)
		self.print(f"Client connected: {address}")
		try:
			buffer = BytesIO()
			while True:
				data = client_socket.recv(1024)
				if data:
					buffer.write(data)
					if b'\n' not in data:
						continue

				buffer.seek(0)
				with BytesImporter(buffer.read().rstrip(b'\n')) as imp:
					obj = imp.read()
				set_session(obj)
				self.session_hash = self.get_hash()
				buffer.truncate(0)
				self.print('Session changed in one of the clients')

		except Exception as e:
			self.print(f"Error handling client: {type(e).__name__}: {e}")
		finally:
			self.clients.remove(client_socket)
			client_socket.close()
			self.print(f"Client disconnected: {address}")

	def broadcast(self):
		while True:
			session_hash = self.get_hash()
			for client_socket in self.clients:
				if self.session_hash == session_hash:
					continue
				
				try:
					with BytesExporter() as exp:
						exp.write(get_session())
					client_socket.sendall(exp.data() + b'\n')
					self.session_hash = session_hash
				
				except Exception as e:
					self.print(f"Error broadcasting data to client: {type(e).__name__}: {e}")
			time.sleep(1)

	def listen(self):
		self.socket = sockets.socket(sockets.AF_INET, sockets.SOCK_STREAM)
		self.socket.bind((self.host, self.port))
		self.socket.listen()
		print(f"Server listening on {self.host}:{self.port}")

		if self.flags & ServerFlags.ALLOW_BROADCAST:
			threading.Thread(target=self.broadcast).start()
		
		if self.flags & ServerFlags.ALLOW_RECIEVE:
			while True:
				client_socket, address = self.socket.accept()
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