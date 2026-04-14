import streamlit as st
from groq import Groq
from pypdf import PdfReader

st.set_page_config(page_title="Jurista Conversacional", page_icon="⚖️", layout="wide")

st.title("⚖️ Jurista AI: Chat & Documentos")

# Inicializar memória da conversa se não existir
if "messages" not in st.session_state:
    st.session_state.messages = []

# Barra Lateral
api_key = st.sidebar.text_input("Insira a sua Groq API Key:", type="password")
uploaded_file = st.sidebar.file_uploader("Carregar PDF Jurídico", type="pdf")

contexto_pdf = ""
if uploaded_file:
    reader = PdfReader(uploaded_file)
    for page in reader.pages:
        contexto_pdf += page.extract_text()
    st.sidebar.success("PDF lido com sucesso!")

# Exibir histórico de mensagens
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Lógica de Chat
if prompt := st.chat_input("Faça uma pergunta sobre o caso ou documento..."):
    if not api_key:
        st.error("Por favor, insira a API Key.")
    else:
        # Adicionar mensagem do utilizador ao histórico
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Preparar o contexto para a IA
        client = Groq(api_key=api_key)
        
        # Construir o prompt do sistema com o conteúdo do PDF
        sistema_prompt = "És um jurista de elite. Responde com base no contexto abaixo e no histórico da conversa."
        if contexto_pdf:
            sistema_prompt += f"\n\nCONTEÚDO DO DOCUMENTO:\n{contexto_pdf[:15000]}" # Limite para não travar

        # Chamar a IA com o histórico completo
        with st.chat_message("assistant"):
            full_prompt = [{"role": "system", "content": sistema_prompt}] + [
                {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
            ]
            
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=full_prompt
            )
            response = completion.choices[0].message.content
            st.markdown(response)
            
        # Adicionar resposta ao histórico
        st.session_state.messages.append({"role": "assistant", "content": response})

if st.sidebar.button("Limpar Conversa"):
    st.session_state.messages = []
    st.rerun()
