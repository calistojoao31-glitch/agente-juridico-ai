import streamlit as st
from groq import Groq
from pypdf import PdfReader
from duckduckgo_search import DDGS
from docx import Document
from io import BytesIO

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="AEQUITAS AI | Legal Intelligence", page_icon="⚖️", layout="wide")

# --- DESIGN PREMIUM ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stChatFloatingInputContainer { background-color: #0e1117; padding-bottom: 20px; }
    .stChatMessage { background-color: #1a1c24 !important; border-radius: 15px; border: 1px solid #2d2f3b; margin-bottom: 10px; }
    h1 { color: #c9a44c; text-align: center; font-family: 'Georgia', serif; font-weight: bold; margin-bottom: 5px; }
    .stButton>button { background-color: #c9a44c; color: white; border-radius: 8px; border: none; font-weight: bold; width: 100%; transition: 0.3s; }
    .stButton>button:hover { background-color: #a68539; border: 1px solid white; transform: scale(1.02); }
    .stSelectbox label, .stRadio label { color: #c9a44c !important; font-weight: bold; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- GESTÃO DE CHAVE API (SECRETS) ---
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    api_key = st.sidebar.text_input("Configuração: Chave API", type="password", help="Insira a chave caso não esteja nos Secrets.")

# --- INICIALIZAÇÃO DE SESSÃO ---
if "chats" not in st.session_state:
    st.session_state.chats = {"Processo Alpha": []}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = "Processo Alpha"

def criar_docx(texto):
    doc = Document()
    doc.add_heading('AEQUITAS AI - CONSULTORIA JURÍDICA', 0)
    doc.add_paragraph(texto)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #c9a44c;'>AEQUITAS AI</h2>", unsafe_allow_html=True)
    st.caption("<p style='text-align: center; margin-top: -15px;'>V 1.0 | Professional Suite</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    if st.button("➕ NOVO CASO"):
        novo_id = f"Processo {len(st.session_state.chats) + 1}"
        st.session_state.chats[novo_id] = []
        st.session_state.current_chat = novo_id
        st.rerun()
    
    st.markdown("### 📂 Gestão de Ficheiros")
    escolha = st.radio("Selecione o chat ativo:", list(st.session_state.chats.keys()))
    st.session_state.current_chat = escolha
    
    st.markdown("---")
    perfil = st.selectbox("Área do Direito:", ["Geral", "Civil", "Penal", "Laboral", "Comercial", "Administrativo"])
    uploaded_file = st.file_uploader("📥 Anexar Peça/Acórdão (PDF)", type="pdf")
    
    st.markdown("---")
    if st.button("🗑️ ARQUIVAR CASO ATUAL"):
        if len(st.session_state.chats) > 1:
            del st.session_state.chats[st.session_state.current_chat]
            st.session_state.current_chat = list(st.session_state.chats.keys())[0]
            st.rerun()
        else:
            st.session_state.chats = {"Processo Alpha": []}
            st.rerun()

# --- ÁREA DE TRABALHO ---
st.markdown("<h1>⚖️ AEQUITAS AI</h1>", unsafe_allow_html=True)

# Processamento de PDF (com Cache para velocidade)
contexto_pdf = ""
if uploaded_file:
    try:
        pdf_reader = PdfReader(uploaded_file)
        # Extraímos apenas as primeiras 15 páginas para evitar sobrecarga de memória
        contexto_pdf = "\n".join([page.extract_text() for page in pdf_reader.pages[:15] if page.extract_text()])
        st.sidebar.success("📚 Documento Indexado")
    except Exception:
        st.sidebar.error("Falha ao ler o PDF.")

# Exibição do Histórico
for msg in st.session_state.chats[st.session_state.current_chat]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Fluxo de Resposta
if prompt := st.chat_input("Ex: Analise a validade deste contrato ou procure jurisprudência sobre..."):
    # 1. Mostrar e Guardar Mensagem do Utilizador
    st.session_state.chats[st.session_state.current_chat].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if not api_key:
        st.error("⚠️ Configuração Pendente: A API Key não foi detetada.")
    else:
        client = Groq(api_key=api_key)
        
        with st.chat_message("assistant"):
            with st.spinner("A consultar jurisprudência e doutrina..."):
                # Pesquisa Web Dinâmica
                info_web = ""
                try:
                    with DDGS() as ddgs:
                        q = f"{prompt} direito portugal site:dre.pt OR site:pgdlisboa.pt"
                        results = ddgs.text(q, max_results=2)
                        info_web = "\n".join([r['body'] for r in results])
                except: pass

                # Prompt Estruturado
                system_instruction = f"""És o AEQUITAS AI, uma inteligência artificial especializada no Direito de Portugal.
                Área: {perfil}.
                Contexto PDF: {contexto_pdf[:6000]}
                Info Web Recente: {info_web}
                Diretrizes: Resposta técnica, formal e objetiva. Se citar legislação, deve ser Portuguesa. 
                Prioriza o conteúdo do PDF se este tiver sido carregado."""

                try:
                    # Limitar histórico enviado para manter foco e rapidez
                    mensagens_prompt = [{"role": "system", "content": system_instruction}] + st.session_state.chats[st.session_state.current_chat][-4:]
                    
                    chat_completion = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=mensagens_prompt,
                        temperature=0.1
                    )
                    
                    full_response = chat_completion.choices[0].message.content
                    st.markdown(full_response)
                    
                    # Guardar no Estado
                    st.session_state.chats[st.session_state.current_chat].append({"role": "assistant", "content": full_response})
                    
                    # Ferramenta de Download
                    st.download_button(
                        label="📥 Exportar para Relatório (.docx)",
                        data=criar_docx(full_response),
                        file_name=f"Aequitas_Relatorio_{st.session_state.current_chat}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                except Exception as e:
                    st.error("Serviço temporariamente congestionado. Por favor, aguarde 15 segundos.")
