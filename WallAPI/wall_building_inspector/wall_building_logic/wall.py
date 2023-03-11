"""
Contains business logic related to wall data calculations
"""
import logging
import os
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Optional, Iterator, Iterable

from django.conf import settings

from wall_building_inspector.exceptions import InvalidDayException

logging.basicConfig(
    filename="logs.txt",
    filemode="a",
    level=logging.DEBUG
)

logger = logging.getLogger(__name__)


@dataclass
class SectionData:
    profile_number: int
    section_number: int
    section_height: int


def parse_profiles_from_config() -> Iterator[Iterator[int]]:
    current_path = os.path.dirname(__file__)
    input_config_file_path = os.path.join(current_path, "input_config")
    with open(input_config_file_path, "r") as file_pointer:
        # strip for convenience since code editors keep adding newline
        profiles_data = file_pointer.read()
    return (
        (int(section) for section in profile.strip().split(settings.SECTIONS_DELIMITER))
        for profile
        in profiles_data.strip().split(settings.PROFILES_DELIMITER)
    )


def prepare_sections_generator(profiles: Iterable[Iterable[int]]) -> Iterator[SectionData]:
    for profile_number, profile in enumerate(profiles, 1):
        for section_number, section_height in enumerate(profile, 1):
            if section_height < settings.TARGET_HEIGHT:  # skip 30's initially in config
                yield SectionData(profile_number, section_number, section_height)


class ThreadSafeGenerator:
    def __init__(self, generator):
        self.lock = threading.Lock()
        self.generator = generator

    def next(self):
        self.lock.acquire()
        try:
            return next(self.generator)
        finally:
            self.lock.release()


class WorkTeam:
    _counter = 0

    current_section: Optional[SectionData]
    sections_generator: ThreadSafeGenerator
    id: int

    @classmethod
    def get_next_id(cls):
        cls._counter += 1
        return cls._counter

    def __init__(self, shared_sections_generator):
        self.id = self.__class__.get_next_id()
        self.sections_generator = shared_sections_generator
        try:
            self.current_section = self.sections_generator.next()
        except StopIteration:
            self.current_section = None
            logger.info(f"Work team {self.id} relieved immediately (on day 1)")

    @staticmethod
    def do_some_heavy_lifting():
        """
                   O
           /~~~|#|]|=\|---\__
         |-=_____________  |\\ ,             O       O
        I|_/,-.-.-.-.-,-.\_|='(             T/\     /\=,---.
           ( o )( o )( o )     \            U /\   /\   `O'    cww
            `-'-'-'-'-`-'
        """
        time.sleep(1)

    def do_days_work(self, day: int):
        self.do_some_heavy_lifting()

        profile_number = self.current_section.profile_number
        self.current_section.section_height += 1
        if self.current_section.section_height == settings.TARGET_HEIGHT:
            logger.info(
                f"Work team {self.id} "
                f"finished section {self.current_section.section_number} "
                f"in profile {self.current_section.profile_number} "
                f"on day {day}"
            )
            try:
                self.current_section = self.sections_generator.next()
            except StopIteration:
                self.current_section = None
                logger.info(f"Work team {self.id} relieved on day {day}")

        return profile_number


class WallWorkDataCollector:
    def __init__(self, number_of_teams=settings.NUMBER_OF_TEAMS):
        self.number_of_teams = number_of_teams

    def work_on_wall(self, up_to_day: Optional[int] = None):
        logger.debug("---------------------------------------------")
        logger.debug(f"Starting new run with {self.number_of_teams} teams")
        feet_per_day_per_profile = {}

        shared_sections_generator = ThreadSafeGenerator(prepare_sections_generator(parse_profiles_from_config()))
        teams_working = [WorkTeam(shared_sections_generator) for _ in range(self.number_of_teams)]
        # In case there are more teams than total sections
        teams_working = [team for team in teams_working if team.current_section]

        pool = ThreadPoolExecutor(max_workers=len(teams_working))

        day = 1
        while teams_working:
            feet_per_day_per_profile[day] = defaultdict(int)

            futures = [pool.submit(team.do_days_work, day) for team in teams_working]
            for future in as_completed(futures):
                processed_profile_number = future.result()
                feet_per_day_per_profile[day][processed_profile_number] += 1

            # just so we don't go on with calculations after the day we are asking for
            if up_to_day and day == up_to_day:
                break

            teams_working = [team for team in teams_working if team.current_section]
            day += 1

        pool.shutdown()
        return feet_per_day_per_profile

    def get_ice_data_on_specific_day(self, profile_number, day_number):
        feet_per_day_per_profile = self.work_on_wall(up_to_day=day_number)
        try:
            profiles_data_for_the_day = feet_per_day_per_profile[day_number]
        except KeyError:
            raise InvalidDayException()

        feet_built_on_that_day = profiles_data_for_the_day.get(profile_number, 0)

        ice_count = feet_built_on_that_day * settings.ICE_USED_PER_FEET
        return ice_count

    def get_profile_cost_to_specific_day(self, profile_number, day_number):
        feet_per_day_per_profile = self.work_on_wall(up_to_day=day_number)
        feet_built_so_far = sum(
            profiles_results[profile_number]
            for day, profiles_results
            in feet_per_day_per_profile.items()
        )

        ice_count = feet_built_so_far * settings.ICE_USED_PER_FEET
        cost = ice_count * settings.COST_OF_ICE_PER_UNIT
        return cost

    def get_full_cost(self, day_number=None):
        feet_per_day_per_profile = self.work_on_wall(day_number)
        feet_built_so_far = sum(
            sum(profiles_results.values())
            for day, profiles_results
            in feet_per_day_per_profile.items()
        )

        ice_count = feet_built_so_far * settings.ICE_USED_PER_FEET
        cost = ice_count * settings.COST_OF_ICE_PER_UNIT
        return cost
