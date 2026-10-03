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


@app.cell
def _(get_data):
    def generate_timetable(from_folder='./dados/'):
        data = get_data(from_folder)
        expected = {'disciplinas', 'disponibilidade_excecoes', 'salas', 'turmas'}
        unknown = sorted(data.keys() - expected)
        if unknown:
            raise ValueError(
                f"Ficheiros CSV não reconhecidos em {from_folder}: {', '.join(unknown)}. "
                f"Esperados: {', '.join(sorted(expected))}."
            )

    return (generate_timetable,)


@app.cell
def _(generate_timetable, w):
    if w.value["clicks"] > 0:
        generate_timetable()
    return


if __name__ == "__main__":
    app.run()
