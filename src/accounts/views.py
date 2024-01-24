from rest_framework import mixins, viewsets
from .models import Profile
from .serializers import ProfileSerializer


class ProfileViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    lookup_field = "user__intra_id"
    lookup_url_kwarg = "user"
