import csv


def export_account(account, output_path):
    with open(output_path, 'a', newline='') as fp:
        writer = csv.writer(fp, delimiter=':')
        writer.writerow([account['username'], account['password']])
