from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
from django.contrib.auth import views as auth_views
from .views import RegisterView, PublicHomeView

router = DefaultRouter()
router.register(r'books', views.BookViewSet)
router.register(r'authors', views.AuthorViewSet)
router.register(r'borrowers', views.BorrowerViewSet)
router.register(r'borrowingrecords', views.BorrowingRecordViewSet)

urlpatterns = [
    # Public homepage for unauthenticated users
    path('', PublicHomeView.as_view(), name='public-home'),
    path('register/', RegisterView.as_view(), name='register'),
    # Dashboard as homepage (login required)
    path('dashboard/', views.DashboardView.as_view(), name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='catalog/login.html'), name='login'),
    path('logout/', views.custom_logout, name='logout'),

    # Book HTML pages
    path('books/', views.BookListView.as_view(), name='books'),
    path('book/<int:pk>/', views.BookDetailView.as_view(), name='book-detail'),
    path('book/create/', views.BookCreateView.as_view(), name='book-create'),
    path('book/<int:pk>/update/', views.BookUpdateView.as_view(), name='book-update'),
    path('book/<int:pk>/delete/', views.BookDeleteView.as_view(), name='book-delete'),
    path('book/<int:pk>/borrow/', views.BorrowBookView.as_view(), name='book-borrow'),
    path('book/<int:pk>/update-quantity/', views.BookUpdateQuantityView.as_view(), name='book-update-quantity'),

    # Author HTML pages
    path('authors/', views.AuthorListView.as_view(), name='authors'),
    path('author/create/', views.AuthorCreateView.as_view(), name='author-create'),
    path('author/<int:pk>/update/', views.AuthorUpdateView.as_view(), name='author-update'),
    path('author/<int:pk>/delete/', views.AuthorDeleteView.as_view(), name='author-delete'),

    # Borrower HTML pages
    path('borrowers/', views.BorrowerListView.as_view(), name='borrowers'),
    path('borrower/<int:pk>/', views.BorrowerDetailView.as_view(), name='borrower-html-detail'),
    path('borrower/create/', views.BorrowerCreateView.as_view(), name='borrower-create'),
    path('borrower/<int:pk>/update/', views.BorrowerUpdateView.as_view(), name='borrower-update'),
    path('borrower/<int:pk>/delete/', views.BorrowerDeleteView.as_view(), name='borrower-delete'),

    # Borrowing Record HTML pages
    path('borrowingrecords/', views.BorrowingRecordListView.as_view(), name='borrowing-records'),
    path('borrowingrecord/<int:pk>/', views.BorrowingRecordDetailView.as_view(), name='borrowing-record-detail'),
    path('borrowingrecord/create/', views.BorrowingRecordCreateView.as_view(), name='borrowing-record-create'),
    path('borrowingrecord/<int:pk>/update/', views.BorrowingRecordUpdateView.as_view(), name='borrowing-record-update'),
    path('borrowingrecord/<int:pk>/delete/', views.BorrowingRecordDeleteView.as_view(), name='borrowing-record-delete'),
    path('borrowingrecord/<int:pk>/return/', views.ReturnBookView.as_view(), name='return-book'),

    # Approve/Reject Borrowing Request (for staff)
    path('borrowingrequest/<int:pk>/<str:action>/', views.ApproveBorrowingRequestView.as_view(), name='borrowing-record-approve'),

    # API routes
    path('api/', include(router.urls)),
]
