import sys

# Ensure UTF-8 output streams even in piped/isolated environments (Windows CI, agent subshells)
for _s in ("stdout", "stderr", "stdin"):
    _stream = getattr(sys, _s, None)
    if _stream and hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

from harpy.cli import main

if __name__ == "__main__":
    sys.exit(main())
