from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import Friendship
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, 
    UserSerializer, FriendshipSerializer
)

User = get_user_model()

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login(request):
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        user.is_online = True
        user.save()
        
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def logout(request):
    request.user.is_online = False
    request.user.save()
    return Response({'message': 'Successfully logged out'})

@api_view(['GET'])
def profile(request):
    return Response(UserSerializer(request.user).data)

@api_view(['GET'])
def search_users(request):
    query = request.GET.get('q', '')
    if len(query) < 2:
        return Response({'results': []})
    
    users = User.objects.filter(
        Q(username__icontains=query) | Q(email__icontains=query)
    ).exclude(id=request.user.id)[:10]
    
    return Response({
        'results': UserSerializer(users, many=True).data
    })

@api_view(['POST'])
def add_friend(request):
    friend_id = request.data.get('friend_id')
    try:
        friend = User.objects.get(id=friend_id)
        if friend == request.user:
            return Response({'error': 'Cannot add yourself as friend'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        friendship, created = Friendship.objects.get_or_create(
            user=request.user, friend=friend
        )
        if not created:
            return Response({'error': 'Already friends'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Create reverse friendship
        Friendship.objects.get_or_create(user=friend, friend=request.user)
        
        return Response({'message': 'Friend added successfully'})
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, 
                      status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def friends_list(request):
    friendships = Friendship.objects.filter(user=request.user)
    return Response(FriendshipSerializer(friendships, many=True).data)