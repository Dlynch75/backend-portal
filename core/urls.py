from django.urls import path
from .views import ApplyPackageView, PackageListView, UserProfileView, UserSignupView, LoginView

urlpatterns = [
    path('signup', UserSignupView.as_view(), name='user_signup'),
    path('login', LoginView.as_view(), name='login'),
    path('profile/update', UserProfileView.as_view(), name='profile_update'),
    path('profile/delete', UserProfileView.as_view(), name='profile_delete'),
    path('package', PackageListView.as_view(), name='get_package'),
    path('package/<int:pk>', ApplyPackageView.as_view(), name='apply_package'),

]
