import os
import hashlib
from pathlib import Path
from bench_utils import measure

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

class FS:
    # root = répertoire racine, les fichiers sont des chemins relatifs à root
    def __init__(self, root_dir: str):
        self.root = Path(root_dir)
    
    # create le répertoire root s’il n’existe pas déjà
    def create(self):
        self.root.mkdir(parents=True, exist_ok=True)

    # list les fichiers (pas les sous-répertoires) du répertoire root
    def list(self):
        if not self.root.exists():
            return []
        return sorted(p.name for p in self.root.iterdir() if p.is_file())

    def _p(self, relpath: str) -> Path:
        return self.root / relpath
    
    # read un fichier relatif à root, write un fichier relatif à root, delete un fichier relatif à root
    def read(self, relpath: str) -> bytes:
        with open(self._p(relpath), "rb") as f:
            return f.read()
    
    # write un fichier relatif à root, créer les sous-répertoires si besoin
    def write(self, relpath: str, data: bytes):
        p = self._p(relpath)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "wb") as f:
            f.write(data)

    def delete(self, relpath: str):
        p = self._p(relpath)
        if p.exists():
            os.remove(p)

# lire un fichier du disque, écrire 5 copies dans R, relire les 5 copies, vérifier non-corruption, mesurer les temps
def read_file(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()

def main():
    fs = FS("R")
    fs.create()

    I = "image.png"
    nb_files = 5

    print("R before:", fs.list())

    #Lire la source une seule fois
    T, t_src = measure("Read source", lambda: read_file(I))
    print(f"Read source: {t_src:.3f} ms")

    #Ecrire 5 copies F_i + mesurer
    write_times = []
    for i in range(1, nb_files + 1):
        fname = f"F_{i}.png"
        _, t_w = measure("Write", lambda fn=fname: fs.write(fn, T))
        write_times.append(t_w)
        print(f"Write {fname}: {t_w:.3f} ms")

    # Relire les 5 copies + vérifier non-corruption + mesurer
    read_times = []
    corrupted = 0
    h0 = sha256_bytes(T)

    for i in range(1, nb_files + 1):
        fname = f"F_{i}.png"
        T2, t_r = measure("Read copy", lambda fn=fname: fs.read(fn))
        read_times.append(t_r)
        ok = (sha256_bytes(T2) == h0)
        if not ok:
            corrupted += 1
        print(f"Read {fname}: {t_r:.3f} ms | ok={ok}")

    print(f"Non-corruption: {corrupted == 0} (corrupted={corrupted})")
    print("R after:", fs.list())

    # afficher moyenne
    avg_w = sum(write_times) / len(write_times)
    avg_r = sum(read_times) / len(read_times)
    print(f"Avg write: {avg_w:.3f} ms")
    print(f"Avg read : {avg_r:.3f} ms")

if __name__ == "__main__":
    main()
