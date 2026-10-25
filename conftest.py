def pytest_addoption(parser):
    # Déclare une option utilisable dans le terminal.
    parser.addoption(
        "--role",
        action="store",
        default="client",
        choices=["client", "admin"]
    )