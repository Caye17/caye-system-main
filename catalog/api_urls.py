from django.urls import path
from catalog.api_views import BookListAPI  # type: ignore # Example API view


urlpatterns = [
    path('books/', BookListAPI.as_view(), name='api-books'),
    # add other API endpoints here
]
