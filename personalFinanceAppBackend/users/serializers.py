from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]

        extra_kwargs = {"password": {"write_only": True, "required": True}}

        def create(self, validated_data):
            user = User.objects.create_user(**validated_data)
            return user

        def update(self, instance, validated_data):
            if "password" in validated_data:
                password = validated_data.pop("password", None)
                instance.set_password(password)
            return super().update(instance, validated_data)
