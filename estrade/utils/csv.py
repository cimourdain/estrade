import csv
import os

REPORT_FOLDER = 'reports'


class CSVWriter:
    @staticmethod
    def open_file(path, filename, report_folder=None):
        path = f'{report_folder or REPORT_FOLDER}/{path}'
        open_mode = 'a'
        if not os.path.exists(path):
            os.makedirs(path)

        file_path = f'{path}/{filename}'
        file_exists = True
        if not os.path.isfile(file_path):
            open_mode = 'w+'
            file_exists = False

        return file_exists, open(file_path, open_mode, newline='')

    @staticmethod
    def dict_to_csv(path, filename, dict_list, headers):
        file_exists, f = CSVWriter.open_file(path, filename)
        with f:
            writer = csv.DictWriter(f, fieldnames=headers)
            if not file_exists:
                writer.writeheader()
                for d in dict_list:
                    writer.writerow(d)
