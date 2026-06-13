from rest_framework import serializers
from .models import CVUpgradeOrder


class CVUpgradeOrderSerializer(serializers.ModelSerializer):
    share_url = serializers.SerializerMethodField()
    can_pay = serializers.SerializerMethodField()

    class Meta:
        model = CVUpgradeOrder
        fields = [
            'id', 'token', 'candidate_name', 'candidate_email', 'status',
            'amount', 'currency', 'paid_at', 'created_at', 'share_url', 'can_pay',
        ]

    def get_share_url(self, obj):
        from .cv_upgrade import build_share_url
        return build_share_url(obj.token)

    def get_can_pay(self, obj):
        return obj.status == 'pending_payment'
