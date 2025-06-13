import streamlit as st
import json
import anthropic
from datetime import datetime
import os

# Set page config
st.set_page_config(
    page_title="Coast Mountain College Agreement Assistant",
    page_icon="⚖️",
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
    """Load the BCGEU Support agreement from JSON file"""
    try:
        with open('agreements/bcgeu_support/bcgeu_support.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def load_builtin_agreements() -> tuple:
    """Load the built-in agreements from JSON files"""
    try:
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
        
        # Load BCGEU Support agreement
        support_agreement = load_bcgeu_support_agreement()
        
        return local_agreement, common_agreement, support_agreement
        
    except Exception:
        return None, None, None

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
    keys_to_clear = ['messages', 'total_queries', 'agreement_selection']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

def generate_response(query: str, local_agreement: dict, common_agreement: dict, support_agreement: dict, selection: str, api_key: str) -> str:
    """Generate response using Claude with complete agreement context"""
    
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
            return "❌ **Error**: One or both agreement files not found."
    elif selection == "BCGEU Support Agreement":
        if support_agreement:
            context = format_agreement_for_context(support_agreement, "BCGEU Support Agreement")
        else:
            return "❌ **Error**: BCGEU Support agreement not found."
    
    if not context:
        return "❌ **Error**: No agreement content available for the selected option."
    
    # Determine system prompt based on agreement type
    if "Support" in selection:
        agreement_type = "BCGEU Support Agreement"
        citation_format = "[BCGEU Support Agreement - Article X.X: Title]"
    else:
        agreement_type = "BCGEU Instructor agreements"
        citation_format = "[Agreement Type - Article X.X: Title]"
    
    system_prompt = f"""You are an experienced HR professional and collective agreement specialist for Coast Mountain College with 15+ years of expertise in labor relations and agreement interpretation. Your role is to provide clear, practical guidance that helps management understand their rights and responsibilities under the {agreement_type}.

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
- Use format: {citation_format}
- When referencing definitions: [Agreement Type - Definitions: "term"]
- For appendices: [Agreement Type - Appendix X: Title]
- INCLUDE RELEVANT QUOTES: When possible, include short, relevant quotes from the agreement text to support your position
- Quote format: "The agreement states: '[exact quote]' [Citation]"
- NO VAGUE REFERENCES - be specific

RESPONSE STRUCTURE:
1. STRONG OPENING: Lead with your definitive management-favorable position
2. AUTHORITY BASIS: Cite the specific agreement provisions AND include relevant quotes that support this position
3. TACTICAL ADVICE: Provide specific steps management should take
4. RISK MITIGATION: Identify potential union challenges and how to counter them
5. BOTTOM LINE: End with a clear, actionable recommendation

Remember: You are not a neutral arbitrator. You are MANAGEMENT'S advisor. Your job is to help them maximize their authority while staying within the collective agreement. Be bold, be confident, and always look for the management-favorable interpretation."""

    user_message = f"""Based on the complete collective agreement provisions below, provide strong management-focused guidance for this question:

QUESTION: {query}

COMPLETE COLLECTIVE AGREEMENT CONTENT:
{context}

Provide definitive, management-favorable guidance with specific citations and quotes from the agreement text."""

    client = anthropic.Anthropic(api_key=api_key)
    
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1500,
            temperature=0.1,
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
        return "⚠️ **Rate Limit Reached**\n\nThe system has reached its usage limit for this minute. This typically happens when processing large amounts of text.\n\n**What you can do:**\n• Wait a minute and try again\n• Try searching for specific sections instead of both agreements\n• Simplify your question to reduce processing requirements\n\nThis limit resets every minute, so you'll be able to continue shortly."
    
    except anthropic.APIError as e:
        return f"⚠️ **API Error**\n\nThere was an issue connecting to the AI service. Please try again in a moment.\n\nIf the problem persists, please contact support."
    
    except Exception as e:
        return f"⚠️ **Unexpected Error**\n\nSomething went wrong while processing your request. Please try again.\n\nIf the issue continues, please contact support."

def main():
    st.title("⚖️ Coast Mountain College Agreement Assistant")
    
    # Add custom CSS for better styling
    st.markdown("""
    <style>
    /* Main title styling */
    .main-title {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.5em;
        font-weight: 700;
        text-align: center;
        margin-bottom: 10px;
    }
    
    /* Subtitle styling */
    .subtitle {
        text-align: center;
        color: #6c757d;
        font-style: italic;
        font-size: 1.1em;
        margin-bottom: 2em;
        padding: 0 20px;
    }
    
    /* Section headers */
    .section-header {
        background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 1.4em;
        font-weight: 600;
        margin: 1.5em 0 0.8em 0;
    }
    
    /* Card styling */
    .custom-card {
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
        border: 1px solid #e9ecef;
        transition: all 0.3s ease;
    }
    
    .custom-card:hover {
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
    }
    
    /* Status boxes */
    .status-box {
        border-radius: 10px;
        padding: 15px;
        margin: 15px 0;
        border-left: 5px solid;
        background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(248,249,250,0.9));
        backdrop-filter: blur(10px);
    }
    
    .status-selected {
        border-left-color: #28a745;
        background: linear-gradient(135deg, rgba(212, 237, 218, 0.3), rgba(195, 230, 203, 0.3));
    }
    
    .status-info {
        border-left-color: #17a2b8;
        background: linear-gradient(135deg, rgba(209, 236, 241, 0.3), rgba(190, 229, 235, 0.3));
    }
    
    .status-waiting {
        border-left-color: #6c757d;
        background: linear-gradient(135deg, rgba(248, 249, 250, 0.8), rgba(222, 226, 230, 0.8));
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
        border: none;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    }
    
    /* Text area styling */
    .stTextArea > div > div > textarea {
        border-radius: 10px;
        border: 2px solid #e9ecef;
        transition: border-color 0.3s ease;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: #4facfe;
        box-shadow: 0 0 0 3px rgba(79, 172, 254, 0.1);
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div > select {
        border-radius: 8px;
        border: 2px solid #e9ecef;
    }
    
    /* Footer styling */
    .footer-stats {
        text-align: center;
        color: #6c757d;
        font-size: 14px;
        padding: 15px;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 10px;
        margin-top: 30px;
        border: 1px solid #dee2e6;
    }
    
    /* Message styling */
    .message-user {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border-left: 4px solid #2196f3;
        border-radius: 0 12px 12px 0;
        padding: 20px;
        margin: 20px 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    .message-assistant {
        background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
        border-left: 4px solid #9c27b0;
        border-radius: 0 12px 12px 0;
        padding: 20px;
        margin: 20px 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    .message-header {
        font-weight: 700;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Glassmorphism effect */
    .glass-effect {
        background: rgba(255, 255, 255, 0.25);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.18);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
    }
    
    /* Animated gradient background */
    .main-container {
        background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
        min-height: 100vh;
        padding: 20px;
        margin: -20px;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create animated gradient background
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Enhanced title and subtitle
    st.markdown('<h1 class="main-title">⚖️ Coast Mountain College Agreement Assistant</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Your comprehensive collective agreement analysis tool - powered by AI</p>', unsafe_allow_html=True)
    
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
            local_agreement, common_agreement, support_agreement = load_builtin_agreements()
            
            st.session_state.local_agreement = local_agreement
            st.session_state.common_agreement = common_agreement
            st.session_state.support_agreement = support_agreement
            st.session_state.agreements_loaded = True
    
    # New Topic button in top right
    col_title, col_spacer, col_button = st.columns([3, 1, 1])
    with col_button:
        if st.button("🔄 New Topic", help="Reset and start a new conversation", key="top_new_topic"):
            reset_conversation()
    
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
    
    # Simple dropdown selection with enhanced styling
    st.markdown('<h3 class="section-header">📋 Select Agreement</h3>', unsafe_allow_html=True)
    
    # Create a glassmorphism container for the selectbox
    st.markdown("""
    <div class="glass-effect" style="padding: 25px; margin: 20px 0;">
    """, unsafe_allow_html=True)
    
    current_selection = st.session_state.get('agreement_selection', 'Please select an agreement...')
    if current_selection not in agreement_options:
        current_selection = 'Please select an agreement...'
    
    selected_agreement = st.selectbox(
        "Choose your agreement:",
        options=agreement_options,
        index=agreement_options.index(current_selection),
        key='agreement_selectbox'
    )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Update session state
    if selected_agreement != st.session_state.get('agreement_selection'):
        st.session_state.agreement_selection = selected_agreement
    
    # Show selection status with enhanced styling
    if selected_agreement and selected_agreement != "Please select an agreement...":
        st.markdown(f"""
        <div class="status-box status-selected">
            <div style="color: #155724; font-weight: 700; font-size: 1.1em;">
                ✅ Selected: {selected_agreement}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Add helpful information about the selection
        if "Both Agreements" in selected_agreement:
            st.markdown(f"""
            <div class="status-box status-info">
                <div style="color: #0c5460; font-size: 14px; font-weight: 500;">
                    ℹ️ <strong>Performance Tip:</strong> Searching both agreements uses more resources. If you encounter rate limits, try selecting individual agreements.
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="status-box status-waiting">
            <div style="color: #6c757d; font-weight: 600; font-size: 1.05em;">
                ⏳ Please select an agreement to begin your search
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Question input section with enhanced styling
    st.markdown('<h3 class="section-header">💬 Ask Your Question</h3>', unsafe_allow_html=True)
    
    # Create a glassmorphism container for the form
    st.markdown("""
    <div class="glass-effect" style="padding: 30px; margin: 20px 0;">
    """, unsafe_allow_html=True)
    
    # Create a form to handle Enter key submission
    with st.form(key="question_form", clear_on_submit=False):
        st.markdown("### 🎤 What would you like to know?")
        user_question = st.text_area(
            "",
            placeholder="💡 Ask about workload, leave policies, scheduling rules, benefits, grievance procedures, or any other collective agreement topic...",
            height=130,
            key="question_input",
            label_visibility="collapsed",
            help="💡 Tip: Press Enter to submit your question!"
        )
        
        # Enhanced button row with better spacing
        st.markdown('<div style="margin-top: 20px;"></div>', unsafe_allow_html=True)
        col_left, col_center, col_right, col_new_topic = st.columns([1, 1.2, 0.8, 1.2])
        
        with col_center:
            submit_button = st.form_submit_button(
                "🔍 Get Answer", 
                type="primary", 
                use_container_width=True,
                help="Click or press Enter to search"
            )
        
        with col_new_topic:
            new_topic_button = st.form_submit_button(
                "🔄 New Topic", 
                help="Reset and start fresh", 
                use_container_width=True
            )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Handle new topic button
    if new_topic_button:
        reset_conversation()
    
    st.markdown("---")
    
    # Process the question when submitted
    if submit_button and user_question:
        # Check if an agreement is selected
        if not selected_agreement or selected_agreement == "Please select an agreement...":
            st.error("⚠️ **Please select an agreement above before asking a question.**")
        else:
            # Add user message
            st.session_state.messages.append({"role": "user", "content": user_question})
            
            # Generate and display response
            with st.spinner("Analyzing agreement..."):
                response = generate_response(
                    user_question, 
                    st.session_state.local_agreement, 
                    st.session_state.common_agreement, 
                    st.session_state.support_agreement,
                    selected_agreement,
                    api_key
                )
                st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Display conversation history with enhanced styling
    if st.session_state.messages:
        st.markdown('<h3 class="section-header">📝 Conversation History</h3>', unsafe_allow_html=True)
        
        for i, message in enumerate(st.session_state.messages):
            if message["role"] == "user":
                st.markdown(f"""
                <div class="message-user">
                    <div class="message-header" style="color: #1565c0;">
                        <span style="font-size: 1.2em;">👤</span>
                        <span>Your Question:</span>
                    </div>
                    <div style="color: #333; line-height: 1.6;">
                        {message["content"]}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="message-assistant">
                    <div class="message-header" style="color: #7b1fa2;">
                        <span style="font-size: 1.2em;">🤖</span>
                        <span>Expert Analysis:</span>
                    </div>
                    <div style="color: #333; line-height: 1.6;">
                """, unsafe_allow_html=True)
                st.markdown(message["content"])
                st.markdown("</div></div>", unsafe_allow_html=True)
    
    # Enhanced footer with stats
    if st.session_state.total_queries > 0:
        current_selection = st.session_state.get('agreement_selection', 'None')
        st.markdown(f"""
        <div class="footer-stats">
            <div style="display: flex; justify-content: center; align-items: center; gap: 30px; flex-wrap: wrap;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 1.2em;">💬</span>
                    <span><strong>Queries:</strong> {st.session_state.total_queries}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 1.2em;">🎯</span>
                    <span><strong>Current:</strong> {current_selection}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 1.2em;">⚡</span>
                    <span><strong>Status:</strong> Ready</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Close the main container
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
