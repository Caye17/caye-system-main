from django import forms
from django.core.exceptions import ValidationError
from .models import Author, Book, Borrower, BorrowingRecord
from django.utils import timezone
    
class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ['first_name', 'last_name', 'birth_date', 'biography']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'biography': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'publisher', 'summary', 'genre', 'language', 'publication_date', 'quantity']
        widgets = {
            'summary': forms.Textarea(attrs={'rows': 4}),
            'publication_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class BorrowerForm(forms.ModelForm):
    class Meta:
        model = Borrower
        fields = ['name', 'email', 'phone', 'address']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_email(self):
        email = self.cleaned_data['email']
        if email and Borrower.objects.filter(email=email).exists():
            raise ValidationError("A borrower with this email already exists")
        return email


class BorrowingRecordForm(forms.ModelForm):
    class Meta:
        model = BorrowingRecord
        fields = ['book', 'borrower', 'due_date', 'returned', 'notes', 'status']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'return_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = 'form-control'
            if isinstance(field.widget, forms.CheckboxInput):
                css_class = 'form-check-input'
            field.widget.attrs['class'] = css_class

    def clean(self):
        cleaned_data = super().clean()
        due_date = cleaned_data.get('due_date')
        return_date = cleaned_data.get('return_date')

         # Ensure that due_date is provided before comparison
        if due_date:
         if due_date < timezone.now().date():
            raise ValidationError({'due_date': "Due date cannot be in the past"})
    
         # Ensure that return_date is provided before comparison to book's publication date
        if return_date:
         book_publication_date = cleaned_data.get('book').publication_date
        if book_publication_date and return_date < book_publication_date:
            raise ValidationError({'return_date': "Return date cannot be before book publication date"})
    
        return cleaned_data