import sys
import os

class TeeOutput:
    def __init__(self, file_path, mode='w'):
        self.file_path = file_path
        self.mode = mode
        self.file = None
        self.original_stdout = None
        self.original_stderr = None

    def __enter__(self):
        self.file = open(self.file_path, self.mode, buffering=1)
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self
        return self

    def write(self, data):
        if data:
            self.original_stdout.write(data)
            self.original_stdout.flush()
            self.file.write(data)
            self.file.flush()

    def flush(self):
        self.original_stdout.flush()
        self.file.flush()

    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        if self.file:
            self.file.close()