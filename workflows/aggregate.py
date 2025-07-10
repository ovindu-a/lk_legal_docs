from lld import AbstractDoc, ReadMe


def main():
    AbstractDoc.write_all()
    ReadMe().build()


if __name__ == "__main__":
    main()
