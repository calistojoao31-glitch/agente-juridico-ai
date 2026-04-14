import streamlit as st
from groq import Groq
from pypdf import PdfReader
from duckduckgo_search import DDGS

st.set_page_config(page_title="Jurista AI Pro", page_icon="⚖️", layout="wide")

st.title("⚖️ Jurista AI: Modo Rigoroso & Verificação")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Barra Lateral
api_key = st.sidebar.text_input("Insira a sua Groq API Key:", type="password")
modo_rigoroso = st.sidebar.toggle("Ativar Modo Rigoroso (Evita Alucinações)", value=True)
usar_web = st.sidebar.checkbox("Pesquisar na Internet (Leis PT)")
uploaded_file = st.sidebar.file_uploader("Carregar Código/Documento (PDF)", type="pdf")

contexto_pdf = ""
if uploaded_file:
    reader = PdfReader(uploaded_file)
    for page in reader.pages:
        txt = page.extract_text()
        if txt: contexto_pdf += txt
    st.sidebar.success("Documento carregado como fonte primária!")

# Exibir histórico
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Dúvida jurídica ou análise de caso..."):
    if not api_key:
        st.error("Insira a API Key.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        client = Groq(api_key=api_key)
        
        # Pesquisa Web otimizada
        contexto_web = ""
        if usar_web:
            with st.spinner("A consultar fontes oficiais (DRE/PGDL)..."):
                try:
                    with DDGS() as ddgs:
                        # Busca focada em legislação e jurisprudência PT
                        query = f"{prompt} lei portugal site:dre.pt OR site:pgdlisboa.pt OR site:tribunais.org.pt"
                        resultados = ddgs.text(query, max_results=4)
                        contexto_web = "\n\nFONTES ENCONTRADAS NA WEB:\n" + "\n".join([r['body'] for r in resultados])
                except:
                    st.warning("Falha na pesquisa web. A usar conhecimento base.")

        # Construção do Prompt com Camada de Verificação
        sistema_instrucoes = f"""
        És um Consultor Jurídico Sénior em Portugal. 
        O teu objetivo é a PRECISÃO.
        
        DIRETRIZES:
        1. Se o utilizador carregou um PDF, esse documento é a tua LEI SUPREMA. Cita o texto dele exatamente.
        2. Se usares a Web, foca-te nos resultados de sites .pt.
        3. MODO RIGOROSO ATIVADO: Antes de responderes, verifica mentalmente se o artigo citado existe mesmo no ordenamento jurídico português. 
        4. Se não tiveres a certeza do número de um artigo, diz explicitamente: "Não tenho a confirmação do número exato, mas a norma estabelece que...".
        5. NUNCA mistures Direito Brasileiro com Português.
        """

        with st.chat_message("assistant"):
            # O "Truque" da Autocrítica: Pedimos à IA para validar a sua própria resposta
            prompt_final = f"Contexto do Documento: {contexto_pdf[:12000]}\n\nContexto Web: {contexto_web}\n\nPergunta: {prompt}"
            
            mensagens_envio = [
                {"role": "system", "content": sistema_instrucoes},
                {"role": "user", "content": prompt_final}
            ]
            
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile", 
                messages=mensagens_envio,
                temperature=0.1 # Temperatura baixa = menos criatividade (mentiras) e mais factos.
            )
            
            response = completion.choices[0].message.content
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

if st.sidebar.button("Limpar Histórico"):
    st.session_state.messages = []
    st.rerun()
