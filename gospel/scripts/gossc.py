# -*- coding: utf-8 -*-

import io
import operator
import os
import sys
import signal
import subprocess

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
    parser = argparse.ArgumentParser(prog='gossc',
                                     description='high-level screen manager')
    subparsers = parser.add_subparsers(title='action', dest='action')

    # create the parser for the "init" command
    parser_init = subparsers.add_parser('init',
                                        help='init screen')
    parser_init.add_argument('screen_name',
                             help='screen name')
    parser_init.add_argument('--lines',
                             dest='lines',
                             type=int,
                             default=10000,
                             help='output buffer lines')

    # create the parser for the "exec" command
    parser_exec = subparsers.add_parser('exec',
                                        help='execute commands in screen')
    parser_exec.add_argument('screen_name',
                             help='screen name')
    parser_exec.add_argument('script_name',
                             nargs='?',
                             default=None,
                             help='script name')

    # create the parser for the "plist" command
    parser_plist = subparsers.add_parser('plist',
                                         help='list all processes in screen')
    parser_plist.add_argument('screen_name',
                              help='screen name')

    # create the parser for the "plist" command
    parser_pkill = subparsers.add_parser('pkill',
                                         help='kill all processes in screen')
    parser_pkill.add_argument('screen_name',
                              help='screen name')
    parser_pkill.add_argument('--force',
                              dest='force',
                              action='store_true',
                              default=False,
                              help='force kill')

    return parser.parse_args(sys.argv[1:])


def _find_screens(screen_name):
    command = ['screen', '-ls', screen_name]
    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    output, unused_err = process.communicate()
    unused_retcode = process.poll()  # `screen -ls` always return 1

    screens = []
    screen_suffix = "." + screen_name
    for raw_line in io.BytesIO(output):
        if not raw_line.startswith("\t"):
            continue
        screen_sockname = raw_line.strip().partition("\t")[0]
        if screen_sockname.endswith(screen_suffix):
            screen_pid = int(screen_sockname.partition(".")[0])
            screens.append(screen_pid)
    return screens


def init_screen(namespace):
    screen_name = namespace.screen_name
    screens = _find_screens(screen_name)

    if not screens:
        _log_info("create screen [{screen_name}]", screen_name=screen_name)
        command = ['screen',
                   '-h', str(namespace.lines),
                   '-dmS', screen_name]
    else:
        _log_info("logout screen [{screen_name}]", screen_name=screen_name)
        command = ['screen',
                   '-D', '-r', str(screens[0]),
                   '-p', '0', '-X', 'stuff', '\n']
    subprocess.call(command)


def exec_jobs(namespace):
    screen_name = namespace.screen_name
    script_name = namespace.script_name

    screens = _find_screens(screen_name)
    if not screens:
        _log_error("screen not exists [{screen_name}]",
                   screen_name=screen_name)
        return

    if script_name is not None:
        try:
            stream = open(script_name, 'r')
        except IOError:
            _log_error("script not exists [{script_name}]",
                       script_name=script_name)
            return
    else:
        stream = sys.stdin

    screen_pid = screens[0]
    script_buf = io.BytesIO()
    script_buf.write('\n')  # add an additional '\n' ahead of the script
    for line in stream:
        script_buf.write(line.rstrip('\r\n'))
        script_buf.write('\n')
    script_buf.seek(0)

    command = ['screen', '-d', str(screen_pid)]
    subprocess.call(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    command = ['screen', '-D', '-r', str(screen_pid),
               '-p', '0', '-X', 'stuff', script_buf.read()]
    subprocess.call(command)


def _get_processes_in_screen(screen_pid):
    if psutil is None:
        _log_error("No module named 'psutil'")
        return
    screen_proc = psutil.Process(screen_pid)
    if hasattr(screen_proc, 'children'):
        # psutil >= 2.0
        get_name = operator.methodcaller('name')
        get_children = operator.methodcaller('children')
    else:
        get_name = operator.attrgetter('name')
        get_children = operator.methodcaller('get_children')
    for level3_proc in get_children(screen_proc):
        if get_name(level3_proc) == 'login':
            # pstree: screen -- login -- sh
            level2_proc_list = get_children(level3_proc)
        else:
            # pstree: screen -- sh
            level2_proc_list = [level3_proc]
        for level2_proc in level2_proc_list:
            for level1_proc in get_children(level2_proc):
                yield level1_proc.pid


def plist_jobs(namespace):
    screen_name = namespace.screen_name
    screens = _find_screens(screen_name)
    if not screens:
        _log_error("screen not exists [{screen_name}]",
                   screen_name=screen_name)
        return

    for child_pid in _get_processes_in_screen(screens[0]):
        _log_info("{child_pid}", child_pid=child_pid)


def pkill_jobs(namespace):
    screen_name = namespace.screen_name
    screens = _find_screens(screen_name)
    if not screens:
        _log_error("screen not exists [{screen_name}]",
                   screen_name=screen_name)
        return

    if namespace.force:
        sig = signal.SIGKILL
    else:
        sig = signal.SIGINT
    for child_pid in _get_processes_in_screen(screens[0]):
        os.kill(child_pid, sig)


def main():
    namespace = _parse_cli_arguments()
    {
        'init': init_screen,
        'exec': exec_jobs,
        'plist': plist_jobs,
        'pkill': pkill_jobs,
    }[namespace.action](namespace)


if __name__ == '__main__':
    main()