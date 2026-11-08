"""Pruebas unitarias del paquete fireca."""

from __future__ import annotations

import numpy as np
import pytest

from fireca.ca import DeterministicCA, MinimumTravelTime, StochasticCA
from fireca.fuels import (
    STANDARD_FUELS,
    base_rate_of_spread,
    directional_rates,
    fuel_property_maps,
)
from fireca.metrics import box_counting_dimension, length_breadth, perimeter, shape_metrics
from fireca.numerics import (
    bisection,
    cancellation_demo,
    convergence_table,
    euler_maruyama,
    false_position,
    game_of_life_step,
    machine_epsilon,
    msd_curve,
    newton_raphson,
    rule184_density_flow,
    rule184_step,
    secant,
)
from fireca.terrain import binary_forest, generate_terrain, ignition_mask


def test_machine_epsilon() -> None:
    assert machine_epsilon() == pytest.approx(np.finfo(float).eps, rel=1e-15)


def test_cancellation() -> None:
    naive, stable = cancellation_demo(1e-8)
    assert naive == 0.0
    assert stable == pytest.approx(0.5, rel=1e-10)


def test_rothermel_monotonic_moisture() -> None:
    model = STANDARD_FUELS["FM1"]
    rates = [
        float(base_rate_of_spread(model.load, model.sav, model.depth, m, model.mx))
        for m in (0.02, 0.04, 0.06, 0.08, 0.10)
    ]
    assert all(r > 0 for r in rates)
    assert all(rates[i] > rates[i + 1] for i in range(len(rates) - 1))


def test_rothermel_extinction() -> None:
    model = STANDARD_FUELS["FM1"]
    r = float(base_rate_of_spread(model.load, model.sav, model.depth, model.mx, model.mx))
    assert r == pytest.approx(0.0, abs=1e-12)


def test_directional_rates_increase_with_wind() -> None:
    model = STANDARD_FUELS["FM10"]
    shape = (8, 8)
    zeros = np.zeros(shape)
    prev = -1.0
    for wind in (0.0, 2.0, 4.0, 6.0):
        rates = directional_rates(
            load=np.full(shape, model.load),
            sav=np.full(shape, model.sav),
            depth=np.full(shape, model.depth),
            moisture=np.full(shape, 0.06),
            mx=np.full(shape, model.mx),
            wind_speed=wind,
            wind_direction=0.0,
            grad_x=zeros,
            grad_y=zeros,
            cell_size=5.0,
        )
        head = float(rates.rates[0, 0, 0])
        assert head > prev
        prev = head


def test_fuel_property_maps() -> None:
    fuel_type = np.array([[0, 1], [2, 3], [-1, 0]], dtype=np.int8)
    props = fuel_property_maps(fuel_type)
    assert props["load"].shape == fuel_type.shape
    assert props["valid"][-1, 0] == 0.0
    assert props["load"][-1, 0] == 0.0


def test_terrain_reproducible() -> None:
    a = generate_terrain(size=64, seed=7)
    b = generate_terrain(size=64, seed=7)
    assert np.allclose(a.elevation, b.elevation)
    assert np.array_equal(a.fuel_type, b.fuel_type)
    assert 0.0 <= a.summary()["burnable_fraction"] <= 1.0


def test_binary_forest_occupancy() -> None:
    t = binary_forest(64, 0.6, seed=1)
    assert 0.5 < np.mean(t.fuel_type >= 0) < 0.7


def test_ignition_mask() -> None:
    mask = ignition_mask((10, 10), "center", radius=1)
    assert mask.sum() == 9
    assert ignition_mask((10, 10), "left").sum() == 6


def test_deterministic_spreads() -> None:
    t = generate_terrain(size=96, seed=2, relief=0.0, moisture=0.05, wind_speed=4.0)
    t.fuel_type[:] = 3
    t.moisture[:] = 0.06
    t.load_factor[:] = 1.0
    t.grad_x[:] = 0.0
    t.grad_y[:] = 0.0
    model = DeterministicCA(t, dt=1.0)
    result = model.run(300.0, record_every=10)
    assert result.final_burned_area > 1
    assert result.head_distance[-1] > 0


def test_no_spread_above_extinction() -> None:
    t = generate_terrain(size=64, seed=3, relief=0.0, moisture=0.2, wind_speed=4.0)
    t.fuel_type[:] = 0  # FM1, mx = 0.12
    t.moisture[:] = 0.20
    t.load_factor[:] = 1.0
    t.grad_x[:] = 0.0
    t.grad_y[:] = 0.0
    model = DeterministicCA(t, dt=1.0)
    result = model.run(100.0)
    assert result.final_burned_area <= 9


