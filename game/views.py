from rest_framework.views import APIView
from rest_framework.decorators import api_view


from asgiref.sync import sync_to_async
from rest_framework.response import Response

from rest_framework import status

from .models import Game, GameRoom
from .serializers import GameSerializer, GameRoomSerializer, GameRoomJoinSerializer
from time import sleep


def wrap_data(serializer):
    return {"data": serializer.data}


@sync_to_async
@api_view(["GET", "POST", "DELETE"])
def game_rooms(request, room_id=None):
    if request.method == "GET":
        if room_id:
            try:
                game_room = GameRoom.objects.select_related("game_id").get(pk=room_id)
                serializer = GameRoomJoinSerializer(game_room)
            except GameRoom.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            game_rooms = GameRoom.objects.select_related("game_id").all()
            serializer = GameRoomJoinSerializer(game_rooms, many=True)
        return Response(wrap_data(serializer), status=status.HTTP_200_OK)

    elif request.method == "POST":
        if room_id:
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
        serializer = GameSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            # return Response(wrap_data(serializer), status=status.HTTP_201_CREATED)
            serializer = GameRoomSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(wrap_data(serializer), status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == "DELETE":
        if room_id:
            try:
                game_room = GameRoom.objects.get(pk=room_id)
                if game_room.status == "waiting":
                    game = Game.objects.get(pk=game_room.game_id)
                    game.delete()
                    return Response(status=status.HTTP_204_NO_CONTENT)
                game_room.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except GameRoom.DoesNotExist or Game.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
