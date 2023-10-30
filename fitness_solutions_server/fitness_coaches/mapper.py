from typing import Annotated, Sequence

from fastapi import Depends

from fitness_solutions_server.storage.base import StorageServiceDependency

from . import models, schemas


class FitnessCoachMapper:
    def __init__(self, storage_service: StorageServiceDependency):
        self.storage_service = storage_service

    def fitness_coach_to_schema(
        self,
        fitness_coach: models.FitnessCoach,
    ) -> schemas.FitnessCoach:
        return schemas.FitnessCoach(
            id=fitness_coach.id,
            email=fitness_coach.email,
            full_name=fitness_coach.full_name,
            title=fitness_coach.title,
            description=fitness_coach.description,
            sex=fitness_coach.sex,
            activated_at=fitness_coach.activated_at,
            profile_image_url=self.storage_service.link(
                fitness_coach.profile_image_path
            ),
            created_at=fitness_coach.created_at,
            updated_at=fitness_coach.updated_at,
            number_of_workouts=fitness_coach.number_of_workouts,
            number_of_fitness_plans=fitness_coach.number_of_fitness_plans,
            is_released=fitness_coach.is_released,
        )

    def fitness_coaches_to_schema(
        self, fitness_coaches: Sequence[models.FitnessCoach]
    ) -> list[schemas.FitnessCoach]:
        return [self.fitness_coach_to_schema(fc) for fc in fitness_coaches]


FitnessCoachMapperDependency = Annotated[FitnessCoachMapper, Depends()]
