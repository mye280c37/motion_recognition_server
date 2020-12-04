from datetime import *
from json import *
from random import *
from math import *

from django.shortcuts import render
from django.http import HttpResponse
from .models import *

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


# flutter로 고유 기기 아이디 받아와서 쓰기 -> 닉네임 중복 issue 고려 않기
# 처음 player 생성할 때 기기 아이디랑 닉네임 받아와서 플레이어 구별을 device id로 수정하기

# 동시간대에 들어온 사람들에게 같은 사람을 걸어주는 issue
# 처음에 짝지을 때 거르거나 짝 짓고 나서 확인하거나

# ready가 안 들어온다는 신호 보내줘야 함, 상대방이 ready 안 보내면 no 보내는데 이 보내는 걸 카운트해서 일정 횟수 이상 되면 상대방이 나갔다고 판단

KEYWORD = ["soccer", "basketball", "football", "basketball", "table tennis", "bowling", "billiards", "tennis", "hockey", "badminton", "rugby", "softball", "gymnastics", "swimming", "diving", "yacht", "surf", "marathon", "sprint", "throw", "cycling", "ski", "snowboard", "skate", "horseback riding", "Judo", "Taekwondo", "boxing", "fencing", "shooting", "Archery", "lion", "giraffe", "bear", "pandas", "otter", "fur seal", "monkey", "cow", "dog", "cat", "octopus", "Tyrannosaurus rex", "pterosaurs", "Spider Man", "Captin America", "Iron Man", "Thor", "Hulk", "Nick Fury"]

def name(request):
    print("ok")
    return render(request, 'main.html')


@method_decorator(csrf_exempt, name='dispatch')
def find_partner(request):
    request_time = datetime.now()
    game_info = {"title": "no",
                 "channel_number": 0}
    # 사용자가 닉네임을 입력하고 들어왔을 때 동시 접속자에 안에서 파트너를 찾아 방 개설
    if request.method == "POST":
        form = request.POST
        nickname = form['nickname']
        deviceID = form['deviceID']
        # Player 정보 확인
        if Player.objects.filter(deviceID=deviceID):
            player1 = Player.objects.get(deviceID=deviceID)
            player1.nick = nickname
            player1.is_active = True
            player1.have_partner = False
            player1.ready = False
            player1.result = False
            player1.save()
        else:
            player1 = Player.objects.create(deviceID=deviceID, nick=nickname)
        # partner 찾을 때까지 return 하지 않고 기다리기
        while True:
            player1 = Player.objects.get(deviceID=deviceID)
            current_time = datetime.now()
            delta = current_time-request_time
            if delta.total_seconds() > 30:
                player1.is_active = False
                player1.save()
                print("there is no partner")
                return HttpResponse("no/timeout")
            if player1.have_partner:
                game = MotionRecognition.objects.filter(player2=player1).order_by('-created_time')
                game_info["title"] = game[0].title
                game_info["channel_number"] = game[0].channel_number
                return HttpResponse(dumps(game_info), content_type='application/json')
            else:
                # partner가 없는 기존의  player 정보 가져오기
                player_query = Player.objects.filter(is_active=True, have_partner=False).exclude(deviceID=deviceID)
                num_player = player_query.count()
                # 기존의 player 안에서 partner가 될 대상 랜덤하게 고르기
                if num_player > 0:
                    partner_index = randint(0, num_player - 1)
                    player2_pk = player_query[partner_index].pk
                    player2 = Player.objects.get(pk=player2_pk)
                    player1.have_partner = True
                    player2.have_partner = True
                    channel_number = randint(1, 500)
                    player1.save()
                    player2.save()
                    title = str(nickname) + " & " + str(player2.nick)
                    keyword_index = randint(0, len(KEYWORD) - 1)
                    MotionRecognition.objects.create(player1=player1, player2=player2, channel_number=channel_number, title=title, keyword_index=keyword_index, keyword_history=str(keyword_index))
                    game_info["title"] = title
                    game_info["channel_number"] = channel_number
                    return HttpResponse(dumps(game_info), content_type='application/json')

    # 더이상 접속하지 않고 게임을 나감
    return HttpResponse(dumps(game_info), content_type='application/json')


