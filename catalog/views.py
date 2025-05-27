from django.contrib import messages
from django.urls import reverse_lazy
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import TemplateView
from .models import Author, Book, Borrower, BorrowingRecord, BorrowRequest
from .forms import AuthorForm, BookForm, BorrowerForm, BorrowingRecordForm
from rest_framework import viewsets, filters
from .serializers import AuthorSerializer, BookSerializer, BorrowingRecordSerializer, BorrowerSerializer
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, OuterRef, Subquery, F, Case, When, IntegerField
from django.db.models import Q
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, logout as auth_logout, get_user_model
from django.shortcuts import redirect, render, get_object_or_404
from django import forms
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.utils import timezone
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from datetime import timedelta
from itertools import chain
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# === Custom Mixin for Restricted Users ===
class RestrictedUserMixin(UserPassesTestMixin):
    def test_func(self):
        # List of usernames that are not allowed to add/edit/delete
        restricted_users = ['restricted_user', 'limited_user']  # Add usernames here
        return self.request.user.username not in restricted_users

    def handle_no_permission(self):
        messages.error(self.request, "You are not authorized to perform this action.")
        return HttpResponseRedirect(self.get_success_url())

# === Mixin for Success Message ===
class SuccessMessageMixin:
    def form_valid(self, form):
        messages.success(self.request, f"{self.model._meta.verbose_name.title()} successfully saved!")
        return super().form_valid(form)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, f"{self.model._meta.verbose_name.title()} deleted successfully!")
        return super().delete(request, *args, **kwargs)


# === PUBLIC HOME VIEW ===
class PublicHomeView(TemplateView):
    template_name = 'catalog/public_home.html'


# === REGISTER VIEW ===
class RegisterView(TemplateView):
    template_name = 'catalog/register.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        form = SimpleUserCreationForm()
        return self.render_to_response({'form': form})

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        form = SimpleUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
        return self.render_to_response({'form': form})


# === DASHBOARD VIEW ===
@method_decorator(login_required, name='dispatch')
class DashboardView(TemplateView):
    template_name = 'catalog/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Total Books
        total_books = Book.objects.count()
        context['total_books'] = total_books

        # Available, Low Stock, and Out of Stock Counts based on quantity
        available_count = Book.objects.filter(quantity__gt=0).count()
        low_stock_count = Book.objects.filter(quantity__gte=1, quantity__lte=2).count()
        out_of_stock_count = Book.objects.filter(quantity__lte=0).count()

        context['available_count'] = available_count
        context['low_stock_count'] = low_stock_count
        context['out_of_stock_count'] = out_of_stock_count

        # Borrowing Records for Staff/Admin
        if self.request.user.is_staff:
            pending_requests = BorrowRequest.objects.filter(status='pending').count()
            context['pending_requests'] = pending_requests
            context['borrowers_with_borrowing_records_url'] = reverse_lazy('borrowers-with-borrowing-records')
        else:
            # All borrowing records for regular users
            borrower = Borrower.objects.filter(email=self.request.user.email).first()
            if borrower:
                context['borrowed_books'] = BorrowingRecord.objects.filter(
                    borrower=borrower
                ).order_by('-borrow_date')  # Show all records, ordered by most recent first

        return context


# === AUTHOR VIEWS ===
class AuthorListView(ListView):
    model = Author
    template_name = 'catalog/author_list.html'
    context_object_name = 'authors'
    paginate_by = 10 # Add pagination

    def get_queryset(self):
        queryset = Author.objects.all()
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
        return queryset


class AuthorDetailView(generic.DetailView):
    model = Author
    template_name = 'catalog/author_detail.html'
    context_object_name = 'author'


class AuthorCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Author
    form_class = AuthorForm
    template_name = 'catalog/author_form.html'
    success_url = reverse_lazy('authors')

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(self.request, "Only staff members can add authors.")
        return HttpResponseRedirect(reverse_lazy('authors'))


class AuthorUpdateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = Author
    form_class = AuthorForm
    template_name = 'catalog/author_form.html'

    def get_success_url(self):
        """Redirect to the author list page after successful update.
        """
        return reverse_lazy('authors')

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(self.request, "Only staff members can edit authors.")
        return HttpResponseRedirect(reverse_lazy('author-detail', args=[str(self.get_object().id)]))


class AuthorDeleteView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, DeleteView):
    model = Author
    template_name = 'catalog/confirm_delete.html'
    success_url = reverse_lazy('authors')

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(self.request, "Only staff members can delete authors.")
        return HttpResponseRedirect(reverse_lazy('authors'))


# === BOOK VIEWS ===
class BookListView(ListView):
    model = Book
    template_name = 'catalog/book_list.html'
    context_object_name = 'books'


class BookDetailView(generic.DetailView):
    model = Book
    template_name = 'catalog/book_detail.html'
    context_object_name = 'book'


class BookCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Book
    form_class = BookForm
    template_name = 'catalog/book_form.html'
    success_url = reverse_lazy('books')

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(self.request, "Only staff members can add books.")
        return HttpResponseRedirect(reverse_lazy('books'))


class BookUpdateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = Book
    form_class = BookForm
    template_name = 'catalog/book_form.html'

    def get_success_url(self):
        """Redirect to the dashboard page after successful update.
        """
        return reverse_lazy('home')

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(self.request, "Only staff members can edit books.")
        return HttpResponseRedirect(reverse_lazy('book-detail', args=[str(self.get_object().id)]))


class BookDeleteView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, DeleteView):
    model = Book
    template_name = 'catalog/confirm_delete.html'
    success_url = reverse_lazy('books')

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(self.request, "Only staff members can delete books.")
        return HttpResponseRedirect(reverse_lazy('books'))


class BookUpdateQuantityView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        """Ensures only staff members can update book quantity.
        """
        return self.request.user.is_staff

    def post(self, request, pk):
        if not self.request.user.is_staff:
            return HttpResponseForbidden("You are not authorized to perform this action.")

        book = get_object_or_404(Book, pk=pk)
        quantity = request.POST.get('quantity', None)

        if quantity is not None:
            try:
                book.quantity = int(quantity)
                book.save()
                messages.success(request, f"Quantity for \'{book.title}\' updated successfully.")
            except ValueError:
                messages.error(request, "Invalid quantity value.")
            except Exception as e:
                messages.error(request, f"Error updating quantity: {e}")

        # Redirect back to the book list page or wherever appropriate
        return HttpResponseRedirect(reverse_lazy('books'))


# === BORROWER VIEWS ===
class BorrowerListView(ListView):
    model = Borrower
    template_name = 'catalog/borrower_list.html'
    context_object_name = 'borrowers'


class BorrowerDetailView(generic.DetailView):
    model = Borrower
    template_name = 'catalog/borrower_detail.html'
    context_object_name = 'borrower'

    def get_context_data(self, **kwargs):
        # Get the default context data from the parent class
        context = super().get_context_data(**kwargs)
        borrower = self.get_object()

        # Get borrowing records for this borrower
        borrowing_records = BorrowingRecord.objects.filter(borrower=borrower).select_related('book')

        # Get rejected borrow requests for the user linked to this borrower by email
        rejected_requests = BorrowRequest.objects.none() # Start with an empty queryset
        associated_user = User.objects.filter(email=borrower.email).first()

        if associated_user:
             rejected_requests = BorrowRequest.objects.filter(user=associated_user, status='rejected').select_related('book')

        # Combine the lists and sort them by date (borrow_date for records, request_date for requests)
        # We'll add a 'type' attribute to differentiate them in the template
        combined_history = []

        for record in borrowing_records:
            record.type = 'record'
            combined_history.append(record)

        for request in rejected_requests:
            request.type = 'request'
            combined_history.append(request)

        # Sort the combined list by date in descending order (most recent first)
        def sort_key(item):
            # Safely get dates, using a fallback for comparison if attribute is missing
            date = getattr(item, 'borrow_date', None)
            if date is None:
                date = getattr(item, 'request_date', None)

            # Convert date to datetime if it's a date object
            if date is not None:
                if isinstance(date, timezone.datetime):
                    return date
                else:
                    # Convert date to datetime at midnight
                    return timezone.make_aware(
                        timezone.datetime.combine(date, timezone.datetime.min.time()),
                        timezone.get_default_timezone()
                    )

            # Define a fallback datetime (timezone-aware)
            return timezone.make_aware(timezone.datetime.min, timezone.get_default_timezone())

        combined_history.sort(key=sort_key, reverse=True)

        # Add the combined history to the context
        context['combined_history'] = combined_history

        # Pass today's date for overdue check in template
        context['today'] = timezone.now().date()

        return context


class BorrowerCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Borrower
    form_class = BorrowerForm
    template_name = 'catalog/borrower_form.html'
    success_url = reverse_lazy('borrowers')

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(self.request, "Only staff members can add borrowers.")
        return HttpResponseRedirect(reverse_lazy('borrowers'))


class BorrowerUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Borrower
    form_class = BorrowerForm
    template_name = 'catalog/borrower_form.html'

    def get_success_url(self):
        return reverse_lazy('borrower-detail', args=[str(self.object.id)])

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(self.request, "Only staff members can edit borrowers.")
        return HttpResponseRedirect(reverse_lazy('borrower-detail', args=[str(self.get_object().id)]))


class BorrowerDeleteView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, DeleteView):
    model = Borrower
    template_name = 'catalog/confirm_delete.html'
    success_url = reverse_lazy('borrowers')

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(self.request, "Only staff members can delete borrowers.")
        return HttpResponseRedirect(reverse_lazy('borrowers'))


# === BORROWING RECORD VIEWS (formerly LOAN VIEWS) ===
class BorrowingRecordListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = BorrowingRecord # Still specify a model, but we're manually handling queryset
    template_name = 'catalog/borrowing_record_list.html'
    context_object_name = 'items' # Change context object name
    paginate_by = 25 # Increase pagination limit for a combined view

    def test_func(self):
        return self.request.user.is_staff # Only staff can view this page

    def get_queryset(self):
        # Get pending borrow requests
        pending_requests_queryset = BorrowRequest.objects.filter(status='pending').order_by('-request_date')

        # Get all borrowing records and ensure we select related book and borrower
        borrowing_records_queryset = BorrowingRecord.objects.all().select_related('book', 'borrower').order_by('-borrow_date')

        combined_list = []

        # Manually annotate pending requests with active borrowing count
        for request in pending_requests_queryset:
            # Safely get the borrower and their active borrowing count
            borrower = getattr(request.user, 'borrower', None)
            if borrower:
                active_count = BorrowingRecord.objects.filter(
                    borrower=borrower,
                    status='approved',
                    returned=False
                ).count()
                request.active_borrowings_count = active_count
            else:
                request.active_borrowings_count = 0 # Or None, depending on desired display
            request.type = 'request'
            combined_list.append(request)

        # Manually annotate borrowing records with active borrowing count
        for record in borrowing_records_queryset:
            # Safely get the borrower and their active borrowing count
            borrower = getattr(record, 'borrower', None)
            if borrower:
                active_count = BorrowingRecord.objects.filter(
                    borrower=borrower,
                    status='approved',
                    returned=False
                ).count()
                record.active_borrowings_count = active_count
            else:
                record.active_borrowings_count = 0 # Or None
            record.type = 'record'
            combined_list.append(record)

        # Sort the combined list. Prioritize pending requests (most recent first), then borrowing records (most recent first).
        def sort_key(item):
            # Safely get dates, using a fallback for comparison if attribute is missing
            request_date = getattr(item, 'request_date', None)
            borrow_date = getattr(item, 'borrow_date', None)

            # Define a fallback datetime (timezone-aware)
            fallback_datetime = timezone.make_aware(timezone.datetime.min, timezone.get_default_timezone())

            if hasattr(item, 'type') and item.type == 'request':
                # For requests, sort by request_date (DateTime) - higher value first for reverse=True
                # Use a fallback datetime for comparison if request_date is None
                return (0, request_date if request_date is not None else fallback_datetime)
            elif hasattr(item, 'type') and item.type == 'record':
                # For records, sort by borrow_date (Date) - higher value first for reverse=True
                # Convert DateField to a comparable value (DateTimeField) for consistent sorting
                # Use a fallback datetime if borrow_date is None
                date_part = timezone.make_aware(timezone.datetime.combine(borrow_date, timezone.datetime.min.time()), timezone.get_default_timezone()) if borrow_date is not None else fallback_datetime
                return (1, date_part)
            # Fallback for unexpected items - lowest priority and earliest possible time
            return (2, fallback_datetime)

        # Sort in descending order
        combined_list.sort(key=sort_key, reverse=True)

        return combined_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Manual pagination for the combined list
        paginator = Paginator(self.object_list, self.paginate_by)
        page = self.request.GET.get('page')

        try:
            items_page = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            items_page = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            items_page = paginator.page(paginator.num_pages)

        # Assign the paginated items to the context variable used in the template
        context['items'] = items_page.object_list
        # Pass pagination related variables to the template
        context['is_paginated'] = items_page.has_other_pages()
        context['page_obj'] = items_page
        context['paginator'] = paginator # Pass paginator to template for page range

        return context


