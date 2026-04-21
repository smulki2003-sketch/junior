from django.urls import path

from .views import (
    SavedFilterCreateView,
    SavedFilterResourceView,
    SearchHousingSuggestionsView,
    SearchHousingView,
    SearchIndexSyncView,
)


urlpatterns = [
    path("search/housing", SearchHousingView.as_view(), name="search-housing"),
    path("search/housing/suggestions", SearchHousingSuggestionsView.as_view(), name="search-housing-suggestions"),
    path("search/index/sync", SearchIndexSyncView.as_view(), name="search-index-sync"),
    path("search/saved-filters", SavedFilterCreateView.as_view(), name="search-saved-filter-create"),
    path("search/saved-filters/<int:resource_id>", SavedFilterResourceView.as_view(), name="search-saved-filter-resource"),
]
