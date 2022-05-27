from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from advertisements.models import Advertisement, AdvertisementStatusChoices, FavoritesAdvertisement


class UserSerializer(serializers.ModelSerializer):
    """Serializer для пользователя."""

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name',
                  'last_name',)


class AdvertisementSerializer(serializers.ModelSerializer):
    """Serializer для объявления."""

    creator = UserSerializer(
        read_only=True,
    )

    class Meta:
        model = Advertisement
        fields = ('id', 'title', 'description', 'creator',
                  'status', 'created_at', 'draft', )
        read_only_fields = ['creator', ]

    def create(self, validated_data):
        """Метод для создания"""

        # Простановка значения поля создатель по-умолчанию.
        # Текущий пользователь является создателем объявления
        # изменить или переопределить его через API нельзя.
        # обратите внимание на `context` – он выставляется автоматически
        # через методы ViewSet.
        # само поле при этом объявляется как `read_only=True`

        validated_data["creator"] = self.context["request"].user
        return super().create(validated_data)

    def validate(self, data):
        """Метод для валидации. Вызывается при создании и обновлении."""

        # Проверка, что у пользователя открыто менее 10 объявлений
        context = self.context["request"]
        if context.user.is_staff is True:
            return data
        elif Advertisement.objects.filter(creator=context.user, status=AdvertisementStatusChoices.OPEN).count() >= 3:
            if context.method == 'POST' or context.data['status'] == 'OPEN':
                raise ValidationError('Лимит открытых объявлений исчерпан.')

        return data


class FavoritesAdvertisementSerializer(serializers.ModelSerializer):
    """Serializer для избранных объявления."""

    user = UserSerializer(
        read_only=True,
    )

    class Meta:
        model = FavoritesAdvertisement
        fields = ('id', 'user', 'advertisement', )
        read_only_fields = ['user', ]

    def create(self, validated_data):
        """Метод для создания"""

        FavoritesAdvertisement.objects.get_or_create(user_id=self.context["request"].user.id, **validated_data)

        return validated_data

    def validate(self, data):
        """Метод для валидации. Вызывается при создании и обновлении."""

        # Проверка, что пользователь не является автором объявления
        context = self.context["request"]
        if context.user.id == Advertisement.objects.get(pk=context.data['advertisement']).creator_id:
            raise ValidationError('Нельзя сохранить собственное объявление в избранном.')

        return data



