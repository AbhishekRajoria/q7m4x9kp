from app.services.metrics import mae, rmse, mean_bias, compute_errors


def test_metrics_example():
    forecast = [100, 120]
    actual = [90, 130]
    errors = compute_errors(forecast, actual)
    assert errors == [10, -10]
    assert mae(errors) == 10.0
    assert rmse(errors) == 10.0
    assert mean_bias(errors) == 0.0
