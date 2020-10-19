import multiprocessing as mp

import bitcoin
import time
import sys
import os

from humanfriendly import format_timespan
from counter import Counter

event = mp.Event()
search = '1'
processors = 1
case_sensitivity = True

counter = Counter()
counter.__init__()


def check_cpu_count(cpu_count: int):
    if cpu_count > os.cpu_count():
        return os.cpu_count()

    return int(cpu_count)


def check_sys_arg():
    if '-l' in sys.argv:
        global case_sensitivity
        case_sensitivity = False
    if len(sys.argv) <= 2:
        return ('1' + sys.argv[1]), 1
    elif len(sys.argv) >= 3:
        if sys.argv[2].isnumeric():
            return ('1' + sys.argv[1]), check_cpu_count(int(sys.argv[2]))
        return ('1' + sys.argv[1]), 1

    return '1', 1


def base58_check(addr):
    base58_chars = ['O', '0', 'l', 'I']

    for word in base58_chars:
        if word in addr:
            raise ValueError("Illegal address characters", base58_chars)

    for letter in addr:
        if not letter.isascii() or not letter.isalnum():
            raise ValueError("Illegal address characters", letter)


def random_secret():
    return bitcoin.random_key()


def bitcoin_address(secret_key):
    pub_key = bitcoin.privkey_to_pubkey(secret_key)
    return bitcoin.pubkey_to_address(pub_key), pub_key


def search_address():
    while True:
        if event.is_set():
            return

        secret = random_secret()
        address, pubkey = bitcoin_address(secret)
        counter.increment()
        hashing_power = counter.value / (time.time() - start)
        estimated_time = int((frequency - counter.value) / hashing_power)
        elapsed_time = time.time() - start

        if counter.value % (processors * 100) == 0:
            if estimated_time <= 0:
                print("\r", int((counter.value / frequency) * 100), "%", "| Tries to freq :",
                      (counter.value, frequency),
                      "| Hashing power: %.2f h/s" % hashing_power,
                      "| Elapsed time: %s" % format_timespan(elapsed_time),
                      end='\r', flush=True)
            else:
                print("\r", int((counter.value / frequency) * 100), "%", "| Tries to freq :",
                      (counter.value, frequency),
                      "| Hashing power: %.2f h/s" % hashing_power,
                      "| Average remaining time: %s" % format_timespan(estimated_time),
                      end='\r', flush=True)

        if case_sensitivity is True:
            if search_addr in address[0:len(search_addr)]:
                event.set()
                return secret, pubkey, address
        else:
            if search_addr.lower() in address[0:len(search_addr)].lower():
                event.set()
                return secret, pubkey, address


if __name__ == "__main__":

    start = time.time()
    search_addr, processors = check_sys_arg()
    base58_check(search_addr)
    if case_sensitivity is True:
        frequency = 58 ** (len(search_addr) - 1)
    else:
        frequency = 58 ** (len(search_addr) - 1) / 2

    pool = mp.Pool(processors)
    results = []

    print("Searching for %s" % search_addr)
    print("Using %d processors" % processors)

    for i in range(processors):
        result = pool.apply_async(search_address)
        results.append(result)
    pool.close()

    solution = []

    for i in results:
        if i.get() is not None:
            solution = i.get()

    pool.terminate()

    assert (bitcoin.is_privkey(solution[0]))
    assert (bitcoin.is_pubkey(solution[1]))
    assert (bitcoin.is_address(solution[2]))

    print("\nPrivate key in HEX :", bitcoin.encode_privkey(solution[0], 'hex'), os.linesep + "Public key in HEX :",
          bitcoin.encode_pubkey(solution[1], 'hex'),
          os.linesep + "Address :", solution[2])

    runtime = float(time.time() - start)
    hash_rate = counter.value / runtime
    print(os.linesep + "Elapsed Time: %.4fs" % runtime)
    print("Amount of tries : %d" % counter.value)
    print("Hash power :  %.4f h/s" % hash_rate)

    if "-d" in sys.argv:
        with open("address.txt", 'w') as address:
            address.write("Private key in HEX : " + bitcoin.encode_privkey(solution[0], 'hex') + os.linesep)
            address.write("Public key in HEX : " +
                          bitcoin.encode_pubkey(solution[1], 'hex') + os.linesep)
            address.write("Address : " + solution[2] + os.linesep)

        address.close()

        with open("metadata.txt", 'w') as meta_data:
            meta_data.write(
                "Used " + str(processors) + " out of " + str(os.cpu_count()) + " available processors" + os.linesep)
            meta_data.write("Elapsed time : " + str(format_timespan(runtime)) + os.linesep)
            meta_data.write("Hash power during mining was : %.4f h/s" % hash_rate + os.linesep)
        meta_data.close()
