from django.db import models


class Player(models.Model):
    nick = models.CharField(max_length=10, null=True)
    deviceID = models.CharField(max_length=20, default="hello")
    is_active = models.BooleanField(default=True)
    have_partner = models.BooleanField(default=False)
    last_access_time = models.DateTimeField(auto_now=True)
    ready = models.BooleanField(default=False)
    result = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.deviceID}({self.nick})"


class MotionRecognition(models.Model):
    title = models.CharField(max_length=20)
    created_time = models.DateTimeField(auto_now_add=True)
    player1 = models.ForeignKey(Player, related_name='player1', on_delete=models.CASCADE)
    player2 = models.ForeignKey(Player, related_name='player2', on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    game_round = models.IntegerField(default=0)
    channel_number = models.IntegerField(default=0)
    keyword_index = models.IntegerField(default=0)
    keyword_history = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.game_round}: {self.title}"


class Point(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    game = models.ForeignKey(MotionRecognition, on_delete=models.CASCADE)
    part = models.IntegerField()
    x = models.IntegerField(default=0)
    y = models.IntegerField(default=0)

    def __str__(self):
        return f"point for player {self.player}"

