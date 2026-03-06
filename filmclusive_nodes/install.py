"""Install hook run by ComfyUI Manager when the Filmclusive pack is added."""

from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent
    print("[Filmclusive] install.py running from", root)


if __name__ == "__main__":
    main()
