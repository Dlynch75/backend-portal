from django.shortcuts import render
from stats.helper import  get_school_dashboard_cards, get_teacher_dashboard_cards
from utils.response import create_message, create_response
from utils.utils import get_user_from_token, require_authentication, response_500
from rest_framework import status
from rest_framework.views import APIView


# Mapping analytics_id to functions
card_functions = {
    'dash_tech': get_teacher_dashboard_cards,
    'dash_sch': get_school_dashboard_cards,
 }

class CardView(APIView):
    @require_authentication
    def get(self, request):
        try:
            user = get_user_from_token(request)
            data = []
            stats_id = request.query_params.get('stats_id', None)

            # Trigger the corresponding function based on the analytics_id
            if stats_id and stats_id in card_functions:
                data = card_functions[stats_id](user)
            else:
                raise Exception(f"Invalid stats_id: {stats_id}")

            return create_response(create_message(data, 1000), status.HTTP_200_OK)
        except Exception as e:
            return response_500(str(e))
