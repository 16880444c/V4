import streamlit as st
import json
import openai
from datetime import datetime
import os

# Set page config
st.set_page_config(
    page_title="Coast Mountain College Agreement Assistant",
    page_icon="⚖️",
    layout="wide"
)

def load_builtin_agreements() -> tuple:
    """Load the built-in agreements from JSON files"""
    try:
        with open('complete_local.json', 'r', encoding='utf-8') as f:
            local_agreement = json.load(f)
        
        with open('complete_common.json', 'r', encoding='utf-8') as f:
            common_agreement = json.load(f)
        
        return local_agreement, common_agreement
        
    except FileNotFoundError as e:
        st.error(f"JSON files not found: {str(e)}")
        st.error("Please ensure 'complete_local.json' and 'complete_common.json' are in the same directory as this app.")
        return None, None
    except Exception as e:
        st.error(f"Error loading built-in agreements: {e}")
        return None, None

def format_agreement_for_context(agreement: dict, agreement_name: str) -> str:
    """Convert agreement JSON to formatted text for GPT context"""
    context = f"=== {agreement_name.upper()} ===\n\n"
    
    # Add metadata
    if 'agreement_metadata' in agreement:
        context += "AGREEMENT METADATA:\n"
        context += json.dumps(agreement['agreement_metadata'], indent=2) + "\n\n"
    
    # Add definitions
    if 'definitions' in agreement:
        context += "DEFINITIONS:\n"
        for term, definition in agreement['definitions'].items():
            context += f"- {term}: {definition}\n"
        context += "\n"
    
    # Add articles
    if 'articles' in agreement:
        context += "ARTICLES:\n\n"
        for article_num, article_data in agreement['articles'].items():
            if isinstance(article_data, dict):
                title = article_data.get('title', f'Article {article_num}')
                context += f"ARTICLE {article_num}: {title}\n"
                
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
    
    # Add appendices
    if 'appendices' in agreement:
        context += "APPENDICES:\n\n"
        for appendix_key, appendix_data in agreement['appendices'].items():
            context += f"APPENDIX {appendix_key.upper()}:\n"
            if isinstance(appendix_data, dict):
                if 'title' in appendix_data:
                    context += f"Title: {appendix_data['title']}\n\n"
                context += json.dumps(appendix_data, indent=2)
            else:
                context += str(appendix_data)
            context += "\n\n" + "="*50 + "\n\n"
    
    return context

