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
    loaded_files = []
    failed_files = []
    
    # List of all split files in the new directory
    split_files = [
        'agreements/bcgeu_local/local_metadata.json',
        'agreements/bcgeu_local/local_definitions.json',
        'agreements/bcgeu_local/local_articles_1_10.json',
        'agreements/bcgeu_local/local_articles_11_20.json', 
        'agreements/bcgeu_local/local_articles_21_30.json',
        'agreements/bcgeu_local/local_articles_31_35.json',
        'agreements/bcgeu_local/local_appendices.json',
        'agreements/bcgeu_local/local_letters_of_agreement.json',
        'agreements/bcgeu_local/local_memorandum.json'
    ]
    
    # Load each file and merge into the complete agreement
    for filename in split_files:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                local_agreement.update(data)
                loaded_files.append(os.path.basename(filename))
        except FileNotFoundError:
            failed_files.append(f"{os.path.basename(filename)} (not found)")
        except json.JSONDecodeError:
            failed_files.append(f"{os.path.basename(filename)} (invalid JSON)")
        except Exception as e:
            failed_files.append(f"{os.path.basename(filename)} ({str(e)})")
    
    # Show debug info
    if loaded_files:
        st.info(f"📁 Loaded {len(loaded_files)} local agreement files: {', '.join(loaded_files)}")
    if failed_files:
        st.warning(f"⚠️ Failed to load {len(failed_files)} files: {', '.join(failed_files)}")
    
    return local_agreement

def load_builtin_agreements() -> tuple:
    """Load the built-in agreements from JSON files"""
    st.write("🔍 **Loading Collective Agreements...**")
    
    try:
        # Try loading split files first
        local_agreement = load_split_local_agreement()
        
        # If split files don't exist or are incomplete, fall back to complete file
        if not local_agreement:
            st.info("📂 Attempting to load complete local agreement file...")
            complete_local_path = 'agreements/bcgeu_local/complete_local.json'
            try:
                with open(complete_local_path, 'r', encoding='utf-8') as f:
                    local_agreement = json.load(f)
                st.success(f"✅ Loaded complete local agreement from {complete_local_path}")
            except FileNotFoundError:
                st.error(f"❌ Complete local agreement not found at {complete_local_path}")
                return None, None
        
        # Load common agreement
        common_agreement_path = 'agreements/bcgeu_common/complete_common.json'
        try:
            with open(common_agreement_path, 'r', encoding='utf-8') as f:
                common_agreement = json.load(f)
            st.success(f"✅ Loaded common agreement from {common_agreement_path}")
        except FileNotFoundError:
            st.error(f"❌ Common agreement not found at {common_agreement_path}")
            return None, None
        
        # Show what was loaded
        local_sections = list(local_agreement.keys())
        common_sections = list(common_agreement.keys())
        
        st.success(f"✅ **Local Agreement loaded successfully** ({len(local_sections)} sections: {', '.join(local_sections)})")
        st.success(f"✅ **Common Agreement loaded successfully** ({len(common_sections)} sections: {', '.join(common_sections)})")
        
        # Verify critical sections
        if 'appendices' in local_agreement and 'appendix_3' in local_agreement.get('appendices', {}):
            st.info("✅ Verified: Appendix 3 (Program Coordinator) is available")
        else:
            st.warning("⚠️ Warning: Appendix 3 (Program Coordinator) not found in local agreement")
        
        return local_agreement, common_agreement
        
    except Exception as e:
        st.error(f"❌ Error loading agreements: {e}")
        import traceback
        st.error(f"Traceback: {traceback.format_exc()}")
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

COLLECTIVE AGREEMENT CONTENT:
{context}

You have access to the complete collective agreement content above. When answering questions:
1. Look for relevant sections across the entire agreement
2. Provide specific article/section citations
3. Quote directly from the agreement when relevant
4. Give clear, management-focused interpretations
5. Consider both operational needs and agreement obligations"""

    user_message = f"""Based on the collective agreement provisions provided, please answer this question:

{query}

Provide clear guidance with specific citations from the agreement text."""

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
    except Exception as e:
        return f"Error generating response: {e}"

def clear_chat():
    """Clear the chat history"""
    st.session_state.messages = []
    st.rerun()

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
                st.error("❌ Could not load agreement files. Please check that the files exist in the correct directories:")
                st.error("- Local agreement files in: agreements/bcgeu_local/")
                st.error("- Common agreement file in: agreements/bcgeu_common/")
                st.stop()
    
    # Agreement Selection
    st.markdown("### 📋 Select Collective Agreement")
    agreement_scope = st.radio(
        "Which agreement do you want to search?",
        ["Local Agreement Only", "Common Agreement Only", "Both Agreements"],
        index=2,  # Default to both
        horizontal=True
    )
    
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
    
    # Bottom section
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if st.session_state.total_queries > 0:
            st.caption(f"💬 Total queries: {st.session_state.total_queries} | 🎯 Current scope: {agreement_scope}")
    
    with col2:
        if len(st.session_state.messages) > 0:
            if st.button("🔄 New Chat", type="primary", use_container_width=True):
                clear_chat()

if __name__ == "__main__":
    main()
