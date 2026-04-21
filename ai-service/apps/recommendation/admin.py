from django.contrib import admin

from .models import HousingFeatureVector, HousingRecommendationResult, RecommendationFeedback, UserPreferenceVector

admin.site.register(HousingFeatureVector)
admin.site.register(UserPreferenceVector)
admin.site.register(HousingRecommendationResult)
admin.site.register(RecommendationFeedback)

