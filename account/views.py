from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from account.models import CustomUser
from account.permissions import IsSelf, IsAdmin
from account.serializers import UserSerializer
from backend.settings import FRONTEND_URL

User = get_user_model()


class UserPost(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


class UserPut(generics.UpdateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsSelf | IsAdmin]


class CurrentUserView(APIView):
    # noinspection PyMethodMayBeStatic
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([])
def reset_password_request(request):
    email = request.data.get('email', None)
    if email is None:
        return HttpResponse('E-mail address required', status=400)

    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        user = None
    if user is None:
        return HttpResponse('E-mail address not found', status=400)

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    link = reverse('reset_password_confirmed', kwargs={'uidb64': uid, 'token': token})

    # TODO: Send e-mail (requires appropriate e-mail service configuration in settings)
    # send_password_reset_confirmation_email(email, f'{BASE_URL}{link}')
    return HttpResponse('E-mail sent successfully', status=200)


def reset_password_confirmed(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64)
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        password = CustomUser.objects.make_random_password()
        user.set_password(password)
        user.save()

        # TODO: Send e-mail (requires appropriate e-mail service configuration in settings)
        # send_password_reset_done_email(user.email, password)
        return HttpResponseRedirect(f'{FRONTEND_URL}/')
    return HttpResponseRedirect(f'{FRONTEND_URL}/')