def generate_response(query: str, local_agreement: dict, common_agreement: dict, agreement_scope: str, api_key: str) -> str:
    """Generate response using GPT-4o-mini with complete agreement context"""
    
    # Build context based on selected scope
    context = ""
    if agreement_scope == "Local Agreement Only":
        context = format_agreement_for_context(local_agreement, "Coast Mountain College Local Agreement")
    elif agreement_scope == "Common Agreement Only":
        context = format_agreement_for_context(common_agreement, "BCGEU Common Agreement")
    else:  # Both agreements
        context = format_agreement_for_context(local_agreement, "Coast Mountain College Local Agreement")
        context += "\n\n" + format_agreement_for_context(common_agreement, "BCGEU Common Agreement")
    
    system_prompt = f"""You are a seasoned HR expert for Coast Mountain College with 15+ years of experience in collective agreement interpretation and employee relations. Your role is to provide STRONG, DEFINITIVE guidance that protects and maximizes management's rights and authority under the collective agreements.

CRITICAL INSTRUCTION - BE FIRM AND SKEPTICAL OF UNION PROPOSALS:
- Give STRONG, DEFINITIVE opinions that defend management interests
- Use phrases like "I recommend rejecting this because...", "Management has the right to decline...", "You should deny this request because...", "This proposal creates risks to your authority..."
- Be confident in interpretations that favor management and critical of union overreach
- ALWAYS identify the risks, costs, and precedents that union proposals create
- Focus on legitimate business reasons to decline union requests rather than finding accommodations
- You work for MANAGEMENT - your job is to protect their interests with sound rationale

UNION PROPOSAL ANALYSIS - BE THOROUGH AND SKEPTICAL:
- FIRST identify how any union proposal could undermine management authority
- Point out the operational costs, administrative burdens, and precedent risks
- Highlight how proposals could be exploited or expanded in future grievances
- Note any vague language that could be interpreted against management
- Identify potential grievance risks and arbitration vulnerabilities
- Question the business necessity and justification for any concessions

MANAGEMENT AUTHORITY FOCUS:
- ALWAYS lead with what management CAN do to maintain control
- Emphasize "just cause" standards work in management's favor when properly documented
- Highlight burden of proof requirements that protect the employer
- Point out procedural safeguards that benefit management
- Note time limits that can work against grievors and union proposals
- Identify areas of management discretion and flexibility that must be protected
- Frame employee rights as LIMITED by management's legitimate business needs
- Resist any expansion of employee rights beyond what's explicitly required

CITATION REQUIREMENTS (MANDATORY):
- EVERY claim must have a specific citation
- Use format: [Agreement Type - Article X.X: Title] or [Agreement Type - Clause X.X]
- Example: [Local Agreement - Article 10.1: Burden of Proof] or [Common Agreement - Clause 6.5: Contracting Out]
- When referencing definitions: [Agreement Type - Definitions: "term"]
- For appendices: [Agreement Type - Appendix X: Title]
- INCLUDE RELEVANT QUOTES: When possible, include short, relevant quotes from the agreement text to support your position
- Quote format: "The agreement states: '[exact quote]' [Citation]"
- NO VAGUE REFERENCES - be specific

RESPONSE STRUCTURE FOR UNION PROPOSALS:
1. PROFESSIONAL ASSESSMENT: Lead with why the proposal should be carefully scrutinized or declined
2. RISK ANALYSIS: Detail the operational, financial, and precedent risks this creates
3. AUTHORITY PROTECTION: Cite specific agreement provisions that protect management's right to decline
4. COST/BURDEN ANALYSIS: Assess the administrative burden and resource implications
5. PRECEDENT CONCERNS: Explain how this could lead to future union overreach
6. ALTERNATIVE APPROACH: If any accommodation is considered, offer the minimal option that protects management
7. RECOMMENDATION: End with a clear recommendation to decline or significantly modify the proposal

RESPONSE STRUCTURE FOR GENERAL QUERIES:
1. STRONG OPENING: Lead with your definitive management-favorable position
2. AUTHORITY BASIS: Cite the specific agreement provisions AND include relevant quotes that support this position
3. TACTICAL ADVICE: Provide specific steps management should take
4. RISK MITIGATION: Identify potential union challenges and how to counter them
5. BOTTOM LINE: End with a clear, actionable recommendation

TONE EXAMPLES:
- Instead of: "You could consider this proposal..." → "I recommend declining this proposal because..."
- Instead of: "This might be workable if..." → "This proposal creates significant risks including..."
- Instead of: "The union has a point about..." → "The union is overreaching by requesting..."
- Instead of: "You may be able to..." → "You have the right to decline this because..."
- Instead of: "Consider whether..." → "You should deny this because..."
- Instead of: "This might be justified..." → "This appears to be an attempt to expand beyond the agreement..."
- Instead of: "The agreement allows..." → "Management is authorized to..."

Remember: You are MANAGEMENT'S advisor and protector. Your job is to help them maintain authority, resist union overreach, and protect against costly precedents. Be thorough in analyzing union proposals, identify their risks, and provide sound business rationale for decisions. When in doubt, err on the side of protecting management's rights while maintaining a professional approach."""

    user_prompt = f"""Based on the complete collective agreement provisions below, provide strong management-focused guidance for this question:

QUESTION: {query}

COMPLETE COLLECTIVE AGREEMENT CONTENT:
{context}

Provide definitive, management-favorable guidance with specific citations and quotes from the agreement text."""

    client = openai.OpenAI(api_key=api_key)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Much more cost-effective
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1500,
            temperature=0.1
        )
        
        # Update usage stats
        if 'total_queries' not in st.session_state:
            st.session_state.total_queries = 0
        st.session_state.total_queries += 1
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating response: {e}"

