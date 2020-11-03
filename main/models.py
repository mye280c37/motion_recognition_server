from django.db import models


class Player(models.Model):
    nick = models.CharField(max_length=10)
    have_partner = models.BooleanField(default=False)


class MotionRecognition(models.Model):
    player1 = models.ForeignKey(Player, related_name='player1', on_delete=models.DO_NOTHING)
    player2 = models.ForeignKey(Player, related_name='player2', on_delete=models.DO_NOTHING)
    score = models.IntegerField(default=0)
    round = models.IntegerField(default=0)
    channel_number = models.IntegerField(default=0)
    ready = models.IntegerField(default=0)