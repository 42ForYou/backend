import os
import django

# Django 설정을 스크립트에서 사용하기 위해 환경 설정
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pong.settings")
django.setup()

from accounts.models import User, Profile

# 정해진 첫 번째 이름의 리스트를 정의합니다.
first_names = ["James", "John", "Robert", "Michael", "William"]


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
            avatar=f"avatar_{intra_id}.jpg",
            two_factor_auth=False,  # 예시를 단순화하기 위해 항상 False로 설정
        )


if __name__ == "__main__":
    print("Creating dummy users and profiles...")
    create_dummy_users(5)  # 사용자와 프로필 생성을 위한 수를 조정할 수 있습니다.
    for i, user in enumerate(User.objects.all().order_by("intra_id")):
        print(f"{i}. {user.username}")
    print("Dummy users and profiles created successfully!")