class BorrowingRecordDetailView(generic.DetailView):
    model = BorrowingRecord
    template_name = 'catalog/borrowing_record_detail.html'
    context_object_name = 'borrowing_record'


class BorrowingRecordCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = BorrowingRecord
    form_class = BorrowingRecordForm
    template_name = 'catalog/borrowing_record_form.html'
    success_url = reverse_lazy('borrowing-records')

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(self.request, "Only staff members can create borrowing records.")
        return HttpResponseRedirect(reverse_lazy('borrowing-records'))


class BorrowingRecordUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = BorrowingRecord
    form_class = BorrowingRecordForm
    template_name = 'catalog/borrowing_record_form.html'

    def get_success_url(self):
        return reverse_lazy('borrowing-record-detail', args=[str(self.object.id)])

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(self.request, "Only staff members can edit borrowing records.")
        return HttpResponseRedirect(reverse_lazy('borrowing-record-detail', args=[str(self.get_object().id)]))


class BorrowingRecordDeleteView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, DeleteView):
    model = BorrowingRecord
    template_name = 'catalog/confirm_delete.html'
    success_url = reverse_lazy('borrowing-records')

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(self.request, "Only staff members can delete borrowing records.")
        return HttpResponseRedirect(reverse_lazy('borrowing-records'))


# === BORROW VIEW (User Request) ===
@login_required
def borrow_book_request(request, pk):
    book = get_object_or_404(Book, pk=pk)

    # Check if the user has a Borrower profile
    borrower = Borrower.objects.filter(email=request.user.email).first()
    if not borrower:
        messages.error(request, "Please complete your borrower profile before requesting a book.")
        # Redirect to a page to complete profile or just back to book list
        return HttpResponseRedirect(reverse_lazy('books'))

    # Check if there's already a pending request for this book by this user
    existing_request = BorrowRequest.objects.filter(user=request.user, book=book, status='pending').exists()
    if existing_request:
        messages.info(request, f"You already have a pending borrow request for \'{book.title}\'.")
    # Check if the user has already borrowed this book and hasn't returned it
    elif BorrowingRecord.objects.filter(borrower=borrower, book=book, returned=False).exists():
         messages.warning(request, f"You have already borrowed \'{book.title}\' and not yet returned it.")
    # Check if the book is available (quantity > 0)
    elif book.quantity <= 0:
        messages.error(request, f"\'{book.title}\' is out of stock and cannot be borrowed.")
    else:
        # Create the borrow request
        BorrowRequest.objects.create(user=request.user, book=book)
        messages.success(request, f"Your borrow request for \'{book.title}\' has been submitted and is pending admin approval.")

    return HttpResponseRedirect(reverse_lazy('books')) # Redirect back to the book list


