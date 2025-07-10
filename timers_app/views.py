from django.shortcuts import render, redirect
from django.utils.timezone import now
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import time, json

def index(request):
    if "tabs" not in request.session:
        request.session["tabs"] = [{
            "name": "Default",
            "timers": []
        }]
        request.session["active_tab"] = 0

    tabs = request.session["tabs"]
    active_tab = request.session.get("active_tab", 0)

    # Select a tab
    if request.method == "POST" and request.POST.get("action") == "switch_tab":
        request.session["active_tab"] = int(request.POST["tab_index"])
        return redirect("index")

    if request.method == "POST" and request.content_type == 'application/json':
        payload = json.loads(request.body)
        if payload.get("action") == "reorder":
            new_order = list(map(int, payload.get("order", [])))
            timers = tabs[active_tab]["timers"]
            reordered = [timers[i] for i in new_order if 0 <= i < len(timers)]
            tabs[active_tab]["timers"] = reordered
            request.session.modified = True
            return JsonResponse({"status": "ok"})

    timers = tabs[active_tab]["timers"]

    if "timer_sets" not in request.session:
        request.session["timer_sets"] = []

    if request.method == "POST":
        action = request.POST.get("action")
        timer_id = int(request.POST.get("timer_id", -1))

        def save():
            request.session["tabs"] = tabs
            request.session.modified = True

        if action == "add_tab":
            tabs.append({"name": f"Tab {len(tabs) + 1}", "timers": []})
            request.session["active_tab"] = len(tabs) - 1
            save()
            return redirect("index")

        elif action == "rename_tab":
            tabs[active_tab]["name"] = request.POST.get("tab_name", "Unnamed Tab")
            save()
            return redirect("index")

        elif action == "delete_tab" and len(tabs) > 1:
            tabs.pop(active_tab)
            request.session["active_tab"] = max(0, active_tab - 1)
            save()
            return redirect("index")

        elif action == "add":
            timers.append({
                "name": "New Timer",
                "elapsed": 0.0,
                "running": False,
                "start_time": None,
                "locked": False
            })
            request.session["new_timer_added"] = True
            save()

        elif action == "apply_timer_set":
            set_name = request.POST.get("set_name")
            current_tab = request.session["active_tab"]
            sets = request.session["timer_sets"]

            selected_set = next((s for s in sets if s["name"] == set_name), None)
            if selected_set:
                timers.extend({
                    "name": t["name"],
                    "elapsed": 0.0,
                    "running": False,
                    "start_time": None,
                    "locked": False
                } for t in selected_set["timers"])
                save()

        elif 0 <= timer_id < len(timers):
            timer = timers[timer_id]

            if action == "toggle":
                now_ts = time.time()

                if not timer["running"]:
                    elapsed = request.POST.get("elapsed")
                    if elapsed:
                        try:
                            timer["elapsed"] = max(0, float(elapsed) * 60)
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
                    timer["name"] = name
                if elapsed is not None and not timer["running"]:
                    try:
                        timer["elapsed"] = max(0, float(elapsed) * 60)
                    except ValueError:
                        pass
                save()

            elif action == "lock":
                timer["locked"] = not timer.get("locked", False)
                if timer["running"]:
                    now_ts = time.time()
                    timer["elapsed"] += now_ts - timer["start_time"]
                    timer["start_time"] = None
                    timer["running"] = False
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

    total_seconds = sum(t.get("elapsed", 0) + (time.time() - t["start_time"] if t["running"] else 0) for t in timers)
    total_minutes = round(total_seconds / 60, 1)
    hours = int(total_minutes // 60)
    minutes = int(total_minutes % 60)
    total_hours_formatted = f"{hours}h{minutes:02d}m"
    current_tab_name = request.session["tabs"][request.session["active_tab"]]["name"]
    new_timer_added = request.session.pop("new_timer_added", False)

    return render(request, "index.html", {
        "timers": timers,
        "enumerate": enumerate,
        "tabs": tabs,
        "active_tab": active_tab,
        "total_minutes": total_minutes,
        "total_hours_formatted": total_hours_formatted,
        "current_tab_name": current_tab_name,
        "new_timer_added": new_timer_added,
        "timer_sets": request.session["timer_sets"],
    })


def manage_timer_sets(request):
    if "timer_sets" not in request.session:
        request.session["timer_sets"] = []

    sets = request.session["timer_sets"]

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add":
            name = request.POST.get("set_name", "").strip()
            timers = request.POST.getlist("timer_names")
            timers = [{"name": t.strip()} for t in timers if t.strip()]
            if name and timers:
                sets.append({"name": name, "timers": timers})
                request.session.modified = True

        elif action == "update":
            index = int(request.POST.get("set_index"))
            name = request.POST.get("set_name", "").strip()
            timers = request.POST.getlist("timer_names")
            timers = [{"name": t.strip()} for t in timers if t.strip()]
            if 0 <= index < len(sets) and name:
                sets[index] = {"name": name, "timers": timers}
                request.session.modified = True

        elif action == "delete":
            index = int(request.POST.get("set_index"))
            if 0 <= index < len(sets):
                del sets[index]
                request.session.modified = True

        return redirect("manage_timer_sets")

    return render(request, "manage_timer_sets.html", {"timer_sets": sets})
