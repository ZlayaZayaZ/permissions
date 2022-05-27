import re

from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from advertisements.filters import AdvertisementFilter
from advertisements.models import Advertisement, FavoritesAdvertisement
from advertisements.permissions import IsOwnerOrReadOnly, Draft
from advertisements.serializers import AdvertisementSerializer, FavoritesAdvertisementSerializer


class AdvertisementViewSet(ModelViewSet):
    """ViewSet для объявлений."""

    queryset = Advertisement.objects.all()
    serializer_class = AdvertisementSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly, ]
    filter_class = AdvertisementFilter

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def get_permissions(self):
        """Получение прав для действий."""

        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsOwnerOrReadOnly(), Draft()]
        return []

    def get_queryset(self):
        """Фильтрация объявлений по создателю и/или статусу."""

        q = Q(draft=False) | Q(draft=True, creator_id=self.request.user.id)
        queryset = Advertisement.objects.filter(q)

        creator = self.request.query_params.get('creator')
        if creator is not None:
            queryset = queryset.filter(creator__id=creator)

        status = self.request.query_params.get('status')
        if status is not None:
            queryset = queryset.filter(status=status)

        return queryset

    @action(detail=False)
    def get_fav_queryset(self, request):
        """Отображение списка избранных объявлений и фильтрация их по статусу."""

        q = Q(draft=False) | Q(draft=True, creator_id=self.request.user.id)
        user = self.request.user
        queryset = user.advertisements.filter(q)

        status = self.request.query_params.get('status')
        if status is not None:
            queryset = queryset.filter(status=status)

        serializer = AdvertisementSerializer(queryset, many=True)

        return Response(serializer.data)


class FavoritesAdvertisementViewSet(ModelViewSet):

    queryset = FavoritesAdvertisement.objects.all()
    serializer_class = FavoritesAdvertisementSerializer
    permission_classes = [IsAuthenticated, Draft]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_permissions(self):
        """Получение прав для действий."""

        if self.action in ["create", "destroy"]:
            return [IsAuthenticated(), Draft()]
        return []

    def destroy(self, request,  *args, **kwargs):
        """Удалеие объявления из списка избранных по номеру объявления."""

        link = str(self.request.path_info)
        list_int = re.findall('\d+', link)
        id_adv = list_int[-1]

        fav_adv = FavoritesAdvertisement.objects.filter(advertisement=id_adv)
        if len(fav_adv) != 0:
            fav_adv.delete()
            return Response({'status': 'Объявление удалено из списка избранных'})

        return Response({'status': 'Объявление не было найдено'})


