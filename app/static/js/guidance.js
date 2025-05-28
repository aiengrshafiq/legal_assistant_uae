
document.getElementById("guidanceForm").addEventListener("submit", async function(e) {
    showLoading();
    const generateBtn = document.getElementById("generateGuiadanceBtn");
    generateBtn.disabled = true;
    e.preventDefault();
    const data = {
        legalIssue: document.getElementById("legalIssue").value,
        userRole: document.getElementById("userRole").value,
        urgencyLevel: document.getElementById("urgencyLevel").value,
        optionalDetails: document.getElementById("optionalDetails").value,
    };
    const resultDiv = document.getElementById("guidanceResult");

    try {
        const res = await fetch("/api/practical-guidance", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });

        const json = await res.json();

        if (typeof marked !== 'undefined') {
            resultDiv.innerHTML = marked.parse(json.guidance);
        } else {
            console.warn("marked.js not found, falling back to <br> replace");
            resultDiv.innerHTML = json.guidance.replace(/\n/g, "<br>");
        }

        resultDiv.scrollIntoView({ behavior: "smooth" });

    } catch (err) {
        alert("Failed to generate guidance.");
    } finally {
        hideLoading();
        generateBtn.disabled = false;
    }

});


function showLoading() {
    document.getElementById("loadingSpinner").style.display = "block";
}
function hideLoading() {
    document.getElementById("loadingSpinner").style.display = "none";
}