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

def test_json_loading():
    """Test JSON loading to diagnose the issue - ENHANCED VERSION"""
    st.write("🔧 **ENHANCED JSON DIAGNOSTICS v2.0** 🔧")
    try:
        # Check file existence and size
        if os.path.exists('complete_local.json'):
            file_size = os.path.getsize('complete_local.json')
            st.write(f"✅ File exists, size: {file_size:,} bytes")
        else:
            st.error("❌ complete_local.json file not found!")
            return
            
        with open('complete_local.json', 'r', encoding='utf-8') as f:
            content = f.read()
            st.write(f"✅ File content length: {len(content):,} characters")
            
            # Check for key sections in raw text
            if '"appendices"' in content:
                st.write("✅ Found 'appendices' key in raw file content")
                appendices_pos = content.find('"appendices"')
                st.write(f"- Appendices section starts at character {appendices_pos:,}")
                
                # Show content around appendices
                start = max(0, appendices_pos - 50)
                end = min(len(content), appendices_pos + 300)
                st.write("📄 Raw content around appendices:")
                st.code(content[start:end])
            else:
                st.write("❌ No 'appendices' key found in raw file content")
            
            if '"appendix_3"' in content:
                st.write("✅ Found 'appendix_3' key in raw file content")
                appendix_3_pos = content.find('"appendix_3"')
                st.write(f"- Appendix 3 section starts at character {appendix_3_pos:,}")
            else:
                st.write("❌ No 'appendix_3' key found in raw file content")
            
            st.write("📄 Last 200 characters of file:")
            st.code(content[-200:])
            
            # Now try to parse JSON
            st.write("🔍 Attempting JSON parse...")
            data = json.loads(content)
            st.write(f"✅ JSON parsed successfully!")
            st.write(f"📋 Top level keys after JSON parse: **{list(data.keys())}**")
            
            if 'appendices' in data:
                st.write(f"✅ **APPENDICES FOUND** in parsed data: {list(data['appendices'].keys())}")
                if 'appendix_3' in data['appendices']:
                    st.write("🎯 **APPENDIX 3 FOUND** in parsed JSON!")
                    app3_data = data['appendices']['appendix_3']
                    st.write(f"- Appendix 3 keys: {list(app3_data.keys())}")
                    st.write(f"- Appendix 3 title: {app3_data.get('title', 'No title')}")
                    st.write(f"- Appendix 3 content length: {len(str(app3_data))} chars")
                else:
                    st.write("❌ Appendix 3 NOT found in parsed JSON")
            else:
                st.write("❌ **NO APPENDICES SECTION** in parsed JSON - THIS IS THE PROBLEM!")
                
        return data if 'data' in locals() else None
                
    except json.JSONDecodeError as e:
        st.error(f"❌ JSON parsing error: {e}")
        st.write(f"Error at line {e.lineno}, column {e.colno}")
        return None
    except Exception as e:
        st.error(f"❌ File reading error: {e}")
        return None

def load_builtin_agreements() -> tuple:
    """Load the built-in agreements from JSON files"""
    st.write("🔍 **LOADING AGREEMENTS v2.0**")
    
    # First run the enhanced diagnostic
    test_data = test_json_loading()
    
    try:
        with open('complete_local.json', 'r', encoding='utf-8') as f:
            local_agreement = json.load(f)
        
        with open('complete_common.json', 'r', encoding='utf-8') as f:
            common_agreement = json.load(f)
        
        # DETAILED LOAD RESULTS
        st.write("📊 **DETAILED LOAD RESULTS:**")
        st.write(f"- Local agreement type: {type(local_agreement)}")
        st.write(f"- Local agreement keys: **{list(local_agreement.keys())}**")
        
        # Check appendices with detailed info
        if 'appendices' in local_agreement:
            appendices = local_agreement['appendices']
            st.write(f"✅ **APPENDICES SECTION FOUND**: {list(appendices.keys())}")
            
            if 'appendix_3' in appendices:
                app3 = appendices['appendix_3']
                st.write("🎯 **APPENDIX 3 CONFIRMED PRESENT**")
                st.write(f"- Title: {app3.get('title', 'No title')}")
                st.write(f"- Structure keys: {list(app3.keys())}")
                st.write(f"- Content preview: {str(app3)[:200]}...")
            else:
                st.write("❌ Appendix 3 missing from appendices")
        else:
            st.write("❌ **NO APPENDICES SECTION** - This is the core issue!")
            
            # Deep search for any appendix content
            st.write("🔍 **DEEP SEARCHING** for appendix content...")
            full_json_text = json.dumps(local_agreement, indent=2).lower()
            
            appendix_mentions = full_json_text.count("appendix")
            st.write(f"- Found {appendix_mentions} mentions of 'appendix' in articles")
            
            if "program coordination" in full_json_text:
                st.write("✅ Found 'program coordination' in articles")
                
        return local_agreement, common_agreement
        
    except Exception as e:
        st.error(f"❌ Error loading agreements: {e}")
        return None, None

