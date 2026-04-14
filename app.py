import streamlit as st
from groq import Groq
from pypdf import PdfReader
from duckduckgo_search import DDGS
from docx import Document
from io import BytesIO
import time

st.set_page_config(page_title="Jurista AI: Multi-Chat", page_icon="⚖️", layout="wide")

# --- INICIALIZAÇÃO DA ESTRUTURA DE DADOS ---
if "chats" not in st.session_state:
    st.session_state.chats = {"Conversa 1": []}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = "Conversa 1"

# Funções auxiliares
def criar_docx(texto):
    doc = Document()
    doc.add_heading('Resposta Jurídica AI', 0)
    doc.add_paragraph(texto)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- BARRA LATERAL: GESTÃO DE CHATS ---
st.sidebar.title("💬 Meus Chats")

if st.sidebar.button("➕ Novo Chat"):
    novo_nome = f"Conversa {len(st.session_state.chats) + 1}"
    st.session_state.chats[novo_nome] = []
    st.session_state.current_chat = novo_nome
    st.rerun()

# Lista de chats para escolher
escolha = st.sidebar.radio("Histórico:", list(st.session_state.chats.keys()), index=list(st.session_state.chats.keys()).index(st.session_state.current_chat))
st.session_state.current_chat = escolha

st.sidebar.markdown("---")

# --- CONFIGURAÇÕES TÉCNICAS ---
api_key = st.sidebar.text_input("Groq API Key:", type="password")
perfil = st.sidebar.selectbox("Especialidade:", ["Consultor Geral", "Analisador de Acórdãos", "Especialista Civil", "Especialista Penal", "Revisor"])
usar_web = st.sidebar.checkbox("Pesquisa Web")
uploaded_file = st.sidebar.file_uploader("PDF (Fonte)", type="pdf")

contexto_pdf = ""
if uploaded_file:
    reader = PdfReader(uploaded_file)
    for page in reader.pages:
        txt = page.extract_text()
        if txt: contexto_pdf += txt
    st.sidebar.success("PDF carregado.")

# --- INTERFACE DE CHAT ---
st.title(f"⚖️ {st.session_state.current_chat}")

# Mostrar mensagens do chat selecionado
for message in st.session_state.chats[st.session_state.current_chat]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Lógica de resposta
if prompt := st.chat_input("Escreva aqui..."):
    if not api_key:
        st.error("Insira a API Key.")
    else:
        # Adicionar pergunta do utilizador
        st.session_state.chats[st.session_state.current_chat].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        client = Groq(api_key=api_key)
        
        contexto_web = ""
        if usar_web:
            with st.spinner("A pesquisar..."):
                try:
                    with DDGS() as ddgs:
                        resultados = ddgs.text(f"{prompt} direito portugal", max_results=2)
                        contexto_web = "\n".join([r['body'] for r in resultados])
                except: pass

        sistema_prompt = f"És um {perfil} em Portugal. PDF: {contexto_pdf[:5000]}. Web: {contexto_web}"

        with st.chat_message("assistant"):
            # Enviar apenas o histórico deste chat específico
            mensagens_envio = [{"role": "system", "content": sistema_prompt}] + st.session_state.chats[st.session_state.current_chat][-6:]
            
            try:
                completion = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=mensagens_envio, temperature=0.1)
                response = completion.choices[0].message.content
                st.markdown(response)
                # Guardar resposta no chat correto
                st.session_state.chats[st.session_state.current_chat].append({"role": "assistant", "content": response})
                
                # Botão de download para a última resposta
                st.download_button("📥 Baixar em Word", data=criar_docx(response), file_name=f"{st.session_state.current_chat}.docx")
            except Exception as e:
                st.error(f"Erro na Groq (pode ser o limite de texto): {e}")

if st.sidebar.button("🗑️ Apagar este Chat"):
    if len(st.session_state.chats) > 1:
        del st.session_state.chats[st.session_state.current_chat]
        st.session_state.current_chat = list(st.session_state.chats.keys())[0]
        st.rerun()
    else:
        st.session_state.chats = {"Conversa 1": []}
        st.rerun()
