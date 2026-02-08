def test_requests_import_and_version():
    """Ensure `requests` can be imported and matches the pinned version."""
    import requests

    # Pin expected version to the one in `requirements.txt`
    assert requests.__version__ == "2.32.5", (
        f"Expected requests==2.32.5 but found {requests.__version__}"
    )