@method_decorator(csrf_exempt, name='dispatch')
def get_two_ready(request):
    # 파트너 두 명의 레디 버튼을 받으면 키워드를 전송
    if request.method == "POST":
        request_time = datetime.now()
        form = request.POST
        deviceID = form['deviceID']
        title = form['title']
        channel_number = form['channel_number']
        # 1. update player's ready
        player = Player.objects.get(deviceID=deviceID)
        player.ready = True
        #   * reset player's result
        player.result = False
        player.save()
        # 2. find game model
        if MotionRecognition.objects.filter(channel_number=channel_number, title=title).count() == 1:
            game = MotionRecognition.objects.get(channel_number=channel_number, title=title)
            player1_pk = game.player1.pk
            player2_pk = game.player2.pk
            print("find game")
            while True:
                current_time = datetime.now()
                delta = current_time-request_time
                game = MotionRecognition.objects.get(channel_number=channel_number, title=title)
                player1 = Player.objects.get(pk=player1_pk)
                player2 = Player.objects.get(pk=player2_pk)
                if player1.ready and player2.ready:
                    break
                # if there is no another ready during 1 minute
                elif delta.total_seconds() > 30:
                    # reset all game player's state
                    all_player = [player1, player2]
                    for each_player in all_player:
                        each_player.have_partner = False
                        each_player.is_active = False
                        each_player.ready = False
                        each_player.result = False
                        each_player.save()
                    print("there is no more ready")
                    return HttpResponse("no/timeout")
            # when both get ready
            keyword = KEYWORD[game.keyword_index]
            return HttpResponse(keyword)
        elif MotionRecognition.objects.filter(channel_number=channel_number, title=title).count() == 0:
            print("there is no game")
            return HttpResponse('no')
        else:
            print("there is too much game model")
            return HttpResponse('no')
    return HttpResponse('no')


# 두 명한테 각각 오나?
# 한 게임 종료에 대해 두 request가 오면 하나는 동작을 처리하고 하나는 결과만 전송해야 함
# 좌표값은 두 명의 플레이어의 디바이스에서 각각 넘어옴 그래서 두 개 받아서 계산해서 넘겨줘야 함
@method_decorator(csrf_exempt, name='dispatch')
def get_result(request):
    # 앱으로부터 posenet 결과 값을 전송받아 비교 후 점수 전송 'keypoints' key의 array가 서버로 전송됨
    if request.method == 'POST':
        request_time = datetime.now()
        form = request.POST
        # get player model
        player = Player.objects.get(deviceID=form['deviceID'])
        # reset player's ready
        player.ready = False
        player.save()
        # find game model
        channel_number = form['channel_number']
        title = form['title']
        if MotionRecognition.objects.filter(channel_number=channel_number, title=title).count():
            game = MotionRecognition.objects.get(channel_number=channel_number, title=title)
            # 1. update round
            game.game_round = form['round']
            game.save()
            # 2. save result in point models
            #   1) json to dict
            result = loads(form['result'])
            #   2) result를 nose를 (50, 20)에 고정시켜 재정렬
            relocate_points(result)
            #   4) save relocated scores in point models
            is_save = save_point(game, player, result)
            if is_save:
                #   5) change player's result flag
                player.result = True
                player.save()
            else:
                print("fail to save points")
                return HttpResponse('no')
            # wait until all player's result becomes true
            game = MotionRecognition.objects.get(channel_number=channel_number, title=title)
            player1_pk = game.player1.pk
            player2_pk = game.player2.pk
            while True:
                current_time = datetime.now()
                delta = current_time - request_time
                game = MotionRecognition.objects.get(channel_number=channel_number, title=title)
                player1 = Player.objects.get(pk=player1_pk)
                player2 = Player.objects.get(pk=player2_pk)
                if player1.result and player2.result:
                    break
                    # if there is no another result during 1 minute
                elif delta.total_seconds() > 30:
                    # reset all game player's state
                    player1 = game.player1
                    player2 = game.player2
                    all_player = [player1, player2]
                    for each_player in all_player:
                        each_player.have_partner = False
                        each_player.is_active = False
                        each_player.ready = False
                        each_player.result = False
                        each_player.save()
                    print("there is no more result")
                    return HttpResponse("no/timeout")
            # when both send result``````````````````````````````````````````````````````````````````````````````
            # 3. get score and save in game model
            score = get_score(game)
            #   score must be saved only one time and also keyword_index
            if game.player1.pk == player.pk:
                keyword_index = randint(0, len(KEYWORD) - 1)
                keyword_history_list = game.keyword_history.split()
                keyword_history_list = list(map(int, keyword_history_list))
                while keyword_index in keyword_history_list:
                    keyword_index = randint(0, len(KEYWORD) - 1)
                game.keyword_index = keyword_index
                game.keyword_history += " "
                game.keyword_history += str(keyword_index)
                game.score += score
                game.save()
            return HttpResponse(score)
        elif MotionRecognition.objects.filter(channel_number=channel_number, title=title).count() == 0:
            print("there is no game")
            return HttpResponse('no')
        else:
            print("there is too much game model")
            return HttpResponse('no')
    return HttpResponse('no')


