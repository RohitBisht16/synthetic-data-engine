import re
import spacy

try:
    nlp = spacy.load("en_core_web_sm")
except Exception:
    import spacy.cli
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Hard PII Regex Patterns
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_REGEX = re.compile(r"(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b")
SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CREDIT_CARD_REGEX = re.compile(r"\b(?:\d[ -]*?){13,16}\b")


def scrub_pii(text: str, column_name: str = "") -> str:
    """Scrubs PII using deterministic column rules, regex, and SpaCy NLP."""
    if not isinstance(text, str) or not text.strip():
        return text

    col_clean = column_name.lower().strip()

    # 1. Direct Column-Name Rules for Tabular Data
    if any(k in col_clean for k in ["first_name", "last_name", "fname", "lname", "full_name", "surname"]):
        return "[PERSON]"

    if any(k in col_clean for k in ["city", "town", "location", "address", "state", "country"]):
        return "[GPE]"

    if "email" in col_clean:
        return "[EMAIL]"

    # 2. Regex Pass for Unstructured Text or Generic Columns
    scrubbed = EMAIL_REGEX.sub("[EMAIL]", text)
    scrubbed = PHONE_REGEX.sub("[PHONE]", scrubbed)
    scrubbed = SSN_REGEX.sub("[SSN]", scrubbed)
    scrubbed = CREDIT_CARD_REGEX.sub("[CARD_NUMBER]", scrubbed)

    if scrubbed in {"[EMAIL]", "[PHONE]", "[SSN]", "[CARD_NUMBER]"}:
        return scrubbed

    # 3. SpaCy NLP Pass for Unstructured Free-Text
    doc = nlp(scrubbed)
    for ent in reversed(doc.ents):
        if ent.text.strip() in {"[EMAIL]", "[PHONE]", "[SSN]", "[CARD_NUMBER]"}:
            continue

        label = ent.label_
        if label in {"PERSON", "ORG", "GPE", "DATE"}:
            start, end = ent.start_char, ent.end_char
            scrubbed = scrubbed[:start] + f"[{label}]" + scrubbed[end:]

    return scrubbed