# === ADMIN APPROVAL VIEW ===
@method_decorator(login_required, name='dispatch')
class ApproveBorrowingRequestView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff # Only staff can approve/reject

    def post(self, request, pk, action):
        if not self.request.user.is_staff:
            return HttpResponseForbidden("You are not authorized to perform this action.")

        # Retrieve the borrow request by pk, regardless of status
        borrow_request = get_object_or_404(BorrowRequest, pk=pk)
        book = borrow_request.book
        borrower = Borrower.objects.filter(email=borrow_request.user.email).first()

        if not borrower:
             messages.error(request, "Borrower profile not found for this user.")
             # Optionally, mark the request as rejected if borrower not found
             if borrow_request.status == 'pending': # Only change status if still pending
                 borrow_request.status = 'rejected'
                 borrow_request.decision_date = timezone.now()
                 borrow_request.admin = request.user
                 borrow_request.save()
             return HttpResponseRedirect(reverse_lazy('home')) # Redirect back to dashboard

        # Check if the request is still pending before processing
        if borrow_request.status != 'pending':
             messages.warning(request, f"Borrow request for \'{book.title}\' by {borrower.name} has already been {borrow_request.status}.")
             # Redirect back to the combined borrowing records list
             return HttpResponseRedirect(reverse_lazy('borrowing-records'))


        if action == 'approve':
            # Check if the book is still available (quantity > 0)
            if book.quantity > 0:
                # Create a BorrowingRecord
                BorrowingRecord.objects.create(
                    book=book,
                    borrower=borrower,
                    due_date=timezone.now().date() + timedelta(days=14), # Example: 14 days borrowing period
                    status='approved',
                    processed_by=request.user,
                    processed_at=timezone.now()
                )
                # Decrease book quantity
                book.quantity -= 1
                book.save()

                borrow_request.status = 'approved'
                messages.success(request, f"Borrow request for \'{book.title}\' by {borrower.name} approved.")
            else:
                borrow_request.status = 'rejected'
                messages.error(request, f"Borrow request for \'{book.title}\' by {borrower.name} rejected: Book is now out of stock.")
        elif action == 'reject':
            borrow_request.status = 'rejected'
            messages.warning(request, f"Borrow request for \'{book.title}\' by {borrower.name} rejected.")
        else:
            messages.error(request, "Invalid action.")

        borrow_request.decision_date = timezone.now()
        borrow_request.admin = request.user
        borrow_request.save()

        # Redirect back to the combined borrowing records list
        return HttpResponseRedirect(reverse_lazy('borrowing-records'))


# === RETURN BOOK VIEW ===
@method_decorator(login_required, name='dispatch')
class ReturnBookView(View):
    def post(self, request, pk):
        # Retrieve the borrowing record by pk alone
        borrowing_record = get_object_or_404(BorrowingRecord, pk=pk)

        # Check if the record is already returned or not approved
        if borrowing_record.returned or borrowing_record.status != 'approved':
            messages.warning(request, f"Book '{borrowing_record.book.title}' cannot be returned as it is already {borrowing_record.status}.")
            # Redirect back to the appropriate page
            if request.user.is_staff:
                return HttpResponseRedirect(reverse_lazy('borrowing-records'))
            else:
                return HttpResponseRedirect(reverse_lazy('home'))

        # Check if the borrowing record belongs to the current user or if the user is staff
        borrower = Borrower.objects.filter(email=request.user.email).first()
        if not (request.user.is_staff or (borrower and borrowing_record.borrower == borrower)):
            return HttpResponseForbidden("You are not authorized to perform this action.")

        # Mark the borrowing record as returned
        borrowing_record.returned = True
        borrowing_record.status = 'returned'
        borrowing_record.return_date = timezone.now().date()
        borrowing_record.processed_by = request.user # Record who processed the return
        borrowing_record.processed_at = timezone.now()
        borrowing_record.save()

        # Increase book quantity
        book = borrowing_record.book
        book.quantity += 1
        book.save()

        messages.success(request, f"Book '{book.title}' returned successfully.")

        # Redirect based on user type (staff to combined list, regular user to dashboard)
        if request.user.is_staff:
            return HttpResponseRedirect(reverse_lazy('borrowing-records'))
        else:
            return HttpResponseRedirect(reverse_lazy('home'))


