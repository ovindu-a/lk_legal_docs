from lld import DocFactory, ReadMe


def main():
    DocFactory.write_all()
    ReadMe().build()


if __name__ == "__main__":
    main()
