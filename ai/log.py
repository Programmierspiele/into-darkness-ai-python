from time import gmtime, strftime


def log(msg):
    print("[" + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + "] " + msg)