# === VIEW BORROWERS WITH BORROWING RECORDS (for staff) ===
# This view is no longer needed as active borrowers count is annotated.
# @method_decorator(login_required, name='dispatch')
# class BorrowersWithBorrowingRecordsView(UserPassesTestMixin, ListView):
#     model = Borrower
#     template_name = 'catalog/borrowers_with_borrowing_records.html'
#     context_object_name = 'borrowers'
#     paginate_by = 10 # Optional: add pagination
#
#     def test_func(self):
#         return self.request.user.is_staff # Only staff can view this page
#
#     def get_queryset(self):
#         # Get all borrowers who have borrowing records and annotate with borrowing record count
#         # Prefetch related borrowing records for efficient access in the template
#         return Borrower.objects.annotate(
#             borrowing_record_count=Count('borrowingrecord')
#         ).filter(borrowing_record_count__gt=0).order_by('name').prefetch_related('borrowingrecord_set')
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         # Optionally, add filtering or search for borrowers
#         return context

# === API VIEWS ===
class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name']


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['author', 'genre', 'language']
    search_fields = ['title', 'summary']


class BorrowingRecordViewSet(viewsets.ModelViewSet):
    queryset = BorrowingRecord.objects.all()
    serializer_class = BorrowingRecordSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['book', 'borrower', 'status', 'returned']
    search_fields = ['book__title', 'borrower__name']


class BorrowerViewSet(viewsets.ModelViewSet):
    queryset = Borrower.objects.all()
    serializer_class = BorrowerSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'email']


# Simple User Creation Form (for registration)
class SimpleUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

def custom_logout(request):
    auth_logout(request)
    messages.success(request, "You have been logged out successfully.")
    return HttpResponseRedirect(reverse_lazy('public-home'))

@method_decorator(login_required, name='dispatch')
class BorrowBookView(View):
    def post(self, request, pk):
        book = get_object_or_404(Book, pk=pk)
        # Check if a pending request already exists for this user and book
        existing_request = BorrowRequest.objects.filter(user=request.user, book=book, status='pending').first()
        if existing_request:
            messages.info(request, f"You already have a pending borrow request for \'{book.title}\'.")
        elif book.quantity > 0:
            BorrowRequest.objects.create(user=request.user, book=book)
            messages.success(request, f"Your borrow request for \'{book.title}\' has been submitted and is pending admin approval.")
        else:
            messages.error(request, f"\'{book.title}\' is out of stock and cannot be borrowed.")
        return redirect('books')

# === PENDING BORROW REQUESTS LIST VIEW (for staff) ===
# This view is no longer needed as pending requests are included in the combined list.
# @method_decorator(login_required, name='dispatch')
# class PendingBorrowRequestsListView(UserPassesTestMixin, ListView):
#     model = BorrowRequest
#     template_name = 'catalog/pending_borrow_requests.html'
#     context_object_name = 'pending_requests'
#     paginate_by = 10 # Optional: add pagination
#
#     def test_func(self):
#         return self.request.user.is_staff # Only staff can view this page
#
#     def get_queryset(self):
#         # Get all pending borrow requests
#         return BorrowRequest.objects.filter(status='pending').order_by('-request_date')
