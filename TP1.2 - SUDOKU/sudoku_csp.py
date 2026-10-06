import random
from ortools.sat.python import cp_model

class box:
    def __init__(self, n, cells=None):
        self.n = n
        self.coords = cells if cells is not None else {}

    def checaLimites(self, i, j):
        if i < 0 or i >= self.n**2 or j < 0 or j >= self.n**2:
            raise ValueError(f"Coordenadas fora da grelha: ({i}, {j})")

    def add(self, i, j, val=None):
        self.checaLimites(i, j)
        if val is not None and not (1 <= val <= self.n**2):
            raise ValueError(f"Valor fora de [1, {self.n**2}]: {val}")
        self.coords[(i, j)] = val

    def matriz(self):
        
        grid = [[0 for _ in range(self.n**2)] for _ in range(self.n**2)]

        for i in range(self.n**2):
            for j in range(self.n**2):
                grid[i][j] = self.coords.get((i, j), 0)
            print(*grid[i])

class cube():
    def __init__(self, n, i, j): 
        self.n = n
        self.coords = {(i * n + a, j * n + b): None for a in range(n) for b in range(n)}

class path():

    def __init__(self, n, start, end):
        self.n = n
        a1, b1 = start
        a2, b2 = end
        if(a1 < 0 or a2 >= n**2 or b1 < 0 or b2 >= n**2):
            raise ValueError(f"Coordenadas inválidas: ({a1},{b1}), ({a2},{b2})")
        if(a1 > a2 or b1 > b2):
            self.coords = {(i,j) : None for i in range(a2, a1+1) for j in range(b2, b1+1)}
        else:
            self.coords = {(i,j) : None for i in range(a1, a2+1) for j in range(b1, b2+1)}

def diagonais(n):
    N = n**2
    return [path(n, (0, 0), (N - 1, N - 1)),      # principal
            path(n, (0, N - 1), (N - 1, 0))]      # secundária

def pistas_aleatorias(n, k=None):

    if k is not None and (k < 0 or k > n**4):
        raise ValueError(f"Valor de k inválido: {k}")
    
    N = n**2
    rng = random.Random()

    if k is not None:
        k = k
    else:
        k = n
    celulas = rng.sample([(i, j) for i in range(N) for j in range(N)], k)
    valores = rng.choices(range(1, N + 1), k=k)       
    return box(n, dict(zip(celulas, valores)))



class Modelo:

    def __init__(self, n):

        self.n = n
        self.N = n**2
        self.m = cp_model.CpModel()
               
        self.x = {                         
            (i, j): self.m.NewIntVar(1,self.N, f"x_{i}_{j}")
            for i in range(self.N) for j in range(self.N)
        } 

    def adicionar(self, *grupos):
        for grupo in grupos: 
            vars_do_grupo = [self.x[i, j] for (i, j) in grupo.coords.keys()] #retorna as variáveis de cada célula do grupo
            if isinstance(grupo, (path, cube)):
                self.m.AddAllDifferent(vars_do_grupo)  #impoe que todas as variáveis do grupo sejam diferentes para o solver
            for (i, j), val in grupo.coords.items():
                if val is not None:
                    self.m.Add(self.x[i, j] == val)  #Se nao é nula, diz ao solver que a variável não é livre, e sim fixa ao valor val

    def resolver(self):
        solver = cp_model.CpSolver()
        status = solver.Solve(self.m)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            return [[solver.Value(self.x[i, j]) for j in range(self.N)] for i in range(self.N)]
        else:
            return None