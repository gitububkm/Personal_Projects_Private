def test_imports():
    import secaudit
    from secaudit.scanners import secrets, deps, configs
    assert callable(secrets.scan)
    assert callable(deps.scan)
    assert callable(configs.scan)
