from django.db import models
from django.conf import settings

class Wallet(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='wallet'
    )
    balance = models.DecimalField(max_digits=100, decimal_places=2, default=0.00, verbose_name="ยอดเงินคงเหลือ")

    class Meta:
        verbose_name = "กระเป๋าเงิน"
        verbose_name_plural = "กระเป๋าเงินทั้งหมด"

    def __str__(self):
        return f"Wallet of {self.user.username} - ฿{self.balance}"

class WalletTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('DEPOSIT', 'เติมเงิน'),
        ('WITHDRAW', 'ถอนเงิน/ชำระเงิน'),
    )
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=100, choices=TRANSACTION_TYPES, verbose_name="ประเภทรายการ")
    amount = models.DecimalField(max_digits=100, decimal_places=2, verbose_name="จำนวนเงิน")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="เวลาทำรายการ")

    class Meta:
        verbose_name = "ประวัติธุรกรรม"
        verbose_name_plural = "ประวัติธุรกรรมทั้งหมด"