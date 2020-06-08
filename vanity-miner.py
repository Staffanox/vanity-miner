import multiprocessing as mp

import bitcoin
import time
import sys
import os

event = mp.Event()
search = '1'
processors = 1


def check_cpu_count(cpu_count: int):
    if cpu_count > os.cpu_count():
        return 1

    return int(cpu_count)


def check_sys_arg():
    if len(sys.argv) == 2:
        return ('1' + sys.argv[1]), 1
    elif len(sys.argv) == 3:
        if sys.argv[2].isnumeric():
            return ('1' + sys.argv[1]), check_cpu_count(int(sys.argv[2]))
        return ('1' + sys.argv[1]), 1
    return '1', 1


def random_secret():
    return bitcoin.random_key()


def bitcoin_address(secret_key):
    pub_key = bitcoin.privkey_to_pubkey(secret_key)
    return bitcoin.pubkey_to_address(pub_key), pub_key


def search_address():
    while True:

        secret = random_secret()
        address, pubkey = bitcoin_address(secret)
        if search_addr in address[0:len(search_addr)]:
            event.set()
            return secret, pubkey, address


if __name__ == "__main__":

    search_addr, processors = check_sys_arg()
    pool = mp.Pool(processors)
    start = time.time()
    results = []

    print("Searching for", search_addr)
    print("Using %d processors" % processors)

    for i in range(processors):
        result = pool.apply_async(search_address)
        results.append(result)

    pool.close()
    event.wait()
    solution = results[0].get()
    pool.terminate()

    print("Private key in HEX :", bitcoin.encode_privkey(solution[0], 'hex'), os.linesep + "Public key in HEX :",
          bitcoin.encode_pubkey(solution[1], 'hex'),
          os.linesep + "Address :", solution[2])

    end = time.time()

    print("Elapsed Time: %.4fs" % float(end - start))
