function updateTimers() {
    const now = Date.now() / 1000;
    let totalSeconds = 0;
    let anyTimerRunning = false;
    const activeTab = document.querySelector(".nav-link.active")?.dataset.tab;

    document.querySelectorAll(`[data-timer][data-tab="${activeTab}"]`).forEach(el => {
        const start = parseFloat(el.dataset.start);
        const elapsedAttr = parseFloat(el.dataset.elapsed);
        const id = el.dataset.id;
        let elapsed = 0;

        if (!isNaN(start) && !isNaN(elapsedAttr)) {
            anyTimerRunning = true;
            elapsed = elapsedAttr + (now - start);
            const minutes = (elapsed / 60).toFixed(1);
            el.textContent = minutes.replace(',', '.') + " min";
        } else {
            const input = document.querySelector(`.elapsed-input[data-id="${id}"][data-tab="${activeTab}"]`);
            if (input) {
                const inputMinutes = parseFloat(input.value);
                if (!isNaN(inputMinutes)) {
                    elapsed = inputMinutes * 60;
                    el.textContent = inputMinutes.toFixed(1).replace(',', '.') + " min";
                }
            }
        }

        totalSeconds += elapsed;
    });

    document.getElementById("total-minutes").textContent = (totalSeconds / 60).toFixed(0);
    const totalHoursInt = Math.floor(totalSeconds / 3600);
    const totalMinutesInt = Math.floor((totalSeconds % 3600) / 60);
    document.getElementById("total-hours").textContent = `${totalHoursInt}h${String(totalMinutesInt).padStart(2, '0')}m`;
    checkInactivity(anyTimerRunning);
    checkActivity(anyTimerRunning);
}

setInterval(updateTimers, 1000);

function allowDrop(ev) {
    ev.preventDefault();
    document.querySelectorAll('.card').forEach(card => card.classList.remove('drag-over'));

    const target = ev.target.closest('.card');
    if (target) {
        target.classList.add('drag-over');
    }
}

function drop(ev) {
    ev.preventDefault();
    const data = ev.dataTransfer.getData("text");
    const dragged = document.getElementById(data);
    const dropTarget = ev.target.closest('.card');
    const context = document.getElementById("js-context");
    const csrfToken = context.dataset.csrfToken;
    const reorderUrl = context.dataset.reorderUrl;

    document.querySelectorAll('.card').forEach(card => card.classList.remove('drag-over'));

    if (dropTarget && dragged !== dropTarget) {
        const bounding = dropTarget.getBoundingClientRect();
        const offset = ev.clientY - bounding.top;

        if (offset > bounding.height / 2) {
            dropTarget.after(dragged);
        } else {
            dropTarget.before(dragged);
        }

        const order = Array.from(document.querySelectorAll('#timer-container .card'))
            .map(el => el.querySelector('[name="timer_id"]').value);

        fetch(reorderUrl, {
            method: "POST",
            headers: {
                "X-CSRFToken": csrfToken,
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ action: "reorder", order: order }),
        }).then(() => window.location.reload());
    }
}

let lastActiveTimestamp = Date.now();
let lastNotified = 0;
let activeTimerStarted  = Date.now();
let lastActivityAlert = 0;

function checkInactivity(anyRunning) {
    const now = Date.now();
    const input = document.getElementById("inactivity-time");
    const customDelay = parseInt(input?.value || "15", 10);
    const delayMinutes = Math.max(customDelay, 1);

    if (anyRunning) {
        lastActiveTimestamp = now;
    } else {
        const diffMinutes = (now - lastActiveTimestamp) / 1000 / 60;

        if (diffMinutes >= delayMinutes && (now - lastNotified) > 1000 * 60 * delayMinutes) {
            sendInactivityNotification(delayMinutes);
            lastNotified = now;
        }
    }
}

function checkActivity(anyRunning) {
    const now = Date.now();
    const input = document.getElementById("activity-time");
    const activityDelay = parseInt(input?.value || "60", 10);
    const delayMinutes = Math.max(activityDelay, 1);

    if (anyRunning) {
        if (!activeTimerStarted) {
            activeTimerStarted = now;
        }

        const runningMinutes = (now - activeTimerStarted) / 1000 / 60;

        if (runningMinutes >= delayMinutes && (now - lastActivityAlert) > 1000 * 60 * delayMinutes) {
            sendActivityNotification(delayMinutes);
            lastActivityAlert = now;
        }
    } else {
        activeTimerStarted = null;
    }
}

function sendInactivityNotification(delay) {
    if (Notification.permission === "granted") {
        new Notification("⏱ Reminder", {
            body: `No timers have been running for ${delay} minutes. Get to work!`,
            icon: "/static/img/favicon.png"
        });
    }
}

