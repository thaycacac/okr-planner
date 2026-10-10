"""Print the argon2 hash to put in ``APP_PASSWORD_HASH``.

Usage: ``python -m app.hash_password`` (prompts twice), or pipe the password on stdin.
"""

import getpass
import sys

from app.api.security import hash_password


def read_password() -> str:
    if not sys.stdin.isatty():
        return sys.stdin.readline().rstrip("\r\n")
    password = getpass.getpass("Password: ")
    if getpass.getpass("Repeat password: ") != password:
        raise SystemExit("Passwords do not match")
    return password


def main() -> None:
    password = read_password()
    if not password:
        raise SystemExit("Password must not be empty")
    print(hash_password(password))


if __name__ == "__main__":
    main()
