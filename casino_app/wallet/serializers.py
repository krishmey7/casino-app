from rest_framework import serializers


class WalletActionSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, allow_blank=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
