"""Frozen/source entry point for the hybrid Prayer Music Guard UI.

Dispatches on argv so a single frozen executable can act as BOTH the
selector process and the WebView2 child process:

  --webview-child [--probe | --ready-file PATH]
        Run webview_main in-process (never spawn another EXE).

  (no --webview-child)
        Run the selector in launcher.main(), which picks the HTML
        frontend on Windows 10/11 + WebView2 or the Tkinter fallback.

main.py is never imported here; the selector reaches it only through
launcher's existing runpy path, exactly as before.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _base_dir() -> str:
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(HERE))
    return os.path.dirname(HERE)


def main() -> int:
    base = _base_dir()
    for path in (base, HERE):
        if path and path not in sys.path:
            sys.path.insert(0, path)

    args = sys.argv[1:]
    if "--webview-child" in args:
        import webview_main
        if "--probe" in args:
            return int(webview_main.probe())
        ready = None
        if "--ready-file" in args:
            idx = args.index("--ready-file")
            if idx + 1 < len(args):
                ready = args[idx + 1]
        return int(webview_main.run(ready))

    import launcher
    launcher.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())