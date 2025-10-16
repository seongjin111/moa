# from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_GET
from .models import BusStop

def route_page(request):
    return render(request, "mobility/route.html")

@require_GET
def route_to_stop(request):
    try:
        lat = float(request.GET.get("origin_lat", 37.5663))
        lng = float(request.GET.get("origin_lng", 126.9779))
        stop_id = int(request.GET.get("stop_id", 1))
    except (TypeError, ValueError):
        return HttpResponseBadRequest("invalid parameters")

    try:
        stop = BusStop.objects.get(pk=stop_id)
    except BusStop.DoesNotExist:
        return HttpResponseBadRequest("unknown stop")

    steps = [
        {"type":"depart","text":"현재 위치에서 북쪽으로 50m 직진","distance_m":50,"landmark":"편의점 앞","crosswalk":False,"slope":"gentle","bearing":"N"},
        {"type":"turn_right","text":"오른쪽으로 80m 진행 (인도 넓음)","distance_m":80,"landmark":"은행 건물","crosswalk":False,"slope":"flat","bearing":"E"},
        {"type":"crosswalk","text":"신호등 있는 횡단보도를 건너세요","distance_m":15,"landmark":"큰 사거리","crosswalk":True,"slope":"flat","bearing":"E"},
        {"type":"arrive","text":f"{stop.name} 도착 (쉼터 {'있음' if stop.has_shelter else '없음'})","distance_m":0,"landmark":"버스 정류장","crosswalk":False,"slope":"flat","bearing":"E"},
    ]
    return JsonResponse({
        "origin": {"lat": lat, "lng": lng},
        "destination": {"lat": float(stop.lat), "lng": float(stop.lng), "name": stop.name},
        "steps": steps
    })
