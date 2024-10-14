from django.shortcuts import render
from stats.helper import  get_school_dashboard_cards, get_school_dashboard_graph, get_teacher_dashboard_cards
from utils.response import create_message, create_response
from utils.utils import get_user_from_token, require_authentication, response_500
from rest_framework import status
from rest_framework.views import APIView


# Mapping analytics_id to functions
card_functions = {
    'dash_tech': get_teacher_dashboard_cards,
    'dash_sch': get_school_dashboard_cards,
 }
graph_functions = {
    'dash_sch': get_school_dashboard_graph,
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
        
class GraphView(APIView):
    @require_authentication
    def get(self, request):
        try:
            user = get_user_from_token(request)
            data = []
            graph_id = request.query_params.get('graph_id', None)

            # Trigger the corresponding function based on the analytics_id
            if graph_id and graph_id in card_functions:
                data = graph_functions[graph_id](user)
            else:
                raise Exception(f"Invalid graph_id: {graph_id}")

            return create_response(create_message(data, 1000), status.HTTP_200_OK)
        except Exception as e:
            return response_500(str(e))