def format_agreement_for_context(agreement: dict, agreement_name: str) -> str:
    """Convert agreement JSON to formatted text for Claude context"""
    st.write(f"🔧 **FORMATTING CONTEXT v2.0** for: {agreement_name}")
    
    context = f"=== {agreement_name.upper()} ===\n\n"
    
    # Add metadata
    if 'agreement_metadata' in agreement:
        context += "AGREEMENT METADATA:\n"
        context += json.dumps(agreement['agreement_metadata'], indent=2) + "\n\n"
        st.write("✅ Added metadata")
    
    # Add definitions
    if 'definitions' in agreement:
        context += "DEFINITIONS:\n"
        for term, definition in agreement['definitions'].items():
            context += f"- {term}: {definition}\n"
        context += "\n"
        st.write(f"✅ Added {len(agreement['definitions'])} definitions")
    
    # Add articles
    if 'articles' in agreement:
        context += "ARTICLES:\n\n"
        article_count = 0
        for article_num, article_data in agreement['articles'].items():
            if isinstance(article_data, dict):
                title = article_data.get('title', f'Article {article_num}')
                context += f"ARTICLE {article_num}: {title}\n"
                article_count += 1
                
                # Add sections
                if 'sections' in article_data:
                    for section_key, section_data in article_data['sections'].items():
                        context += f"\nSection {section_key}:\n"
                        if isinstance(section_data, dict):
                            if 'title' in section_data:
                                context += f"Title: {section_data['title']}\n"
                            if 'content' in section_data:
                                context += f"Content: {section_data['content']}\n"
                            if 'subsections' in section_data:
                                context += "Subsections:\n"
                                for sub_key, sub_content in section_data['subsections'].items():
                                    context += f"  {sub_key}) {sub_content}\n"
                        else:
                            context += f"{section_data}\n"
                
                # Add other content if no sections
                if 'sections' not in article_data and 'content' in article_data:
                    context += f"\n{article_data['content']}\n"
                
                context += "\n" + "="*50 + "\n\n"
        
        st.write(f"✅ Added {article_count} articles")
    
    # ENHANCED APPENDICES PROCESSING
    if 'appendices' in agreement:
        st.write(f"🎯 **PROCESSING APPENDICES SECTION**")
        context += "APPENDICES:\n\n"
        appendices = agreement['appendices']
        st.write(f"- Found appendices: {list(appendices.keys())}")
        
        appendix_count = 0
        for appendix_key, appendix_data in appendices.items():
            st.write(f"📄 Processing: '{appendix_key}'")
            
            # Convert appendix_3 to "APPENDIX 3" for better readability
            display_key = appendix_key.replace('_', ' ').upper()
            context += f"{display_key}:\n"
            
            if isinstance(appendix_data, dict):
                if 'title' in appendix_data:
                    context += f"Title: {appendix_data['title']}\n\n"
                    st.write(f"  - Title: {appendix_data['title']}")
                
                # Add the full appendix content
                context += json.dumps(appendix_data, indent=2)
                st.write(f"  - Added content ({len(str(appendix_data))} chars)")
            else:
                context += str(appendix_data)
            
            context += "\n\n" + "="*50 + "\n\n"
            appendix_count += 1
            
            # Special confirmation for Appendix 3
            if appendix_key == 'appendix_3':
                st.write("🎯 **APPENDIX 3 SUCCESSFULLY PROCESSED!**")
        
        st.write(f"✅ Successfully processed {appendix_count} appendices")
    else:
        st.write(f"❌ **NO APPENDICES SECTION** found in {agreement_name}")
    
    # Final verification
    final_length = len(context)
    st.write(f"📊 **FINAL CONTEXT STATS:**")
    st.write(f"- Total length: {final_length:,} characters")
    
    context_lower = context.lower()
    if "appendix 3" in context_lower:
        st.write("✅ 'appendix 3' confirmed in final context")
    else:
        st.write("❌ 'appendix 3' missing from final context")
    
    if "program coordination" in context_lower:
        st.write("✅ 'program coordination' confirmed in final context")
    else:
        st.write("❌ 'program coordination' missing from final context")
    
    return context

