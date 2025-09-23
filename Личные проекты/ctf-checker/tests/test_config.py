from ctfchecker.config import load_config

def test_load_config():
    cfg = load_config('examples/config.yaml')
    assert len(cfg.challenges) >= 2
    assert cfg.global_timeout > 0
