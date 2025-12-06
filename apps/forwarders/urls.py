"""
URL configuration for forwarders app.
"""

from django.urls import path

from .views import (
    ForwarderProfileCreateView,
    ForwarderProfileUpdateView,
    ForwarderMyProfileView,
    ForwarderListView,
    ForwarderDetailView,
    ForwarderReviewCreateView,
    ForwarderReviewUpdateView,
    ForwarderReviewDeleteView,
    ForwarderRecommendationView,
    ForwarderStatisticsView,
)

app_name = "forwarders"

urlpatterns = [
    # Forwarder Profile
    path("profile/", ForwarderProfileCreateView.as_view(), name="profile-create"),
    path("profile/me/", ForwarderMyProfileView.as_view(), name="profile-me"),
    path("profile/<int:profile_id>/", ForwarderProfileUpdateView.as_view(), name="profile-update"),
    # Forwarders List & Detail
    path("", ForwarderListView.as_view(), name="list"),
    path("<int:forwarder_id>/", ForwarderDetailView.as_view(), name="detail"),
    # Forwarder Reviews
    path("<int:forwarder_id>/reviews/", ForwarderReviewCreateView.as_view(), name="review-create"),
    path("<int:forwarder_id>/reviews/<int:review_id>/", ForwarderReviewUpdateView.as_view(), name="review-update"),
    path("<int:forwarder_id>/reviews/<int:review_id>/delete/", ForwarderReviewDeleteView.as_view(), name="review-delete"),
    # Recommendations & Statistics
    path("recommendations/", ForwarderRecommendationView.as_view(), name="recommendations"),
    path("<int:forwarder_id>/statistics/", ForwarderStatisticsView.as_view(), name="statistics"),
]

