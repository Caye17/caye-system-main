from rest_framework import generics
from catalog.models import Book
from catalog.serializers import BookSerializer


class BookListAPI(generics.ListAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
