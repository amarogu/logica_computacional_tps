from z3 import *

def resolver_trabalho(n=16):

  # 1
  a, b, x, y, z = BitVecs('a b x y z', n)
  x_next, y_next, z_next = BitVecs('x_next y_next z_next', n)
  a_next, b_next = BitVecs('a_next b_next', n)

  loc, loc_next = Ints('loc loc_next')

  inputs = And(a_next == a, b_next == b)

  init = And(
      loc == 0,
      x == a,
      y == b,
      z == 0,
      a >= 0,
      b >= 0,
  )

  overflow_soma = Or(
      Not(BVAddNoOverflow(z, x, False))
  )
  overflow_shift = UGE(x, 1 << (n - 1))

  tr_0_1 = And(loc == 0, loc_next == 1, x_next == x, y_next == y, z_next == z)
  tr_loop_end = And(
      loc == 1, y == 0, loc_next == 2, x_next == x, y_next == y, z_next == z
  )
  tr_erro = And(
      loc == 1,
      y != 0,
      loc_next == 3,
      Or(
          And((y & 1) == 0, overflow_shift),
          And((y & 1) != 0, overflow_soma),
      )
  )
  tr_par = And(
      loc == 1,
      y != 0,
      (y & 1) == 0,
      Not(overflow_shift),
      loc_next == 1,
      x_next == x << 1,
      y_next == LShR(y, 1),
      z_next == z,
  )
  tr_impar = And(
      loc == 1,
      y != 0,
      (y & 1) != 0,
      Not(overflow_soma),
      loc_next == 1,
      x_next == x,
      y_next == y - 1,
      z_next == z + x,
  )

  transicao = And(
      Or(tr_0_1, tr_loop_end, tr_erro, tr_par, tr_impar), inputs
  )

  # Função auxiliar gerada por IA
  def k_inducao(nome, P, P_next, custom_init=init):

    s_base = Solver()
    s_base.add(custom_init)
    s_base.add(Not(P))
    res_base = s_base.check()

    s_ind = Solver()
    s_ind.add(P)
    s_ind.add(transicao)
    s_ind.add(Not(P_next))
    res_ind = s_ind.check()

    print(f'[{nome}]')
    print(
        '  - Caso Base:',
        'Válido (unsat)' if res_base == unsat else 'Falhou',
    )
    print(
        '  - Passo Indutivo:',
        'Válido (unsat)' if res_ind == unsat else 'Falhou',
    )
    if res_base == unsat and res_ind == unsat:
      print('  -> Resultado: PROVADO por k-indução!\n')
    else:
      print('  -> Resultado: Não provado diretamente.\n')

  inv = And(
    Implies(loc == 0, And(x == a, y == b, z == 0)),
    Implies(Or(loc == 1, loc == 2), x * y + z == a * b)
    )
  inv_next = And(
    Implies(loc_next == 0, And(x_next == a_next, y_next == b_next, z_next == 0)),
    Implies(Or(loc_next == 1, loc_next == 2), x_next * y_next + z_next == a_next * b_next)
    )
  k_inducao('Invariante (x*y + z == a*b)', inv, inv_next)

  limite =  2 ** (n // 2)
  init_seguro = And(init, a < limite, b < limite)
  limites_estado = And(
      ULE(y, b),
      ULE(z, a * b),
      ULE(x, a * (b + 1)),
      Implies(UGT(y, 0), ULE(x, a * b)),
      BVMulNoOverflow(x, y, False),
      BVAddNoOverflow(x * y, z, False),
  )
  limites_estado_next = And(
      ULE(y_next, b_next),
      ULE(z_next, a_next * b_next),
      ULE(x_next, a_next * (b_next + 1)),
      Implies(UGT(y_next, 0), ULE(x_next, a_next * b_next)),
      BVMulNoOverflow(x_next, y_next, False),
      BVAddNoOverflow(x_next * y_next, z_next, False),
  )
  seguranca = And(
      inv,
      loc != 3,
      ULE(a, limite - 1),
      ULE(b, limite - 1),
      limites_estado,
  )
  seguranca_next = And(
      inv_next,
      loc_next != 3,
      ULE(a_next, limite - 1),
      ULE(b_next, limite - 1),
      limites_estado_next,
  )
  k_inducao(
      'Segurança (Sem Overflow)',
      seguranca,
      seguranca_next,
      custom_init=init_seguro
  ) 

  # A medida de progresso e unsigned: y deve diminuir enquanto o laço
  # continua. A transição de erro não faz parte do laço normal.
  progresso = Or(ULT(y_next, y), y == 0)

  s_term = Solver()
  s_term.add(
      loc == 1,
      UGT(y, 0),
      transicao,
      loc_next != 3,
      Not(progresso),
  )
  res_term = s_term.check()

  print('[Terminação]')
  print(
      '  - Verificação de Progresso (y decresce ou zera):',
      'Válido (unsat)' if res_term == unsat else 'Falhou',
  )
  if res_term == unsat:
    print(
        '  -> Provado: O programa termina sempre\n'
    )


if __name__ == '__main__':
  resolver_trabalho(4)