import marimo

__generated_with = "0.25.2"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    # Índice dos chats com LLM; a transcrição de cada um está nesta pasta (chat_<n>_*.md). Nas células,
    # "# Gerado por LLM: chat (n)" marca o que esse chat gerou e "# Chat associado (n)" o que foi apenas discutido nele.
    mo.md(r"""
    🔗 **Chats com LLM** (transcrições nesta pasta)

    1. [Discussão do enunciado: visão geral do problema](https://github.com/amarogu/logica_computacional_tps/blob/main/TP2.2%20-%20CVP/chat_1_cvp_notebook_exercise_goal.md)
    2. [Geração da interface: figura, parâmetros e resultado](https://github.com/amarogu/logica_computacional_tps/blob/main/TP2.2%20-%20CVP/chat_2_vector_search_ui.md)
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    # Chat associado (1)
    mo.md(r"""
    # O "Closest Vector Problem" (CVP)

    Seja um conjunto específico de vetores linearmente independentes $G \equiv \set{g_1, g_2, \dots, g_k \mid g_i \in \reals^m}$; o reticulado determinado por $G$, $\mathcal{L}_G \equiv \set{x = z_1g_1, z_2g_2, \dots, z_kg_k  \mid z_i \in \Z}$. E finalmente um vetor aleatório $t$ (target), com cada um de seus componentes >= 0, qual é o vetor $x \in \mathcal{L}_G$ que está mais próximo de (closest to) $t$?
    """)
    return


@app.cell
def _():
    # Gerado por LLM: chat (2)
    import clarabel

    def solve_cvp(k, m, l):
        raise NotImplementedError("A função solve_cvp ainda não está implementada.")

    return (solve_cvp,)


@app.cell(hide_code=True)
def _(mo):
    # Gerado por LLM: chat (2)
    # Ilustração do problema: o reticulado gerado por g1 e g2, o alvo t e o vetor x mais próximo dele
    _g1, _g2 = (52, 12), (18, -36)
    _o, _t = (296, 112), (478, 52)
    _pontos = [
        (_o[0] + _a * _g1[0] + _b * _g2[0], _o[1] + _a * _g1[1] + _b * _g2[1])
        for _a in range(-8, 9)
        for _b in range(-6, 7)
    ]
    _x = min(_pontos, key=lambda _p: (_p[0] - _t[0]) ** 2 + (_p[1] - _t[1]) ** 2)
    _pontos_svg = "".join(f'<circle cx="{_p[0]}" cy="{_p[1]}" r="2.2"/>' for _p in _pontos)

    figura = mo.Html(f"""
    <svg viewBox="0 0 720 150" role="img"
         aria-label="Reticulado gerado por g1 e g2: x é o ponto do reticulado mais próximo do alvo t."
         style="display: block; width: 100%; height: auto; color: var(--foreground);
                mask-image: linear-gradient(90deg, transparent, #000 16%, #000 84%, transparent)">
      <defs>
        <marker id="cvp-seta" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto">
          <path d="M1 1 7 4 1 7" fill="none" stroke="context-stroke" stroke-width="1.3"/>
        </marker>
      </defs>
      <g fill="currentColor" opacity=".4">{_pontos_svg}</g>
      <g stroke="currentColor" stroke-width="1.2" opacity=".6" marker-end="url(#cvp-seta)">
        <line x1="{_o[0]}" y1="{_o[1]}" x2="{_o[0] + _g1[0]}" y2="{_o[1] + _g1[1]}"/>
        <line x1="{_o[0]}" y1="{_o[1]}" x2="{_o[0] + _g2[0]}" y2="{_o[1] + _g2[1]}"/>
      </g>
      <line x1="{_t[0]}" y1="{_t[1]}" x2="{_x[0]}" y2="{_x[1]}" stroke="currentColor" stroke-width="1.2" stroke-dasharray="3 3"/>
      <circle cx="{_t[0]}" cy="{_t[1]}" r="5" fill="var(--background)" stroke="currentColor" stroke-width="1.5"/>
      <circle cx="{_x[0]}" cy="{_x[1]}" r="6" fill="var(--action)" stroke="var(--action-foreground)" stroke-width="1.5"/>
      <g fill="currentColor" font-family="KaTeX_Math, serif" font-style="italic" font-size="16">
        <text x="{_t[0] - 18}" y="{_t[1] - 4}">t</text>
        <text x="{_x[0] + 12}" y="{_x[1] + 5}">x</text>
        <text x="{_o[0] + _g1[0] + 8}" y="{_o[1] + _g1[1] + 13}" opacity=".7">g<tspan dy="3" font-size="11" font-family="KaTeX_Main, serif" font-style="normal">1</tspan></text>
        <text x="{_o[0] + _g2[0] - 19}" y="{_o[1] + _g2[1] - 3}" opacity=".7">g<tspan dy="3" font-size="11" font-family="KaTeX_Main, serif" font-style="normal">2</tspan></text>
      </g>
    </svg>
    """)
    return (figura,)


@app.cell(hide_code=True)
def _(figura, mo):
    # Gerado por LLM: chat (2)
    def _validar(p):
        if None in p.values():
            return "Preenche todos os parâmetros: k, m e l."
        if p["k"] < 1 or p["m"] < 1 or p["k"] % 1 or p["m"] % 1:
            return "k e m têm de ser números inteiros positivos."
        if p["k"] > p["m"]:
            return "Reduz k ou aumenta m: em dimensão m não há mais de m vetores linearmente independentes."

    parametros = (
        mo.Html("""
        <div style="display: grid; gap: 1rem; align-items: end; grid-template-columns: repeat(auto-fit, minmax(11rem, 1fr))">
          {k} {m} {l}
        </div>
        """)
        .batch(
            k=mo.ui.number(start=1, step=1, value=3, label=r"$k$ · vetores em $G$", full_width=True),
            m=mo.ui.number(start=1, step=1, value=5, label=r"$m$ · dimensão de cada vetor", full_width=True),
            l=mo.ui.number(value=10, label=r"$l$", full_width=True),
        )
        .form(bordered=False, submit_button_label="Search for closest vector…", validate=_validar)
    )

    mo.vstack([figura, parametros], gap=0)
    return (parametros,)


@app.cell(hide_code=True)
def _(mo, parametros, solve_cvp):
    # Gerado por LLM: chat (2)
    from numbers import Number

    mo.stop(parametros.value is None)

    try:
        with mo.status.spinner(title="À procura do vetor mais próximo…"):
            _x = solve_cvp(**parametros.value)
    except (NotImplementedError, ValueError) as _erro:
        mo.stop(True, mo.callout(str(_erro), kind="danger"))
    mo.stop(_x is None, mo.callout("O solver não encontrou nenhum vetor.", kind="danger"))

    # Uma sequência de números é escrita como vetor (e parte de linha se for longa);
    # qualquer outro resultado é mostrado tal como vem
    if hasattr(_x, "__iter__") and all(isinstance(_c, Number) for _c in _x):
        _coordenadas = r",\allowbreak ".join(map(str, _x))
        _resposta = mo.md(f"$x = ({_coordenadas})$")
    else:
        _resposta = mo.as_html(_x)
    _dados = ", ".join(f"{_n} = {_v}" for _n, _v in parametros.value.items())

    mo.callout(mo.vstack([mo.md(f"**Vetor mais próximo** para ${_dados}$"), _resposta]), kind="success")
    return


if __name__ == "__main__":
    app.run()
