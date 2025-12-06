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
        
        Input: destination_country (from ExportAnalysis or Costing)
        Query: ForwarderProfile WHERE destination IN specialization_routes
        Sort by: average_rating DESC, total_reviews DESC
        Return top 5 forwarders
        Output: Array of {id, company_name, rating, contact_info}
        """
        # Build route pattern (e.g., 'ID-US' for destination 'US')
        route_pattern = f"ID-{destination_country}"
        
        # Query forwarders with matching routes
        # Note: JSONB contains check - PostgreSQL specific
        # For SQLite/other DBs, we'll use a simpler approach
        forwarders = ForwarderProfile.objects.filter(
            specialization_routes__contains=[route_pattern]
        ).order_by("-average_rating", "-total_reviews")[:limit]
        
        recommendations = []
        for forwarder in forwarders:
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

