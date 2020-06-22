import multiprocessing as mp

import bitcoin
import time
import sys
import os
from humanfriendly import format_timespan

event = mp.Event()
search = '1'
processors = 1


class Counter(object):
    def __init__(self):
        self.val = mp.Value('i', 0)

    def increment(self, n=1):
        with self.val.get_lock():
            self.val.value += n

    @property
    def value(self):
        return self.val.value


counter = Counter()
counter.__init__()


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

        if estimated_time < 0:
            estimated_time = 0
        if counter.value % 100 == 0:
            print(int((counter.value / frequency) * 100), "%", "| Tries to freq :", (counter.value, frequency),
                  "| Hashing power: %.2f h/s" % hashing_power,
                  "| Average remaining time: ", format_timespan(estimated_time),
                  end='\r')

        if search_addr.lower() in address[0:len(search_addr)].lower():
            event.set()
            return secret, pubkey, address


if __name__ == "__main__":

    start = time.time()
    search_addr, processors = check_sys_arg()
    base58_check(search_addr)
    frequency = 58 ** (len(search_addr) - 1)
    pool = mp.Pool(processors)
    results = []

    print("Searching for", search_addr)
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

    end = time.time()
    runtime = float(end - start)
    print(os.linesep + "Elapsed Time: %.4fs" % runtime)
    print("Amount of tries : %d" % counter.value)
    print("Hash power :  %.4f h/s" % (counter.value / runtime))
