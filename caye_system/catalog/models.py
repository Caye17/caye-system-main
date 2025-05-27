from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings

class Author(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    birth_date = models.DateField(null=True, blank=True)
    biography = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = 'Author'
        verbose_name_plural = 'Authors'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_absolute_url(self):
        return reverse('author-detail', args=[str(self.id)])


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.SET_NULL, null=True)
    publisher = models.CharField(max_length=200, blank=True, help_text="Name of the publisher")
    summary = models.TextField(help_text="Brief description of the book")
    genre = models.CharField(max_length=100, blank=True)
    language = models.CharField(max_length=50, blank=True)
    cover_image = models.ImageField(upload_to='covers/', null=True, blank=True)
    publication_date = models.DateField(null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1, help_text='Number of copies available')

    class Meta:
        ordering = ['title']
        verbose_name = 'Book'
        verbose_name_plural = 'Books'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('book-detail', args=[str(self.id)])

    def display_genre(self):
        return self.genre
    display_genre.short_description = 'Genre'

    def get_available_quantity(self):
        """Get the number of available copies."""
        return self.quantity


class Borrower(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(null=True, blank=True, unique=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    registration_date = models.DateField(default=timezone.now)

    class Meta:
        ordering = ['name']
        verbose_name = 'Borrower'
        verbose_name_plural = 'Borrowers'

    def __str__(self):
        return self.name

    # Add a method to get the total borrowing record count for a borrower
    def get_total_borrowing_records(self):
        return BorrowingRecord.objects.filter(borrower=self).count()


class BorrowingRecord(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('returned', 'Returned'),
    ]
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    borrower = models.ForeignKey(Borrower, on_delete=models.SET_NULL, null=True)
    borrow_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    returned = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_borrowing_records')
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['borrow_date']
        verbose_name = 'Borrowing Record'
        verbose_name_plural = 'Borrowing Records'

    def __str__(self):
        return f"{self.book.title} borrowed by {self.borrower.name} (Status: {self.get_status_display()})"

    # No save method needed here as quantity is handled in views

    def clean(self):
        # Ensure due_date is not before borrow_date
        if self.due_date and self.borrow_date and self.due_date < self.borrow_date:
            raise ValidationError("Due date cannot be before borrow date.")

        # Ensure return_date is not before borrow_date
        if self.return_date and self.borrow_date and self.return_date < self.borrow_date:
            raise ValidationError("Return date cannot be before borrow date.")

        # Ensure return_date is not before due_date if both are set
        if self.return_date and self.due_date and self.return_date < self.due_date:
            raise ValidationError("Return date cannot be before the due date.")

    def is_overdue(self):
        # If the borrowing record has been returned, it is not overdue
        if self.returned:
            return False

        # If the due_date is in the past and the book hasn't been returned, it is overdue
        if self.due_date and timezone.now().date() > self.due_date and not self.returned:
            return True

        # Otherwise, it's not overdue
        return False
    is_overdue.boolean = True

class BorrowRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    request_date = models.DateTimeField(auto_now_add=True)
    decision_date = models.DateTimeField(null=True, blank=True)
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_borrow_requests')
    
    def __str__(self):
        return f"{self.user.username} requests {self.book.title} ({self.status})"
