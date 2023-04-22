import csv
import os

FIELDS = [
    'region',
    'username',
    'password',
    'email',
    'creation_date',
    'dob',
    'ip_address',
    'country',
    'city',
]


def export_account(account, output_path):
    exists = os.path.exists(output_path)
    with open(output_path, 'a', newline='') as fp:
        writer = csv.DictWriter(fp, fieldnames=FIELDS, delimiter=':')
        if not exists:
            writer.writeheader()
        writer.writerow({f: account.get(f) for f in FIELDS})
