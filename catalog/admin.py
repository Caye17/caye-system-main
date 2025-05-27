from django.contrib import admin
from .models import Author, Book, Borrower, BorrowingRecord
from django.utils import timezone

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'birth_date')
    list_filter = ('last_name',)
    search_fields = ('first_name', 'last_name')
    ordering = ('last_name', 'first_name')

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'display_genre', 'quantity')
    list_filter = ('author', 'genre', 'language')
    search_fields = ('title', 'summary')
    fieldsets = (
        (None, {
            'fields': ('title', 'author', 'summary', 'genre', 'language', 'cover_image', 'publication_date', 'quantity')
        }),
    )
    
    def display_genre(self, obj):
        return obj.genre
    display_genre.short_description = 'Genre'

@admin.register(Borrower)
class BorrowerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'registration_date')
    search_fields = ('name', 'email', 'phone')
    list_filter = ('registration_date',)

@admin.register(BorrowingRecord)
class BorrowingRecordAdmin(admin.ModelAdmin):
    list_display = ('book', 'borrower', 'borrow_date', 'due_date', 'return_date', 'status', 'is_overdue')
    list_filter = ('status', 'borrow_date', 'return_date', 'returned')
    search_fields = ('book__title', 'borrower__name')
    date_hierarchy = 'borrow_date'
    actions = ['mark_returned']

    def is_overdue(self, obj):
        return obj.is_overdue()
    is_overdue.boolean = True
    is_overdue.short_description = 'Overdue'

    def mark_returned(self, request, queryset):
        queryset.update(returned=True, status='returned', return_date=timezone.now().date())
        # Optionally, increase book quantity when marked as returned. We need to loop through to do this.
        for record in queryset:
            record.book.quantity += 1
            record.book.save()
        self.message_user(request, f"{queryset.count()} borrowing record(s) marked as returned and book quantity updated.")

    mark_returned.short_description = "Mark selected borrowing records as returned"
    
