from src.abstract.file_reader import FileReader 

class FileReaderService:
    def __init__(self, provider: FileReader):
        self.provider = provider

    def readFile(self, file_path: str) -> str:
        return self.provider.readFile(file_path)