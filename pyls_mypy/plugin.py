import os
import re
import hashlib
from mypy import api as mypy_api
from pyls import hookimpl

line_pattern_re = re.compile(r"([^:]+):(?:(\d+):)?(?:(\d+):)? (\w+): (.*)")


def parse_line(line, path):
    result = line_pattern_re.match(line)
    if result:
        filename, lineno, offset, severity, msg = result.groups()
        filename = os.path.join(os.path.dirname(path), filename)
        if os.path.samefile(filename, path):
            lineno = max(int(lineno or 1), 1)
            offset = max(int(offset or 1), 1)
            errno = 2
            if severity == 'error':
                errno = 1
            return {
                'source': 'mypy',
                'range': {
                    'start': {'line': lineno - 1, 'character': offset - 1},
                    # There may be a better solution, but mypy does not provide end
                    'end': {'line': lineno - 1, 'character': offset}
                },
                'message': msg,
                'severity': errno
            }


@hookimpl
def pyls_lint(document):
    diagnostics = []

    sys_path = os.pathsep.join(document._extra_sys_path)
    cache_dir = os.path.expanduser('~/.mypy_cache/%s' % hashlib.md5(sys_path.encode('utf-8')).hexdigest())
    args = ('--incremental',
            '--show-column-numbers',
            '--follow-imports', 'skip',
            '--command', document.source,
            '--filename', document.path,
            '--sys-path', sys_path,
            '--cache-dir', cache_dir)
    report, errors, _ = mypy_api.run(args)

    for line in report.splitlines():
        diag = parse_line(line, document.path)
        if diag:
            diagnostics.append(diag)

    return diagnostics
