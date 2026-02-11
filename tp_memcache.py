import hashlib
from pymemcache.client.base import Client
from bench_utils import measure

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def read_file(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()

class Mem:
    def __init__(self, host="127.0.0.1", port=11211):
        self.client = Client((host, port))

    def create(self, key: str, value: bytes):
        self.client.set(key, value)

    def read(self, key: str):
        return self.client.get(key)

    def delete(self, key: str):
        self.client.delete(key)

def main():
    

    I = "image.png"
    nb_keys = 5
    mem = Mem()

    # Lire le disque une fois
    T, t_disk = measure("Read disk", lambda: read_file(I))
    print(f"Read disk: {t_disk:.3f} ms")

    h0 = sha256_bytes(T)
    set_times = []
    get_times = []
    corrupted = 0

    # Set 5 clés
    for i in range(1, nb_keys + 1):
        k = f"K_{i}"
        _, t_set = measure("Mem set", lambda kk=k: mem.create(kk, T))
        set_times.append(t_set)
        print(f"Mem set {k}: {t_set:.3f} ms")

    # Get 5 clés + check
    for i in range(1, nb_keys + 1):
        k = f"K_{i}"
        T2, t_get = measure("Mem get", lambda kk=k: mem.read(kk))
        get_times.append(t_get)

        ok = (T2 is not None and sha256_bytes(T2) == h0)
        if not ok:
            corrupted += 1
        print(f"Mem get {k}: {t_get:.3f} ms | ok={ok}")

    print(f"Non-corruption: {corrupted == 0} (corrupted={corrupted})")

    avg_set = sum(set_times) / len(set_times)
    avg_get = sum(get_times) / len(get_times)
    print(f"Avg mem set: {avg_set:.3f} ms")
    print(f"Avg mem get: {avg_get:.3f} ms")

    for i in range(1, nb_keys + 1):
        mem.delete(f"K_{i}")

if __name__ == "__main__":
    main()
