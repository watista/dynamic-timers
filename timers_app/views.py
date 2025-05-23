from django.shortcuts import render, redirect
from django.utils.timezone import now
from django.http import JsonResponse
import time, json

def index(request):
    if "timers" not in request.session:
        request.session["timers"] = []

    timers = request.session["timers"]

    if request.method == "POST" and request.content_type == 'application/json':
        payload = json.loads(request.body)
        if payload.get("action") == "reorder":
            new_order = list(map(int, payload.get("order", [])))
            original = request.session.get("timers", [])
            reordered = [original[i] for i in new_order if 0 <= i < len(original)]
            request.session["timers"] = reordered
            request.session.modified = True
            return JsonResponse({"status": "ok"})

    if request.method == "POST":
        action = request.POST.get("action")
        timer_id = int(request.POST.get("timer_id", -1))

        def save():
            request.session["timers"] = timers
            request.session.modified = True

        if action == "add":
            timers.append({
                "name": "New Timer",
                "elapsed": 0.0,
                "running": False,
                "start_time": None
            })
            save()

        elif 0 <= timer_id < len(timers):
            if action == "toggle":
                now_ts = time.time()
                for i, t in enumerate(timers):
                    if i == timer_id:
                        if not t["running"]:
                            t["start_time"] = now_ts
                        else:
                            t["elapsed"] += now_ts - t["start_time"]
                            t["start_time"] = None
                        t["running"] = not t["running"]
                    else:
                        if t["running"]:
                            t["elapsed"] += now_ts - t["start_time"]
                            t["start_time"] = None
                            t["running"] = False
                save()

            elif action == "update":
                name = request.POST.get("name", "").strip()
                if name:
                    timers[timer_id]["name"] = name
                    save()

            elif action == "delete":
                timers.pop(timer_id)
                save()

        return redirect("index")

    now_ts = time.time()
    for t in timers:
        if t["running"]:
            t["elapsed_display"] = (t["elapsed"] + (now_ts - t["start_time"])) / 60
        else:
            t["elapsed_display"] = t["elapsed"] / 60

    return render(request, "timers_app/index.html", {"timers": timers})
