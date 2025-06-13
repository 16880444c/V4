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
    # Add simple, clean CSS
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
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 15px;
        margin: 15px 0;
        border-radius: 0 8px 8px 0;
    }
    .assistant-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
        padding: 15px;
        margin: 15px 0;
        border-radius: 0 8px 8px 0;
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
    st.markdown('<div class="big-font">⚖️ Coast Mountain College Agreement Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Your comprehensive collective agreement analysis tool</div>', unsafe_allow_html=True)
    
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
    
    # Agreement selection
    st.markdown("### 📋 Select Agreement")
    
    current_selection = st.session_state.get('agreement_selection', 'Please select an agreement...')
    if current_selection not in agreement_options:
        current_selection = 'Please select an agreement...'
    
    selected_agreement = st.selectbox(
        "Choose which agreement to search:",
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
        
        # Add helpful information about the selection
        if "Both Agreements" in selected_agreement:
            st.markdown('<div class="status-info">ℹ️ Searching both agreements uses more resources. If you encounter rate limits, try selecting individual agreements.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-waiting">ℹ️ Please select an agreement to begin</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Question input section
    st.markdown("### 💬 Ask Your Question")
    
    # Create a form to handle Enter key submission
    with st.form(key="question_form", clear_on_submit=False):
        user_question = st.text_area(
            "",
            placeholder="Enter your question about workload, leave, scheduling, benefits, or any other collective agreement topic...",
            height=120,
            key="question_input",
            label_visibility="collapsed",
            help="💡 Press Enter to submit your question!"
        )
        
        # Button row
        col1, col2, col3, col4 = st.columns([1, 1.2, 1.2, 1])
        
        with col2:
            submit_button = st.form_submit_button("🔍 Get Answer", type="primary", use_container_width=True)
        
        with col3:
            new_topic_button = st.form_submit_button("🔄 New Topic", help="Reset and start fresh", use_container_width=True)
    
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
    
    # Display conversation history
    if st.session_state.messages:
        st.markdown("### 📝 Conversation History")
        
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(f"""
                <div class="user-message">
                    <div style="color: #1565c0; font-weight: 600; margin-bottom: 8px;">
                        👤 Your Question:
                    </div>
                    <div style="color: #333;">
                        {message["content"]}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="assistant-message">
                    <div style="color: #7b1fa2; font-weight: 600; margin-bottom: 8px;">
                        🤖 Expert Analysis:
                    </div>
                    <div style="color: #333;">
                """, unsafe_allow_html=True)
                st.markdown(message["content"])
                st.markdown("</div></div>", unsafe_allow_html=True)
    
    # Footer with stats
    if st.session_state.total_queries > 0:
        current_selection = st.session_state.get('agreement_selection', 'None')
        st.markdown(f"""
        <div class="footer-stats">
            💬 Total queries: {st.session_state.total_queries} | 🎯 Current selection: {current_selection}
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
