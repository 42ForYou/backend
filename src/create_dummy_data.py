import os
import django

# Django 설정을 스크립트에서 사용하기 위해 환경 설정
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pong.settings")
django.setup()

from accounts.models import User, Profile
from game.models import Game, GameRoom, GamePlayer
from friends.models import Friend

# 정해진 첫 번째 이름의 리스트를 정의합니다.
first_names = [
    "James",
    "Olivia",
    "Michael",
    "Emma",
    "Robert",
    "Ava",
    "John",
    "Sophia",
    "David",
    "Isabella",
    "Chris",
    "Mia",
    "Daniel",
    "Charlotte",
    "Joseph",
    "Amelia",
    "William",
    "Evelyn",
    "Matthew",
    "Harper",
    "Benjamin",
    "Liam",
    "Samuel",
    "Lucas",
    "Henry",
    "Owen",
    "Dylan",
    "Gabriel",
    "Aaron",
    "Elijah",
    "Nora",
    "Scarlett",
    "Zoe",
    "Lily",
    "Grace",
    "Victoria",
    "Riley",
    "Madison",
    "Leah",
    "Hazel",
]


def create_dummy_users(num_users=10):
    for i in range(num_users):
        # 이름 배열의 크기로 순서를 반복합니다.
        name_index = i % len(first_names)  # 배열의 길이로 나눈 나머지를 사용
        first_name = first_names[name_index]
        intra_id = f"{first_name.lower()}"

        email = f"{intra_id}@example.com"
        nickname = f"nick_{intra_id}"

        user = User.objects.create_user(
            intra_id=intra_id,
            username=intra_id,  # 여기서는 username도 intra_id와 동일하게 설정합니다.
            email=email,
            password="password",
        )

        Profile.objects.create(
            user=user,
            nickname=nickname,
            email=email,
            avatar=f"default.jpg",
            two_factor_auth=False,  # 예시를 단순화하기 위해 항상 False로 설정
        )


def create_friends():
    users = User.objects.all()

    for i in range(len(users)):
        if users[i].username == "admin":
            continue
        for j in range(i + 1, len(users)):
            if users[j].username == "admin":
                continue
            status = "pending"
            if (j + i) % 2 == 0:
                status = "friend"
            friend = Friend.objects.create(
                requester=users[i],
                receiver=users[j],
                status=status,
            )


def create_game_room(num_games=10):
    users = User.objects.all()

    for i in range(len(users)):
        if users[i].username == "admin":
            continue
        is_tournament = True
        if i % 2 == 0:
            is_tournament = False
        game = Game.objects.create(
            is_tournament=is_tournament,
            game_point=5,
            time_limit=180,
            n_players=4,
        )

        game_room = GameRoom.objects.create(
            host=users[i],
            game=game,
            title=f"GameRoom {i}",
            is_playing=False,
            join_players=1,
        )

        profile = Profile.objects.get(user=users[i])

        player = GamePlayer.objects.create(
            user=users[i],
            game=game,
            nickname=profile.nickname,
            rank=0,
        )


if __name__ == "__main__":
    print("Creating dummy users and profiles...")
    create_dummy_users(40)  # 사용자와 프로필 생성을 위한 수를 조정할 수 있습니다.
    create_friends()
    create_game_room(40)
    for i, user in enumerate(User.objects.all().order_by("intra_id")):
        print(f"{i}. {user.username}")
    print("Dummy users and profiles created successfully!")
