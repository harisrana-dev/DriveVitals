import logging

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.db.models.scenario import SimulationRun, SimulationScenario
from backend.db.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class ScenarioRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
        self._run_repo = _RunRepository(session)

    @property
    def runs(self) -> "_RunRepository":
        return self._run_repo

    # ------------------------------------------------------------------
    # Scenarios
    # ------------------------------------------------------------------

    async def create(
        self,
        name: str,
        *,
        description: str | None = None,
        status: str = "draft",
        duration_seconds: int | None = None,
        simulation_speed: float = 1.0,
        seed: int | None = None,
        scenario_id: str | None = None,
    ) -> SimulationScenario:
        scenario = SimulationScenario(
            name=name,
            description=description,
            status=status,
            duration_seconds=duration_seconds,
            simulation_speed=simulation_speed,
            seed=seed,
        )
        if scenario_id is not None:
            scenario.scenario_id = scenario_id
        self._session.add(scenario)
        await self._session.flush()
        return scenario

    async def get(self, scenario_id: str) -> SimulationScenario | None:
        result = await self._session.execute(
            select(SimulationScenario).where(
                SimulationScenario.scenario_id == scenario_id
            )
        )
        return result.scalar_one_or_none()

    async def update(
        self,
        scenario: SimulationScenario,
        *,
        name: str | None = None,
        description: str | None = None,
        status: str | None = None,
        duration_seconds: int | None = None,
        simulation_speed: float | None = None,
        seed: int | None = None,
    ) -> SimulationScenario:
        values: dict = {}
        if name is not None:
            values["name"] = name
        if description is not None:
            values["description"] = description
        if status is not None:
            values["status"] = status
        if duration_seconds is not None:
            values["duration_seconds"] = duration_seconds
        if simulation_speed is not None:
            values["simulation_speed"] = simulation_speed
        if seed is not None:
            values["seed"] = seed
        if values:
            await self._session.execute(
                update(SimulationScenario)
                .where(SimulationScenario.scenario_id == scenario.scenario_id)
                .values(**values)
            )
            await self._session.flush()
        return scenario

    async def delete(self, scenario_id: str) -> bool:
        result = await self._session.execute(
            delete(SimulationScenario).where(
                SimulationScenario.scenario_id == scenario_id
            )
        )
        await self._session.flush()
        return result.rowcount > 0

    async def list(
        self, limit: int, offset: int, status: str | None = None
    ) -> tuple[list[SimulationScenario], int]:
        query = (
            select(SimulationScenario)
            .options(selectinload(SimulationScenario.assignments))
            .order_by(SimulationScenario.created_at.desc())
        )
        if status is not None:
            query = query.where(SimulationScenario.status == status)
        total_result = await self._session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = total_result.scalar_one()
        result = await self._session.execute(query.limit(limit).offset(offset))
        return list(result.scalars().all()), total


class _RunRepository(BaseRepository):
    async def create(
        self,
        scenario_id: str,
        *,
        status: str = "ready",
        seed: int | None = None,
        run_id: str | None = None,
    ) -> SimulationRun:
        run = SimulationRun(
            scenario_id=scenario_id,
            status=status,
            seed=seed,
        )
        if run_id is not None:
            run.run_id = run_id
        self._session.add(run)
        await self._session.flush()
        return run

    async def get(self, run_id: str) -> SimulationRun | None:
        result = await self._session.execute(
            select(SimulationRun).where(SimulationRun.run_id == run_id)
        )
        return result.scalar_one_or_none()

    async def update(
        self,
        run: SimulationRun,
        *,
        status: str | None = None,
        start_time=None,
        end_time=None,
        vehicles_active: int | None = None,
        trips_completed: int | None = None,
        error: str | None = None,
    ) -> SimulationRun:
        values: dict = {}
        if status is not None:
            values["status"] = status
        if start_time is not None:
            values["start_time"] = start_time
        if end_time is not None:
            values["end_time"] = end_time
        if vehicles_active is not None:
            values["vehicles_active"] = vehicles_active
        if trips_completed is not None:
            values["trips_completed"] = trips_completed
        if error is not None:
            values["error"] = error
        if values:
            await self._session.execute(
                update(SimulationRun)
                .where(SimulationRun.run_id == run.run_id)
                .values(**values)
            )
            await self._session.flush()
        return run

    async def list_for_scenario(
        self, scenario_id: str, limit: int, offset: int
    ) -> tuple[list[SimulationRun], int]:
        query = (
            select(SimulationRun)
            .where(SimulationRun.scenario_id == scenario_id)
            .order_by(SimulationRun.created_at.desc())
        )
        total_result = await self._session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = total_result.scalar_one()
        result = await self._session.execute(query.limit(limit).offset(offset))
        return list(result.scalars().all()), total

    async def latest_for_scenario(self, scenario_id: str) -> SimulationRun | None:
        result = await self._session.execute(
            select(SimulationRun)
            .where(SimulationRun.scenario_id == scenario_id)
            .order_by(SimulationRun.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
