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
    
    # List of all split files with the correct naming pattern
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
    
    # Load each file and merge into the complete agreement
    for filename in split_files:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                local_agreement.update(data)
        except:
            pass  # Silently skip any files that can't be loaded
    
    return local_agreement

def load_bcgeu_support_agreement() -> dict:
    """Load the BCGEU Support agreement from split JSON files"""
    support_agreement = {}
    
    # List of all BCGEU support split files
    support_files = [
        'agreements/bcgeu_support/definitions_json.json',
        'agreements/bcgeu_support/articles_1_10_json.json',
        'agreements/bcgeu_support/articles_11_20_json.json',
        'agreements/bcgeu_support/articles_21_30_json.json',
        'agreements/bcgeu_support/articles_31_36_json.json',
        'agreements/bcgeu_support/appendices_json.json',
        'agreements/bcgeu_support/memoranda_json.json'
    ]
    
    # Load each file and merge into the complete agreement
    for filename in support_files:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                support_agreement.update(data)
        except:
            pass  # Silently skip any files that can't be loaded
    
    # If no files were loaded, try the old single file as fallback
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
    """Load the CUPE Common agreement from GitHub or local file"""
    # First try to load from local file
    try:
        with open('agreements/cupe_common/cupe_common.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        # If local file doesn't exist, try to fetch from GitHub
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
        # Load BCGEU agreements
        # Try loading split files first
        local_agreement = load_split_local_agreement()
        
        # Only fall back to complete file if NO sections were loaded from splits
        if not local_agreement or len(local_agreement) == 0:
            complete_local_path = 'agreements/bcgeu_local/complete_local.json'
            try:
                with open(complete_local_path, 'r', encoding='utf-8') as f:
                    local_agreement = json.load(f)
            except:
                local_agreement = None
        
        # Load common agreement
        common_agreement_path = 'agreements/bcgeu_common/complete_common.json'
        try:
            with open(common_agreement_path, 'r', encoding='utf-8') as f:
                common_agreement = json.load(f)
        except:
            common_agreement = None
        
        # Load BCGEU Support agreement (now from multiple files)
        support_agreement = load_bcgeu_support_agreement()
        
        # Load CUPE agreements
        cupe_local_agreement = load_cupe_local_agreement()
        cupe_common_agreement = load_cupe_common_agreement()
        
        return local_agreement, common_agreement, support_agreement, cupe_local_agreement, cupe_common_agreement
        
    except Exception:
        return None, None, None, None, None

def format_agreement_for_context(agreement: dict, agreement_name: str) -> str:
    """Convert agreement JSON to formatted text for Claude context"""
    context = f"=== {agreement_name.upper()} ===\n\n"
    
    # Process each section generically
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
    # Clear all relevant session state
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
            context += f"Previous Response {i//2 + 1}: {message['content'][:500]}...\n"  # Truncate for context
    
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
    
    # Determine system prompt based on analysis type
    if analysis_type == "Management Proposal":
        system_prompt = """You are an expert collective bargaining strategist and labor relations specialist with 20+ years of experience in higher education negotiations. You provide balanced, strategic analysis for collective bargaining proposals.

ANALYSIS FRAMEWORK FOR MANAGEMENT PROPOSALS:

1. **EXISTING RIGHTS ASSESSMENT**
   - First, thoroughly examine if management already has the authority to implement this change
   - Review management rights clauses, current language, and precedents
   - If rights already exist, explain how to exercise them without bargaining

2. **STRATEGIC IMPACT ANALYSIS**
   - Operational impacts (positive and negative)
   - Financial implications (costs, savings, resources needed)
   - Employee relations effects
   - Union reaction assessment
   - Legal and compliance considerations

3. **BARGAINING RECOMMENDATIONS**
   - If change requires bargaining: prioritization level (high/medium/low)
   - Timing considerations
   - Potential trade-offs or concessions needed
   - Implementation challenges
   - Alternative approaches to achieve similar outcomes

4. **STRUCTURED RESPONSE FORMAT**
   Use clear headers and provide:
   - Executive Summary
   - Current Authority Analysis
   - Impact Assessment
   - Strategic Recommendations
   - Implementation Considerations

CITATION REQUIREMENTS:
- Include specific citations: [Agreement - Article X.X: Title]
- Quote relevant language when applicable
- Reference definitions, appendices, and memoranda as needed

Provide balanced, professional analysis that considers both opportunities and risks."""

    elif analysis_type == "Union Proposal":
        system_prompt = """You are an expert collective bargaining strategist and labor relations specialist with 20+ years of experience in higher education negotiations. You provide CRITICAL, management-focused analysis of union proposals.

ANALYSIS FRAMEWORK FOR UNION PROPOSALS (MANAGEMENT PERSPECTIVE):

1. **CRITICAL ISSUE ASSESSMENT**
   - Is this really a problem that needs solving?
   - How much of this is union positioning vs. legitimate concern?
   - Are current provisions already adequate?
   - Is this an attempt to expand beyond reasonable scope?

2. **COST AND IMPACT ANALYSIS** 
   - Financial costs (immediate and long-term)
   - Operational disruptions and administrative burden
   - Loss of management flexibility and rights
   - Precedent dangers for future negotiations
   - Impact on institutional mission and efficiency

3. **PROBLEMS WITH THE PROPOSAL**
   - What management rights would be compromised?
   - Unintended consequences and loopholes
   - How this could be exploited or misused
   - Conflicts with other agreement provisions
   - Legal compliance risks

4. **STRATEGIC RISKS**
   - Signal this sends to union about future demands
   - Impact on other bargaining units (pattern bargaining)
   - Public perception and stakeholder concerns
   - Long-term institutional flexibility
   - Competitive disadvantage vs. other institutions

5. **RESISTANCE STRATEGIES**
   - Strong rationale for rejection
   - Alternative approaches that maintain management control
   - Counter-proposals that address minimal concerns
   - Information to gather to strengthen rejection
   - Communication strategy to justify position

6. **IF FORCED TO NEGOTIATE**
   - Minimum modifications to make it barely acceptable
   - Sunset clauses and review mechanisms
   - Offsetting concessions to demand from union
   - Ways to limit scope and application

APPROACH:
- Default position should be SKEPTICAL and RESISTANT
- Focus on protecting management rights and institutional flexibility
- Emphasize costs, risks, and unintended consequences
- Look for ways the proposal could backfire or be misused
- Frame union demands as overreach where appropriate
- Protect the institution's long-term interests

CITATION REQUIREMENTS:
- Include specific citations: [Agreement - Article X.X: Title]
- Quote current language that already addresses issues
- Reference management rights provisions
- Show conflicts with existing provisions

Provide CRITICAL analysis that helps management understand the risks and build strong resistance to problematic union demands."""

    else:  # General Analysis
        system_prompt = """You are an expert collective bargaining strategist and labor relations specialist with 20+ years of experience in higher education negotiations. You provide comprehensive, balanced analysis for collective bargaining questions.

COMPREHENSIVE ANALYSIS APPROACH:

1. **CONTEXTUAL UNDERSTANDING**
   - Current state analysis using agreement provisions
   - Historical context and trends
   - Stakeholder perspectives (management, union, employees)
   - External factors (legal, economic, industry trends)

2. **MULTI-DIMENSIONAL ANALYSIS**
   - Legal and contractual implications
   - Financial impact assessment
   - Operational considerations
   - Employee relations effects
   - Strategic positioning for future negotiations

3. **BALANCED RECOMMENDATIONS**
   - Multiple options with pros/cons
   - Risk assessment for each approach
   - Implementation considerations
   - Timeline and resource requirements
   - Success metrics

4. **STRATEGIC INSIGHTS**
   - Leverage points and opportunities
   - Potential challenges and mitigation strategies
   - Best practices from similar institutions
   - Future-proofing considerations

CITATION REQUIREMENTS:
- Include specific citations: [Agreement - Article X.X: Title]
- Quote relevant language to support analysis
- Reference related provisions and precedents

Provide thorough, professional analysis that considers all angles and helps inform strategic decision-making."""

    # Add follow-up instruction if needed
    follow_up_instruction = ""
    if is_followup:
        follow_up_instruction = "\n\nIMPORTANT: This is a FOLLOW-UP question in an ongoing conversation. Consider the previous conversation context when formulating your response. Build upon previous analysis where relevant, and reference earlier discussion points when appropriate."

    system_prompt += follow_up_instruction

    # Customize user message based on analysis type
    if analysis_type == "Management Proposal":
        analysis_header = "MANAGEMENT PROPOSAL ANALYSIS"
        instruction = "Analyze this proposed change from management's perspective. Examine existing rights, assess impacts, and provide strategic recommendations."
    elif analysis_type == "Union Proposal":
        analysis_header = "UNION PROPOSAL ANALYSIS"
        instruction = "Analyze this union proposal. Identify the underlying issues, assess the request, suggest alternatives, and provide strategic response recommendations."
    else:
        analysis_header = "GENERAL BARGAINING ANALYSIS"
        instruction = "Provide comprehensive analysis of this collective bargaining topic."

    user_message = f"""Based on the complete collective agreement provisions below, provide expert collective bargaining analysis:

{conversation_context}

{analysis_header}:
{instruction}

{"FOLLOW-UP " if is_followup else ""}QUESTION: {query}

COMPLETE COLLECTIVE AGREEMENT CONTENT:
{context}

Provide structured, balanced analysis with specific citations and strategic recommendations."""

    client = anthropic.Anthropic(api_key=api_key)
    
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            temperature=0.2,
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
    
    except anthropic.APIError as e:
        return f"⚠️ **API Error**\n\nThere was an issue connecting to the AI service. Please try again in a moment."
    
    except Exception as e:
        return f"⚠️ **Unexpected Error**\n\nSomething went wrong while processing your request. Please try again."

def process_strikethrough_text(text: str) -> str:
    """Process text to preserve strikethrough formatting by converting to [REMOVED: text] format"""
    import re
    
    # Pattern to match various strikethrough formats
    patterns = [
        (r'~~(.+?)~~', r'[REMOVED: \1]'),  # Markdown strikethrough
        (r'<s>(.+?)</s>', r'[REMOVED: \1]'),  # HTML strikethrough
        (r'<del>(.+?)</del>', r'[REMOVED: \1]'),  # HTML del tag
        (r'<strike>(.+?)</strike>', r'[REMOVED: \1]'),  # HTML strike tag
    ]
    
    processed_text = text
    for pattern, replacement in patterns:
        processed_text = re.sub(pattern, replacement, processed_text, flags=re.DOTALL)
    
    return processed_text

def render_analysis_section(selected_agreement: str, api_key: str):
    """Render the analysis input section"""
    
    # Analysis type selection
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
    
    # Show description based on selection
    if analysis_type == "Management Proposal":
        st.info("📋 **Management Proposal Analysis**: Evaluate proposed changes from management, assess existing rights, analyze impacts, and provide strategic recommendations.")
    elif analysis_type == "Union Proposal":
        st.info("🔍 **Union Proposal Analysis**: Examine union requests, identify underlying issues, suggest alternatives, and recommend response strategies.")
    else:
        st.info("📊 **General Analysis**: Comprehensive analysis of collective bargaining topics, trends, and strategic considerations.")
    
    st.markdown("---")
    
    # Question input section
    if not st.session_state.messages:
        section_title = "💬 Describe Your Proposal or Question"
        placeholder_text = f"""Enter your {analysis_type.lower()} details here...

Examples:
• "We want to change the workload formula to include online course weighting"
• "The union is proposing 3 additional professional development days"
• "What are the trends in sabbatical leave provisions?"

Note: Strikethrough text (~~text~~) will be preserved as [REMOVED: text] to show deletions.
"""
        form_key = "initial_analysis_form"
        button_text = "🔍 Analyze"
    else:
        section_title = "💬 Continue the Analysis"
        placeholder_text = "Ask a follow-up question or explore another aspect..."
        form_key = "followup_analysis_form"
        button_text = "💬 Continue Analysis"
    
    st.markdown(f"### {section_title}")
    
    # Create form
    with st.form(key=form_key, clear_on_submit=True):
        user_question = st.text_area(
            "",
            placeholder=placeholder_text,
            height=150,
            key=f"analysis_input_{len(st.session_state.messages)}",
            label_visibility="collapsed",
            help="💡 Be specific about the proposed changes or issues you want analyzed. Strikethrough text will be preserved to show removals."
        )
        
        # Button layout
        col1, col2, col3, col4 = st.columns([1, 1.5, 1.5, 1])
        
        with col2:
            submit_button = st.form_submit_button(button_text, type="primary", use_container_width=True)
        
        with col3:
            new_analysis_button = st.form_submit_button("🔄 New Analysis", help="Reset and start fresh", use_container_width=True)
    
    # Handle new analysis button
    if new_analysis_button:
        reset_conversation()
        return None, None, False
    
    # Handle question submission
    if submit_button and user_question:
        # Check if an agreement is selected
        if not selected_agreement or selected_agreement == "Please select an agreement...":
            st.error("⚠️ **Please select an agreement above before starting analysis.**")
            return None, None, False
        else:
            # Process strikethrough text
            processed_question = process_strikethrough_text(user_question)
            is_followup = len(st.session_state.messages) > 0
            return processed_question, analysis_type, is_followup
    
    return None, None, False

def main():
    # Add CSS styling
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
    </style>
    """, unsafe_allow_html=True)
    
    # Main title
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
    
    # Create list of available options
    agreement_options = ["Please select an agreement..."]
    
    # Add BCGEU Instructor options if available
    if st.session_state.local_agreement and st.session_state.common_agreement:
        agreement_options.extend([
            "BCGEU Instructor - Local Only",
            "BCGEU Instructor - Common Only", 
            "BCGEU Instructor - Both Agreements"
        ])
    
    # Add BCGEU Support option if available
    if st.session_state.support_agreement:
        agreement_options.append("BCGEU Support Agreement")
    
    # Add CUPE options if available
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
        
        # Update session state
        if selected_agreement != st.session_state.get('agreement_selection'):
            st.session_state.agreement_selection = selected_agreement
        
        # Show selection status
        if selected_agreement and selected_agreement != "Please select an agreement...":
            st.markdown(f'<div class="status-success">✅ Selected: {selected_agreement}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-waiting">ℹ️ Please select an agreement to begin</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Analysis section
        user_question, analysis_type, is_followup = render_analysis_section(selected_agreement, api_key)
        
    else:
        # If there's an active conversation, get the stored agreement selection
        selected_agreement = st.session_state.get('agreement_selection', 'Please select an agreement...')
        
        # Show current selection at top but not editable during conversation
        st.markdown(f'<div class="status-success">✅ Current Agreement: {selected_agreement}</div>', unsafe_allow_html=True)
        
        # Show current analysis type if stored
        if 'current_analysis_type' in st.session_state:
            st.markdown(f'<div class="analysis-type-badge">📊 Analysis Type: {st.session_state.current_analysis_type}</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Display conversation history first
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
        
        # Then show analysis section for follow-ups
        user_question, analysis_type, is_followup = render_analysis_section(selected_agreement, api_key)
    
    # Process the question when submitted
    if user_question and analysis_type:
        # Store analysis type for future reference
        st.session_state.current_analysis_type = analysis_type
        
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_question})
        
        # Generate and display response
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
        
        # Rerun to show the new conversation state
        st.rerun()
    
    # Footer with stats (only show if there are queries)
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
