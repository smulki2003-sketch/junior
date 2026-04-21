from django.urls import path

from .views import (
    AmenityListCreateView,
    HousingUnitAvailabilityView,
    HousingUnitDetailView,
    HousingUnitListCreateView,
    HousingUnitOccupancyAdjustView,
)


urlpatterns = [
    path("housing/units", HousingUnitListCreateView.as_view(), name="housing-unit-list-create"),
    path("housing/units/<int:unit_id>", HousingUnitDetailView.as_view(), name="housing-unit-detail"),
    path(
        "housing/units/<int:unit_id>/availability",
        HousingUnitAvailabilityView.as_view(),
        name="housing-unit-availability",
    ),
    path(
        "housing/units/<int:unit_id>/occupancy",
        HousingUnitOccupancyAdjustView.as_view(),
        name="housing-unit-occupancy-adjust",
    ),
    path("housing/amenities", AmenityListCreateView.as_view(), name="housing-amenities"),
]
