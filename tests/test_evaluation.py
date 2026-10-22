from scripts.evaluate import metrics

def test_ranking_metrics():
    assert metrics(["a","a","b"],["b","c"])==(0.5,0.5)
    assert metrics(["a"],["b"])==(0.0,0)
