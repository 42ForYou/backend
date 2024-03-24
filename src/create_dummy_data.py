import random
import django

django.setup()

# pylint: disable=wrong-import-position
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import User, Profile
from game.models import Game, GameRoom, GamePlayer
from friends.models import Friend
from authentication.models import OAuth

# pylint: enable=wrong-import-position


def create_dummy_users(num_users=100):
    for i in range(1, num_users + 1):
        intra_id = "intra_" + str(i)  # 사용자 이름을 숫자로 설정
        email = f"{intra_id}@example.com"
        nickname = f"nick_{intra_id}"

        user = User.objects.create_user(
            intra_id=intra_id,
            username=intra_id,
            email=email,
            password="password",
        )

        Profile.objects.create(
            user=user,
            nickname=nickname,
            email=email,
            avatar="",
            two_factor_auth=False,
        )


def create_friends():
    users = User.objects.exclude(username="admin")

    for i, user_a in enumerate(users):
        for j, user_b in enumerate(users, i + 1):
            status = "friend" if (i + j) % 2 == 0 else "pending"
            Friend.objects.create(
                requester=user_a,
                receiver=user_b,
                status=status,
            )


def create_game_room(num_games=50):
    users = User.objects.exclude(username="admin")[
        :num_games
    ]  # 1부터 30까지의 사용자만 선택

    for i, user in enumerate(users):
        is_tournament = (i + 1) % 3 == 0
        n_players = 4 if is_tournament else 2
        game = Game.objects.create(
            is_tournament=is_tournament,
            game_point=5,
            time_limit=180,
            n_players=n_players,
        )

        GameRoom.objects.create(
            host=user,
            game=game,
            title=f"GameRoom {i + 1}",
            is_playing=False,
            join_players=1,
        )

        profile = Profile.objects.get(user=user)
        GamePlayer.objects.create(
            user=user,
            game=game,
            nickname=profile.nickname,
            rank=0,
        )


def assign_remaining_users_to_games(user_num):
    # 남은 50명의 사용자를 가져옵니다.
    remaining_users = User.objects.exclude(username="admin").order_by("-intra_id")[
        :user_num
    ]

    # 이미 생성된 50개의 게임을 가져옵니다.
    games = Game.objects.all()

    # 게임별로 현재 참가자 수를 추적하기 위한 딕셔너리
    game_players_count = {
        game.game_id: GamePlayer.objects.filter(game=game).count() for game in games
    }

    # 각 게임에 대해 랜덤한 최대 참가자 수 설정 (is_tournament인 경우)
    max_players_for_tournament_games = {
        game.game_id: (
            random.randint(1, game.n_players) if game.is_tournament else game.n_players
        )
        for game in games
    }

    # 남은 사용자를 순회하며 적절한 게임에 할당
    for user in remaining_users:
        for game in games:
            # 현재 게임의 참가자 수가 설정된 랜덤 최대 참가자 수를 넘지 않는 경우에만 추가
            if (
                game_players_count[game.game_id]
                < max_players_for_tournament_games[game.game_id]
            ):
                profile = Profile.objects.get(user=user)
                GamePlayer.objects.create(
                    user=user,
                    game=game,
                    nickname=profile.nickname,
                    rank=0,
                )
                game_room = GameRoom.objects.get(game=game)
                game_room.join_players += 1
                game_room.save()
                # 게임의 참가자 수 업데이트
                game_players_count[game.game_id] += 1
                break  # 현재 사용자에 대한 적절한 게임을 찾았으므로 다음 사용자로 넘어감


def create_jwt():
    users = User.objects.exclude(username="admin")

    for user in users:
        refresh = RefreshToken.for_user(user)
        OAuth.objects.create(
            user=user,
            access_token=str(refresh.access_token),
            refresh_token=str(refresh),
            token_type="JWT",
        )


if __name__ == "__main__":
    print("Creating dummy users and profiles...")
    create_dummy_users(5)  # 기본값으로 100명의 사용자 생성
    create_jwt()
    # create_friends()
    # create_game_room(10)  # 기본값으로 30개의 게임룸 생성
    # assign_remaining_users_to_games(10)
    print("Dummy users and profiles created successfully!")
