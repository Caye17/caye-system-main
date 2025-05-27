from rest_framework import serializers
from .models import Book, Author, BorrowingRecord, Borrower

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ('id', 'first_name', 'last_name', 'birth_date', 'biography')

class BookSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)

    class Meta:
        model = Book
        fields = ('id', 'title', 'author', 'summary', 'genre', 'language', 'cover_image', 'publication_date', 'quantity')

class BorrowerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrower
        fields = ('id', 'name', 'email', 'phone', 'address', 'registration_date')

class BorrowingRecordSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)
    borrower = BorrowerSerializer(read_only=True)

    class Meta:
        model = BorrowingRecord
        fields = ('id', 'book', 'borrower', 'borrow_date', 'due_date', 'return_date', 'returned', 'notes', 'status', 'processed_by', 'processed_at')
