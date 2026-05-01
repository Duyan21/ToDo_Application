import csv

def read_tasks_from_csv(file_path):
    with open(file_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header

        for row in reader:
            yield row