# Pour les tests pytests - on ajoute un paramètre --role
def pytest_addoption(parser):
    parser.addoption(
        "--role",
        action="store",
        default="client",
        choices=["client", "admin"]
    )