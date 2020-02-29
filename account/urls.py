from django.urls import path, re_path
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView

from account.views import UserPost, UserPut, CurrentUserView, reset_password_request, reset_password_confirmed

urlpatterns = [
    path('', UserPost.as_view(), name='user_post'),
    path('token/', TokenObtainPairView.as_view(),
         name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(),
         name='token_refresh'),
    path('<int:pk>/', UserPut.as_view(), name='user_put'),
    path('user/', CurrentUserView.as_view(), name='current_user'),
    path('reset_password/', reset_password_request, name='reset_password_request'),
    re_path(r'auth/reset_password_confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/', reset_password_confirmed,
            name='reset_password_confirmed'),
]

urlpatterns = format_suffix_patterns(urlpatterns)