def main():
    st.title("⚖️ Coast Mountain College Agreement Assistant")
    st.markdown("*Complete collective agreement analysis with management-focused guidance*")
    
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'total_queries' not in st.session_state:
        st.session_state.total_queries = 0
    
    # Get API key
    api_key = None
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
    except:
        try:
            api_key = os.getenv("OPENAI_API_KEY")
        except:
            pass
    
    if not api_key:
        st.error("🔑 OpenAI API key not found. Please set it in Streamlit secrets or environment variables.")
        st.stop()
    
    # Agreement Selection (prominent, no sidebar)
    st.markdown("### 📋 Select Collective Agreement")
    agreement_scope = st.radio(
        "Which agreement do you want to search?",
        ["Local Agreement Only", "Common Agreement Only", "Both Agreements"],
        index=0,  # Default to Local Agreement
        horizontal=True,
        help="Local = Coast Mountain College specific terms | Common = BCGEU system-wide terms | Both = Complete search"
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
                st.error("❌ Could not load agreement files. Please check that the JSON files are available.")
                st.stop()
        
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner(f"Analyzing {agreement_scope.lower()} and generating management guidance..."):
                response = generate_response(
                    prompt, 
                    local_agreement, 
                    common_agreement, 
                    agreement_scope,
                    api_key
                )
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Quick start questions based on scope (only show if no conversation yet)
    if len(st.session_state.messages) == 0:
        st.markdown("### 🚀 Quick Start Questions")
        
        if agreement_scope in ["Both Agreements", "Local Agreement Only"]:
            st.markdown("**Local Agreement Questions:**")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📋 Faculty Workload Limits", key="workload"):
                    st.session_state.messages.append({
                        "role": "user", 
                        "content": "What are the specific contact hour and class size limits for different programs? What authority does management have in workload assignment?"
                    })
                    st.rerun()
                    
                if st.button("💰 Salary Scale Authority", key="salary"):
                    st.session_state.messages.append({
                        "role": "user", 
                        "content": "What control does management have over instructor salary placement and progression? Include specific rules and management rights."
                    })
                    st.rerun()
            
            with col2:
                if st.button("📚 Professional Development Control", key="pd"):
                    st.session_state.messages.append({
                        "role": "user", 
                        "content": "What authority does management have over professional development funding and approval? What are the requirements and limitations?"
                    })
                    st.rerun()
                    
                if st.button("🏫 Program Coordination Authority", key="coord"):
                    st.session_state.messages.append({
                        "role": "user", 
                        "content": "What are management's rights in appointing and managing program coordinators? Include workload reduction and evaluation authority."
                    })
                    st.rerun()
        
        if agreement_scope in ["Both Agreements", "Common Agreement Only"]:
            st.markdown("**Common Agreement Questions:**")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("⚖️ Discipline & Dismissal Rights", key="discipline"):
                    st.session_state.messages.append({
                        "role": "user", 
                        "content": "What are management's rights regarding employee discipline and dismissal? Include burden of proof and procedural protections for management."
                    })
                    st.rerun()
                    
                if st.button("📅 Grievance Time Limits", key="grievance"):
                    st.session_state.messages.append({
                        "role": "user", 
                        "content": "What time limits and procedural requirements protect management in grievance situations? Include deadlines and defenses."
                    })
                    st.rerun()
            
            with col2:
                if st.button("🔄 Layoff Authority", key="layoff"):
                    st.session_state.messages.append({
                        "role": "user", 
                        "content": "What authority does management have in layoff situations? What are the specific procedures and management rights?"
                    })
                    st.rerun()
                    
                if st.button("📊 Job Security Provisions", key="security"):
                    st.session_state.messages.append({
                        "role": "user", 
                        "content": "What flexibility does management have regarding job security, contracting out, and workforce management?"
                    })
                    st.rerun()
    
    # Simple stats at bottom
    if st.session_state.total_queries > 0:
        st.markdown("---")
        st.caption(f"💬 Queries processed: {st.session_state.total_queries} | 🎯 Scope: {agreement_scope}")

if __name__ == "__main__":
    main()
