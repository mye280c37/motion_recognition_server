from django import forms
from . import models

# class ResultForm(forms.Form):
#     result1 = forms.JSONField()
#     result2 = forms.JSONField(decoder='dict')

class ReadyForm(forms.Form):
    nickname = forms.CharField(max_length=20)
    channelNumber = forms.IntegerField()