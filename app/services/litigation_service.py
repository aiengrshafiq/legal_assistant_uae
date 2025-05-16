# Folder: services/litigation_service.py
from app.qachain import run_case_analysis_chain
from app.utils import extract_text_from_upload

async def analyze_case(
    case_title, case_type, jurisdiction, party_roles,
    claim_description, evidence_summary, desired_outcome,
    representation, language, file
):
    text = claim_description + "\n" + evidence_summary
    if file and file.filename:
        file_bytes = await file.read()
        if file_bytes:  # ensure it's not empty
            try:
                file_text = extract_text_from_upload(file_bytes)
                text += "\n" + file_text
            except Exception as e:
                print(f"[⚠️] Failed to extract PDF text: {e}")

    structured_input = {
        "title": case_title,
        "type": case_type,
        "jurisdiction": jurisdiction,
        "parties": party_roles,
        "claim": text,
        "outcome": desired_outcome,
        "representation": representation
    }

    return run_case_analysis_chain(structured_input, language)
