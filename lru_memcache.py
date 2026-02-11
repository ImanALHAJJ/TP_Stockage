from dataclasses import dataclass
from typing import Optional, Dict, List
from pymemcache.client.base import Client
from bench_utils import measure

@dataclass
class Node:
    key: str
    prev: Optional["Node"] = None
    next: Optional["Node"] = None
    

# Implémentation d’un LRU en mémoire, avec un wrapper pour memcache
class LRU:
    """head = plus récent, tail = moins récent"""
    def __init__(self, N: int, M: int):
        self.N = N
        self.M = M
        self.map: Dict[str, Node] = {}
        self.head: Optional[Node] = None
        self.tail: Optional[Node] = None

    def _remove(self, node: Node):
        if node.prev:
            node.prev.next = node.next
        else:
            self.head = node.next
        if node.next:
            node.next.prev = node.prev
        else:
            self.tail = node.prev
        node.prev = None
        node.next = None

    def _add_head(self, node: Node):
        node.prev = None
        node.next = self.head
        if self.head:
            self.head.prev = node
        self.head = node
        if self.tail is None:
            self.tail = node

    def create(self, key: str) -> List[str]:
        evicted: List[str] = []

        if key in self.map:
            self._remove(self.map[key])

        node = Node(key)
        self.map[key] = node
        self._add_head(node)

        # éviction si dépasse N (jusqu’à M éléments)
        while len(self.map) > self.N and len(evicted) < self.M:
            if self.tail is None:
                break
            k = self.tail.key
            self._remove(self.tail)
            del self.map[k]
            evicted.append(k)

        return evicted

    def read(self, key: str):
        if key not in self.map:
            return
        node = self.map[key]
        self._remove(node)
        self._add_head(node)

    def delete(self, key: str):
        if key in self.map:
            self._remove(self.map[key])
            del self.map[key]

    def order(self) -> List[str]:
        cur, res = self.head, []
        while cur:
            res.append(cur.key)
            cur = cur.next
        return res

# Wrapper pour memcache avec LRU en local
class Mem:

    def __init__(self, N: int, M: int, host="127.0.0.1", port=11211):
        self.client = Client((host, port))
        self.lru = LRU(N, M)

    def create(self, key: str, value: bytes) -> List[str]:
        evicted = self.lru.create(key)
        self.client.set(key, value)
        for k in evicted:
            self.client.delete(k)
        return evicted

    def read(self, key: str):
        v = self.client.get(key)
        if v is not None:
            self.lru.read(key)
        return v

    def delete(self, key: str):
        self.lru.delete(key)
        self.client.delete(key)

def main():
    mem = Mem(N=3, M=1)
    data = b"demo"
    # Set 5 clés, montrer les évictions et l’ordre LRU
    keys = ["A", "B", "C", "D", "E"]

    for k in keys:
        ev, t = measure("set", lambda kk=k: mem.create(kk, data))
        print(f"SET {k}: {t:.3f} ms | evicted={ev} | LRU={mem.lru.order()}")

    # Un read pour montrer remontée
    mem.read("C")
    print("After read(C):", mem.lru.order())

    # Un delete
    mem.delete("D")
    print("After delete(D):", mem.lru.order())

if __name__ == "__main__":
    main()
