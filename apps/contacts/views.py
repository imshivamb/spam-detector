from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from .models import Contact
from .serializers import ContactSerializer
from apps.spam.models import SpamReport

class ContactViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ContactSerializer
    
    def get_queryset(self):
        return Contact.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def destroy(self, request, pk=None):  
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {'message': 'Contact deleted successfully'},
            status=status.HTTP_200_OK
        )

    def put(self, request):
        return self.update(request)

    def patch(self, request):
        return self.partial_update(request)
    
    @action(detail=False, methods=['get'], url_path='phone/(?P<phone_number>[^/.]+)')
    def by_phone_number(self, request, phone_number=None):
        contact = self.get_queryset().filter(phone_number=phone_number).first()
        if contact:
            serializer = self.get_serializer(contact)
            data = serializer.data
            data['spam_likelihood'] = SpamReport.get_spam_likelihood(phone_number)
            return Response(data)
        return Response(
            {'error': 'Contact not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    @action(detail=False, methods=['post'], url_path='bulk-create')
    def bulk_create(self, request):
        serializer = self.get_serializer(data=request.data, many=True)
        if serializer.is_valid():
            contacts = serializer.save(user=self.request.user)
            return Response(
                self.get_serializer(contacts, many=True).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)