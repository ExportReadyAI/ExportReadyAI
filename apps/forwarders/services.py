"""
Services for Module 6B: Forwarders

Implements:
- PBI-BE-M6-23: Calculate Forwarder Average Rating
- PBI-BE-M6-24: Forwarder Recommendation Engine
"""

import logging
from typing import List, Dict
from decimal import Decimal
from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import ForwarderProfile, ForwarderReview

logger = logging.getLogger(__name__)


class ForwarderRatingService:
    """
    Service for calculating forwarder ratings.
    
    PBI-BE-M6-23: Calculate Forwarder Average Rating
    """

    @staticmethod
    def recalculate_rating(forwarder_id: int):
        """
        Recalculate average rating and total reviews for a forwarder.
        
        Triggered after: create, update, delete review
        Query: SELECT AVG(rating), COUNT(*) FROM ForwarderReview WHERE forwarder_id = X
        Update ForwarderProfile: average_rating, total_reviews
        Round average_rating to 1 decimal place
        Handle edge case: 0 reviews → average_rating = 0
        """
        try:
            forwarder = ForwarderProfile.objects.get(id=forwarder_id)
            
            # Calculate average and count
            stats = ForwarderReview.objects.filter(forwarder=forwarder).aggregate(
                avg_rating=Avg("rating"),
                total=Count("id")
            )
            
            avg_rating = stats["avg_rating"]
            total_reviews = stats["total"] or 0
            
            # Round to 1 decimal place
            if avg_rating is not None:
                average_rating = round(Decimal(str(avg_rating)), 1)
            else:
                average_rating = Decimal("0.0")
            
            # Update forwarder profile
            forwarder.average_rating = average_rating
            forwarder.total_reviews = total_reviews
            forwarder.save()
            
            logger.info(f"Recalculated rating for forwarder {forwarder_id}: {average_rating} ({total_reviews} reviews)")
            
            return {
                "average_rating": float(average_rating),
                "total_reviews": total_reviews,
            }
        except ForwarderProfile.DoesNotExist:
            logger.error(f"ForwarderProfile {forwarder_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error recalculating rating for forwarder {forwarder_id}: {e}")
            return None


class ForwarderRecommendationService:
    """
    Service for forwarder recommendations.
    
    PBI-BE-M6-24: Forwarder Recommendation Engine
    """

    @staticmethod
    def get_recommendations(destination_country: str, limit: int = 5) -> List[Dict]:
        """
        Get recommended forwarders for a destination country.
        
        Logic:
        1. Extract destinations from forwarder routes (e.g., "ID-JP" → "JP")
        2. Match extracted destinations with the recommended country code
        
        Input: destination_country (country code like "JP", "US", "SG")
        Query: ForwarderProfile WHERE any route destination matches destination_country
        Sort by: average_rating DESC
        Return top N forwarders (default 5, can be customized)
        Output: Array of forwarder details with all fields
        """
        # Get all forwarders and filter by matching destinations
        all_forwarders = ForwarderProfile.objects.all().order_by("-average_rating")
        
        matching_forwarders = []
        for forwarder in all_forwarders:
            # Extract destinations from specialization_routes
            # Routes format: ["ID-JP", "ID-US", "ID-SG"] → destinations: ["JP", "US", "SG"]
            destinations = []
            for route in forwarder.specialization_routes:
                if isinstance(route, str) and "-" in route:
                    # Split route (e.g., "ID-JP" → ["ID", "JP"])
                    parts = route.split("-", 1)
                    if len(parts) == 2:
                        destination = parts[1].strip().upper()  # Take destination part (e.g., "JP")
                        destinations.append(destination)
            
            # Check if the recommended country code matches any extracted destination
            destination_country_upper = destination_country.strip().upper()
            if destination_country_upper in destinations:
                matching_forwarders.append(forwarder)
                
                # Stop when we have enough forwarders
                if len(matching_forwarders) >= limit:
                    break
        
        # Build recommendations list
        recommendations = []
        for forwarder in matching_forwarders:
            recommendations.append({
                "id": forwarder.id,
                "company_name": forwarder.company_name,
                "contact_info": forwarder.contact_info,
                "specialization_routes": forwarder.specialization_routes,
                "service_types": forwarder.service_types,
                "average_rating": float(forwarder.average_rating),
                "total_reviews": forwarder.total_reviews,
            })
        
        return recommendations

    @staticmethod
    def get_statistics(forwarder_id: int) -> Dict:
        """
        Get statistics for a forwarder profile.
        
        PBI-BE-M6-26: GET /forwarders/:id/statistics
        """
        try:
            forwarder = ForwarderProfile.objects.get(id=forwarder_id)
            
            # Rating distribution
            distribution = (
                ForwarderReview.objects.filter(forwarder=forwarder)
                .values("rating")
                .annotate(count=Count("id"))
            )
            total = forwarder.total_reviews
            rating_distribution = {str(i): 0 for i in range(1, 6)}
            if total > 0:
                for item in distribution:
                    rating_distribution[str(item["rating"])] = round((item["count"] / total) * 100, 1)
            
            # Total UMKM partnerships (unique UMKM who reviewed)
            total_partnerships = (
                ForwarderReview.objects.filter(forwarder=forwarder)
                .values("umkm")
                .distinct()
                .count()
            )
            
            # Recent review trend (last 30 days)
            thirty_days_ago = timezone.now() - timedelta(days=30)
            recent_reviews = (
                ForwarderReview.objects.filter(
                    forwarder=forwarder,
                    created_at__gte=thirty_days_ago
                )
                .values("created_at__date")
                .annotate(count=Count("id"))
                .order_by("created_at__date")
            )
            recent_trend = [
                {
                    "date": str(item["created_at__date"]),
                    "count": item["count"],
                }
                for item in recent_reviews
            ]
            
            return {
                "total_reviews": forwarder.total_reviews,
                "average_rating": float(forwarder.average_rating),
                "rating_distribution": rating_distribution,
                "total_umkm_partnerships": total_partnerships,
                "recent_review_trend": recent_trend,
            }
        except ForwarderProfile.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error getting statistics for forwarder {forwarder_id}: {e}")
            return None

