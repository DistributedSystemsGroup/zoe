def pytest_addoption(parser):
    parser.addoption("--test-environment", default="local", help="Test environment: 'local' or 'travis'")
