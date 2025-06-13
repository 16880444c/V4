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
                return None, None
        
        # Load common agreement
        common_agreement_path = 'agreements/bcgeu_common/complete_common.json'
        try:
            with open(common_agreement_path, 'r', encoding='utf-8') as f:
                common_agreement = json.load(f)
        except:
            return None, None
        
        return local_agreement, common_agreement
        
    except Exception:
        return None, None

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

def generate_response(query: str, local_agreement: dict, common_agreement: dict, agreement_scope: str, api_key: str) -> str:
    """Generate response using Claude with complete agreement context"""
    
    # Build context based on selected scope
    context = ""
    if agreement_scope == "Local Agreement Only":
        context = format_agreement_for_context(local_agreement, "Coast Mountain College Local Agreement")
    elif agreement_scope == "Common Agreement Only":
        context = format_agreement_for_context(common_agreement, "BCGEU Common Agreement")
    else:  # Both agreements
        context = format_agreement_for_context(local_agreement, "Coast Mountain College Local Agreement")
        context += "\n\n" + format_agreement_for_context(common_agreement, "BCGEU Common Agreement")
    
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
            local_agreement, common_agreement = load_builtin_agreements()
            
            if local_agreement and common_agreement:
                st.session_state.local_agreement = local_agreement
                st.session_state.common_agreement = common_agreement
                st.session_state.agreements_loaded = True
            else:
                st.error("❌ Could not load agreement files. Please check that the files exist in:")
                st.error("• Local: agreements/bcgeu_local/")
                st.error("• Common: agreements/bcgeu_common/")
                st.stop()
    
    # Agreement Selection with three boxes
    st.markdown("### 📋 Select Agreement Type")
    
    col1, col2, col3 = st.columns(3)
    
    # Box 1: BCGEU Instructor (Active)
    with col1:
        with st.container():
            st.markdown("""
                <div style="
                    background-color: #f0f8ff;
                    padding: 20px;
                    border-radius: 10px;
                    border: 2px solid #1e90ff;
                    height: 200px;
                ">
                    <h4 style="color: #1e90ff; margin-top: 0;">📘 BCGEU Instructor</h4>
                </div>
            """, unsafe_allow_html=True)
            
            # Use a container to overlay content on the styled div
            with st.container():
                agreement_scope = st.radio(
                    "",
                    ["Local Agreement Only", "Common Agreement Only", "Both Agreements"],
                    index=2,
                    key="bcgeu_instructor_radio",
                    help="Searching 'Both Agreements' uses more resources. If you encounter rate limits, try searching one agreement at a time."
                )
    
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
    
    # Box 3: BCGEU Support (Coming Soon)
    with col3:
        st.markdown("""
            <div style="
                background-color: #f5f5f5;
                padding: 20px;
                border-radius: 10px;
                border: 2px solid #d3d3d3;
                height: 200px;
                opacity: 0.6;
            ">
                <h4 style="color: #808080; margin-top: 0;">📗 BCGEU Support</h4>
                <p style="color: #808080; font-style: italic; text-align: center; margin-top: 50px;">
                    Coming Soon
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Display conversation history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about collective agreement provisions..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing agreements..."):
                response = generate_response(
                    prompt, 
                    st.session_state.local_agreement, 
                    st.session_state.common_agreement, 
                    agreement_scope,
                    api_key
                )
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Example questions for new users
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
    
    # Bottom section with query count
    if st.session_state.total_queries > 0:
        st.markdown("---")
        st.caption(f"💬 Total queries: {st.session_state.total_queries} | 🎯 Current scope: {agreement_scope}")

if __name__ == "__main__":
    main()
