import streamlit as st
from groq import Groq

st.set_page_config(page_title="Agente Jurídico de Elite", page_icon="⚖️")
st.title("⚖️ Assistente de Escrita e Estratégia Jurídica")

# Configuração da API Key (Introduzida pelo utilizador na interface)
api_key = st.sidebar.text_input("Insira a sua Groq API Key:", type="password")

if api_key:
    client = Groq(api_key=api_key)
    
    texto_original = st.text_area("Cole aqui o seu rascunho jurídico:", height=300)
    
    if st.button("Otimizar Texto"):
        if texto_original:
            with st.spinner("O Agente está a analisar..."):
                prompt = f"Atua como um consultor jurídico de elite. Revê o seguinte texto para torná-lo mais claro, direto e inatacável. Remove juridiquês inútil e aponta falhas lógicas:\n\n{texto_original}"
                
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                )
                
                resposta = chat_completion.choices[0].message.content
                st.subheader("Sugestão de Melhoria:")
                st.write(resposta)
        else:
            st.warning("Por favor, insira algum texto.")
else:
    st.info("Insira a sua API Key na barra lateral para começar.")
