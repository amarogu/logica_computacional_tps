import random

class box:

    coords = {}
    n = 3

    def __init__(self, cells=None):
        self.coords = cells if cells is not None else {}

    def checaLimites(self, i, j): 
            if(i < 0 or i >= self.n**2 or j < 0 or j >= self.n**2):
                raise ValueError(f"Coordenadas fora da grelha: ({i}, {j})")
        
    def add(self, i, j, val=None): 
        if(self.checaLimites(i, j)):
            self.coords[(i, j)] = val

    def matriz(self):
        
        grid = [[0 for _ in range(self.n**2)] for _ in range(self.n**2)]

        for i in range(self.n**2):
            for j in range(self.n**2):
                grid[i][j] = self.coords.get((i, j), 0)
            print(*grid[i])

class cube(box):
    def __init__(self, n, i, j): 
        self.n = n
        self.coords = {(i * n + a, j * n + b): None for a in range(n) for b in range(n)}
        print(self.coords)

class path(box):

    coords = {}

    def __init__(self, n, inicio, fim): 
        if(inicio < 0 or fim >= n**2):
            raise ValueError(f"Coordenadas inválidas: inicio={inicio}, fim={fim}")
        if(inicio > fim):
            self.coords = {(i,j) : None for i in range(fim, inicio+1) for j in range(fim, inicio+1)}
        else:
            self.coords = {(i,j) : None for i in range(inicio, fim+1) for j in range(inicio, fim+1)}
        print(self.coords)


def pistas_aleatorias(n, k=None):
    coords = {}
    for _ in range(k if k is not None else n**2):
        i = random.randint(0, n**2 - 1)
        j = random.randint(0, n**2 - 1)
        val = random.randint(1, n**2)
        coords[(i, j)] = val
    print(coords)
    return box(coords)



class Modelo:
    def __init__(self, n): ...              # variáveis [1, n²]
    def adicionar(self, *grupos): ...       # AllDifferent + fixações
    def resolver(self): ...                 # grelha ou None