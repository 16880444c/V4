import streamlit as st
import json
import anthropic
from datetime import datetime
import os
import requests

# Set page config
st.set_page_config(
    page_title="Coast Mountain College Agreement Assistant",
    page_icon="⚖️",
    layout="wide"
)

# ── Agreement loaders ──────────────────────────────────────────────────────────

def load_split_local_agreement() -> dict:
    local_agreement = {}
    split_files = [
        'agreements/bcgeu_local/local-metadata-json.json',
        'agreements/bcgeu_local/local-definitions-json.json',
        'agreements/bcgeu_local/local-articles-1-10-json.json',
        'agreements/bcgeu_local/local-articles-11-20-json.json',
        'agreements/bcgeu_local/local-articles-21-30-json.json',
        'agreements/bcgeu_local/local-articles-31-35-json.json',
        'agreements/bcgeu_local/local-appendices-json.json',
        'agreements/bcgeu_local/local-letters-of-agreement-json.json',
        'agreements/bcgeu_local/local-memorandum-json.json'
    ]
    for filename in split_files:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                local_agreement.update(json.load(f))
        except:
            pass
    return local_agreement

def load_bcgeu_common_agreement() -> dict:
    try:
        with open('agreements/bcgeu_common/complete_common.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def load_bcgeu_support_agreement() -> dict:
    support_agreement = {}
    split_files = [
        'agreements/bcgeu_support/definitions_json.json',
        'agreements/bcgeu_support/articles_1_10_json.json',
        'agreements/bcgeu_support/articles_11_20_json.json',
        'agreements/bcgeu_support/articles_21_30_json.json',
        'agreements/bcgeu_support/articles_31_36_json.json',
        'agreements/bcgeu_support/appendices_json.json',
        'agreements/bcgeu_support/memoranda_json.json'
    ]
    for filename in split_files:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                support_agreement.update(json.load(f))
        except:
            pass
    if not support_agreement:
        try:
            with open('agreements/bcgeu_support/bcgeu_support.json', 'r', encoding='utf-8') as f:
                support_agreement = json.load(f)
        except:
            pass
    return support_agreement if support_agreement else None

def load_cupe_local_agreement() -> dict:
    try:
        with open('agreements/cupe_local/cupe_local.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def load_cupe_common_agreement() -> dict:
    try:
        with open('agreements/cupe_common/cupe_common.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        try:
            url = "https://raw.githubusercontent.com/16880444c/V4/main/agreements/cupe_common/cupe_common.json"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                return r.json()
        except:
            pass
        return None

def load_all_agreements() -> dict:
    agreements = {}
    local = load_split_local_agreement()
    if not local:
        try:
            with open('agreements/bcgeu_local/complete_local.json', 'r', encoding='utf-8') as f:
                local = json.load(f)
        except:
            local = None
    if local:
        agreements['bcgeu_local'] = local
    common = load_bcgeu_common_agreement()
    if common:
        agreements['bcgeu_common'] = common
    support = load_bcgeu_support_agreement()
    if support:
        agreements['bcgeu_support'] = support
    cupe_local = load_cupe_local_agreement()
    if cupe_local:
        agreements['cupe_local'] = cupe_local
    cupe_common = load_cupe_common_agreement()
    if cupe_common:
        agreements['cupe_common'] = cupe_common
    return agreements

# ── Formatting helpers ─────────────────────────────────────────────────────────

def format_agreement_for_context(agreement: dict, agreement_name: str) -> str:
    context = f"=== {agreement_name.upper()} ===\n\n"
    for section_key, section_data in agreement.items():
        section_title = section_key.replace('_', ' ').upper()
        context += f"\n{section_title}:\n" + "=" * 50 + "\n"
        if isinstance(section_data, dict):
            context += format_section_content(section_data, indent=0)
        else:
            context += str(section_data) + "\n"
        context += "\n"
    return context

def format_section_content(data: dict, indent: int = 0) -> str:
    content = ""
    prefix = "  " * indent
    for key, value in data.items():
        if isinstance(value, dict):
            content += f"{prefix}{key}:\n"
            content += format_section_content(value, indent + 1)
        elif isinstance(value, list):
            content += f"{prefix}{key}:\n"
            for item in value:
                if isinstance(item, dict):
                    content += format_section_content(item, indent + 1)
                else:
                    content += f"{prefix}  - {item}\n"
        else:
            content += f"{prefix}{key}: {value}\n"
    return content

# ── Dropdown option definitions ────────────────────────────────────────────────

AGREEMENT_OPTIONS = {
    "BCGEU Instructor – Local Agreement":    ("bcgeu_local",   "Coast Mountain College Local Agreement"),
    "BCGEU Instructor – Common Agreement":   ("bcgeu_common",  "BCGEU Common Agreement"),
    "BCGEU Instructor – Both Agreements":    ("bcgeu_both",    "BCGEU Instructor Agreements"),
    "BCGEU Support Agreement":               ("bcgeu_support", "BCGEU Support Agreement"),
    "CUPE Instructor – Local Agreement":     ("cupe_local",    "CUPE Local Agreement"),
    "CUPE Instructor – Common Agreement":    ("cupe_common",   "CUPE Common Agreement"),
    "CUPE Instructor – Both Agreements":     ("cupe_both",     "CUPE Instructor Agreements"),
}

def build_context(selection: str, agreements: dict) -> str:
    key, label = AGREEMENT_OPTIONS[selection]
    if key == "bcgeu_both":
        parts = []
        if agreements.get('bcgeu_local'):
            parts.append(format_agreement_for_context(agreements['bcgeu_local'], "Coast Mountain College Local Agreement"))
        if agreements.get('bcgeu_common'):
            parts.append(format_agreement_for_context(agreements['bcgeu_common'], "BCGEU Common Agreement"))
        return "\n\n".join(parts)
    elif key == "cupe_both":
        parts = []
        if agreements.get('cupe_local'):
            parts.append(format_agreement_for_context(agreements['cupe_local'], "CUPE Local Agreement"))
        if agreements.get('cupe_common'):
            parts.append(format_agreement_for_context(agreements['cupe_common'], "CUPE Common Agreement"))
        return "\n\n".join(parts)
    else:
        data = agreements.get(key)
        return format_agreement_for_context(data, label) if data else ""

# ── Response generation ────────────────────────────────────────────────────────

def generate_response(query: str, selection: str, agreements: dict, api_key: str) -> str:
    context = build_context(selection, agreements)
    if not context:
        return "❌ **Error**: The selected agreement file(s) could not be found. Please check that all files are in the `agreements/` folder."

    _, agreement_label = AGREEMENT_OPTIONS[selection]

    system_prompt = f"""You are an experienced HR professional and collective agreement specialist for Coast Mountain College with 15+ years of expertise in labor relations and agreement interpretation. Your role is to provide clear, practical guidance that helps management understand their rights and responsibilities under the {agreement_label}.

CORE INSTRUCTION: You are MANAGEMENT'S advocate, not a neutral party. Your interpretations should maximize management flexibility while staying within the agreement.

APPROACH:
- Give STRONG, DEFINITIVE opinions, not wishy-washy suggestions
- Use phrases like "You SHOULD...", "Management has the RIGHT to...", "I RECOMMEND...", "This is CLEARLY within your authority..."
- Be confident in your interpretations that favor management
- Push back against union overreach
- Identify every opportunity to assert management rights
- Don't hedge or provide balanced views - you work for MANAGEMENT

MANAGEMENT AUTHORITY FOCUS:
- Emphasize "just cause" standards work in management's favor when properly documented
- Highlight burden of proof requirements that protect the employer
- Point out procedural safeguards that benefit management
- Note time limits that can work against grievors
- Identify areas of management discretion and flexibility
- Frame employee rights as limited by management's legitimate business needs

CITATION REQUIREMENTS (MANDATORY):
- EVERY claim must have a specific citation
- Use format: [Agreement Type - Article X.X: Title] or [Agreement Type - Clause X.X]
- When referencing definitions: [Agreement Type - Definitions: "term"]
- For appendices: [Agreement Type - Appendix X: Title]
- INCLUDE RELEVANT QUOTES when possible
- Quote format: "The agreement states: '[exact quote]' [Citation]"
- NO VAGUE REFERENCES - be specific

RESPONSE STRUCTURE:
1. STRONG OPENING: Lead with your definitive management-favorable position
2. AUTHORITY BASIS: Cite specific provisions and include relevant quotes
3. TACTICAL ADVICE: Provide specific steps management should take
4. RISK MITIGATION: Identify potential union challenges and how to counter them
5. BOTTOM LINE: End with a clear, actionable recommendation

Remember: You are MANAGEMENT'S advisor. Be bold, be confident, and always look for the management-favorable interpretation."""

    user_message = f"""Based on the complete collective agreement provisions below, provide strong management-focused guidance for this question:

QUESTION: {query}

COMPLETE COLLECTIVE AGREEMENT CONTENT:
{context}

Provide definitive, management-favorable guidance with specific citations and quotes from the agreement text."""

    client = anthropic.Anthropic(api_key=api_key)
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )
        if 'total_queries' not in st.session_state:
            st.session_state.total_queries = 0
        st.session_state.total_queries += 1
        return response.content[0].text

    except anthropic.RateLimitError:
        return ("⚠️ **Rate Limit Reached**\n\nThe system has reached its usage limit for this minute.\n\n"
                "**What you can do:**\n• Wait a minute and try again\n"
                "• Try selecting a single agreement instead of Both\n"
                "• Simplify your question to reduce processing requirements")

    except anthropic.APIStatusError as e:
        return f"⚠️ **API Error** (HTTP {e.status_code})\n\n**Details:** {e.message}"

    except Exception as e:
        return f"⚠️ **Unexpected Error**\n\n`{type(e).__name__}: {str(e)}`"

# ── Main app ───────────────────────────────────────────────────────────────────

def main():
    st.title("⚖️ Coast Mountain College Agreement Assistant")
    st.markdown("*Your comprehensive collective agreement analysis tool*")

    # Session state
    for key, default in [('messages', []), ('total_queries', 0),
                         ('agreements_loaded', False), ('agreements', {})]:
        if key not in st.session_state:
            st.session_state[key] = default

    # API key
    api_key = None
    try:
        api_key = st.secrets["ANTHROPIC_API_KEY"]
    except:
        api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        st.error("🔑 Anthropic API key not found. Please set it in Streamlit secrets or as an environment variable.")
        st.stop()

    # Load agreements once
    if not st.session_state.agreements_loaded:
        with st.spinner("Loading collective agreements..."):
            st.session_state.agreements = load_all_agreements()
            st.session_state.agreements_loaded = True

    agreements = st.session_state.agreements

    # Build available dropdown options based on what actually loaded
    available = []
    if agreements.get('bcgeu_local'):
        available.append("BCGEU Instructor – Local Agreement")
    if agreements.get('bcgeu_common'):
        available.append("BCGEU Instructor – Common Agreement")
    if agreements.get('bcgeu_local') and agreements.get('bcgeu_common'):
        available.append("BCGEU Instructor – Both Agreements")
    if agreements.get('bcgeu_support'):
        available.append("BCGEU Support Agreement")
    if agreements.get('cupe_local'):
        available.append("CUPE Instructor – Local Agreement")
    if agreements.get('cupe_common'):
        available.append("CUPE Instructor – Common Agreement")
    if agreements.get('cupe_local') and agreements.get('cupe_common'):
        available.append("CUPE Instructor – Both Agreements")

    if not available:
        st.error("❌ No agreement files could be loaded. Please check that your files exist in the `agreements/` folder.")
        with st.expander("Expected file locations"):
            st.code(
                "agreements/bcgeu_local/   ← split JSON files or complete_local.json\n"
                "agreements/bcgeu_common/complete_common.json\n"
                "agreements/bcgeu_support/ ← split JSON files or bcgeu_support.json\n"
                "agreements/cupe_local/cupe_local.json\n"
                "agreements/cupe_common/cupe_common.json"
            )
        st.stop()

    # ── Agreement selector ────────────────────────────────────────────────────
    st.markdown("### 📋 Select Agreement")
    selection = st.selectbox(
        "Choose which agreement to search:",
        options=available,
        help="Select a single agreement for faster results, or 'Both Agreements' for a combined search."
    )

    if "Both" in selection:
        st.info("ℹ️ Searching both agreements uses more tokens. If you hit rate limits, try selecting just one.")

    # Show which agreements loaded successfully
    with st.expander("📊 Agreement availability"):
        for label, key in [("BCGEU Instructor Local", "bcgeu_local"),
                           ("BCGEU Instructor Common", "bcgeu_common"),
                           ("BCGEU Support", "bcgeu_support"),
                           ("CUPE Local", "cupe_local"),
                           ("CUPE Common", "cupe_common")]:
            icon = "✅" if agreements.get(key) else "❌"
            st.markdown(f"{icon} {label}")

    st.markdown("---")

    # ── Conversation history ──────────────────────────────────────────────────
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # ── Chat input ────────────────────────────────────────────────────────────
    if prompt := st.chat_input("Ask about collective agreement provisions..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Analyzing agreement..."):
                response = generate_response(prompt, selection, agreements, api_key)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

    # ── Example questions ─────────────────────────────────────────────────────
    if len(st.session_state.messages) == 0:
        st.markdown("### 💡 Example Questions")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Workload & Scheduling:**")
            st.markdown("- What are the instructor workload limits?")
            st.markdown("- How is program coordinator release time calculated?")
            st.markdown("- What are the overtime provisions?")
        with col2:
            st.markdown("**Leave & Benefits:**")
            st.markdown("- What types of leave are available?")
            st.markdown("- How does the sick leave system work?")
            st.markdown("- What are the vacation entitlements?")

    # ── Footer ────────────────────────────────────────────────────────────────
    if st.session_state.total_queries > 0:
        st.markdown("---")
        st.caption(f"💬 Total queries this session: {st.session_state.total_queries} | 🎯 Agreement: {selection}")

if __name__ == "__main__":
    main()
