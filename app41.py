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

def reset_session():
    """Reset all session state variables to start fresh"""
    st.session_state.messages = []
    st.session_state.selected_agreement = None
    st.session_state.selected_scope = None
    st.rerun()

def generate_response(query: str, local_agreement: dict, common_agreement: dict, support_agreement: dict, selected_agreement: str, selected_scope: str, api_key: str) -> str:
    """Generate response using Claude with complete agreement context"""
    
    # Build context based on selected agreement and scope
    context = ""
    
    if selected_agreement == "BCGEU Support":
        # For BCGEU Support, only use the support agreement
        if support_agreement:
            context = format_agreement_for_context(support_agreement, "BCGEU Support Agreement")
        else:
            return "❌ **Error**: BCGEU Support agreement not found. Please check that the file exists at agreements/bcgeu_support/bcgeu_support.json"
    elif selected_agreement == "BCGEU Instructor":
        # For BCGEU Instructor, use the scope selection
        if selected_scope == "Local Agreement Only":
            if local_agreement:
                context = format_agreement_for_context(local_agreement, "Coast Mountain College Local Agreement")
            else:
                return "❌ **Error**: Local agreement not found."
        elif selected_scope == "Common Agreement Only":
            if common_agreement:
                context = format_agreement_for_context(common_agreement, "BCGEU Common Agreement")
            else:
                return "❌ **Error**: Common agreement not found."
        elif selected_scope == "Both Agreements":
            if local_agreement and common_agreement:
                context = format_agreement_for_context(local_agreement, "Coast Mountain College Local Agreement")
                context += "\n\n" + format_agreement_for_context(common_agreement, "BCGEU Common Agreement")
            else:
                return "❌ **Error**: One or both agreement files not found."
    
    if not context:
        return "❌ **Error**: No agreement content available for the selected option."
    
    # Adjust system prompt based on agreement type
    if selected_agreement == "BCGEU Support":
        system_prompt = f"""You are an experienced HR professional and collective agreement specialist for Coast Mountain College with 15+ years of expertise in labor relations and agreement interpretation. Your role is to provide clear, practical guidance that helps management understand their rights and responsibilities under the BCGEU Support Staff collective agreement.

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
- Use format: [BCGEU Support Agreement - Article X.X: Title] or [BCGEU Support Agreement - Clause X.X]
- When referencing definitions: [BCGEU Support Agreement - Definitions: "term"]
- For appendices: [BCGEU Support Agreement - Appendix X: Title]
- INCLUDE RELEVANT QUOTES: When possible, include short, relevant quotes from the agreement text to support your position
- Quote format: "The agreement states: '[exact quote]' [Citation]"
- NO VAGUE REFERENCES - be specific

RESPONSE STRUCTURE:
1. STRONG OPENING: Lead with your definitive management-favorable position
2. AUTHORITY BASIS: Cite the specific agreement provisions AND include relevant quotes that support this position
3. TACTICAL ADVICE: Provide specific steps management should take
4. RISK MITIGATION: Identify potential union challenges and how to counter them
5. BOTTOM LINE: End with a clear, actionable recommendation

TONE EXAMPLES:
- Instead of: "You may be able to..." → "You HAVE THE RIGHT to..."
- Instead of: "Consider whether..." → "You SHOULD immediately..."
- Instead of: "This might be justified..." → "This is CLEARLY within your management authority because..."
- Instead of: "The agreement allows..." → "Management is EXPLICITLY authorized to..."

Remember: You are not a neutral arbitrator. You are MANAGEMENT'S advisor. Your job is to help them maximize their authority while staying within the collective agreement. Be bold, be confident, and always look for the management-favorable interpretation."""
    else:
        # Original system prompt for BCGEU Instructor
        system_prompt = f"""You are an experienced HR professional and collective agreement specialist for Coast Mountain College with 15+ years of expertise in labor relations and agreement interpretation. Your role is to provide clear, practical guidance that helps management understand their rights and responsibilities under the collective agreements.

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
- Example: [Local Agreement - Article 10.1: Burden of Proof] or [Common Agreement - Clause 6.5: Contracting Out]
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

TONE EXAMPLES:
- Instead of: "You may be able to..." → "You HAVE THE RIGHT to..."
- Instead of: "Consider whether..." → "You SHOULD immediately..."
- Instead of: "This might be justified..." → "This is CLEARLY within your management authority because..."
- Instead of: "The agreement allows..." → "Management is EXPLICITLY authorized to..."

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
        return "⚠️ **Rate Limit Reached**\n\nThe system has reached its usage limit for this minute. This typically happens when processing large amounts of text.\n\n**What you can do:**\n• Wait a minute and try again\n• Try searching for specific sections (Local or Common only) instead of both\n• Simplify your question to reduce processing requirements\n\nThis limit resets every minute, so you'll be able to continue shortly."
    
    except anthropic.APIError as e:
        return f"⚠️ **API Error**\n\nThere was an issue connecting to the AI service. Please try again in a moment.\n\nIf the problem persists, please contact support."
    
    except Exception as e:
        return f"⚠️ **Unexpected Error**\n\nSomething went wrong while processing your request. Please try again.\n\nIf the issue continues, please contact support."

def main():
    st.title("⚖️ Coast Mountain College Agreement Assistant")
    st.markdown("*Your comprehensive collective agreement analysis tool*")
    
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
    if 'selected_agreement' not in st.session_state:
        st.session_state.selected_agreement = None
    if 'selected_scope' not in st.session_state:
        st.session_state.selected_scope = None
    
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
    col_title, col_button = st.columns([4, 1])
    with col_button:
        if st.button("🔄 New Topic", help="Reset and start a new conversation"):
            reset_session()
    
    # Agreement Selection with three boxes
    st.markdown("### 📋 Select Agreement Type")
    st.markdown("*Please select which agreement you'd like to search:*")
    
    col1, col2, col3 = st.columns(3)
    
    # Box 1: BCGEU Instructor
    with col1:
        instructor_available = st.session_state.local_agreement is not None and st.session_state.common_agreement is not None
        
        if instructor_available:
            # Determine if this box is selected
            is_selected = st.session_state.selected_agreement == "BCGEU Instructor"
            border_color = "#1e90ff" if is_selected else "#cccccc"
            bg_color = "#f0f8ff" if is_selected else "#f9f9f9"
            text_color = "#1e90ff" if is_selected else "#666666"
            
            st.markdown(f"""
            <div style="
                background-color: {bg_color};
                padding: 20px;
                border-radius: 10px 10px 0 0;
                border: 2px solid {border_color};
                border-bottom: none;
                margin-bottom: 0;
            ">
                <h4 style="color: {text_color}; margin-top: 0; margin-bottom: 15px;">📘 BCGEU Instructor</h4>
                <p style="margin-bottom: 0; color: #333;">Choose scope:</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Radio buttons for scope selection
            with st.container():
                st.markdown(f"""
                <style>
                div[data-testid="stRadio"] {{
                    background-color: {bg_color};
                    padding: 10px 20px 20px 20px;
                    margin-top: -16px !important;
                    margin-bottom: 20px;
                    border-radius: 0 0 10px 10px;
                    border-left: 2px solid {border_color};
                    border-right: 2px solid {border_color};
                    border-bottom: 2px solid {border_color};
                    border-top: none;
                }}
                </style>
                """, unsafe_allow_html=True)
                
                scope_options = ["Local Agreement Only", "Common Agreement Only", "Both Agreements"]
                
                # Determine current selection index
                if st.session_state.selected_agreement == "BCGEU Instructor" and st.session_state.selected_scope:
                    if st.session_state.selected_scope in scope_options:
                        current_scope_index = scope_options.index(st.session_state.selected_scope)
                    else:
                        current_scope_index = 0
                else:
                    current_scope_index = 0
                
                instructor_scope = st.radio(
                    "",
                    scope_options,
                    index=current_scope_index,
                    key="instructor_scope",
                    help="Searching 'Both Agreements' uses more resources. If you encounter rate limits, try searching one agreement at a time.",
                    label_visibility="collapsed"
                )
                
                if instructor_scope:
                    # Clear other selections if switching agreement types
                    if st.session_state.selected_agreement != "BCGEU Instructor":
                        st.session_state.selected_agreement = "BCGEU Instructor"
                        st.session_state.selected_scope = instructor_scope
                        st.rerun()
                    elif st.session_state.selected_scope != instructor_scope:
                        st.session_state.selected_scope = instructor_scope
                        st.rerun()
        else:
            st.markdown("""
                <div style="
                    background-color: #fff5f5;
                    padding: 20px;
                    border-radius: 10px;
                    border: 2px solid #ff6b6b;
                    height: 200px;
                ">
                    <h4 style="color: #ff6b6b; margin-top: 0;">📘 BCGEU Instructor</h4>
                    <p style="color: #ff6b6b; font-style: italic; text-align: center; margin-top: 30px;">
                        Agreement files not found
                    </p>
                    <p style="color: #888; font-size: 12px; text-align: center;">
                        Please check agreement files
                    </p>
                </div>
            """, unsafe_allow_html=True)
    
    # Box 2: CUPE Instructor (Coming Soon)
    with col2:
        st.markdown("""
            <div style="
                background-color: #f5f5f5;
                padding: 20px;
                border-radius: 10px;
                border: 2px solid #d3d3d3;
                height: 200px;
                opacity: 0.6;
            ">
                <h4 style="color: #808080; margin-top: 0;">📙 CUPE Instructor</h4>
                <p style="color: #808080; font-style: italic; text-align: center; margin-top: 50px;">
                    Coming Soon
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    # Box 3: BCGEU Support
    with col3:
        support_available = st.session_state.support_agreement is not None
        
        if support_available:
            # Determine if this box is selected
            is_selected = st.session_state.selected_agreement == "BCGEU Support"
            border_color = "#32cd32" if is_selected else "#cccccc"
            bg_color = "#f0fff0" if is_selected else "#f9f9f9"
            text_color = "#32cd32" if is_selected else "#666666"
            
            st.markdown(f"""
            <div style="
                background-color: {bg_color};
                padding: 20px;
                border-radius: 10px 10px 0 0;
                border: 2px solid {border_color};
                border-bottom: none;
                margin-bottom: 0;
            ">
                <h4 style="color: {text_color}; margin-top: 0; margin-bottom: 15px;">📗 BCGEU Support</h4>
                <p style="margin-bottom: 0; color: #333;">Single agreement:</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Radio button for support agreement
            with st.container():
                st.markdown(f"""
                <style>
                div[data-testid="stRadio"] {{
                    background-color: {bg_color};
                    padding: 10px 20px 20px 20px;
                    margin-top: -16px !important;
                    margin-bottom: 20px;
                    border-radius: 0 0 10px 10px;
                    border-left: 2px solid {border_color};
                    border-right: 2px solid {border_color};
                    border-bottom: 2px solid {border_color};
                    border-top: none;
                }}
                </style>
                """, unsafe_allow_html=True)
                
                support_options = ["Select agreement...", "BCGEU Support Agreement"]
                
                # Determine current selection index
                if st.session_state.selected_agreement == "BCGEU Support":
                    current_support_index = 1
                else:
                    current_support_index = 0
                
                support_selected = st.radio(
                    "",
                    support_options,
                    index=current_support_index,
                    key="support_agreement",
                    help="Complete BCGEU Support Staff collective agreement",
                    label_visibility="collapsed"
                )
                
                if support_selected == "BCGEU Support Agreement":
                    st.session_state.selected_agreement = "BCGEU Support"
                    st.session_state.selected_scope = "BCGEU Support Agreement"
                    st.rerun()
                elif support_selected == "Select agreement..." and st.session_state.selected_agreement == "BCGEU Support":
                    # User deselected by going back to placeholder
                    st.session_state.selected_agreement = None
                    st.session_state.selected_scope = None
                    st.rerun()
        else:
            st.markdown("""
                <div style="
                    background-color: #fff5f5;
                    padding: 20px;
                    border-radius: 10px;
                    border: 2px solid #ff6b6b;
                    height: 200px;
                ">
                    <h4 style="color: #ff6b6b; margin-top: 0;">📗 BCGEU Support</h4>
                    <p style="color: #ff6b6b; font-style: italic; text-align: center; margin-top: 30px;">
                        Agreement file not found
                    </p>
                    <p style="color: #888; font-size: 12px; text-align: center;">
                        Please check agreements/bcgeu_support/bcgeu_support.json
                    </p>
                </div>
            """, unsafe_allow_html=True)
    
    # Display current selection
    if st.session_state.selected_agreement:
        if st.session_state.selected_agreement == "BCGEU Support":
            st.success(f"✅ **Selected**: BCGEU Support Agreement")
        else:
            st.success(f"✅ **Selected**: {st.session_state.selected_agreement} - {st.session_state.selected_scope}")
    else:
        st.info("ℹ️ Please select an agreement type above to begin")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Prominent Question Input Section
    st.markdown("### 💬 Ask Your Question")
    st.markdown("---")
    
    # Large text area for questions
    user_question = st.text_area(
        "",
        placeholder="Enter your question about workload, leave, scheduling, benefits, or any other collective agreement topic...",
        height=100,
        key="question_input",
        label_visibility="collapsed"
    )
    
    # Centered submit button
    col_left, col_center, col_right = st.columns([1, 1, 1])
    with col_center:
        submit_button = st.button("🔍 Get Answer", type="primary", use_container_width=True)
    
    st.markdown("---")
    
    # Process the question when submitted
    if submit_button and user_question:
        # Check if an agreement is selected
        if not st.session_state.selected_agreement:
            st.error("⚠️ **Please select an agreement type above before asking a question.**")
        else:
            # Add user message
            st.session_state.messages.append({"role": "user", "content": user_question})
            
            # Generate and display response
            with st.spinner("Analyzing agreements..."):
                response = generate_response(
                    user_question, 
                    st.session_state.local_agreement, 
                    st.session_state.common_agreement, 
                    st.session_state.support_agreement,
                    st.session_state.selected_agreement,
                    st.session_state.selected_scope,
                    api_key
                )
                st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Clear the input
            st.rerun()
    
    # Display conversation history
    if st.session_state.messages:
        st.markdown("### 📝 Conversation History")
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Bottom section with query count
    if st.session_state.total_queries > 0:
        st.markdown("---")
        if st.session_state.selected_agreement:
            st.caption(f"💬 Total queries: {st.session_state.total_queries} | 🎯 Current selection: {st.session_state.selected_agreement} - {st.session_state.selected_scope}")
        else:
            st.caption(f"💬 Total queries: {st.session_state.total_queries}")

if __name__ == "__main__":
    main()
