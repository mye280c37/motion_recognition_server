from django.db import models


class MotionRecognition(models.Model):
    nick1 = models.CharField(max_length=10)
    nick2 = models.CharField(max_length=10)
    score = models.IntegerField(null=True)
    round = models.IntegerField()
    channel_number = models.IntegerField()