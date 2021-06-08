from .auto_import import AutoImporter


def load_ipython_extension(ip):
    # TODO: unload function
    ai = AutoImporter(ip)
    ip.events.register("post_run_cell", ai.on_post_run_cell)