def generate_response(query: str, local_agreement: dict, common_agreement: dict, agreement_scope: str, api_key: str) -> str:
    """Generate response using Claude with complete agreement context"""
    
    st.write(f"🚀 **GENERATING RESPONSE v2.0** for scope: {agreement_scope}")
    
    # Build context based on selected scope
    context = ""
    if agreement_scope == "Local Agreement Only":
        context = format_agreement_for_context(local_agreement, "Coast Mountain College Local Agreement")
    elif agreement_scope == "Common Agreement Only":
        context = format_agreement_for_context(common_agreement, "BCGEU Common Agreement")
    else:  # Both agreements
        context = format_agreement_for_context(local_agreement, "Coast Mountain College Local Agreement")
        context += "\n\n" + format_agreement_for_context(common_agreement, "BCGEU Common Agreement")
    
    # Final verification before sending to Claude
    st.write(f"🔍 **PRE-CLAUDE VERIFICATION:**")
    st.write(f"- Context length: {len(context):,} characters")
    st.write(f"- Contains 'appendix 3': {'appendix 3' in context.lower()}")
    st.write(f"- Contains 'program coordination': {'program coordination' in context.lower()}")
    
    system_prompt = f"""You are an experienced HR professional and collective agreement specialist for Coast Mountain College with 15+ years of expertise in labor relations and agreement interpretation. Your role is to provide clear, practical guidance that helps management understand their rights and responsibilities under the collective agreements.

COLLECTIVE AGREEMENT CONTENT:
{context}

IMPORTANT: You have access to the complete collective agreement content above. Look carefully for Appendix 3 content about Program Coordination."""

    user_message = f"""Based on the complete collective agreement provisions provided in the system prompt, provide strong management-focused guidance for this question:

QUESTION: {query}

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
    except Exception as e:
        return f"Error generating response: {e}"

def clear_chat():
    """Clear the chat history"""
    st.session_state.messages = []
    st.rerun()

def main():
    st.title("⚖️ Coast Mountain College Agreement Assistant")
    st.markdown("*Enhanced Debug Version 2.0 - Complete collective agreement analysis*")
    
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'total_queries' not in st.session_state:
        st.session_state.total_queries = 0
    
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
    
    # Agreement Selection
    st.markdown("### 📋 Select Collective Agreement")
    agreement_scope = st.radio(
        "Which agreement do you want to search?",
        ["Local Agreement Only", "Common Agreement Only", "Both Agreements"],
        index=0,
        horizontal=True
    )
    
    st.markdown("---")
    
    # Display conversation history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about collective agreement provisions..."):
        # Load agreements when user submits question
        with st.spinner("Loading agreements..."):
            local_agreement, common_agreement = load_builtin_agreements()
            
            if not local_agreement or not common_agreement:
                st.error("❌ Could not load agreement files.")
                st.stop()
        
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Generating response..."):
                response = generate_response(
                    prompt, 
                    local_agreement, 
                    common_agreement, 
                    agreement_scope,
                    api_key
                )
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Quick test button
    if len(st.session_state.messages) == 0:
        st.markdown("### 🧪 Quick Test")
        if st.button("🔍 Test Appendix 3 Detection", type="primary"):
            st.session_state.messages.append({
                "role": "user", 
                "content": "Can you give me the text for appendix 3?"
            })
            st.rerun()
    
    # Bottom section
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if st.session_state.total_queries > 0:
            st.caption(f"💬 Queries: {st.session_state.total_queries} | 🎯 Scope: {agreement_scope}")
    
    with col2:
        if len(st.session_state.messages) > 0:
            if st.button("🔄 New Chat", type="primary", use_container_width=True):
                clear_chat()

if __name__ == "__main__":
    main()
