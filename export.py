import csv

FIELDS = [
    'region',
    'username',
    'password',
    'email',
    'creation_date',
    'dob',
    'ip_address',
    'country',
    'city'
]


def export_account(account, output_path):
    with open(output_path, 'a', newline='') as fp:
        writer = csv.writer(fp, delimiter=':')
        writer.writerow([account.get(f) for f in FIELDS])
