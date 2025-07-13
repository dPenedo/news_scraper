import csv


class CSVWriter:
    def __init__(self, filename, headers):
        self.filename = filename
        self.headers = headers

    def write_headers(self):
        with open(self.filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=self.headers)
            writer.writeheader()

    def append_data(self, data):
        with open(self.filename, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=self.headers)
            writer.writerows(data)
