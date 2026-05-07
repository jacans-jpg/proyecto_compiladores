from abc import ABC, abstractmethod

class FileReader(ABC):
    @abstractmethod
    def readFile(self, file_path: str):
        pass