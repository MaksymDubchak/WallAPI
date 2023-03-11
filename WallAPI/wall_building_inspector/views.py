from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from wall_building_inspector.wall_building_logic.wall import WallWorkDataCollector
from wall_building_inspector.exceptions import InvalidDayException


@api_view()
def ice_data(request, profile_number, day_number):
    data_collector = WallWorkDataCollector()
    try:
        ice_used = data_collector.get_ice_data_on_specific_day(profile_number, day_number)
    except InvalidDayException:
        return Response(
            data={"message": f"Work on wall finished before day {day_number}"}, status=status.HTTP_400_BAD_REQUEST
        )

    return Response(data={"ice_amount": ice_used, "day": day_number})


@api_view()
def profile_day_overview(request, profile_number, day_number):
    data_collector = WallWorkDataCollector()
    cost = data_collector.get_profile_cost_to_specific_day(profile_number, day_number)
    return Response(data={"cost": cost, "day": day_number})


@api_view()
def full_day_overview(request, day_number):
    data_collector = WallWorkDataCollector()
    cost = data_collector.get_full_cost(day_number)
    return Response(data={"cost": cost, "day": day_number})


@api_view()
def full_overview(request):
    data_collector = WallWorkDataCollector()
    cost = data_collector.get_full_cost()
    return Response(data={"cost": cost, "day": None})
