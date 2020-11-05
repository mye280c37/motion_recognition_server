from json import *
from random import *
from math import *

from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Q
from .models import *


def find_partner(request):
    # 사용자가 닉네임을 입력하고 들어왔을 때 동시 접속자에 안에서 파트너를 찾아 방 개설
    if request.method == "POST":
        form = request.POST
        nickname = form['nickname']
        sig = form['sig']
        # ToDo: nickname 겹치는 건 고려 안해도 되는가
        if sig == 'ok':
            if Player.objects.filter(nick='nickname').exists():
                player1 = Player.objects.get(nick=nickname)
            else:
                player1 = Player.objects.create(nick=nickname)
            # partner가 없는 기존의  player 정보 가져오기
            player_query = Player.objects.filter(have_partner=False).exclude(nick=nickname)
            num_player = player_query.count()
            # 기존의 player 안에서 partner가 될 대상 랜덤하게 고르기
            if num_player > 0:
                partner_index = randint(0, num_player - 1)
                player2_pk = player_query[partner_index].pk
                player2 = Player.objects.get(pk=player2_pk)
                MotionRecognition.create(player1=player1, player2=player2)
                player1.have_partner = True
                player2.have_partner = True
                channel_number = randint(1, 100)
                player1.save()
                player2.save()
                return HttpResponse(channel_number)
            return HttpResponse("no")
        else:
            # 더이상 접속하지 않고 게임을 나감
            Player.objects.get(nick=nickname).delete()
            return HttpResponse('exit')




def get_two_ready(request):
    # 파트너 두 명의 레디 버튼을 받으면 키워드를 전송
    if request.method == "POST":
        form = request.POST
        nickname = form['nickname']
        if MotionRecognition.objects.filter(Q(nick1=nickname) | Q(nick2=nickname)).exists():
            ready = MotionRecognition.objects.get(Q(nick1=nickname) | Q(nick2=nickname)).ready
            if ready == 2:
                return HttpResponse('keyword')
            else:
                ready += 1

    return HttpResponse('no')


def get_result(request):
    # 앱으로부터 posenet 결과 값을 전송받아 비교 후 점수 전송 'keypoints' key의 array가 서버로 전송됨
    if request.method == 'POST':
        form = request.POST
        player1 = Player.objects.get(nick=form['nick1'])
        player2 = Player.objects.get(nick=form['nick2'])
        game = MotionRecognition.objects.get(player1=player1, player2=player2)
        # json to dict
        result1 = loads(form['result1'])
        result2 = loads(form['result2'])
        relocate_points(result1)
        relocate_points(result2)
        # game 정보 업데이트
        round_score = get_score(result1, result2)
        game.score += round_score
        game.round += 1
        game.save()
        # round 판단 후 점수 혹은 랭킹 return
        # TODO: rank view를 따로 만들어야 할지
        if game.round == 7:
            # when game over, get total_score
            rank = []
            # ranking 정보 점수 내림차순 정렬
            all_rank_query = MotionRecognition.objects.all().order_by('score')
            for rank_query in all_rank_query:
                rank_dict = {'nickname1': rank_query.nick1, 'nickname2': rank_query.nick2,
                             'score': rank_query.score}
                rank.append(rank_dict)
            return HttpResponse(dumps(rank), content_type='application/json')
        else:
            return HttpResponse(str(round_score))

    return HttpResponse('no')


def relocate_points(result):
    # 서버로 들어오 result를 nose 값을 고정해서 nose 기준으로 재배치
    dx = dy = 0
    for key, value in result:
        if value['part'] != 'nose':
            value['x'] = value['x'] * 100 + dx
            value['y'] = value['y'] * 100 + dy
        else:
            dx = 50 - value['x'] * 100
            dy = 20 - value['y'] * 100
            value['x'] = 50
            value['y'] = 20


def get_score(result1, result2):
    distance = 0
    for key, value in result1:
        dx = result2[key]['x'] - value['x']
        dy = result2[key]['y'] - value['y']
        distance += sqrt(pow(dx, 2) + pow(dy, 2))

    # distance 바탕으로 점수 산출
    if distance < 170:
        score = 100
    elif distance < 340:
        score = 90
    elif distance < 510:
        score = 80
    elif distance < 680:
        score = 70
    elif distance < 850:
        score = 60
    elif distance < 1020:
        score = 50
    else:
        score = 0
    return score


# 없앨 수도 있음
def send_rank(request):
    # when game over, get total_score
    rank = []
    # ranking 정보 점수 내림차순 정렬
    all_rank_query = MotionRecognition.objects.all().order_by('score')
    for rank_query in all_rank_query:
        rank_dict = {'nickname1': rank_query.nick1, 'nickname2': rank_query.nick2, 'score': rank_query.score}
        rank.append(rank_dict)
    return HttpResponse(dumps(rank), content_type='application/json')
