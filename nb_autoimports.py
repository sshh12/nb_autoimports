import glob
import json
import re
import os

from IPython.display import Javascript, display
from common_index import COMMON_IMPORTS, COMMON_ALIASES

AUTO_IMPORT_LINE = "# autoimport: "


def build_index_from_import_name(import_name):
    path = __import__(import_name).__path__[0]
    index = {}
    for fn in glob.iglob(os.path.join(path, "**", "*.py"), recursive=True):
        with open(fn, "r") as f:
            text = f.read()
        func_names = re.findall(r"[\n\r]def (\S+)\(", text)
        class_names = re.findall(r"[\n\r]class (\S+?)[\(:]", text)
        mod_path = import_name + "." + re.sub(r"[\\/]", ".", os.path.relpath(fn, path).replace(".py", ""))
        mod_path = mod_path.replace(".__init__", "")
        for func in func_names:
            index[func] = mod_path
        for func in class_names:
            index[func] = mod_path
        index[mod_path.split(".")[-1]] = ".".join(mod_path.split(".")[:-1])
    return index


def set_cell(original_cell, new_cell, cell_id):
    js_code = """
        setTimeout(function() {{
            var nbb_cell_id = {};
            var nbb_original_code = {};
            var nbb_new_code = {};
            var nbb_cells = Jupyter.notebook.get_cells();
            for (var i = 0; i < nbb_cells.length; ++i) {{
                if (nbb_cells[i].input_prompt_number == nbb_cell_id) {{
                    if (nbb_cells[i].get_text() == nbb_original_code) {{
                         nbb_cells[i].set_text(nbb_new_code);
                    }}
                    break;
                }}
            }}
        }}, 500);
    """.format(
        cell_id, json.dumps(original_cell), json.dumps(new_cell)
    )
    display(Javascript(js_code))


def coalesce_import_lines(lines):
    # TODO: fancy merging
    return sorted(set(lines))


class AutoImporter:
    def __init__(self, ip):
        self.ip = ip
        self.indexes = COMMON_IMPORTS.copy()
        self.aliases = COMMON_ALIASES.copy()

    def lookup_name(self, name):
        for index in self.indexes.values():
            if name in index:
                return index[name], "import"
        for aliases in self.aliases.values():
            if name in aliases:
                return aliases[name], "alias"
        return None

    def on_name_error(self, name):
        import_text, mode = self.lookup_name(name)
        if import_text is None:
            return
        cells = self.ip.user_ns["In"]
        imports_cell, imports_cell_id = None, -1
        for i, cell in enumerate(cells):
            if cell.startswith(AUTO_IMPORT_LINE):
                imports_cell = cell
                imports_cell_id = i
        if imports_cell is None:
            return
        lines = imports_cell.split("\n")
        if mode == "import":
            lines.append("from " + import_text + " import " + name)
        else:
            lines.append(import_text)
        lines[1:] = coalesce_import_lines(lines[1:])
        set_cell(imports_cell, "\n".join(lines), imports_cell_id)

    def on_autoimport_cell(self, cell_id, cell_text):
        import_names = cell_text.replace(AUTO_IMPORT_LINE, "").split("\n")[0].split(",")
        import_names = [n.strip() for n in import_names]
        for import_name in import_names:
            if import_name in self.indexes:
                continue
            self.indexes[import_name] = build_index_from_import_name(import_name)
        print(self.indexes)

    def on_post_run_cell(self, exec_result):
        cell_id = len(self.ip.user_ns["In"]) - 1
        cell_text = self.ip.user_ns["_i" + str(cell_id)]
        if cell_text.startswith(AUTO_IMPORT_LINE):
            return self.on_autoimport_cell(cell_id, cell_text)
        err = exec_result.error_in_exec
        if err is None or type(err) != NameError:
            return
        name_match = re.search(r"name \'([^\']+)\' is not defined", str(err))
        if name_match is None:
            return
        name = name_match.group(1)
        return self.on_name_error(name)


def load_ipython_extension(ip):
    ai = AutoImporter(ip)
    ip.events.register("post_run_cell", ai.on_post_run_cell)