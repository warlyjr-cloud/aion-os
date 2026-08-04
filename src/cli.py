import argparse
import sys
import logging
from aiond.daemon import start_daemon

def main():
    parser = argparse.ArgumentParser(description="AION OS P2P Node CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Start command
    start_parser = subparsers.add_parser("start", help="Start the AION P2P Grid Node")
    
    # Init command (Future configuration)
    init_parser = subparsers.add_parser("init", help="Initialize local node crypto keys")

    args = parser.parse_args()

    if args.command == "start":
        print("[*] Booting AION Daemon...")
        start_daemon()
    elif args.command == "init":
        print("[*] Generating Node Keys... (Not implemented in this MVP)")
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
