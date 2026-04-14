import streamlit as st
from groq import Groq
from pypdf import PdfReader
from duckduckgo_search import DDGS

st.set_page_config(page_title="Jurista AI Conectado", page_icon="⚖️", layout="wide")

st.title("⚖️ Jurista AI: Chat, Documentos & Web")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Barra Lateral
api_key = st.sidebar.text_input("Insira a sua Groq API Key:", type="password")
usar_web = st.sidebar.checkbox("Ativar Pesquisa na Internet (Códigos/Leis)")
uploaded_file = st.sidebar.file_uploader("Carregar PDF Jurídico", type="pdf")

contexto_pdf = ""
if uploaded_file:
    reader = PdfReader(uploaded_file)
    for page in reader.pages:
        contexto_pdf += page.extract_text()
    st.sidebar.success("PDF lido com sucesso!")

# Exibir histórico
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Faça uma pergunta sobre o caso, lei ou código..."):
    if not api_key:
        st.error("Por favor, insira a API Key.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        client = Groq(api_key=api_key)
        
        contexto_web = ""
        if usar_web:
            with st.spinner("A pesquisar na internet (Leis/Diário da República)..."):
                try:
                    with DDGS() as ddgs:
                        # Forçamos a pesquisa a focar em sites fidedignos de Portugal
                        resultados = ddgs.text(f"{prompt} legislação portuguesa site:dre.pt OR site:pgdlisboa.pt", max_results=3)
                        contexto_web = "\n\nRESULTADOS DA WEB:\n" + "\n".join([r['body'] for r in resultados])
                except Exception as e:
                    st.error(f"Erro na pesquisa: {e}")

        # Construção do Cérebro
        sistema_prompt = "És um jurista de elite especializado no Direito Português. Responde de forma técnica e cita artigos se possível."
        if contexto_pdf:
            sistema_prompt += f"\n\nCONTEÚDO DO DOCUMENTO CARREGADO:\n{contexto_pdf[:10000]}"
        if contexto_web:
            sistema_prompt += f"\n\nCONTEÚDO ATUALIZADO DA WEB:\n{contexto_web}"

        with st.chat_message("assistant"):
            full_prompt = [{"role": "system", "content": sistema_prompt}] + [
                {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
            ]
            
            completion = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=full_prompt)
            response = completion.choices[0].message.content
            st.markdown(response)
            
        st.session_state.messages.append({"role": "assistant", "content": response})

if st.sidebar.button("Limpar Conversa"):
    st.session_state.messages = []
    st.rerun()
