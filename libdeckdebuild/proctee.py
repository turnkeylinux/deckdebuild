import io
import os
import shlex
import subprocess
import sys
from subprocess import PIPE
from threading import Lock, Thread
from typing import TextIO

EXPERIMENTAL_COLORS = os.getenv("EXPERIMENTAL_COLORS", False)
if EXPERIMENTAL_COLORS:
    try:
        import colorama
    except ImportError:
        EXPERIMENTAL_COLORS = False

if EXPERIMENTAL_COLORS:
    colorama.init(autoreset=True)


def _proctee(
    cmd: list[str],
    stdout_sinks: list[TextIO],
    stderr_sinks: list[TextIO],
    prefix: str | None = None,
    **kwargs,  # noqa: ANN003
) -> int:
    if prefix is None:
        prefix = ""
    elif prefix and EXPERIMENTAL_COLORS:
        prefix = colorama.Fore.CYAN + prefix + " => " + colorama.Fore.RESET
    else:
        prefix = prefix + " => "

    print("# {}".format(" ".join(map(shlex.quote, cmd))))

    proc = subprocess.Popen(
        cmd, stdout=PIPE, stderr=PIPE, bufsize=0, text=True, **kwargs
    )
    lock = Lock()

    def reader(io_in: io.StringIO, io_out: list[io.StringIO]) -> None:
        buff = ""
        while True:
            buff += io_in.read(1)
            with lock:
                if proc.poll() is not None and not buff:
                    break

            while "\n" in buff:
                line, buff = buff.split("\n", 1)
                with lock:
                    for io_obj in io_out:
                        if io_obj in (sys.stdout, sys.stderr):
                            io_obj.write(prefix + line + "\n")
                        else:
                            io_obj.write(line + "\n")
                        io_obj.flush()

    stdout_reader = Thread(target=reader, args=(proc.stdout, stdout_sinks))
    stderr_reader = Thread(target=reader, args=(proc.stderr, stderr_sinks))

    stdout_reader.start()
    stderr_reader.start()

    proc.wait()
    stdout_reader.join()
    stderr_reader.join()

    return proc.returncode


def proctee(
    cmd: list[str],
    stdout: io.StringIO | None,
    stderr: io.StringIO | None,
    check: bool = False,
    **kwargs,  # noqa: ANN003
) -> tuple[int, str, str]:
    if stdout is None:
        stdout = io.StringIO()
    if stderr is None:
        stderr = io.StringIO()

    code = _proctee(cmd, [stdout, sys.stdout], [stderr, sys.stderr], **kwargs)
    if code != 0 and check:
        raise subprocess.CalledProcessError(
            returncode=code,
            cmd=cmd,
            output=stdout.getvalue(),
            stderr=stderr.getvalue(),
        )
    return code, stdout.getvalue(), stderr.getvalue()


def proctee_joined(
    cmd: list[str],
    output: io.StringIO | None,
    check: bool = False,
    **kwargs,  # noqa: ANN003
) -> tuple[int, str]:
    if output is None:
        output = io.StringIO()

    code = _proctee(cmd, [output, sys.stdout], [output, sys.stderr], **kwargs)
    if code != 0 and check:
        raise subprocess.CalledProcessError(
            returncode=code, cmd=cmd, output=output.getvalue()
        )
    return code, output.getvalue()
