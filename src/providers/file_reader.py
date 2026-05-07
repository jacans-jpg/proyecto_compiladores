from src.abstract.file_reader import FileReader;

class FileReaderProvider(FileReader):
    def readFile(self, file_path: str):
        with open(file_path, 'r') as f:
            content = f.read();
            f.close()
            return content