import streamlit as st
from groq import Groq
from pypdf import PdfReader
from duckduckgo_search import DDGS
from docx import Document
from io import BytesIO

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="AEQUITAS AI", page_icon="⚖️", layout="wide")

# CSS para esconder a barra lateral por padrão em telemóveis e dar aspeto limpo
st.markdown("""
    <style>
    .stChatFloatingInputContainer { background-color: #0e1117; }
    .stChatMessage { background-color: #1a1c24 !important; border-radius: 15px; }
    h1 { color: #c9a44c; text-align: center; font-family: 'Georgia', serif; }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DA CHAVE SECRETA ---
# Aqui o código vai buscar a chave que acabaste de pôr nos Secrets
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    st.error("Erro de configuração: Chave não encontrada nos Secrets.")
    st.stop()

# --- INICIALIZAÇÃO ---
if "chats" not in st.session_state:
    st.session_state.chats = {"Consulta Inicial": []}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = "Consulta Inicial"

def criar_docx(texto):
    doc = Document()
    doc.add_heading('AEQUITAS AI - PARECER JURÍDICO', 0)
    doc.add_paragraph(texto)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='color: #c9a44c; text-align: center;'>AEQUITAS AI</h2>", unsafe_allow_html=True)
    if st.button("➕ Novo Processo", use_container_width=True):
        n = f"Processo {len(st.session_state.chats) + 1}"
        st.session_state.chats[n] = []
        st.session_state.current_chat = n
        st.rerun()
    
    st.markdown("---")
    escolha = st.radio("Histórico de Casos:", list(st.session_state.chats.keys()))
    st.session_state.current_chat = escolha
    
    st.markdown("---")
    perfil = st.selectbox("Especialidade:", ["Geral", "Civil", "Penal", "Trabalho"])
    uploaded_file = st.file_uploader("Anexar Prova/Acórdão (PDF)", type="pdf")

# --- CHAT PRINCIPAL ---
st.title("⚖️ AEQUITAS AI")
st.caption("Suíte de Inteligência Jurídica para o Direito Português")

contexto_pdf = ""
if uploaded_file:
    reader = PdfReader(uploaded_file)
    contexto_pdf = "\n".join([p.extract_text() for p in reader.pages if p.extract_text()])

# Mostrar histórico
for msg in st.session_state.chats[st.session_state.current_chat]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input do utilizador
if prompt := st.chat_input("Em que posso ajudar hoje?"):
    st.session_state.chats[st.session_state.current_chat].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    client = Groq(api_key=api_key)
    
    with st.chat_message("assistant"):
        with st.spinner("A analisar ordenamento jurídico..."):
            sistema = f"És o AEQUITAS AI. Especialista em Direito Português ({perfil}). Contexto PDF: {contexto_pdf[:6000]}"
            mensagens = [{"role": "system", "content": sistema}] + st.session_state.chats[st.session_state.current_chat][-5:]
            
            comp = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=mensagens, temperature=0.1)
            res = comp.choices[0].message.content
            st.markdown(res)
            st.session_state.chats[st.session_state.current_chat].append({"role": "assistant", "content": res})
            
            st.download_button("📥 Baixar Parecer (.docx)", data=criar_docx(res), file_name=f"Parecer_Aequitas.docx")
