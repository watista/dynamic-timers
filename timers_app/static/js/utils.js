function updateTimers() {
    const now = Date.now() / 1000;
    let totalSeconds = 0;
    const activeTab = document.querySelector(".nav-link.active")?.dataset.tab;

    document.querySelectorAll(`[data-timer][data-tab="${activeTab}"]`).forEach(el => {
        const start = parseFloat(el.dataset.start);
        const elapsedAttr = parseFloat(el.dataset.elapsed);
        const id = el.dataset.id;
        let elapsed = 0;

        if (!isNaN(start) && !isNaN(elapsedAttr)) {
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

    updateTimers(); // initial
});
