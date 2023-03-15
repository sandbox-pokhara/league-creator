def get_user_agents():
    with open('user_agents.txt') as fp:
        return fp.read().splitlines()