def test_stochastic_reproducible() -> None:
    t = generate_terrain(size=64, seed=4, relief=0.0, moisture=0.05, wind_speed=4.0)
    t.fuel_type[:] = 3
    t.moisture[:] = 0.06
    t.load_factor[:] = 1.0
    t.grad_x[:] = 0.0
    t.grad_y[:] = 0.0
    r1 = StochasticCA(t, dt=1.0, seed=10).run(200.0)
    r2 = StochasticCA(t, dt=1.0, seed=10).run(200.0)
    assert r1.final_burned_area == r2.final_burned_area
    assert np.array_equal(r1.state, r2.state)


def test_mtt_solves() -> None:
    t = generate_terrain(size=64, seed=5, relief=0.0, moisture=0.05, wind_speed=4.0)
    t.fuel_type[:] = 3
    t.moisture[:] = 0.06
    t.load_factor[:] = 1.0
    t.grad_x[:] = 0.0
    t.grad_y[:] = 0.0
    mtt = MinimumTravelTime(t)
    assert np.isfinite(mtt.arrival).sum() > 10
    assert mtt.area_at(500.0) > 0


def test_perimeter_and_fractal() -> None:
    mask = np.zeros((20, 20), dtype=bool)
    mask[5:15, 5:15] = True
    assert perimeter(mask, 1.0) == pytest.approx(40.0)
    assert box_counting_dimension(mask) == pytest.approx(2.0, abs=0.05)
    metrics = shape_metrics(mask, 1.0)
    assert metrics.area_m2 == pytest.approx(100.0)


def test_length_breadth_rectangle() -> None:
    mask = np.zeros((40, 40), dtype=bool)
    mask[10:14, 5:35] = True
    assert length_breadth(mask) > 3.0


def test_root_finders() -> None:
    def f(x: float) -> float:
        return x**3 - 2.0 * x - 5.0

    def df(x: float) -> float:
        return 3.0 * x**2 - 2.0

    ref = 2.0945514815423265
    for result in (
        bisection(f, 1.0, 3.0),
        false_position(f, 1.0, 3.0),
        newton_raphson(f, df, 2.0),
        secant(f, 1.0, 3.0),
    ):
        assert result.converged
        assert result.root == pytest.approx(ref, rel=1e-9)


def test_convergence_orders() -> None:
    rows = convergence_table()
    for method, expected in (("euler", 1.0), ("rk2", 2.0), ("rk4", 4.0)):
        orders = [r["orden"] for r in rows if r["metodo"] == method and np.isfinite(r["orden"])]
        assert np.mean(orders) == pytest.approx(expected, abs=0.15)


def test_rule184_conserves_and_moves() -> None:
    road = np.array([1, 0, 1, 0, 0, 1, 0, 0], dtype=np.int8)
    new = rule184_step(road)
    assert new.sum() == road.sum()
    flow, density = rule184_density_flow(0.5, size=200, steps=100, seed=0)
    assert 0.2 < flow < 0.5
    assert 0.4 < density < 0.6


def test_game_of_life_blinker() -> None:
    grid = np.zeros((5, 5), dtype=np.int8)
    grid[2, 1:4] = 1
    new = game_of_life_step(grid)
    assert np.array_equal(
        new,
        np.array(
            [[0, 0, 0, 0, 0], [0, 0, 1, 0, 0], [0, 0, 1, 0, 0], [0, 0, 1, 0, 0], [0, 0, 0, 0, 0]],
            dtype=np.int8,
        ),
    )


def test_langevin_msd() -> None:
    times, paths = euler_maruyama(
        lambda t, x: np.array([0.0]),
        lambda t, x: np.array([1.0]),
        [0.0],
        5.0,
        0.01,
        n_paths=500,
        seed=0,
    )
    _, msd, slope = msd_curve(times, paths)
    assert slope == pytest.approx(1.0, abs=0.12)
    assert msd[-1] == pytest.approx(5.0, rel=0.25)


def test_deg2num() -> None:
    from fireca.dem import deg2num

    x, y = deg2num(0.0, 0.0, 1)
    assert x == pytest.approx(1.0)
    assert y == pytest.approx(1.0)


def test_real_cases_geometry() -> None:
    from fireca.real_cases import ACOS, LITTLE_GIANT, build_case_terrain, observed_mask

    for case in (ACOS, LITTLE_GIANT):
        terrain = build_case_terrain(case, size=64)
        assert terrain.shape == (64, 64)
        assert terrain.cell_size > 0
        mask = observed_mask(case, terrain.shape)
        assert mask.shape == (64, 64)
        assert mask.any()

    terrain = build_case_terrain(ACOS, size=64)
    mask = observed_mask(ACOS, terrain.shape)
    area_ha = mask.sum() * terrain.cell_size**2 / 1e4
    assert 200.0 < area_ha < 400.0


def test_real_case_short_run() -> None:
    from fireca.real_cases import ACOS, run_case

    terrain, result, observed, metrics = run_case(ACOS, size=48, dt=20.0, t_end=3600.0)
    assert result.final_burned_area >= 1
    assert np.isfinite(metrics["simulated_area_ha"])
    assert 0.0 <= metrics["area_error_rel"] < 100.0
