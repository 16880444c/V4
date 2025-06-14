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
    loaded_files = []
    
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
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    support_agreement.update(data)
                    loaded_files.append(filename)
            else:
                # File doesn't exist - this helps debug path issues
                continue
        except Exception as e:
            # Skip files that can't be loaded but continue trying others
            continue
    
    # Store debug info for later use
    if hasattr(st.session_state, '__dict__'):
        st.session_state.support_loaded_files = loaded_files
    
    # If no files were loaded, try the old single file as fallback
    if not support_agreement:
        try:
            fallback_path = 'agreements/bcgeu_support/bcgeu_support.json'
            if os.path.exists(fallback_path):
                with open(fallback_path, 'r', encoding='utf-8') as f:
                    support_agreement = json.load(f)
                    if hasattr(st.session_state, '__dict__'):
                        st.session_state.support_loaded_files = [fallback_path]
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

def extract_debug_info(agreement_data: dict, agreement_name: str) -> dict:
    """Extract article numbers and appendices from agreement data for debugging"""
    debug_info = {
        'agreement_name': agreement_name,
        'articles': [],
        'appendices': [],
        'other_sections': []
    }
    
    if not agreement_data:
        return debug_info
    
    for section_key, section_data in agreement_data.items():
        section_lower = section_key.lower()
        
        # Check for articles
        if 'article' in section_lower and isinstance(section_data, dict):
            for key, value in section_data.items():
                if 'article' in key.lower():
                    debug_info['articles'].append(key)
        
        # Check for appendices
        elif 'appendix' in section_lower or 'appendices' in section_lower:
            if isinstance(section_data, dict):
                for key in section_data.keys():
                    debug_info['appendices'].append(key)
            else:
                debug_info['appendices'].append(section_key)
        
        # Track other sections
        else:
            debug_info['other_sections'].append(section_key)
    
    return debug_info

def show_debug_modal():
    """Show debug information in a modal"""
    if st.session_state.get('show_debug', False):
        with st.expander("🔍 DEBUG: Loaded Agreement Content", expanded=True):
            selected_agreement = st.session_state.get('agreement_selection', '')
            
            if "BCGEU Instructor - Local Only" in selected_agreement:
                debug_info = extract_debug_info(st.session_state.local_agreement, "BCGEU Local Agreement")
                display_debug_info([debug_info])
            
            elif "BCGEU Instructor - Common Only" in selected_agreement:
                debug_info = extract_debug_info(st.session_state.common_agreement, "BCGEU Common Agreement")
                display_debug_info([debug_info])
            
            elif "BCGEU Instructor - Both Agreements" in selected_agreement:
                local_info = extract_debug_info(st.session_state.local_agreement, "BCGEU Local Agreement")
                common_info = extract_debug_info(st.session_state.common_agreement, "BCGEU Common Agreement")
                display_debug_info([local_info, common_info])
            
            elif "BCGEU Support Agreement" in selected_agreement:
                debug_info = extract_debug_info(st.session_state.support_agreement, "BCGEU Support Agreement")
                display_debug_info([debug_info])
            
            elif "CUPE - Local Agreement" in selected_agreement:
                debug_info = extract_debug_info(st.session_state.cupe_local_agreement, "CUPE Local Agreement")
                display_debug_info([debug_info])
            
            elif "CUPE - Common Agreement" in selected_agreement:
                debug_info = extract_debug_info(st.session_state.cupe_common_agreement, "CUPE Common Agreement")
                display_debug_info([debug_info])
            
            elif "CUPE - Both Agreements" in selected_agreement:
                local_info = extract_debug_info(st.session_state.cupe_local_agreement, "CUPE Local Agreement")
                common_info = extract_debug_info(st.session_state.cupe_common_agreement, "CUPE Common Agreement")
                display_debug_info([local_info, common_info])
            
            if st.button("❌ Close Debug", key="close_debug"):
                st.session_state.show_debug = False
                st.rerun()

def display_debug_info(debug_infos: list):
    """Display debug information for one or more agreements"""
    for debug_info in debug_infos:
        st.markdown(f"**{debug_info['agreement_name']}**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Articles:**")
            if debug_info['articles']:
                for article in sorted(debug_info['articles']):
                    st.markdown(f"• {article}")
            else:
                st.markdown("*No articles found*")
        
        with col2:
            st.markdown("**Appendices:**")
            if debug_info['appendices']:
                for appendix in sorted(debug_info['appendices']):
                    st.markdown(f"• {appendix}")
            else:
                st.markdown("*No appendices found*")
        
        with col3:
            st.markdown("**Other Sections:**")
            if debug_info['other_sections']:
                for section in sorted(debug_info['other_sections']):
                    st.markdown(f"• {section}")
            else:
                st.markdown("*No other sections found*")
        
        st.markdown("---")

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
    keys_to_clear = ['messages', 'total_queries', 'conversation_context', 'current_question_type', 'show_debug']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    # Reset question type to initial
    st.session_state.current_question_type = "initial"
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

