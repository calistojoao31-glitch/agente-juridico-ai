import streamlit as st
from groq import Groq

st.set_page_config(page_title="Jurista AI 360", page_icon="⚖️", layout="wide")

st.title("⚖️ Sistema Jurista Completo AI")
st.markdown("---")

# Barra Lateral
api_key = st.sidebar.text_input("Insira a sua Groq API Key:", type="password")
st.sidebar.info("Este agente atua como Consultor, Estrategista e Revisor.")

if api_key:
    client = Groq(api_key=api_key)
    
    # Abas para diferentes funções de um jurista
    tab1, tab2, tab3 = st.tabs(["📝 Otimização de Peças", "🧠 Análise Estratégica", "📋 Resumo de Processo"])

    with tab1:
        texto_escrita = st.text_area("Insira o texto jurídico para polir:", height=250, key="txt1")
        if st.button("Refinar Escrita"):
            prompt = f"Como um jurista de elite, reescreve o texto abaixo para ser mais persuasivo, claro e direto, eliminando juridiquês arcaico:\n\n{texto_escrita}"
            
            with st.spinner("A polir..."):
                chat_completion = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
                st.success("Versão Sugerida:")
                st.write(chat_completion.choices[0].message.content)

    with tab2:
        tese_juridica = st.text_area("Descreve a tua tese ou o caso:", height=250, key="txt2")
        if st.button("Analisar Riscos"):
            prompt = f"Atua como o advogado da parte contrária e um juiz rigoroso. Analisa esta tese jurídica e aponta 3 pontos fracos e 3 argumentos contrários que devo esperar:\n\n{tese_juridica}"
            
            with st.spinner("A simular oposição..."):
                chat_completion = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
                st.info("Análise de Vulnerabilidades:")
                st.write(chat_completion.choices[0].message.content)

    with tab3:
        processo_longo = st.text_area("Cola aqui o conteúdo bruto do processo/decisão:", height=250, key="txt3")
        if st.button("Extrair Pontos Chave"):
            prompt = f"Resume este documento jurídico extraindo: 1. Partes envolvidas, 2. Pedido principal, 3. Fundamentos de direito, 4. Decisão ou prazo iminente:\n\n{processo_longo}"
            
            with st.spinner("A resumir..."):
                chat_completion = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
                st.warning("Resumo Executivo:")
                st.write(chat_completion.choices[0].message.content)
else:
    st.warning("Aguardando API Key na barra lateral...")
