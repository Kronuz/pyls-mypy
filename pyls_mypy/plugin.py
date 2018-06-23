import os
import re
from mypy import api as mypy_api
from pyls import hookimpl

line_pattern_re = re.compile(r"([^:]+):(?:(\d+):)?(?:(\d+):)? (\w+): (.*)")


def parse_line(line):
    result = line_pattern_re.match(line)
    if result:
        _, lineno, offset, severity, msg = result.groups()
        lineno = int(lineno or 1)
        offset = int(offset or 0)
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
    args = ('--incremental',
            '--show-column-numbers',
            '--follow-imports', 'skip',
            '--command', document.source,
            '--filename', document.path,
            '--sys-path', os.pathsep.join(document._extra_sys_path),
            '--cache-dir', os.path.expanduser('~/.mypy_cache'))
    report, errors, _ = mypy_api.run(args)

    diagnostics = []
    for line in report.splitlines():
        diag = parse_line(line)
        if diag:
            diagnostics.append(diag)

    return diagnostics
