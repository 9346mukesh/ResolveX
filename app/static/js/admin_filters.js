function filterTickets() {
    const status = document.getElementById("filterStatus")?.value || "";
    const priority = document.getElementById("filterPriority")?.value || "";
    const assigned = document.getElementById("filterAssigned")?.value || "";
    const agent = document.getElementById("filterAgent")?.value.toLowerCase() || "";
    const subject = document.getElementById("filterSubject")?.value.toLowerCase() || "";
    const creator = document.getElementById("filterCreator")?.value.toLowerCase() || "";

    document.querySelectorAll(".ticket").forEach(ticket => {
        const tStatus = ticket.dataset.status || "";
        const tPriority = ticket.dataset.priority || "";
        const tAssigned = ticket.dataset.assigned || "";
        const tAgent = (ticket.dataset.agent || "").toLowerCase();
        const tSubject = (ticket.dataset.subject || "").toLowerCase();
        const tCreator = (ticket.dataset.creator || "").toLowerCase();

        const statusMatch = !status || tStatus === status;
        const priorityMatch = !priority || tPriority === priority;
        const assignedMatch = !assigned || tAssigned === assigned;
        const agentMatch = !agent || tAgent.includes(agent);
        const subjectMatch = !subject || tSubject.includes(subject);
        const creatorMatch = !creator || tCreator.includes(creator);

        ticket.style.display =
            statusMatch &&
            priorityMatch &&
            assignedMatch &&
            agentMatch &&
            subjectMatch &&
            creatorMatch
            ? "flex"
            : "none";
    });
}

function resetFilters() {
    document
        .querySelectorAll(".filter-bar input, .filter-bar select")
        .forEach(el => el.value = "");

    filterTickets();
}