def generate_response(query: str, local_agreement: dict, common_agreement: dict, support_agreement: dict, 
                     cupe_local_agreement: dict, cupe_common_agreement: dict, selection: str, api_key: str, 
                     is_followup: bool = False) -> str:
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
            return "❌ **Error**: CUPE Common agreement not found."
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
    
    # Determine system prompt based on agreement type
    if "Support" in selection:
        agreement_type = "BCGEU Support Agreement"
        citation_format = "[BCGEU Support Agreement - Article X.X: Title]"
    elif "CUPE" in selection:
        agreement_type = "CUPE agreements"
        citation_format = "[CUPE Agreement - Article X.X: Title]"
    else:
        agreement_type = "BCGEU Instructor agreements"
        citation_format = "[Agreement Type - Article X.X: Title]"
    
    follow_up_instruction = ""
    if is_followup:
        follow_up_instruction = "\n\nIMPORTANT: This is a FOLLOW-UP question in an ongoing conversation. Consider the previous conversation context when formulating your response. Build upon previous answers where relevant, and reference earlier discussion points when appropriate."
    
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

Remember: You are not a neutral arbitrator. You are MANAGEMENT'S advisor. Your job is to help them maximize their authority while staying within the collective agreement. Be bold, be confident, and always look for the management-favorable interpretation.{follow_up_instruction}"""

    user_message = f"""Based on the complete collective agreement provisions below, provide strong management-focused guidance for this question:

{conversation_context}

{"FOLLOW-UP " if is_followup else ""}QUESTION: {query}

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

def render_question_section(selected_agreement: str, api_key: str):
    """Render the question input section based on current state"""
    
    # Initialize question type if not set
    if 'current_question_type' not in st.session_state:
        st.session_state.current_question_type = "initial"
    
    # Determine question type and section title
    if st.session_state.current_question_type == "initial" or not st.session_state.messages:
        section_title = "💬 Ask Your Question"
        placeholder_text = "Enter your question about workload, leave, scheduling, benefits, or any other collective agreement topic..."
        form_key = "initial_question_form"
        button_text = "🔍 Get Answer"
    else:
        section_title = "💬 Continue the Conversation"
        placeholder_text = "Ask a follow-up question about the topic, or start a new topic..."
        form_key = "followup_question_form"
        button_text = "💬 Ask Follow-up"
    
    st.markdown(f"### {section_title}")
    
    # Create form with dynamic key to ensure proper handling
    with st.form(key=form_key, clear_on_submit=True):
        user_question = st.text_area(
            "",
            placeholder=placeholder_text,
            height=120,
            key=f"question_input_{st.session_state.current_question_type}",
            label_visibility="collapsed",
            help="💡 Press Ctrl+Enter to submit your question!"
        )
        
        # Button layout
        if st.session_state.current_question_type == "initial" or not st.session_state.messages:
            # Initial question - submit, new topic, and debug buttons
            col1, col2, col3, col4, col5 = st.columns([0.5, 1.2, 1.2, 1, 0.5])
            
            with col2:
                submit_button = st.form_submit_button(button_text, type="primary", use_container_width=True)
            
            with col3:
                new_topic_button = st.form_submit_button("🔄 New Topic", help="Reset and start fresh", use_container_width=True)
            
            with col4:
                debug_button = st.form_submit_button("🔍 Debug", help="Show loaded agreement content", use_container_width=True)
        else:
            # Follow-up question - show all three options
            col1, col2, col3, col4, col5 = st.columns([0.3, 1.2, 1.2, 1, 0.3])
            
            with col2:
                submit_button = st.form_submit_button(button_text, type="primary", use_container_width=True)
            
            with col3:
                new_topic_button = st.form_submit_button("🔄 New Topic", help="Clear conversation and start fresh", use_container_width=True)
            
            with col4:
                debug_button = st.form_submit_button("🔍 Debug", help="Show loaded agreement content", use_container_width=True)
    
    # Handle debug button
    if debug_button:
        st.session_state.show_debug = True
        st.rerun()
    
    # Handle new topic button
    if new_topic_button:
        reset_conversation()
        return None, False
    
    # Handle question submission
    if submit_button and user_question:
        # Check if an agreement is selected
        if not selected_agreement or selected_agreement == "Please select an agreement...":
            st.error("⚠️ **Please select an agreement above before asking a question.**")
            return None, False
        else:
            is_followup = st.session_state.current_question_type == "followup" and len(st.session_state.messages) > 0
            return user_question, is_followup
    
    return None, False

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
    .agreement-group {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 10px;
        margin: 5px 0;
        border-left: 4px solid #007bff;
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
    if 'cupe_local_agreement' not in st.session_state:
        st.session_state.cupe_local_agreement = None
    if 'cupe_common_agreement' not in st.session_state:
        st.session_state.cupe_common_agreement = None
    if 'current_question_type' not in st.session_state:
        st.session_state.current_question_type = "initial"
    if 'show_debug' not in st.session_state:
        st.session_state.show_debug = False
    
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
    
    # Show debug modal if requested
    if st.session_state.get('show_debug', False):
        show_debug_modal()
    
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
    cupe_options = []
    if st.session_state.cupe_local_agreement:
        cupe_options.append("CUPE - Local Agreement")
    if st.session_state.cupe_common_agreement:
        cupe_options.append("CUPE - Common Agreement")
    if st.session_state.cupe_local_agreement and st.session_state.cupe_common_agreement:
        cupe_options.append("CUPE - Both Agreements")
    
    agreement_options.extend(cupe_options)
    
    # Agreement selection (only show if no active conversation or at the start)
    if not st.session_state.messages:
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
        
        # Show agreement availability status
        with st.expander("📊 Agreement Availability Status"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**BCGEU Agreements:**")
                bcgeu_local_status = "✅ Available" if st.session_state.local_agreement else "❌ Not found"
                bcgeu_common_status = "✅ Available" if st.session_state.common_agreement else "❌ Not found"
                
                # Enhanced support agreement status with file details
                if st.session_state.support_agreement:
                    loaded_files = getattr(st.session_state, 'support_loaded_files', [])
                    if loaded_files:
                        bcgeu_support_status = f"✅ Available ({len(loaded_files)} files loaded)"
                        st.markdown(f"• Support Agreement: {bcgeu_support_status}")
                        st.markdown("  Files loaded:")
                        for file in loaded_files:
                            file_name = file.split('/')[-1]  # Just show filename
                            st.markdown(f"    - {file_name}")
                    else:
                        bcgeu_support_status = "✅ Available (source unknown)"
                        st.markdown(f"• Support Agreement: {bcgeu_support_status}")
                else:
                    st.markdown("• Support Agreement: ❌ Not found")
                    st.markdown("  Expected files:")
                    expected_files = [
                        'definitions_json.json',
                        'articles_1_10_json.json', 
                        'articles_11_20_json.json',
                        'articles_21_30_json.json',
                        'articles_31_36_json.json',
                        'appendices_json.json',
                        'memoranda_json.json'
                    ]
                    for file in expected_files:
                        file_path = f'agreements/bcgeu_support/{file}'
                        exists = "✅" if os.path.exists(file_path) else "❌"
                        st.markdown(f"    {exists} {file}")
                
                st.markdown(f"• Local Agreement: {bcgeu_local_status}")
                st.markdown(f"• Common Agreement: {bcgeu_common_status}")
            
            with col2:
                st.markdown("**CUPE Agreements:**")
                cupe_local_status = "✅ Available" if st.session_state.cupe_local_agreement else "❌ Not found"
                cupe_common_status = "✅ Available" if st.session_state.cupe_common_agreement else "❌ Not found"
                
                st.markdown(f"• Local Agreement: {cupe_local_status}")
                st.markdown(f"• Common Agreement: {cupe_common_status}")
                
                if not st.session_state.cupe_common_agreement:
                    st.markdown("  *Attempted to load from GitHub*")
        
        st.markdown("---")
        
        # Initial question section (only if no conversation started)
        user_question, is_followup = render_question_section(selected_agreement, api_key)
        
    else:
        # If there's an active conversation, get the stored agreement selection
        selected_agreement = st.session_state.get('agreement_selection', 'Please select an agreement...')
        
        # Show current selection at top but not editable during conversation
        st.markdown(f'<div class="status-success">✅ Current Agreement: {selected_agreement}</div>', unsafe_allow_html=True)
        st.markdown("---")
        
        # Display conversation history first
        st.markdown("### 📝 Conversation History")
        
        for message in st.session_state.messages:
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.markdown(f"**Your Question:** {message['content']}")
            else:
                with st.chat_message("assistant"):
                    st.markdown("**Expert Analysis:**")
                    st.markdown(message["content"])
        
        st.markdown("---")
        
        # Then show question section for follow-ups
        user_question, is_followup = render_question_section(selected_agreement, api_key)
    
    # Process the question when submitted
    if user_question:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_question})
        
        # Set question type for next iteration
        st.session_state.current_question_type = "followup"
        
        # Generate and display response
        with st.spinner("Analyzing agreement..."):
            response = generate_response(
                user_question, 
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
        conversation_length = len(st.session_state.messages) // 2
        st.markdown(f"""
        <div class="footer-stats">
            💬 Total queries: {st.session_state.total_queries} | 🎯 Current selection: {current_selection} | 📊 Questions in conversation: {conversation_length}
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
