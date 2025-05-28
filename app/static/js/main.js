function showLoading() {
    document.getElementById("loadingSpinner").style.display = "block";
}
function hideLoading() {
    document.getElementById("loadingSpinner").style.display = "none";
}

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const chatBox = document.getElementById('chatBox');
    const message = input.value.trim();
    if (!message) return;

    const sendBtn = document.querySelector("button[onclick='sendMessage()']");
    sendBtn.disabled = true;
    showLoading();

    chatBox.innerHTML += `<div><strong>You:</strong> ${message}</div>`;
    input.value = '';

    try {
        const response = await fetch("/api/query", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({question: message})
        });

        const data = await response.json();
        const shortAnswer = data.short_answer || "No response.";
        const detailedAnswer = data.detailed_answer || "";
        const sources = data.sources || [];

        let sourcesHTML = "";
        if (sources.length > 0 && !shortAnswer.includes("Sorry") && sources.some(s => s.excerpt.trim())) {
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

        chatBox.innerHTML += `
            <div>
                <strong>Assistant (Summary):</strong> ${shortAnswer}<br/>
                ${detailedAnswer ? `
                    <button class="btn btn-link p-0 mt-2" data-bs-toggle="collapse" data-bs-target="#detail${Date.now()}">📚 Show Detailed Provisions from UAE Law</button>
                    <div class="collapse mt-2" id="detail${Date.now()}">
                        <div class="border rounded p-3 bg-light" style="white-space:pre-wrap;">
                            ${detailedAnswer}
                        </div>
                    </div>` : ""}
                ${sourcesHTML}
            </div>`;
        chatBox.scrollTop = chatBox.scrollHeight;

    } catch (err) {
        alert("Something went wrong. Please try again.");
        console.error(err);
    } finally {
        hideLoading();
        sendBtn.disabled = false;
    }
}





async function handleDraft() {
    const file = document.querySelector("#draftFile").files[0];
    const type = document.querySelector("#draftType").value;
    if (!file || !type) return alert("File and draft type required");

    const generateBtn = document.querySelector("button[onclick='handleDraft()']");
    generateBtn.disabled = true;
    showLoading();

    const formData = new FormData();
    formData.append("file", file);
    formData.append("draft_type", type);

    try {
        const res = await fetch("/api/draft", {method: "POST", body: formData});
        const data = await res.json();
        document.querySelector("#draftResult").innerText = data.draft;
    } catch (err) {
        alert("Failed to generate draft.");
    } finally {
        hideLoading();
        generateBtn.disabled = false;
    }
}


async function handleSummarize() {
    const file = document.querySelector("#summaryFile").files[0];
    if (!file) return alert("Please upload a PDF");

    const summarizeBtn = document.querySelector("button[onclick='handleSummarize()']");
    summarizeBtn.disabled = true;
    showLoading();

    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await fetch("/api/summarize", {method: "POST", body: formData});
        const data = await res.json();
        console.log(data.summary);
        const resultDiv = document.querySelector("#summaryResult");

        
        if (typeof marked !== 'undefined') {
            resultDiv.innerHTML = marked.parse(data.summary);
        } else {
            console.warn("marked.js not found, falling back to <br> replace");
            resultDiv.innerHTML = data.summary.replace(/\n/g, "<br>");
        }
        
    } catch (err) {
        alert("Failed to summarize case.");
    } finally {
        hideLoading();
        summarizeBtn.disabled = false;
    }
}