'''
result 양식
{
    0: {
            'score' : 0.895,
            'part': 'nose',
            'x': 50,
            'y': 20
        },
    1: {
            'score': 0.845,
            ...
}
'''


# result part별로 point 모델 생성해서 game, player에 foreignkey
def save_point(game, player, result):
    i = 0
    # create or get Point model and save points
    for value in result:
        if Point.objects.filter(game=game, player=player, part=i).count() == 1:
            point = Point.objects.get(game=game, player=player, part=i)
        elif Point.objects.filter(game=game, player=player, part=i).count() == 0:
            point = Point.objects.create(game=game, player=player, part=i)
        else:
            return False
        point.x = value['x']
        point.y = value['y']
        point.save()
        i += 1
    return True


def relocate_points(result):
    # 서버로 들어온 result를 nose 값을 고정해서 nose 기준으로 재배치
    dx = dy = 0
    for value in result:
        if value['part'] != 'nose':
            value['x'] = value['x'] * 100 + dx
            value['y'] = value['y'] * 100 + dy
        else:
            dx = 50 - value['x'] * 100
            dy = 20 - value['y'] * 100
            value['x'] = 50
            value['y'] = 20


def get_score(game):
    print("11111")
    player1 = game.player1
    player2 = game.player2
    print("22222")
    # get each player's all points query
    result1 = Point.objects.filter(game=game, player=player1).order_by('part')
    result2 = Point.objects.filter(game=game, player=player2).order_by('part')
    if result1.count() and result2.count():
        # get L2Distance of each points of two players and add to total distance
        distance = 0
        for i in range(0, 17):
            dx = result2[i].x - result1[i].x
            dy = result2[i].y - result1[i].y
            distance += sqrt(pow(dx, 2) + pow(dy, 2))

        print("distance: ", distance)

        # distance 바탕으로 점수 산출
        if distance < 50:
            score = 100
        elif distance < 100:
            score = 90
        elif distance < 200:
            score = 80
        elif distance < 350:
            score = 70
        elif distance < 500:
            score = 60
        elif distance < 650:
            score = 50
        elif distance < 800:
            score = 40
        elif distance < 950:
            score = 30
        else:
            score = 0
        return score
    else:
        return -1


def send_rank(request):
    # when game over, get total_score
    rank = []
    if request.method == "GET":
        # ranking 정보 점수 내림차순 정렬
        all_rank_query = MotionRecognition.objects.filter(game_round=7).order_by('-score')
        for rank_query in all_rank_query:
            rank_dict = {'title': rank_query.title, 'score': rank_query.score}
            rank.append(rank_dict)
    return HttpResponse(dumps(rank), content_type='application/json')


'''
rank = [
            {
                'title': 'Tom&Peter',
                'score': 690,
            },
            {
                'title': 'Tom&James',
                'score': 500
            },
            {
                'title': 'Lily&Anne',
                'score': 440
            }
        ]
'''