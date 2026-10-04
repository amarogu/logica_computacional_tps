# /// script
# dependencies = ["anywidget", "marimo"]
# requires-python = ">=3.14"
# ///

import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    # https://claude.ai/code/session_01UKPx4PhmMbk1saWW2Rvzkk
    import anywidget, traitlets

    class Clickable(anywidget.AnyWidget):
        _esm = """
        function render({ model, el }) {
          el.innerHTML = model.get("html");
          el.style.cursor = "pointer";
          el.style.display = "inline";
          el.onclick = () => { model.set("clicks", model.get("clicks") + 1); model.save_changes(); };
        }
        export default { render };
        """
        html = traitlets.Unicode("").tag(sync=True)
        clicks = traitlets.Int(0).tag(sync=True)

    w = mo.ui.anywidget(Clickable(html="<b style=\"display: inline\">clique aqui</b>"))
    return (w,)


@app.cell(hide_code=True)
def _(mo, w):
    mo.md(f"""
    # Horário escolar ⏱️

    Para gerar um horário com base nos dados
    em <code>./dados/</code>, {w}.
    <div style="width: 100%; height: 1px; background-color: #ccc" />
    """)
    return


@app.cell
def _():
    from pathlib import Path
    import csv

    # https://claude.ai/code/session_01F7LZyQp7Dv7GgNpcerp6aS
    def get_data(from_folder):
        data = {}
        for file in Path(from_folder).rglob('*.csv'):
            with file.open(encoding='utf-8', newline='') as f:
                data[file.stem] = list(csv.DictReader(f))
        return data

    return (get_data,)


@app.function
# https://claude.ai/code/session_011oP4T7nB5aq5sgZ9XxvDvf
def assert_data(from_folder, data):
    expected = {'disciplinas', 'disponibilidade_excecoes', 'salas', 'turmas'}
    unknown = sorted(data.keys() - expected)
    if unknown:
        raise ValueError(
            f"Ficheiros CSV não reconhecidos em {from_folder}: {', '.join(unknown)}. "
            f"Esperados: {', '.join(sorted(expected))}."
        )

    missing = sorted(expected - data.keys())
    if missing:
        raise ValueError(
            f"Ficheiros CSV em falta: {missing}"
        )


@app.cell
def _(Timetable, get_data, mo):
    from ortools.sat.python import cp_model

    def generate_timetable(from_folder='./dados/'):
        data = get_data(from_folder)
        try:
            assert_data(from_folder, data=data)
        except ValueError as e:
            mo.output.replace(mo.callout(str(e), kind="danger"))
        timetable = Timetable([])
        mo.output.append(mo.md(f"""
            <code>generate_timetable(from_folder='./dados/')</code> <br />
            A função inicia com o carregamento dos dados de 📁 <code>from_folder</code>,
            em seguida os ficheiros são validados por <code>assert_data</code> e um modelo é
            inicializado.
        """))
        model = cp_model.CpModel()
        variables = []
        for grade in data['turmas']:
            slot = model.new_int_var(0, 4, f'slot_{grade['turma']}')
            day = model.new_int_var(0, 5, f'day_{grade['turma']}')
            variables.append((slot, day, grade['turma']))
        model.add_all_different([day * 5 + slot for slot, day, _ in variables])
        solver = cp_model.CpSolver()
        status = solver.solve(model)
        print(solver.value(variables[0][1]), solver.value(variables[1][1]))

    return (generate_timetable,)


@app.cell(hide_code=True)
def _(generate_timetable, w):
    if w.value["clicks"] > 0:
        generate_timetable()
    return


@app.cell
def _():
    class Lecture:
        def __init__(self, subject, classroom, grade, slot, day):
            self.subject = subject
            self.classroom = classroom
            self.grade = grade
            self.slot = slot
            self.day = day

    class Timetable:
        def __init__(self, lectures):
            self.days = list(range(1, 6))
            self.lectures = lectures

    return (Timetable,)


@app.cell
def _():
    from collections import Counter


    return


if __name__ == "__main__":
    app.run()
