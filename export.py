def export_account(account, output_path):
    with open(output_path, 'a') as fp:
        fp.write(f'{account["username"]}:{account["password"]}\n')
