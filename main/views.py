from datetime import *
from json import *
from random import *
from math import *

from django.shortcuts import render
from django.http import HttpResponse
from .models import *
from .forms import *

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
            player1.save()
        else:
            player1 = Player.objects.create(deviceID=deviceID, nick=nickname)
        # partner 찾을 때까지 return 하지 않고 기다리기
        last_access = player1.last_access_time.minute
        while True:
            player1 = Player.objects.get(deviceID=deviceID)
            current_time = datetime.now().minute
            delta = current_time-last_access
            if delta:
                player1.is_active = False
                player1.save()
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
                    MotionRecognition.objects.create(player1=player1, player2=player2, channel_number=channel_number, title=title, keyword_index=keyword_index)
                    game_info["title"] = title
                    game_info["channel_number"] = channel_number
                    return HttpResponse(dumps(game_info), content_type='application/json')

    # 더이상 접속하지 않고 게임을 나감
    return HttpResponse(dumps(game_info), content_type='application/json')


def get_total_ready(game):
    ready1 = game.player1.ready
    ready2 = game.player2.ready
    total_ready = 0
    if ready1 >= 1:
        total_ready += 1
    if ready2 >= 1:
        total_ready += 1

    return total_ready


def reset_ready(game):
    player1 = game.player1
    player2 = game.player2
    player1.ready = 0
    player1.save()
    player2.ready = 0
    player2.save()


@method_decorator(csrf_exempt, name='dispatch')
def get_two_ready(request):
    # 파트너 두 명의 레디 버튼을 받으면 키워드를 전송
    #ToDo: CRSF Token
    if request.method == "POST":
        request_time = datetime.now().minute
        form = request.POST
        deviceID = form['deviceID']
        title = form['title']
        channel_number = form['channel_number']
        if Player.objects.filter(deviceID=deviceID).exists():
            print("find player")
            player = Player.objects.get(deviceID=deviceID)
            # Player의 게임에 대한 ready update
            player.ready = 1
            print("update ready")
            player.save()
            # 상대방도 ready를 했는지 확인
            # 1. find game model
            if MotionRecognition.objects.filter(channel_number=channel_number, title=title).exists():
                print("find game")
                # game = MotionRecognition.objects.get(channel_number=channel_number, title=title)
                while True:
                    game = MotionRecognition.objects.get(channel_number=channel_number, title=title)
                    if get_total_ready(game) == 2:
                        print("total ready")
                        keyword = KEYWORD[game.keyword_index]
                        break
                    now_time = datetime.now().minute
                    if now_time - request_time:
                        # game에 해당하는 모든 플레이어
                        game.player1.have_partner = False
                        game.player1.is_active = False
                        game.player2.have_partner = False
                        game.player2.is_active = False
                        game.save()
                        return HttpResponse("no/timeout")
                if not game.send_keyword:
                    game.send_keyword = 1
                    game.save()
                else:
                    game.send_keyword = 2
                    game.save()
                # get recent model and check player's ready until total ready is 2
                # print("total ready", get_total_ready(game))
                game = MotionRecognition.objects.get(channel_number=channel_number, title=title)
                if game.send_keyword == 2:
                    print("second send keyword")
                    reset_ready(game)
                    game.send_keyword = 0
                    game.save()
                return HttpResponse(keyword)
                # 다음 라운드를 위해 ready reset
            else:
                print("there is no game")
                return HttpResponse("no")

    return HttpResponse('no')


# 두 명한테 각각 오나?
# 한 게임 종료에 대해 두 request가 오면 하나는 동작을 처리하고 하나는 결과만 전송해야 함
# 좌표값은 두 명의 플레이어의 디바이스에서 각각 넘어옴 그래서 두 개 받아서 계산해서 넘겨줘야 함
@method_decorator(csrf_exempt, name='dispatch')
def get_result(request):
    print("hi")
    # 앱으로부터 posenet 결과 값을 전송받아 비교 후 점수 전송 'keypoints' key의 array가 서버로 전송됨
    if request.method == 'POST':
        form = request.POST
        player = Player.objects.get(deviceID=form['deviceID'])
        channel_number = form['channel_number']
        title = form['title']
        game = MotionRecognition.objects.get(channel_number=channel_number, title=title)  # channel number가 고유
        # game_round 모델 생성 or get
        print("round: ", form['round'])
        r = int(form['round'])
        if Round.objects.filter(game=game, game_round=r).exists():
            game_round = Round.objects.get(game=game, game_round=r)  # 모델에 저장된 라운드보다 +1된 값, game 모델 라운드는 게임 종료 후 업데이트 된다.
        else:
            game_round = Round.objects.create(game=game, game_round=r)

        print("game_round: ", game_round.game_round)
        print(game_round.result_number)
        print(type(game_round))
        print("================================")
        print(form['result'])
        # json to dict
        result = loads(form['result'])
        # result를 nose를 (50, 20)에 고정시켜 재정렬
        relocate_points(result)
        # player의 result 값 저장
        # pose는 한 게임의 각 라운드 당 player 두 명 것만 존재해야함, (game, game_round, player)에 대해 고유
        pose = PoseEstimation.objects.create(game=game, player=player, game_round=game_round)
        print("================================")
        print(game_round.result_number)
        print(pose.game_round.id)
        save_point(pose, result)
        game_round.result_number += 1
        game_round.save()
        # game_round.result_number 가 2이면 점수 계산
        request_time = datetime.now().minute
        while True:
            now_time = datetime.now().minute
            if now_time - request_time:
                print("time over")
                # game에 해당하는 모든 플레이어
                game.player1.have_partner = False
                game.player1.is_active = False
                game.player2.have_partner = False
                game.player2.is_active = False
                game.save()
                return HttpResponse("no/timeout")
            game_round = Round.objects.get(game=game, game_round=r)
            if game_round.result_number >= 2:
                print("game_round.result_number")
                score = get_score(game, game_round)
                game_round.result_number += 1
                game_round.save()
                if score == -1:
                    print("get score error: too much pose in one round")
                    return HttpResponse('no')
                else:
                    # game_round, keyword_index 갱신
                    if game_round.result_number > 2:
                        game_round.result_number = 2
                        game_round.save()
                        game.game_round += 1
                        game.keyword_index = randint(0, len(KEYWORD))
                        game.save()
                    return HttpResponse(score)
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


# result part별로 point 모델 생성해서 pose에 foreignkey
def save_point(pose, result):
    i = 0
    for value in result:
        x = value['x']
        y = value['y']
        Point.objects.create(pose=pose, part=i, x=x, y=y)
        i+=1


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


def get_score(game, game_round):
    print("11111")
    pose = PoseEstimation.objects.filter(game=game, game_round=game_round)
    if pose.count() == 2:
        print("22222")
        result1 = Point.objects.filter(pose_id=pose[0].id).order_by('part')
        result2 = Point.objects.filter(pose_id=pose[1].id).order_by('part')
        # 두 결과의 각 점의 L2Distance 구해서 총 거리 합을 바탕으로 점수 배정
        distance = 0
        for i in range(0, 17):
            dx = result2[i].x - result1[i].x
            dy = result2[i].y - result1[i].y
            distance += sqrt(pow(dx, 2) + pow(dy, 2))

        print("distance: ", distance)

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