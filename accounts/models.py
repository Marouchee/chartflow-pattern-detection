from django.contrib.auth.models import AbstractUser
from django.db import models
import decimal

class User(AbstractUser):
    # AbstractUser에 장고의 기본 사용자 필드가 포함되어 있음
    # 회원가입 시 기본 100,000 USDT 지급
    balance = models.DecimalField(
        max_digits=20, #최대 자리수
        decimal_places=8, #사토시에 맞추어 소수점 이하 자리수 8자리로 설정함
        default=decimal.Decimal("100000.00")
    )

    pass

    def __str__(self):
        return self.username