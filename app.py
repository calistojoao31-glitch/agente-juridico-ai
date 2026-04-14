import streamlit as st
from groq import Groq
from pypdf import PdfReader
from duckduckgo_search import DDGS
from docx import Document
from io import BytesIO

st.set_page_config(page_title="Jurista AI: Word & Jurisprudência", page_icon="⚖️", layout="wide")

# Função para criar o ficheiro Word
def criar_docx(texto):
    doc = Document()
    doc.add_heading('Resposta do Assistente Jurídico AI', 0)
    doc.add_paragraph(texto)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

st.title("⚖️ Jurista AI: Inteligência & Documentos")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_response" not in st.session_state:
    st.session_state.last_response = ""

# --- BARRA LATERAL ---
api_key = st.sidebar.text_input("Insira a sua Groq API Key:", type="password")
perfil = st.sidebar.selectbox(
    "Especialidade:",
    ["Consultor Geral", "Analisador de Acórdãos/Jurisprudência", "Especialista em Direito Civil", "Especialista em Direito Penal", "Revisor de Estilo"]
)
usar_web = st.sidebar.checkbox("Pesquisa Web Ativa")
uploaded_file = st.sidebar.file_uploader("Upload de Acórdão ou Peça (PDF)", type="pdf")

contexto_pdf = ""
if uploaded_file:
    reader = PdfReader(uploaded_file)
    for page in reader.pages:
        txt = page.extract_text()
        if txt: contexto_pdf += txt
    st.sidebar.success("Documento lido.")

# --- CHAT ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Dúvida, análise de acórdão ou redação..."):
    if not api_key:
        st.error("Insira a API Key.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        client = Groq(api_key=api_key)
        
        contexto_web = ""
        if usar_web:
            with st.spinner("A pesquisar jurisprudência e leis..."):
                try:
                    with DDGS() as ddgs:
                        query = f"{prompt} acórdão tribunal portugal site:dgsi.pt OR site:dre.pt"
                        resultados = ddgs.text(query, max_results=3)
                        contexto_web = "\n\nWEB:\n" + "\n".join([r['body'] for r in resultados])
                except: pass

        # Configuração do Prompt conforme o perfil
        instrucoes = {
            "Analisador de Acórdãos/Jurisprudência": "És um especialista em analisar decisões dos tribunais superiores (STJ, Relação). Identifica o sumário, a tese vencedora, eventuais votos de vencido e o impacto prático da decisão.",
            "Consultor Geral": "És um jurista sénior português. Responde com precisão técnica.",
            "Revisor de Estilo": "Atua como revisor. Melhora o texto jurídico sem alterar o sentido legal."
        }

        sistema_prompt = f"{instrucoes.get(perfil, 'És um jurista de elite.')}\n\nPDF: {contexto_pdf[:10000]}\nWEB: {contexto_web}"

        with st.chat_message("assistant"):
            mensagens_envio = [{"role": "system", "content": sistema_prompt}] + st.session_state.messages[-5:]
            
            completion = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=mensagens_envio, temperature=0.1)
            response = completion.choices[0].message.content
            st.markdown(response)
            st.session_state.last_response = response # Guarda para o Word
            
        st.session_state.messages.append({"role": "assistant", "content": response})

# --- BOTÃO DE DOWNLOAD (Apenas se houver resposta) ---
if st.session_state.last_response:
    docx_file = criar_docx(st.session_state.last_response)
    st.download_button(
        label="📥 Descarregar Resposta em Word (.docx)",
        data=docx_file,
        file_name="resposta_juridica.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

if st.sidebar.button("Limpar Tudo"):
    st.session_state.messages = []
    st.session_state.last_response = ""
    st.rerun()
