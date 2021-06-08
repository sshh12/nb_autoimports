from functools import cmp_to_key
import glob
import json
import re
import os

from IPython.display import Javascript, display
from .common_index import COMMON_IMPORTS, COMMON_ALIASES

AUTO_IMPORT_LINE = "# autoimport"


class Options:
    QUIET = "quiet"
    IGNORE_PRIVATE = "ignoreprivate"
    RERUN = "rerun"


def build_index_from_import_name(import_name):
    # TODO: cache
    module = __import__(import_name)
    try:
        path = module.__path__[0]
    except AttributeError:
        path = os.path.dirname(module.__file__)
    index = {}
    for fn in glob.iglob(os.path.join(path, "**", "*.py"), recursive=True):
        with open(fn, "r", encoding="utf-8") as f:
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


def run_cells(cell_ids):
    js_code = """
        setTimeout(function() {{
            var nbb_cell_ids = {};
            var nbb_cells = Jupyter.notebook.get_cells();
            var run_cells = nbb_cell_ids.map(cell_id => {{
                var cell = nbb_cells.findIndex(nb_cell => nb_cell.input_prompt_number == cell_id);
                return cell;
            }});
            console.log(run_cells);
            Jupyter.notebook.execute_cells(run_cells);
        }}, 500);
    """.format(
        json.dumps(cell_ids)
    )
    display(Javascript(js_code))


def coalesce_import_lines(lines):
    # TODO: fancy merging
    lines = set(lines)
    lines_with_import = [line for line in lines if line.startswith("import ")]
    lines_without_import = [line for line in lines if line not in lines_with_import]
    return sorted(lines_with_import) + sorted(lines_without_import)


def parse_opts(cell_text):
    opts = cell_text.replace(AUTO_IMPORT_LINE, "").split(":", 1)[0]
    if opts == "":
        return []
    opts = [o.strip().lower().replace("_", "") for o in opts[1:-1].split(",")]
    return opts


class AutoImporter:
    def __init__(self, ip):
        self.ip = ip
        self.options = []
        # mappings from modules to top level func/class names
        self.indexes = COMMON_IMPORTS.copy()
        # mappings from names to what the import statement looks like
        # ... basically just a fallback if the import doesn't fit
        # the index format.
        self.aliases = COMMON_ALIASES.copy()

    def lookup_name(self, name):
        if name.startswith("_") and Options.IGNORE_PRIVATE in self.options:
            return None, None
        for index in self.indexes.values():
            if name in index:
                return index[name], "import"
        for aliases in self.aliases.values():
            if name in aliases:
                return aliases[name], "alias"
        return None, None

    def on_name_error(self, name, cell_id):
        import_text, mode = self.lookup_name(name)
        if import_text is None:
            if Options.QUIET not in self.options:
                print('[autoimport] Name "{}" was not found in index.'.format(name))
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
        if "(" not in import_text:
            # "(" means imports were edited...dont want to deal with that.
            lines[1:] = coalesce_import_lines(lines[1:])
        set_cell(imports_cell, "\n".join(lines), imports_cell_id)
        if Options.RERUN in self.options:
            run_cells([imports_cell_id, cell_id])

    def on_autoimport_cell(self, cell_text):
        self.options = parse_opts(cell_text)
        import_names = cell_text.split(":", 1)[1].split("\n")[0].split(",")
        import_names = [n.strip() for n in import_names if n != ""]
        for import_name in import_names:
            if import_name in self.indexes:
                continue
            self.indexes[import_name] = build_index_from_import_name(import_name)
        total_imports = sum(len(imps) for imps in self.indexes.values())
        if Options.QUIET not in self.options:
            print(
                "[autoimport] Loaded {} modules, {} aliases, {} imports. Using options {}.".format(
                    len(self.indexes), len(self.aliases), total_imports, self.options
                )
            )

    def on_post_run_cell(self, exec_result):
        cell_id = len(self.ip.user_ns["In"]) - 1
        cell_text = self.ip.user_ns["_i" + str(cell_id)]
        if cell_text.startswith(AUTO_IMPORT_LINE):
            return self.on_autoimport_cell(cell_text)
        err = exec_result.error_in_exec
        if err is None or type(err) != NameError:
            return
        name_match = re.search(r"name \'([^\']+)\' is not defined", str(err))
        if name_match is None:
            return
        name = name_match.group(1)
        if name not in cell_text:
            return
        return self.on_name_error(name, cell_id)