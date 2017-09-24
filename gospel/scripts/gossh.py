# -*- coding: utf-8 -*-

import operator
import os
import re
import sys
import signal

import argparse
try:
    import psutil
except ImportError:
    psutil = None


def _log_info(msg, **kwds):
    if kwds:
        msg = msg.format(**kwds)
    sys.stdout.write(msg)
    sys.stdout.write('\n')


def _log_error(msg, **kwds):
    if kwds:
        msg = msg.format(**kwds)
    sys.stderr.write(msg)
    sys.stderr.write('\n')


def _parse_cli_arguments():
    parser = argparse.ArgumentParser(prog='gossh',
                                     description='high-level shell manager')
    subparsers = parser.add_subparsers(title='action', dest='action')

    # create the parser for the "psck" command
    parser_psck = subparsers.add_parser('psck',
                                        help='check processes in shell')
    parser_psck.add_argument('patterns',
                             nargs='?',
                             default=None,
                             help='patterns of entry')

    # create the parser for the "pkill" command
    parser_pkill = subparsers.add_parser('pkill',
                                         help='kill all processes in shell')
    parser_pkill.add_argument('--force',
                              dest='force',
                              action='store_true',
                              default=False,
                              help='force kill')
    parser_pkill.add_argument('patterns',
                              nargs='?',
                              default=None,
                              help='patterns of entry')

    return parser.parse_args(sys.argv[1:])


def _compile_patterns(patterns):
    if patterns is None:
        stream = sys.stdin
    else:
        stream = patterns.splitlines()

    entries = []
    for line in stream:
        line = line.strip()
        if not line:
            continue
        patterns = []
        for regex in line.split('&&'):
            regex = regex.strip()
            if not regex:
                continue
            patterns.append(re.compile(regex))
        if patterns:
            entries.append((line, tuple(patterns)))
    return entries


def _get_processes(with_cmdline=False):
    if psutil is None:
        _log_error("No module named 'psutil'")
        return
    if psutil.version_info[0] >= 2:
        # psutil >= 2.0
        get_cmdline = operator.methodcaller('cmdline')
    else:
        get_cmdline = operator.attrgetter('cmdline')
    for level1_proc in psutil.process_iter():
        try:
            if with_cmdline:
                yield level1_proc.pid, get_cmdline(level1_proc)
            else:
                yield level1_proc.pid
        except psutil.NoSuchProcess:
            pass


def _filter_processes(entries):
    missing_cnt = 0
    matched_pids = []
    processes = dict(_get_processes(with_cmdline=True))
    for line, patterns in entries:
        matched_pid = None
        for child_pid, arguments in processes.items():
            if all(any(pattern.search(arg)
                       for arg in arguments)
                   for pattern in patterns):
                matched_pid = child_pid
                break
        if matched_pid is None:
            missing_cnt += 1
            _log_error('{pid}\t{entry}', pid='NIL', entry=line)
        else:
            matched_pids.append(matched_pid)
            processes.pop(matched_pid, None)
            _log_info('{pid}\t{entry}', pid=matched_pid, entry=line)
    return missing_cnt, matched_pids


def psck_jobs(namespace):
    entries = _compile_patterns(namespace.patterns)
    if not entries:
        return

    missing_cnt, _ = _filter_processes(entries)
    if missing_cnt == len(entries):
        exit(code=255)
    else:
        exit(code=missing_cnt)


def pkill_jobs(namespace):
    entries = _compile_patterns(namespace.patterns)
    if not entries:
        return

    if namespace.force:
        sig = signal.SIGKILL
    else:
        sig = signal.SIGINT
    _, matched_pids = _filter_processes(entries)
    for child_pid in matched_pids:
        os.kill(child_pid, sig)


def main():
    namespace = _parse_cli_arguments()
    {
        'psck': psck_jobs,
        'pkill': pkill_jobs,
    }[namespace.action](namespace)


if __name__ == '__main__':
    main()
