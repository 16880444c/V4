import streamlit as st
import json
import anthropic
from datetime import datetime
import os
import requests

# Set page config
st.set_page_config(
    page_title="Coast Mountain College Collective Bargaining Assistant",
    page_icon="🤝",
    layout="wide"
)

def load_split_local_agreement() -> dict:
    """Load the local agreement from split JSON files"""
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
                data = json.load(f)
                local_agreement.update(data)
        except:
            pass
    
    return local_agreement

def load_bcgeu_support_agreement() -> dict:
    """Load the BCGEU Support agreement from split JSON files"""
    support_agreement = {}
    
    support_files = [
        'agreements/bcgeu_support/definitions_json.json',
        'agreements/bcgeu_support/articles_1_10_json.json',
        'agreements/bcgeu_support/articles_11_20_json.json',
        'agreements/bcgeu_support/articles_21_30_json.json',
        'agreements/bcgeu_support/articles_31_36_json.json',
        'agreements/bcgeu_support/appendices_json.json',
        'agreements/bcgeu_support/memoranda_json.json'
    ]
    
    for filename in support_files:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                support_agreement.update(data)
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
    """Load the CUPE Local agreement from JSON file"""
    try:
        with open('agreements/cupe_local/cupe_local.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def load_cupe_common_agreement() -> dict:
    """Load the CUPE Common agreement from local file or GitHub"""
    try:
        with open('agreements/cupe_common/cupe_common.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        try:
            github_url = "https://raw.githubusercontent.com/16880444c/V4/main/agreements/cupe_common/cupe_common.json"
            response = requests.get(github_url, timeout=10)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None

def load_builtin_agreements() -> tuple:
    """Load all built-in agreements from JSON files"""
    try:
        local_agreement = load_split_local_agreement()
        
        if not local_agreement or len(local_agreement) == 0:
            try:
                with open('agreements/bcgeu_local/complete_local.json', 'r', encoding='utf-8') as f:
                    local_agreement = json.load(f)
            except:
                local_agreement = None
        
        try:
            with open('agreements/bcgeu_common/complete_common.json', 'r', encoding='utf-8') as f:
                common_agreement = json.load(f)
        except:
            common_agreement = None
        
        support_agreement = load_bcgeu_support_agreement()
        cupe_local_agreement = load_cupe_local_agreement()
        cupe_common_agreement = load_cupe_common_agreement()
        
        return local_agreement, common_agreement, support_agreement, cupe_local_agreement, cupe_common_agreement
        
    except Exception:
        return None, None, None, None, None

def format_agreement_for_context(agreement: dict, agreement_name: str) -> str:
    """Convert agreement JSON to formatted text for Claude context"""
    context = f"=== {agreement_name.upper()} ===\n\n"
    
    for section_key, section_data in agreement.items():
        section_title = section_key.replace('_', ' ').upper()
        context += f"\n{section_title}:\n"
        context += "="*50 + "\n"
        
        if isinstance(section_data, dict):
            context += format_section_content(section_data, indent=0)
        else:
            context += str(section_data) + "\n"
        
        context += "\n"
    
    return context

def format_section_content(data: dict, indent: int = 0) -> str:
    """Recursively format nested dictionary content"""
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

def reset_conversation():
    """Reset conversation and selections"""
    keys_to_clear = ['messages', 'total_queries', 'conversation_context']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

def build_conversation_context(messages: list) -> str:
    """Build conversation context from message history"""
    if not messages:
        return ""
    
    context = "\n\nPREVIOUS CONVERSATION CONTEXT:\n"
    context += "="*50 + "\n"
    
    for i, message in enumerate(messages):
        if message["role"] == "user":
            context += f"\nPrevious Question {i//2 + 1}: {message['content']}\n"
        else:
            context += f"Previous Response {i//2 + 1}: {message['content'][:500]}...\n"
    
    context += "\nEND OF PREVIOUS CONVERSATION\n"
    context += "="*50 + "\n\n"
    
    return context

def generate_bargaining_response(query: str, analysis_type: str, local_agreement: dict, common_agreement: dict,
                                  support_agreement: dict, cupe_local_agreement: dict, cupe_common_agreement: dict,
                                  selection: str, api_key: str, is_followup: bool = False) -> str:
    """Generate response using Claude with complete agreement context for bargaining analysis"""

    # Build context based on selection
    context = ""

    if selection == "BCGEU Instructor - Local Only":
        if local_agreement:
            context = format_agreement_for_context(local_agreement, "Coast Mountain College Local Agreement")
        else:
            return "❌ **Error**: Local agreement not found."
    elif selection == "BCGEU Instructor - Common Only":
        if common_agreement:
            context = format_agreement_for_context(common_agreement, "BCGEU Common Agreement")
        else:
            return "❌ **Error**: Common agreement not found."
    elif selection == "BCGEU Instructor - Both Agreements":
        if local_agreement and common_agreement:
            context = format_agreement_for_context(local_agreement, "Coast Mountain College Local Agreement")
            context += "\n\n" + format_agreement_for_context(common_agreement, "BCGEU Common Agreement")
        else:
            return "❌ **Error**: One or both BCGEU agreement files not found."
    elif selection == "BCGEU Support Agreement":
        if support_agreement:
            context = format_agreement_for_context(support_agreement, "BCGEU Support Agreement")
        else:
            return "❌ **Error**: BCGEU Support agreement not found."
    elif selection == "CUPE - Local Agreement":
        if cupe_local_agreement:
            context = format_agreement_for_context(cupe_local_agreement, "CUPE Local Agreement")
        else:
            return "❌ **Error**: CUPE Local agreement not found."
    elif selection == "CUPE - Common Agreement":
        if cupe_common_agreement:
            context = format_agreement_for_context(cupe_common_agreement, "CUPE Common Agreement")
        else:
            return "❌ **Error**: CUPE Common Agreement not found."
    elif selection == "CUPE - Both Agreements":
        if cupe_local_agreement and cupe_common_agreement:
            context = format_agreement_for_context(cupe_local_agreement, "CUPE Local Agreement")
            context += "\n\n" + format_agreement_for_context(cupe_common_agreement, "CUPE Common Agreement")
        else:
            return "❌ **Error**: One or both CUPE agreement files not found."

    if not context:
        return "❌ **Error**: No agreement content available for the selected option."

    # Add conversation context for follow-up questions
    conversation_context = ""
    if is_followup and st.session_state.get('messages'):
        conversation_context = build_conversation_context(st.session_state.messages)

    # Brevity preamble applied to all prompts
    BREVITY_PREAMBLE = (
        "Be concise but complete. Aim for 500–700 words. Never truncate a section — if you begin a section, finish it fully. "
        "Use headers and bullets only where essential. Cite specific article numbers inline, e.g. [Article X.X].\n\n"
    )

    # -----------------------------------------------------------------------
    # SYSTEM PROMPTS — perspective and output format are both locked
    # -----------------------------------------------------------------------

    # Shared format rule appended to every prompt to prevent heading drift
    FORMAT_LOCK = """

CRITICAL FORMAT RULES — follow these exactly, every time, without exception:
- Use ONLY the section headings shown above, word-for-word. Do not rename, reorder, merge, or add sections.
- Every section heading must be formatted as bold markdown exactly as shown (e.g. **1. EXISTING AUTHORITY**).
- Do not add an introduction, preamble, summary, or closing paragraph outside the numbered sections.
- Do not vary the structure based on the question. Always produce all sections in order, even if a section is brief.
- Cite article numbers inline within sections, e.g. [Article X.X]. Do not create a separate citations section."""

    if analysis_type == "Management Proposal":
        system_prompt = BREVITY_PREAMBLE + """You are an expert collective bargaining strategist with 20+ years in higher education, retained exclusively by MANAGEMENT (the employer/college). You are advising the management bargaining team on how to ADVANCE and IMPLEMENT their own proposal. The user IS management. You are never advising the union. Do not suggest management reject, withdraw, or reconsider its own proposal.

Your response MUST use these four sections, in this order, with these exact headings:

**1. EXISTING AUTHORITY**
Does management already have the contractual right to act on this without bargaining? Cite relevant clauses. If current language already supports the proposal, note how it strengthens or clarifies management's position.

**2. JUSTIFICATION & RATIONALE**
Provide 3–5 compelling, operationally grounded reasons management can use to defend this proposal at the bargaining table (e.g., operational efficiency, fiscal responsibility, alignment with post-secondary sector norms).

**3. ANTICIPATED UNION OBJECTIONS & RESPONSES**
Identify the 2–3 most likely union objections and provide management's tactical response to each.

**4. IMPLEMENTATION STRATEGY**
How should management prioritize and advance this proposal? Note trade-offs, packaging opportunities with other bargaining items, or minimum acceptable fallback positions that still achieve management's core objective.""" + FORMAT_LOCK

    elif analysis_type == "Union Proposal":
        system_prompt = BREVITY_PREAMBLE + """You are an expert collective bargaining strategist with 20+ years in higher education, retained exclusively by MANAGEMENT (the employer/college). Analyze the union's proposal from management's perspective.

Your response MUST use these four sections, in this order, with these exact headings:

**1. IS THIS A REAL PROBLEM?**
Are current provisions already adequate? Cite relevant language that may already address the union's concern.

**2. COST & RISK**
Financial cost, loss of management flexibility, precedent dangers (3–5 bullets max).

**3. PROBLEMS WITH THE PROPOSAL**
Rights compromised, unintended consequences, conflicts with existing provisions.

**4. RECOMMENDED RESPONSE**
Reject / counter / accept with modifications — with brief rationale and any minimum counter-proposal language.""" + FORMAT_LOCK

    else:  # General Analysis
        system_prompt = BREVITY_PREAMBLE + """You are an expert collective bargaining strategist with 20+ years in higher education, retained by MANAGEMENT (the employer/college). Provide concise, management-oriented analysis.

Your response MUST use these three sections, in this order, with these exact headings:

**1. CURRENT STATE**
What the agreement says now. Key citations.

**2. KEY CONSIDERATIONS**
Legal, financial, operational, and employee-relations angles from management's perspective (3–5 bullets max).

**3. OPTIONS & RECOMMENDATION**
Two or three options with brief pros/cons, and your recommended approach for management.""" + FORMAT_LOCK

    if is_followup:
        system_prompt += "\n\nThis is a follow-up question. Build on the prior exchange without repeating context already established. Still use all sections with the exact headings above — do not skip or rename any section."

    # -----------------------------------------------------------------------
    # USER MESSAGE — reinforce perspective in the prompt itself
    # -----------------------------------------------------------------------

    if analysis_type == "Management Proposal":
        analysis_header = "MANAGEMENT PROPOSAL — ADVANCE THIS PROPOSAL"
        instruction = (
            "You are advising management. Help them advance, justify, and implement this proposal. "
            "Identify existing contractual authority, build the rationale, anticipate union resistance, "
            "and recommend a bargaining strategy to get this proposal across the line."
        )
    elif analysis_type == "Union Proposal":
        analysis_header = "UNION PROPOSAL — MANAGEMENT RESPONSE STRATEGY"
        instruction = "Analyze this union proposal from management's perspective and recommend how management should respond."
    else:
        analysis_header = "GENERAL BARGAINING ANALYSIS — MANAGEMENT PERSPECTIVE"
        instruction = "Provide analysis of this collective bargaining topic from management's perspective."

    user_message = f"""You are advising MANAGEMENT (the employer). Provide expert bargaining analysis from management's perspective.

{conversation_context}

{analysis_header}:
{instruction}

{"FOLLOW-UP " if is_followup else ""}QUESTION / PROPOSAL: {query}

COLLECTIVE AGREEMENT:
{context}"""

    client = anthropic.Anthropic(api_key=api_key)

    try:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        if 'total_queries' not in st.session_state:
            st.session_state.total_queries = 0
        st.session_state.total_queries += 1

        return response.content[0].text

    except anthropic.RateLimitError:
        return "⚠️ **Rate Limit Reached**\n\nThe system has reached its usage limit for this minute. Please wait a moment and try again."
    except anthropic.AuthenticationError as e:
        return f"⚠️ **Authentication Error**\n\nYour API key is invalid or missing. Please check your `ANTHROPIC_API_KEY`.\n\n`{e}`"
    except anthropic.BadRequestError as e:
        return f"⚠️ **Bad Request**\n\nThe request was rejected by the API (often a context length issue).\n\n`{e}`"
    except Exception as e:
        return f"⚠️ **Error: {type(e).__name__}**\n\n`{str(e)}`"

def process_strikethrough_text(text: str) -> str:
    """Process text to preserve strikethrough formatting by converting to [REMOVED: text] format"""
    import re
    
    patterns = [
        (r'~~(.+?)~~', r'[REMOVED: \1]'),
        (r'<s>(.+?)</s>', r'[REMOVED: \1]'),
        (r'<del>(.+?)</del>', r'[REMOVED: \1]'),
        (r'<strike>(.+?)</strike>', r'[REMOVED: \1]'),
    ]
    
    processed_text = text
    for pattern, replacement in patterns:
        processed_text = re.sub(pattern, replacement, processed_text, flags=re.DOTALL)
    
    return processed_text

def render_analysis_section(selected_agreement: str, api_key: str):
    """Render the analysis input section"""
    
    st.markdown("### 🎯 Analysis Type")
    analysis_type = st.selectbox(
        "What type of analysis do you need?",
        [
            "Management Proposal",
            "Union Proposal",
            "General Analysis"
        ],
        help="Select the type of bargaining analysis you need"
    )
    
    if analysis_type == "Management Proposal":
        st.info("📋 **Management Proposal Analysis**: Get strategic advice on how to advance and implement management's own proposals — including existing authority, justification, anticipated union objections, and bargaining strategy.")
    elif analysis_type == "Union Proposal":
        st.info("🔍 **Union Proposal Analysis**: Examine union requests from management's perspective, identify underlying issues, suggest alternatives, and recommend response strategies.")
    else:
        st.info("📊 **General Analysis**: Management-oriented analysis of collective bargaining topics, trends, and strategic considerations.")
    
    st.markdown("---")
    
    if not st.session_state.messages:
        section_title = "💬 Describe Your Proposal or Question"
        placeholder_text = f"""Enter your {analysis_type.lower()} details here...

Examples:
• "We want to change the workload formula to include online course weighting"
• "The union is proposing 3 additional professional development days"
• "What are the trends in sabbatical leave provisions?"

💡 STRIKETHROUGH TIPS:
• If pasting from Word/Google Docs loses formatting, manually type [REMOVED: old text] new text
• Or use ~~text~~ markdown format for deletions
• Example: "Change from [REMOVED: 15 hours] to 12 hours per week"
"""
        form_key = "initial_analysis_form"
        button_text = "🔍 Analyze"
    else:
        section_title = "💬 Continue the Analysis"
        placeholder_text = "Ask a follow-up question or explore another aspect..."
        form_key = "followup_analysis_form"
        button_text = "💬 Continue Analysis"
    
    st.markdown(f"### {section_title}")
    
    if not st.session_state.messages:
        st.markdown("""
        <div class="strikethrough-help">
        <strong>📝 Handling Text Changes:</strong><br>
        • For deleted text: Use [REMOVED: old text] or ~~old text~~<br>
        • For added text: Just type the new text normally<br>
        • Example: "Change salary from [REMOVED: $50,000] to $55,000"
        </div>
        """, unsafe_allow_html=True)
    
    with st.form(key=form_key, clear_on_submit=True):
        user_question = st.text_area(
            "",
            placeholder=placeholder_text,
            height=150,
            key=f"analysis_input_{len(st.session_state.messages)}",
            label_visibility="collapsed",
            help="💡 Be specific about the proposed changes or issues you want analyzed."
        )
        
        col1, col2, col3, col4 = st.columns([1, 1.5, 1.5, 1])
        
        with col2:
            submit_button = st.form_submit_button(button_text, type="primary", use_container_width=True)
        
        with col3:
            new_analysis_button = st.form_submit_button("🔄 New Analysis", help="Reset and start fresh", use_container_width=True)
    
    if new_analysis_button:
        reset_conversation()
        return None, None, False
    
    if submit_button and user_question:
        if not selected_agreement or selected_agreement == "Please select an agreement...":
            st.error("⚠️ **Please select an agreement above before starting analysis.**")
            return None, None, False
        else:
            processed_question = process_strikethrough_text(user_question)
            is_followup = len(st.session_state.messages) > 0
            return processed_question, analysis_type, is_followup
    
    return None, None, False

def main():
    st.markdown("""
    <style>
    .big-font {
        font-size: 2.5em !important;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.5em;
    }
    .subtitle {
        text-align: center;
        color: #666;
        font-style: italic;
        margin-bottom: 2em;
    }
    .status-success {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 12px;
        margin: 15px 0;
        color: #155724;
        font-weight: 600;
    }
    .status-info {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 8px;
        padding: 10px;
        margin: 10px 0;
        color: #0c5460;
    }
    .status-waiting {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 12px;
        margin: 15px 0;
        color: #6c757d;
        font-weight: 500;
    }
    .analysis-type-badge {
        background-color: #e7f3ff;
        border: 1px solid #b3d9ff;
        border-radius: 20px;
        padding: 5px 15px;
        color: #0066cc;
        font-weight: 600;
        display: inline-block;
        margin: 5px 0;
    }
    .footer-stats {
        text-align: center;
        color: #6c757d;
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        margin-top: 20px;
        border: 1px solid #dee2e6;
    }
    .strikethrough-help {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 12px;
        margin: 10px 0;
        color: #856404;
    }
    textarea {
        font-family: 'Courier New', monospace !important;
    }
    </style>

    <script>
    document.addEventListener('DOMContentLoaded', function() {
        const textareas = document.querySelectorAll('textarea');
        textareas.forEach(function(textarea) {
            textarea.addEventListener('paste', function(e) {
                e.preventDefault();
                const clipboardData = e.clipboardData || window.clipboardData;
                const pastedData = clipboardData.getData('text/html') || clipboardData.getData('text/plain');
                
                let processedData = pastedData;
                if (pastedData.includes('<s>') || pastedData.includes('<del>') || pastedData.includes('<strike>')) {
                    processedData = pastedData
                        .replace(/<s[^>]*>(.*?)<\/s>/gi, '[REMOVED: $1]')
                        .replace(/<del[^>]*>(.*?)<\/del>/gi, '[REMOVED: $1]')
                        .replace(/<strike[^>]*>(.*?)<\/strike>/gi, '[REMOVED: $1]')
                        .replace(/<[^>]*>/g, '');
                }
                
                const start = textarea.selectionStart;
                const end = textarea.selectionEnd;
                const text = textarea.value;
                const before = text.substring(0, start);
                const after = text.substring(end, text.length);
                textarea.value = before + processedData + after;
                textarea.selectionStart = textarea.selectionEnd = start + processedData.length;
                
                const event = new Event('input', { bubbles: true });
                textarea.dispatchEvent(event);
            });
        });
    });
    </script>
    """, unsafe_allow_html=True)

    st.markdown('<div class="big-font">🤝 Coast Mountain College Collective Bargaining Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Strategic analysis for collective bargaining proposals and negotiations</div>', unsafe_allow_html=True)

    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'total_queries' not in st.session_state:
        st.session_state.total_queries = 0
    if 'agreements_loaded' not in st.session_state:
        st.session_state.agreements_loaded = False
    if 'local_agreement' not in st.session_state:
        st.session_state.local_agreement = None
    if 'common_agreement' not in st.session_state:
        st.session_state.common_agreement = None
    if 'support_agreement' not in st.session_state:
        st.session_state.support_agreement = None
    if 'cupe_local_agreement' not in st.session_state:
        st.session_state.cupe_local_agreement = None
    if 'cupe_common_agreement' not in st.session_state:
        st.session_state.cupe_common_agreement = None

    # Get API key
    api_key = None
    try:
        api_key = st.secrets["ANTHROPIC_API_KEY"]
    except:
        try:
            api_key = os.getenv("ANTHROPIC_API_KEY")
        except:
            pass

    if not api_key:
        st.error("🔑 Anthropic API key not found. Please set it in Streamlit secrets or environment variables.")
        st.stop()

    # Load agreements once
    if not st.session_state.agreements_loaded:
        with st.spinner("Loading collective agreements..."):
            local_agreement, common_agreement, support_agreement, cupe_local_agreement, cupe_common_agreement = load_builtin_agreements()

            st.session_state.local_agreement = local_agreement
            st.session_state.common_agreement = common_agreement
            st.session_state.support_agreement = support_agreement
            st.session_state.cupe_local_agreement = cupe_local_agreement
            st.session_state.cupe_common_agreement = cupe_common_agreement
            st.session_state.agreements_loaded = True

    # Build agreement options list
    agreement_options = ["Please select an agreement..."]

    if st.session_state.local_agreement and st.session_state.common_agreement:
        agreement_options.extend([
            "BCGEU Instructor - Local Only",
            "BCGEU Instructor - Common Only",
            "BCGEU Instructor - Both Agreements"
        ])

    if st.session_state.support_agreement:
        agreement_options.append("BCGEU Support Agreement")

    if st.session_state.cupe_local_agreement:
        agreement_options.append("CUPE - Local Agreement")
    if st.session_state.cupe_common_agreement:
        agreement_options.append("CUPE - Common Agreement")
    if st.session_state.cupe_local_agreement and st.session_state.cupe_common_agreement:
        agreement_options.append("CUPE - Both Agreements")

    # Agreement selection (only show if no active conversation)
    if not st.session_state.messages:
        st.markdown("### 📋 Select Agreement")

        current_selection = st.session_state.get('agreement_selection', 'Please select an agreement...')
        if current_selection not in agreement_options:
            current_selection = 'Please select an agreement...'

        selected_agreement = st.selectbox(
            "Choose which agreement to analyze:",
            options=agreement_options,
            index=agreement_options.index(current_selection),
            key='agreement_selectbox'
        )

        if selected_agreement != st.session_state.get('agreement_selection'):
            st.session_state.agreement_selection = selected_agreement

        if selected_agreement and selected_agreement != "Please select an agreement...":
            st.markdown(f'<div class="status-success">✅ Selected: {selected_agreement}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-waiting">ℹ️ Please select an agreement to begin</div>', unsafe_allow_html=True)

        st.markdown("---")

        user_question, analysis_type, is_followup = render_analysis_section(selected_agreement, api_key)

    else:
        selected_agreement = st.session_state.get('agreement_selection', 'Please select an agreement...')

        st.markdown(f'<div class="status-success">✅ Current Agreement: {selected_agreement}</div>', unsafe_allow_html=True)

        if 'current_analysis_type' in st.session_state:
            st.markdown(f'<div class="analysis-type-badge">📊 Analysis Type: {st.session_state.current_analysis_type}</div>', unsafe_allow_html=True)

        st.markdown("---")

        st.markdown("### 📝 Analysis History")

        for message in st.session_state.messages:
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.markdown(f"**Your Request:** {message['content']}")
            else:
                with st.chat_message("assistant"):
                    st.markdown("**Strategic Analysis:**")
                    st.markdown(message["content"])

        st.markdown("---")

        user_question, analysis_type, is_followup = render_analysis_section(selected_agreement, api_key)

    # Process submitted question
    if user_question and analysis_type:
        st.session_state.current_analysis_type = analysis_type
        st.session_state.messages.append({"role": "user", "content": user_question})

        with st.spinner("Conducting strategic analysis..."):
            response = generate_bargaining_response(
                user_question,
                analysis_type,
                st.session_state.local_agreement,
                st.session_state.common_agreement,
                st.session_state.support_agreement,
                st.session_state.cupe_local_agreement,
                st.session_state.cupe_common_agreement,
                selected_agreement,
                api_key,
                is_followup
            )
            st.session_state.messages.append({"role": "assistant", "content": response})

        st.rerun()

    # Footer stats
    if st.session_state.total_queries > 0:
        current_selection = st.session_state.get('agreement_selection', 'None')
        analysis_count = len(st.session_state.messages) // 2
        current_analysis = st.session_state.get('current_analysis_type', 'None')
        st.markdown(f"""
        <div class="footer-stats">
            📊 Total analyses: {st.session_state.total_queries} | 🎯 Current agreement: {current_selection} | 📈 Analysis type: {current_analysis} | 💬 Exchanges: {analysis_count}
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
