from json import *
from random import *

from django.shortcuts import render
from django.http import HttpResponse
from .models import *

accessor_dict = {}

def find_partner(request):
    # 사용자가 닉네임을 입력하고 들어왔을 때 동시 접속자에 안에서 파트너를 찾아 방 개설
    # 동시 접속 기준: 연속 4번의 신호
    # return: channel_number
    find_partner = False
    if request.method == "POST":
        form = request.POST
        nickname = form['nickname']
        # ToDo: nickname 겹치는 이슈는 고려 안해도 되는가
        if nickname in accessor_dict:
            accessor_dict[nickname] += 1
        else:
            accessor_dict[nickname] = 1

        if accessor_dict[nickname] >= 4:
            while not find_partner:
                nickname_list = []
                # val이 4인 닉네임만 nickname_list에 담기
                for key, val in accessor_dict:
                    if val == 4:
                        nickname_list.append(key)
                tmp = randint(1, len(nickname_list))
                while(nickname == nickname_list[tmp]):
                    tmp = randint(1, len(nickname_list))
                partner = nickname_list[tmp]
                #요청 리스트와 파트너 명으로 모델 만들기
                #모델 만들어지면 find_partner 1로
                find_partner = True

    if find_partner:
        channel_number = randint(1, 100)
        return HttpResponse(channel_number)

    return HttpResponse("no")


def get_two_ready():
    # 파트너 두 명의 레디 버튼을 받으면 키워드를 전송
    ready = 0
    if ready == 2:
        return HttpResponse('keyword')
    return HttpResponse('no')


def get_result(request):
    # 앱으로부터 posenet 결과 값을 전송받아 비교 후 점수 전송
    if request.method == 'POST':
        form = request.POST
        # json to dict
        result1 = modify_values(loads(form['result1']))
        result2 = modify_values(loads(form['result2']))
        score = get_score(result1, result2)
        return HttpResponse(score)
    else:
        return HttpResponse('no')


def modify_values(result):
    target = {}
    nose_value_x = result['0']['x']
    nose_value_y = result['0']['y']
    target['nose'] = {}
    target['nose']['x'] = target['nose']['y'] = 0
    for key, value in result:
        part = value['part']
        target[part] = {}
        target[part]['x'] = value['x'] - nose_value_x
        target[part]['y'] = value['y'] - nose_value_y
    return target


def get_score(result1, result2):
    score = 0
    return score


def send_rank(request):
    # when game over, get total_score

    rank = []
    # ranking 정보 점수 내림차순 정렬
    all_rank_query = MotionRecognition.objects.all().order_by('score')
    for rank_query in all_rank_query:
        rank_dict = {'nickname1': rank_query.nick1, 'nickname2': rank_query.nick2, 'score': rank_query.score}
        rank.append(rank_dict)
    return HttpResponse(dumps(rank), content_type='application/json')
