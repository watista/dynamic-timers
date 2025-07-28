from django.shortcuts import render, redirect
from django.utils.timezone import now
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import time, json, base64, uuid, logging


logger = logging.getLogger('timers_app')
SHARE_DIR = "shared_states"


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
            tabs.append({"id": str(uuid.uuid4()), "name": f"Tab {len(tabs) + 1}", "timers": []})
            request.session["active_tab"] = len(tabs) - 1
            request.session["tab_is_new"] = True
            request.session.modified = True
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
                "id": str(uuid.uuid4()),
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
            sets = request.session["timer_sets"]

            selected_set = next((s for s in sets if s["name"] == set_name), None)
            if selected_set:
                timers.extend({
                    "name": t["name"],
                    "elapsed": t.get("elapsed", 0) * 60,
                    "running": False,
                    "start_time": None,
                    "locked": False
                } for t in selected_set["timers"])
                save()

            # for s in timer_sets:
            #     if s["name"] == set_name:
            #         tabs[active_tab]["timers"].extend([
            #             {
            #                 "name": t["name"],
            #                 "elapsed": t.get("elapsed", 0),
            #                 "running": False,
            #                 "start_time": None,
            #                 "locked": False,
            #             }
            #             for t in s["timers"]
            #         ])
            #         request.session.modified = True
            #         break

        elif action == "export_tab":
            current_tab = request.session["tabs"][request.session["active_tab"]]
            response = JsonResponse(current_tab)
            response["Content-Disposition"] = f'attachment; filename="{current_tab["name"]}.json"'
            return response

        elif "import_file" in request.FILES:
            file = request.FILES["import_file"]
            try:
                data = json.load(file)
                if isinstance(data, dict) and "name" in data and "timers" in data:
                    request.session["tabs"].append(data)
                    request.session["active_tab"] = len(request.session["tabs"]) - 1
                    request.session.modified = True
            except Exception as e:
                logger.warning(f"Import failed: {e}")
            return redirect("index")

        elif action == "reorder_tabs":
            from_index = int(request.POST.get("from_index", -1))
            to_index = int(request.POST.get("to_index", -1))

            if 0 <= from_index < len(tabs) and 0 <= to_index < len(tabs):
                tab = tabs.pop(from_index)
                tabs.insert(to_index, tab)
                request.session.modified = True

        elif 0 <= timer_id < len(timers):
            timer = timers[timer_id]

            if action == "toggle":
                now_ts = time.time()

                if not timer["running"]:
                    elapsed = request.POST.get("elapsed")
                    if elapsed:
                        try:
                            timer["elapsed"] = max(0, float(elapsed) * 60)
                        except ValueError as ve:
                            logger.warning(f"Value error action toggle: {ve}")
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
                    except ValueError as ve:
                        logger.warning(f"Value error action update: {ve}")
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

            elif action == "reset":
                timers[timer_id]["elapsed"] = 0.0
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

    for t in timers:
        if "id" not in t:
            t["id"] = str(uuid.uuid4())

    for tab in tabs:
        if "id" not in tab:
            tab["id"] = str(uuid.uuid4())

    total_seconds = sum(t.get("elapsed", 0) + (time.time() - t["start_time"] if t["running"] else 0) for t in timers)
    total_minutes = round(total_seconds / 60, 1)
    hours = int(total_minutes // 60)
    minutes = int(total_minutes % 60)
    total_hours_formatted = f"{hours}h{minutes:02d}m"
    current_tab_name = request.session["tabs"][request.session["active_tab"]]["name"]
    new_timer_added = request.session.pop("new_timer_added", False)
    tab_is_new = request.session.pop("tab_is_new", False)

    return render(request, "index.html", {
        "timers": timers,
        "enumerate": enumerate,
        "tabs": tabs,
        "active_tab": active_tab,
        "total_minutes": total_minutes,
        "total_hours_formatted": total_hours_formatted,
        "current_tab_name": current_tab_name,
        "new_timer_added": new_timer_added,
        "tab_is_new": tab_is_new,
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
            timer_names = request.POST.getlist("timer_names")
            timer_minutes = request.POST.getlist("timer_minutes")

            timers = []
            for t_name, t_min in zip(timer_names, timer_minutes):
                t_name = t_name.strip()
                try:
                    elapsed = max(0, float(t_min))
                except ValueError:
                    elapsed = 0
                if t_name:
                    timers.append({"name": t_name, "elapsed": elapsed})

            if name and timers:
                sets.append({
                    "name": name,
                    "timers": timers
                })
                request.session["timer_sets"] = sets
                request.session.modified = True
            return redirect("manage_timer_sets")

        elif action == "update":
            try:
                set_index = int(request.POST.get("set_index", -1))
            except ValueError:
                return redirect("manage_timer_sets")
            if 0 <= set_index < len(sets):
                set_name = request.POST.get("set_name", "").strip()
                timer_names = request.POST.getlist("timer_names")
                elapsed_times = request.POST.getlist("timer_minutes")
                timers = []
                for name, minutes in zip(timer_names, elapsed_times):
                    try:
                        elapsed = max(0, float(minutes))
                    except ValueError:
                        elapsed = 0.0
                    timers.append({"name": name.strip(), "elapsed": elapsed})
                sets[set_index]["name"] = set_name
                sets[set_index]["timers"] = timers
                request.session.modified = True
            return redirect("manage_timer_sets")

        elif action == "delete_timer_row":
            set_index = int(request.POST.get("set_index", -1))
            row_index = int(request.POST.get("timer_row_index", -1))
            if 0 <= set_index < len(sets):
                timers = sets[set_index]["timers"]
                if 0 <= row_index < len(timers):
                    del timers[row_index]
                    request.session.modified = True

        elif action == "delete":
            set_index = int(request.POST.get("set_index", -1))
            if 0 <= set_index < len(sets):
                del sets[set_index]
                request.session.modified = True

        return redirect("manage_timer_sets")

    return render(request, "manage_timer_sets.html", {"timer_sets": sets})


def share_state(request):
    state = {
        "tabs": request.session.get("tabs", []),
        "timer_sets": request.session.get("timer_sets", []),
    }
    token = str(uuid.uuid4())
    data = json.dumps(state)
    path = f"{SHARE_DIR}/{token}.json"
    default_storage.save(path, ContentFile(data))
    share_url = request.build_absolute_uri(f"/load/{token}/")
    return JsonResponse({"url": share_url})


def load_shared_state(request, token):
    path = f"{SHARE_DIR}/{token}.json"
    if default_storage.exists(path):
        content = default_storage.open(path).read()
        try:
            state = json.loads(content)
            request.session["tabs"] = state.get("tabs", [])
            request.session["timer_sets"] = state.get("timer_sets", [])
            request.session["active_tab"] = 0
            request.session.modified = True
        except Exception as e:
            logger.exception(f"Load error: {e}")
    return redirect("index")
