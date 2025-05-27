from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Author, Book, Borrower, BorrowingRecord
from datetime import date, timedelta
from django.core.exceptions import ValidationError

class AuthorModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        Author.objects.create(first_name='John', last_name='Doe', birth_date=date(1980, 1, 1))
    
    def test_author_str(self):
        author = Author.objects.get(id=1)
        self.assertEqual(str(author), "John Doe")
    
    def test_author_get_absolute_url(self):
        author = Author.objects.get(id=1)
        self.assertEqual(author.get_absolute_url(), reverse('author-detail', args=[1]))

class BookViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        author = Author.objects.create(first_name='John', last_name='Doe')
        Book.objects.create(
            title='Test Book', 
            author=author, 
            isbn='1234567890123',
            summary='Test summary'
        )
        cls.user = User.objects.create_user(username='testuser', password='12345')
    
    def test_book_list_view(self):
        response = self.client.get(reverse('books'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Book')
        self.assertTemplateUsed(response, 'catalog/book_list.html')
    
    def test_book_create_view_requires_login(self):
        response = self.client.get(reverse('book-create'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('book-create'))
        self.assertEqual(response.status_code, 200)

class BorrowingRecordModelTest(TestCase):
    def test_overdue_status(self):
        book = Book.objects.create(title="Test Book")
        borrower = Borrower.objects.create(name="Test Borrower")
        BorrowingRecord.objects.create(
            book=book,
            borrower=borrower,
            borrow_date=date.today() - timedelta(days=10),
            due_date=date.today() - timedelta(days=1)
        )
        
        borrowing_record = BorrowingRecord.objects.get(id=1)
        self.assertTrue(borrowing_record.is_overdue())
        
        # Test validation
        borrowing_record = BorrowingRecord.objects.get(id=1)
        borrowing_record.due_date = borrowing_record.borrow_date - timedelta(days=1)
        with self.assertRaises(ValidationError):
            borrowing_record.clean()