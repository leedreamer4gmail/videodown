"""videodown 入口：python -m videodown"""

from __future__ import annotations

from videodown.gui.app import run_app


def main() -> None:
    """CLI 入口。"""
    run_app()


if __name__ == "__main__":
    main()
