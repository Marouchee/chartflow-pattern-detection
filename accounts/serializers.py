from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from accounts.models import User
import decimal

class UserCreateSerializer(serializers.ModelSerializer):
    """
    회원가입 API (POST /api/accounts/register/) 용 Serializer
    """
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ["username", "password", "password_confirm"]

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs

    def create(self, validated_data):
        username = validated_data["username"]
        password = validated_data["password"]

        try:
            user = User(username=username)
            user.set_password(password)
            user.balance = decimal.Decimal("100000.00") # 회원가입 시 잔액 100,000 설정

            user.save()
        except ValidationError as e:
            raise serializers.ValidationError(detail=e.messages)
        except Exception as e:
            raise serializers.ValidationError(detail=str(e))
        return user