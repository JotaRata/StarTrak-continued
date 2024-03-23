from codecs import StreamWriter
from io import BytesIO, StringIO
import startrak
import asyncio

from startrak.types.importers import TextImporter

def connect(host : str = 'localhost', port : int = 8080):
	client = SocketClient(host, port)

	async def routine():
		await client.connect()
	asyncio.run(routine)

class SocketClient:
	def __init__(self, host : str = 'localhost', port : int = 8080) -> None:
		self.host = host
		self.port = port

	async def connect(self):
		reader, writer = await asyncio.open_connection(self.host, self.port)
		send_task = asyncio.create_task(self.send_update(writer))
		receive_task = asyncio.create_task(self.receive_updates(reader))
		await asyncio.gather(send_task, receive_task)

	async def send_update(self, writer : StreamWriter):
		while True:
			session = startrak.sessionutils.__session__
			writer.write(session.__pprint__(0, 5).encode())
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