function sendActivityNotification(delay) {
    if (Notification.permission === "granted") {
        new Notification("⏳ Reminder", {
            body: `The same timer has been running for more than ${delay} minutes, this is correct?`,
            icon: "/static/img/favicon.png"
        });
    }
}

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".drag-handle").forEach(handle => {
        handle.setAttribute("draggable", true);

        handle.addEventListener("dragstart", e => {
            const card = e.target.closest(".card");
            e.dataTransfer.setData("text", card.id);
            card.classList.add("dragging");
        });

        handle.addEventListener("dragend", e => {
            const card = e.target.closest(".card");
            card.classList.remove("dragging");
        });
    });

    document.querySelectorAll("button[name='action'][value='toggle']").forEach(button => {
        button.addEventListener("click", (e) => {
            const form = button.closest("form");
            const elapsedInput = form.querySelector("input[name='elapsed']");
            if (elapsedInput) {
                form.submit();
            }
        });
    });

    document.querySelectorAll(".edit-tab-name").forEach(icon => {
        icon.addEventListener("click", () => {
            const container = icon.closest(".tab-name-container");
            const text = container.querySelector(".tab-name-text");
            const input = container.querySelector(".tab-name-input");

            text.classList.add("d-none");
            icon.classList.add("d-none");
            input.classList.remove("d-none");

            input.focus();
            input.select();
        });
    });

    document.querySelectorAll(".tab-name-input").forEach(input => {
        const revertToViewMode = (el) => {
            const container = el.closest(".tab-name-container");
            const text = container.querySelector(".tab-name-text");
            const icon = container.querySelector(".edit-tab-name");

            el.classList.add("d-none");
            text.classList.remove("d-none");
            icon.classList.remove("d-none");
        };

        input.addEventListener("blur", () => {
            if (input.value.trim() !== "") {
                input.closest("form").submit();
            }
            revertToViewMode(input);
        });

        input.addEventListener("keydown", e => {
            if (e.key === "Enter") {
                e.preventDefault();
                input.closest("form").submit();
                revertToViewMode(input);
            } else if (e.key === "Escape") {
                e.preventDefault();
                revertToViewMode(input);
            }
        });
    });

    document.querySelectorAll(".nav-link").forEach(tab => {
        tab.addEventListener("click", () => {
            document.querySelectorAll(".nav-link").forEach(t => t.classList.remove("active"));
            tab.classList.add("active");

            // const activeTab = tab.dataset.tab;
            // document.querySelectorAll(".tab-content").forEach(container => {
            //     container.style.display = container.dataset.tab === activeTab ? "block" : "none";
            // });

            updateTimers(); // Recalculate total time
        });
    });


    const autoFocusInput = document.querySelector('textarea[data-autofocus="true"]');
    if (autoFocusInput) {
        autoFocusInput.focus();
        autoFocusInput.select();
    }

    // Handle Enter to submit timer name
    document.querySelectorAll("textarea.name-input").forEach(textarea => {
        textarea.addEventListener("keydown", function (e) {
            if (e.key === "Enter") {
                e.preventDefault();  // prevent newline
                const form = textarea.closest("form");
                if (form) {
                    const hiddenAction = document.createElement("input");
                    hiddenAction.type = "hidden";
                    hiddenAction.name = "action";
                    hiddenAction.value = "update";
                    form.appendChild(hiddenAction);
                    form.submit();
                }
            }
        });
    });

    document.querySelectorAll(".name-input, .elapsed-input").forEach(field => {
        field.addEventListener("blur", async (e) => {
            const el = e.target;
            const id = el.dataset.id;
            const name = document.querySelector(`.name-input[data-id="${id}"]`).value;
            const elapsed = document.querySelector(`.elapsed-input[data-id="${id}"]`)?.value;
            const csrf = document.querySelector("input[name=csrfmiddlewaretoken]").value;

            await fetch("/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrf,
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                body: new URLSearchParams({
                    action: "update",
                    timer_id: id,
                    name: name,
                    elapsed: elapsed
                })
            });

            updateTimers();
        });
    });

    document.querySelectorAll(".name-input").forEach(field => {
        const id = field.dataset.id;
        const savedWidth = localStorage.getItem(`name-width-${id}`);
        if (savedWidth) {
            field.style.width = savedWidth;
        }

        field.addEventListener("mouseup", () => {
            localStorage.setItem(`name-width-${id}`, field.style.width);
        });

        field.addEventListener("blur", () => {
            localStorage.setItem(`name-width-${id}`, field.style.width);
        });
    });

    if (Notification.permission !== "granted" && Notification.permission !== "denied") {
        Notification.requestPermission();
    }

    const inactivityInput = document.getElementById("inactivity-time");
    const activityInput = document.getElementById("activity-time");

    const savedDelay = localStorage.getItem("inactivityDelay");
    const savedDelayActive = localStorage.getItem("activityDelay");
    inactivityInput.value = savedDelay ? parseInt(savedDelay, 10) : 15;
    activityInput.value = savedDelayActive ? parseInt(savedDelayActive, 10) : 60;

    inactivityInput.addEventListener("input", () => {
        const value = parseInt(inactivityInput.value, 10);
        if (!isNaN(value) && value >= 1) {
            localStorage.setItem("inactivityDelay", value);
        }
    });

    activityInput.addEventListener("input", () => {
        const value = parseInt(activityInput.value, 10);
        if (!isNaN(value) && value >= 1) {
            localStorage.setItem("activityDelay", value);
        }
    });

    document.getElementById("export-salesforce")?.addEventListener("click", () => {
        window.open("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "_blank");
    });

    updateTimers(); // initial
});
