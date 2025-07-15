import csv
import os
from typing import Dict, List


class CSVWriter:
    def __init__(self, filename: str, headers: List[str]):
        self.filename = filename
        self.headers = headers

    def write_headers(self):
        if not os.path.exists(self.filename):
            with open(self.filename, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=self.headers)
                writer.writeheader()

    def append_data(self, data: Dict[str, str]):
        with open(self.filename, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=self.headers)
            writer.writerow(data)
