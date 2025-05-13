async function sendMessage() {
    const input = document.getElementById('chatInput');
    const chatBox = document.getElementById('chatBox');
    const message = input.value.trim();
    if (!message) return;

    chatBox.innerHTML += `<div><strong>You:</strong> ${message}</div>`;
    input.value = '';

    const response = await fetch("/api/query", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({question: message})
    });

    const data = await response.json();
    const answer = data.answer || "No response.";
    const sources = data.sources || [];

    let sourcesHTML = "";

    if (sources.length > 0 && !answer.includes("Sorry, the information you're asking for isn't available") && sources.some(s => s.excerpt.trim())) {
        sourcesHTML += `<details><summary>📖 View Sources (${sources.length})</summary>`;
        sources.forEach((src, idx) => {
            sourcesHTML += `
                <div style="margin-top: 10px;">
                    <strong>Source ${idx + 1}:</strong><br>
                    <em>File:</em> ${src.filename} <br>
                    <em>Page:</em> ${src.page} <br>
                    <pre>${src.excerpt}...</pre>
                </div>`;
        });
        sourcesHTML += `</details>`;
    }

    chatBox.innerHTML += `<div><strong>Assistant:</strong> ${answer}</div>${sourcesHTML}`;
    chatBox.scrollTop = chatBox.scrollHeight;
}


    async function handleDraft() {
        const file = document.querySelector("#draftFile").files[0];
        const type = document.querySelector("#draftType").value;
        if (!file || !type) return alert("File and draft type required");

        const formData = new FormData();
        formData.append("file", file);
        formData.append("draft_type", type);

        const res = await fetch("/api/draft", {method: "POST", body: formData});
        const data = await res.json();
        document.querySelector("#draftResult").innerText = data.draft;
    }

    async function handleSummarize() {
        const file = document.querySelector("#summaryFile").files[0];
        if (!file) return alert("Please upload a PDF");

        const formData = new FormData();
        formData.append("file", file);

        const res = await fetch("/api/summarize", {method: "POST", body: formData});
        const data = await res.json();
        document.querySelector("#summaryResult").innerText = data.summary;
    }
