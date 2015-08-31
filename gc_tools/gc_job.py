import os
import ast

class GCJobMeta(object):
    def __init__(self, workdir, job_id):
        self.job_id = int(job_id)
        self.workdir = workdir
        self.output_dir = os.path.join(workdir, "output", "job_%d" % self.job_id)
        self.environ = GCJobEnviron(self.gc_stdout)

    def _outdir_filename(self, basename):
        return os.path.join(self.output_dir, basename)

    @property
    def gc_stdout(self):
        return self._outdir_filename("gc.stdout")

    @property
    def gc_stderr(self):
        return self._outdir_filename("gc.stderr")

class GCJobEnviron(object):
    """
    Interface to the environment available in a job
    """
    def __init__(self, gc_stdout):
        self._gc_stdout = gc_stdout
        self._env_cache = {}

    def __getitem__(self, item):
        try:
            return self._env_cache[item]
        except KeyError:
            for line in open(self._gc_stdout):
                if not line.startswith("export"):
                    continue
                v_name, v_val = line[7:].split("=", 1)
                self._env_cache[v_name] = ast.literal_eval(v_val)
            return self._env_cache[item]

    def get(self, item, default=None):
        try:
            return self[item]
        except KeyError:
            return default
