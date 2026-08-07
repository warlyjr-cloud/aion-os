import argparse
import sys

from aiond.daemon import main as start_daemon


def main() -> None:
    parser = argparse.ArgumentParser(description="AION OS P2P Node CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    start_parser = subparsers.add_parser("start", help="Start the AION P2P Grid Node")
    start_parser.add_argument("--once", action="store_true", help="run one health cycle and exit")
    start_parser.add_argument(
        "--interval", type=float, default=5.0, help="heartbeat interval in seconds"
    )

    subparsers.add_parser("init", help="Initialize local node crypto keys")

    args = parser.parse_args()

    if args.command == "start":
        print("[*] Booting AION Daemon...")
        argv = ["--interval", str(args.interval)]
        if args.once:
            argv.append("--once")
        start_daemon(argv)
    elif args.command == "init":
        print("[*] Generating Node Keys... (Not implemented in this MVP)")
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
