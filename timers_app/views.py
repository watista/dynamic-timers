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

                if not timers[timer_id]["running"]:
                    elapsed = request.POST.get("elapsed")
                    if elapsed:
                        try:
                            elapsed_minutes = float(elapsed)
                            timers[timer_id]["elapsed"] = max(0, elapsed_minutes * 60)
                        except ValueError:
                            pass

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
                elapsed = request.POST.get("elapsed", None)

                if name:
                    timers[timer_id]["name"] = name

                if elapsed is not None and not timers[timer_id]["running"]:
                    try:
                        elapsed_minutes = float(elapsed)
                        timers[timer_id]["elapsed"] = max(0, elapsed_minutes * 60)
                    except ValueError:
                        pass

                save()

            elif action == "lock":
                timers[timer_id]["locked"] = not timers[timer_id].get("locked", False)

                if timers[timer_id]["running"]:
                    now_ts = time.time()
                    timers[timer_id]["elapsed"] += now_ts - timers[timer_id]["start_time"]
                    timers[timer_id]["start_time"] = None
                    timers[timer_id]["running"] = False

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

        if "locked" not in t:
            t["locked"] = False

    total_seconds = sum(t.get("elapsed", 0) for t in timers)
    total_minutes = round(total_seconds / 60, 1)
    hours = round(total_minutes // 60)
    minutes = round(total_minutes % 60)
    total_hours_formatted = f"{hours}h{minutes:02d}m"

    return render(request, "timers_app/index.html", {
        "timers": timers,
        "enumerate": enumerate,
        "total_minutes": total_minutes,
        "total_hours_formatted": total_hours_formatted,
    })
