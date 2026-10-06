"""English: Run the same CLI entry point as the installed factorytrace command.

中文：通过 python -m 调用与安装命令相同的入口；参数与退出码由 CLI 统一处理。
"""

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())
