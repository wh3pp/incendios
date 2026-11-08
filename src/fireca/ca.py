"""Autómatas celulares para la propagación de incendios forestales.

Se implementan tres variantes sobre la misma discretización espacial:

``DeterministicCA``
    Autómata celular sincrónico con acumulación de "exposición" térmica. Una
    celda se enciende cuando la exposición acumulada alcanza la unidad. Es el
    límite determinista del modelo probabilístico.

``StochasticCA``
    Autómata celular probabilístico. En cada paso, la probabilidad de
    ignición de una celda es ``1 - exp(-h)``, donde ``h`` es la exposición
    aportada por sus vecinos en ese paso. Reproducido con muchas semillas
    permite construir ensembles Monte Carlo.

``MinimumTravelTime``
    Solución determinista de tiempo mínimo de llegada (Dijkstra sobre el
    grafo de vecinos). Se usa como verificación independiente del autómata
    determinista y como aproximación de la envolvente de propagación.

Estados de celda
----------------
0 : combustible no quemado
1 : combustionando
2 : quemado
3 : incombustible
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

import numpy as np
from numpy.typing import NDArray
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

from .fuels import (
    MOORE_OFFSETS,
    VON_NEUMANN_OFFSETS,
    DirectionalRates,
    FuelModel,
    directional_rates,
    fuel_property_maps,
)
from .terrain import Terrain, ignition_mask

UNBURNED: Final[int] = 0
BURNING: Final[int] = 1
BURNED: Final[int] = 2
UNBURNABLE: Final[int] = 3


def _shift_to_target(arr: NDArray[np.float64], dr: int, dc: int) -> NDArray[np.float64]:
    """Desplaza ``arr`` de modo que el valor de la fuente llegue al vecino.

    Para un desplazamiento ``(dr, dc)``, el resultado en ``(i, j)`` es
    ``arr[i - dr, j - dc]``. Las celdas fuera del dominio valen cero.
    """
    out = np.zeros_like(arr)
    h, w = arr.shape
    src_r = slice(max(0, -dr), h - max(0, dr))
    src_c = slice(max(0, -dc), w - max(0, dc))
    dst_r = slice(max(0, dr), h - max(0, -dr))
    dst_c = slice(max(0, dc), w - max(0, -dc))
    out[dst_r, dst_c] = arr[src_r, src_c]
    return out


@dataclass
class SimulationResult:
    """Resultado de una simulación completa."""

    times: NDArray[np.float64]
    burned_area: NDArray[np.float64]
    active_cells: NDArray[np.int64]
    head_distance: NDArray[np.float64]
    arrival: NDArray[np.float64]
    state: NDArray[np.int8]
    burned_mask: NDArray[np.bool_]
    snapshots: dict[float, NDArray[np.int8]] = field(default_factory=dict)
    parameters: dict[str, float | str] = field(default_factory=dict)

    @property
    def final_burned_area(self) -> float:
        return float(self.burned_area[-1]) if self.burned_area.size else 0.0

    @property
    def final_burned_fraction(self) -> float:
        total = self.state.size
        return self.final_burned_area / total if total else 0.0


class FireCA:
    """Motor base del autómata celular de fuego."""

    def __init__(
        self,
        terrain: Terrain,
        ignition: NDArray[np.bool_] | None = None,
        dt: float = 1.0,
        max_rate: float = 2.5,
        fuel_models: dict[str, FuelModel] | None = None,
        wind_speed: float | None = None,
        wind_direction: float | None = None,
        cooling_time: float = 240.0,
        wind_efficiency: float = 0.30,
    ) -> None:
        if dt <= 0.0:
            raise ValueError("dt debe ser positivo")
        self.terrain = terrain
        self.dt = float(dt)
        self.max_rate = float(max_rate)
        self.fuel_models = fuel_models or terrain.fuel_models()
        self.wind_speed = terrain.wind_speed if wind_speed is None else float(wind_speed)
        self.wind_direction = (
            terrain.wind_direction if wind_direction is None else float(wind_direction)
        )
        self.cooling_time = float(cooling_time)
        self.wind_efficiency = float(wind_efficiency)

        self.props = fuel_property_maps(terrain.fuel_type, self.fuel_models)
        self.load = self.props["load"] * terrain.load_factor
        self.sav = self.props["sav"]
        self.depth = self.props["depth"]
        self.mx = self.props["mx"]
        self.residence = self.props["residence_time"]
        self.valid = self.props["valid"] > 0.0

        # La velocidad de propagación se evalúa una sola vez: el terreno, la
        # humedad y el viento son estáticos durante la simulación.
        self.rates: DirectionalRates = directional_rates(
            load=self.load,
            sav=self.sav,
            depth=self.depth,
            moisture=terrain.moisture,
            mx=self.mx,
            wind_speed=self.wind_speed,
            wind_direction=self.wind_direction,
            grad_x=terrain.grad_x,
            grad_y=terrain.grad_y,
            cell_size=terrain.cell_size,
            max_rate=self.max_rate,
            wind_efficiency=self.wind_efficiency,
            offsets=MOORE_OFFSETS,
        )

        shape = terrain.shape
        self.state = np.where(self.valid, UNBURNED, UNBURNABLE).astype(np.int8)
        self.arrival = np.full(shape, np.inf)
        self.hazard = np.zeros(shape)
        self.burn_age = np.zeros(shape)
        self.time = 0.0
        self._history_time: list[float] = []
        self._history_area: list[float] = []
        self._history_active: list[int] = []
        self._history_head: list[float] = []
        self._snapshots: dict[float, NDArray[np.int8]] = {}
        self._ignition = (
            ignition_mask(shape, "center") if ignition is None else np.asarray(ignition, bool)
        )
        self._ignition = self._ignition & self.valid
        self._head_origin = self._head_projection_origin()
        self.ignite(self._ignition)

    # ------------------------------------------------------------------
    # Inicialización y propiedades
    # ------------------------------------------------------------------
    def _head_projection_origin(self) -> float:
        rows, cols = np.nonzero(self._ignition)
        if rows.size == 0:
            return 0.0
        direction = np.array([np.cos(self.wind_direction), np.sin(self.wind_direction)])
        coords = np.column_stack([cols * self.terrain.cell_size, -rows * self.terrain.cell_size])
        return float(np.mean(coords @ direction))

    @property
    def burning(self) -> NDArray[np.bool_]:
        return self.state == BURNING

    @property
    def burned(self) -> NDArray[np.bool_]:
        return (self.state == BURNING) | (self.state == BURNED)

    @property
    def unburned(self) -> NDArray[np.bool_]:
        return self.state == UNBURNED

    def ignite(self, mask: NDArray[np.bool_]) -> int:
        """Enciende las celdas indicadas que sean combustibles y no quemadas."""
        target = mask & self.unburned & self.valid
        count = int(np.count_nonzero(target))
        if count:
            self.state[target] = BURNING
            self.arrival[target] = self.time
            self.burn_age[target] = 0.0
            self.hazard[target] = 0.0
        return count

    # ------------------------------------------------------------------
    # Dinámica
    # ------------------------------------------------------------------
    def _accumulate_hazard(self, burning: NDArray[np.bool_]) -> NDArray[np.float64]:
        hazard = np.zeros_like(self.hazard)
        for k, (dr, dc) in enumerate(MOORE_OFFSETS):
            contrib = self.rates.rates[k] * (self.dt / self.rates.distances[k])
            hazard += _shift_to_target(contrib * burning, dr, dc)
        return hazard

    def _age_and_burnout(self) -> None:
        burning = self.burning
        self.burn_age[burning] += self.dt
        burnout = burning & (self.burn_age >= self.residence)
        self.state[burnout] = BURNED
        self.burn_age[burnout] = 0.0

    def step(self) -> None:
        """Avanza un paso temporal."""
        burning = self.burning
        contribution = self._accumulate_hazard(burning)

        # Enfriamiento de la exposición acumulada de las celdas no quemadas.
        self.hazard *= np.exp(-self.dt / self.cooling_time)
        self.hazard += contribution
        self.hazard[~self.unburned] = 0.0

        self._age_and_burnout()
        self._ignite_from_hazard()
        self.time += self.dt

    def _ignite_from_hazard(self) -> None:
        raise NotImplementedError

    def run(
        self,
        t_end: float,
        snapshot_times: tuple[float, ...] = (),
        record_every: float = 0.0,
    ) -> SimulationResult:
        """Ejecuta la simulación hasta ``t_end`` [s]."""
        if t_end <= 0:
            raise ValueError("t_end debe ser positivo")
        snapshots = sorted(float(t) for t in snapshot_times)
        snap_idx = 0
        next_record = 0.0
        self._record()
        steps = int(np.ceil(t_end / self.dt))
        for _ in range(steps):
            self.step()
            while snap_idx < len(snapshots) and self.time >= snapshots[snap_idx] - 1e-9:
                self._snapshots[snapshots[snap_idx]] = self.state.copy()
                snap_idx += 1
            if record_every > 0.0 and self.time >= next_record - 1e-9:
                self._record()
                next_record += record_every
        # Garantiza que el último estado quede registrado.
        if not self._history_time or self._history_time[-1] < self.time - 1e-9:
            self._record()
        return SimulationResult(
            times=np.asarray(self._history_time),
            burned_area=np.asarray(self._history_area),
            active_cells=np.asarray(self._history_active),
            head_distance=np.asarray(self._history_head),
            arrival=self.arrival.copy(),
            state=self.state.copy(),
            burned_mask=self.burned.copy(),
            snapshots=self._snapshots,
            parameters={
                "dt": self.dt,
                "wind_speed": self.wind_speed,
                "wind_direction_deg": float(np.degrees(self.wind_direction) % 360.0),
                "cell_size": self.terrain.cell_size,
                "max_rate": self.max_rate,
                "model": self.__class__.__name__,
            },
        )

    def _record(self) -> None:
        burned = self.burned
        self._history_time.append(self.time)
        self._history_area.append(float(np.count_nonzero(burned)))
        self._history_active.append(int(np.count_nonzero(self.burning)))
        self._history_head.append(self.head_distance())

    def head_distance(self) -> float:
        """Distancia del frente en la dirección del viento [m]."""
        rows, cols = np.nonzero(self.burned)
        if rows.size == 0:
            return 0.0
        direction = np.array([np.cos(self.wind_direction), np.sin(self.wind_direction)])
        coords = np.column_stack([cols * self.terrain.cell_size, -rows * self.terrain.cell_size])
        projected = coords @ direction
        return max(0.0, float(np.max(projected) - self._head_origin))


class DeterministicCA(FireCA):
    """Autómata celular determinista por umbral de exposición."""

    def _ignite_from_hazard(self) -> None:
        ignite = self.unburned & self.valid & (self.hazard >= 1.0)
        if np.any(ignite):
            self.state[ignite] = BURNING
            self.arrival[ignite] = self.time + self.dt
            self.burn_age[ignite] = 0.0
            self.hazard[ignite] = 0.0


class StochasticCA(FireCA):
    """Autómata celular probabilístico con ruido de Bernoulli."""

    def __init__(self, *args: object, seed: int = 0, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.rng = np.random.default_rng(seed)
        self.seed = int(seed)

    def _ignite_from_hazard(self) -> None:
        candidates = self.unburned & self.valid & (self.hazard > 0.0)
        if not np.any(candidates):
            self.hazard.fill(0.0)
            return
        probability = 1.0 - np.exp(-self.hazard)
        draw = self.rng.random(self.state.shape)
        ignite = candidates & (draw < probability)
        if np.any(ignite):
            self.state[ignite] = BURNING
            self.arrival[ignite] = self.time + self.dt
            self.burn_age[ignite] = 0.0
        # El hazard es un intento por paso: se reinicia para que la
        # probabilidad sea memoryless (proceso de Poisson).
        self.hazard.fill(0.0)

    def run(
        self,
        t_end: float,
        snapshot_times: tuple[float, ...] = (),
        record_every: float = 0.0,
    ) -> SimulationResult:
        return super().run(t_end, snapshot_times, record_every)


class MinimumTravelTime:
    """Tiempo mínimo de llegada mediante el algoritmo de Dijkstra.

    El grafo tiene un nodo por celda y aristas hacia los ocho vecinos de
    Moore con peso ``d / R`` (tiempo de cruce). La solución es determinista y
    equivale a la envolvente de todos los caminos posibles, por lo que
    sobreestima ligeramente la velocidad de un frente continuo pero sirve
    como cota inferior del tiempo de llegada.
    """

    def __init__(
        self,
        terrain: Terrain,
        ignition: NDArray[np.bool_] | None = None,
        max_rate: float = 2.5,
        fuel_models: dict[str, FuelModel] | None = None,
        wind_speed: float | None = None,
        wind_direction: float | None = None,
        wind_efficiency: float = 0.30,
        neighborhood: str = "moore",
    ) -> None:
        self.terrain = terrain
        self.fuel_models = fuel_models or terrain.fuel_models()
        offsets = MOORE_OFFSETS if neighborhood == "moore" else VON_NEUMANN_OFFSETS
        if neighborhood not in ("moore", "vonneumann"):
            raise ValueError("neighborhood debe ser 'moore' o 'vonneumann'")
        self.wind_speed = terrain.wind_speed if wind_speed is None else float(wind_speed)
        self.wind_direction = (
            terrain.wind_direction if wind_direction is None else float(wind_direction)
        )
        self.wind_efficiency = float(wind_efficiency)
        props = fuel_property_maps(terrain.fuel_type, self.fuel_models)
        load = props["load"] * terrain.load_factor
        rates = directional_rates(
            load=load,
            sav=props["sav"],
            depth=props["depth"],
            moisture=terrain.moisture,
            mx=props["mx"],
            wind_speed=self.wind_speed,
            wind_direction=self.wind_direction,
            grad_x=terrain.grad_x,
            grad_y=terrain.grad_y,
            cell_size=terrain.cell_size,
            max_rate=max_rate,
            wind_efficiency=self.wind_efficiency,
            offsets=offsets,
        )
        self.ignition = (
            ignition_mask(terrain.shape, "center")
            if ignition is None
            else np.asarray(ignition, bool)
        )
        self.arrival = self._solve(rates, props["valid"] > 0.0)

    def _solve(self, rates: DirectionalRates, valid: NDArray[np.bool_]) -> NDArray[np.float64]:
        h, w = self.terrain.shape
        n = h * w
        rows: list[NDArray[np.int64]] = []
        cols: list[NDArray[np.int64]] = []
        weights: list[NDArray[np.float64]] = []
        index = np.arange(n).reshape(h, w)
        for k, (dr, dc) in enumerate(rates.offsets):
            src_r = slice(max(0, -dr), h - max(0, dr))
            src_c = slice(max(0, -dc), w - max(0, dc))
            dst_r = slice(max(0, dr), h - max(0, -dr))
            dst_c = slice(max(0, dc), w - max(0, -dc))
            src = index[src_r, src_c].ravel()
            dst = index[dst_r, dst_c].ravel()
            rate = rates.rates[k][src_r, src_c].ravel()
            ok = valid[src_r, src_c].ravel() & valid[dst_r, dst_c].ravel() & (rate > 1e-12)
            src = src[ok]
            dst = dst[ok]
            rate = rate[ok]
            rows.append(src)
            cols.append(dst)
            weights.append(rates.distances[k] / rate)
        graph = csr_matrix(
            (
                np.concatenate(weights),
                (np.concatenate(rows), np.concatenate(cols)),
            ),
            shape=(n, n),
        )
        sources = np.flatnonzero(self.ignition.ravel() & valid.ravel())
        if sources.size == 0:
            return np.full((h, w), np.inf)
        dist = dijkstra(graph, directed=True, indices=sources, min_only=True)
        return dist.reshape(h, w)

    def burned_at(self, time: float) -> NDArray[np.bool_]:
        return np.isfinite(self.arrival) & (self.arrival <= time)

    def area_at(self, time: float, cell_area: float | None = None) -> float:
        cell_area = cell_area or self.terrain.cell_size**2
        return float(np.count_nonzero(self.burned_at(time)) * cell_area)


def run_ensemble(
    terrain: Terrain,
    n_members: int,
    t_end: float,
    dt: float = 1.0,
    seed: int = 0,
    ignition: NDArray[np.bool_] | None = None,
    snapshot_times: tuple[float, ...] = (),
    record_every: float = 0.0,
) -> list[SimulationResult]:
    """Ejecuta un ensemble Monte Carlo del autómata estocástico."""
    results: list[SimulationResult] = []
    for member in range(n_members):
        model = StochasticCA(
            terrain,
            ignition=ignition,
            dt=dt,
            seed=seed + member,
        )
        results.append(model.run(t_end, snapshot_times=snapshot_times, record_every=record_every))
    return results
