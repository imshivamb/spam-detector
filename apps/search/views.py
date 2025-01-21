from django.db.models import Q, Value, CharField, F
from django.db import models
from django.db.models.functions import Concat
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.paginator import Paginator
from django.core.cache import cache
from django.contrib.postgres.search import TrigramSimilarity
from django.contrib.postgres.search import SearchRank, SearchQuery
from django.db.models import Prefetch

from apps.users.models import User
from apps.contacts.models import Contact
from apps.spam.models import SpamReport
from .serializers import SearchResultSerializer, PhoneSearchResultSerializer

class SearchViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    page_size = 20
    
    def _paginate_results(self, request, queryset):
        """Helper method to handle pagination"""
        page = request.query_params.get('page', 1)
        try:
            page = int(page)
            if page < 1:
                page = 1
        except ValueError:
            page = 1

        paginator = Paginator(queryset, self.page_size)
        page_obj = paginator.get_page(page)

        return {
            'results': page_obj.object_list,
            'total_pages': paginator.num_pages,
            'current_page': page,
            'total_results': paginator.count
        }
    
    @action(detail=False, methods=['get'], url_path='name')
    def search_by_name(self, request):
        """
        Search by name in both users and contacts with proper prioritization
        """
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response(
                {'error': 'Search query is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        cache_key = f'name_search_{query}_{request.user.id}'
        cached_results = cache.get(cache_key)
        if cached_results:
            return Response(cached_results)
        
        users = User.objects.filter(
            Q(name__iexact=query) |
            Q(name__istartswith=query) |
            Q(name__icontains=query)
        ).annotate(
            search_rank=models.Case(
                models.When(name__iexact=query, then=models.Value(1.0)),
                models.When(name__istartswith=query, then=models.Value(0.8)),
                models.When(name__icontains=query, then=models.Value(0.6)),
                default=models.Value(0.0),
                output_field=models.FloatField(),
            )
        ).prefetch_related(
            Prefetch('contacts', queryset=Contact.objects.filter(user=request.user))
        )

        # Search in Contacts
        contacts = Contact.objects.filter(
            Q(name__iexact=query) |
            Q(name__istartswith=query) |
            Q(name__icontains=query)
        ).annotate(
            search_rank=models.Case(
                models.When(name__iexact=query, then=models.Value(1.0)),
                models.When(name__istartswith=query, then=models.Value(0.8)),
                models.When(name__icontains=query, then=models.Value(0.6)),
                default=models.Value(0.0),
                output_field=models.FloatField(),
            )
        )

        # Combine and prioritize results
        results = []
        seen_numbers = set()

        def add_result(name, phone_number, is_registered_user=False, email=None):
            if phone_number in seen_numbers:
                return
            seen_numbers.add(phone_number)
            
            spam_likelihood = SpamReport.get_spam_likelihood(phone_number)
            results.append({
                'name': name,
                'phone_number': phone_number,
                'spam_likelihood': spam_likelihood,
                'is_registered_user': is_registered_user,
                'email': email
            })

        # Process results in priority order
        for user in users.order_by('-search_rank'):
            add_result(user.name, user.phone_number, True, user.email)

        for contact in contacts.order_by('-search_rank'):
            add_result(contact.name, contact.phone_number)

        # Paginate results
        paginated_data = self._paginate_results(request, results)
        
        serializer = SearchResultSerializer(
            paginated_data['results'], 
            many=True,
            context={'request': request}
        )

        response_data = {
            'results': serializer.data,
            'total_pages': paginated_data['total_pages'],
            'current_page': paginated_data['current_page'],
            'total_results': paginated_data['total_results']
        }

        # Cache results for 5 minutes
        cache.set(cache_key, response_data, 300)

        return Response(response_data)

    @action(detail=False, methods=['get'], url_path='phone')
    def search_by_phone(self, request):
        """
        Search by phone number with proper handling of registered users
        """
        phone_number = request.query_params.get('q', '').strip()
        if not phone_number:
            return Response(
                {'error': 'Phone number is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        phone_number = phone_number.strip().replace(" ", "")
        if not phone_number.startswith('+'):
            phone_number = '+' + phone_number

        cache_key = f'phone_search_{phone_number}_{request.user.id}'
        cached_result = cache.get(cache_key)
        if cached_result:
            return Response(cached_result)

        # Check for registered user first
        registered_user = User.objects.filter(
            phone_number=phone_number
        ).prefetch_related(
            Prefetch('contacts', queryset=Contact.objects.filter(user=request.user))
        ).first()

        if registered_user:
            result = {
                'name': registered_user.name,
                'phone_number': registered_user.phone_number,
                'spam_likelihood': SpamReport.get_spam_likelihood(phone_number),
                'is_registered_user': True,
                'email': registered_user.email
            }
            serializer = PhoneSearchResultSerializer(
                result,
                context={'request': request}
            )
            response_data = serializer.data
            cache.set(cache_key, response_data, 300)
            return Response(response_data)

        # If no registered user, get all contact entries
        contacts = Contact.objects.filter(
            phone_number=phone_number
        ).select_related('user')

        if not contacts.exists():
            return Response([], status=status.HTTP_200_OK)
        
        contact_names = list(contacts.values_list('name', flat=True).distinct())
        
        result = {
            'name': contact_names[0],  # Primary name
            'phone_number': phone_number,
            'spam_likelihood': SpamReport.get_spam_likelihood(phone_number),
            'is_registered_user': False,
            'associated_names': contact_names
        }
        
        serializer = PhoneSearchResultSerializer(
            result,
            context={'request': request}
        )
        response_data = serializer.data
        cache.set(cache_key, response_data, 300)
        return Response(response_data)