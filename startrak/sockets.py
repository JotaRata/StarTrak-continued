from codecs import StreamWriter
from io import StringIO
from startrak.sessionutils import __session__
import asyncio
from startrak.types.importers import TextImporter

_is_server = False

def connect(host : str = 'localhost', port : int = 8080):
	if _is_server:
		raise ConnectionResetError('Server used as client')
	client = SocketClient(host, port)
	asyncio.run(client.connect())

class SocketClient:
	def __init__(self, host : str = 'localhost', port : int = 8080) -> None:
		self.host = host
		self.port = port
		self.session_hash = hash(__session__)

	async def connect(self):
		reader, writer = await asyncio.open_connection(self.host, self.port)
		send_task = asyncio.create_task(self.write(writer))
		receive_task = asyncio.create_task(self.recieve(reader))
		await asyncio.gather(send_task, receive_task)

	async def write(self, writer : StreamWriter):
		while True:
			if self.session_hash != (newhash:=hash(__session__)):
				writer.write(__session__.__pprint__(0, 5).encode())
				self.session_hash = newhash
				await writer.drain()

	async def recieve(self, reader : asyncio.StreamReader):
		while True:
			_bytes = await reader.read()
			if not _bytes:
				continue
			
			# TODO: Replace with IO Stream importer
			imp = TextImporter()
			io_reader = StringIO(_bytes.decode())
			imp._file = io_reader
			obj = imp.read()