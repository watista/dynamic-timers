function updateTimers() {
    const now = Date.now() / 1000;
    document.querySelectorAll("[data-timer]").forEach(el => {
        const start = parseFloat(el.dataset.start);
        const elapsed = parseFloat(el.dataset.elapsed);
        if (!isNaN(start) && !isNaN(elapsed)) {
            const minutes = ((elapsed + (now - start)) / 60).toFixed(1);
            el.textContent = minutes.replace(',', '.') + " min";
        }
    });
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
});
