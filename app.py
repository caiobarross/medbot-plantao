import streamlit as st
import google.generativeai as genai
import tempfile
import os

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="MedBot Plantão", page_icon="🚑", layout="wide")

# PEGA A CHAVE SECRETA (Vamos configurar no próximo passo)
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
else:
    st.error("Chave de API não encontrada. Configure nos 'Secrets' do Streamlit.")
    st.stop()

# BARRA LATERAL
with st.sidebar:
    st.title("📂 Base de Protocolos")
    st.info("Anexe os PDFs do seu plantão aqui.")
    uploaded_files = st.file_uploader("Upload PDFs", type=['pdf'], accept_multiple_files=True)
    
    if uploaded_files and st.button("🔄 Carregar Cérebro"):
        with st.spinner("Lendo documentos..."):
            st.session_state.docs = []
            for arquivo in uploaded_files:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(arquivo.getvalue())
                    tmp_path = tmp.name
                # Envia para o Google
                doc = genai.upload_file(tmp_path, mime_type="application/pdf")
                st.session_state.docs.append(doc)
                os.remove(tmp_path)
            st.success(f"{len(st.session_state.docs)} protocolos ativos!")

# CHAT PRINCIPAL
st.title("🚑 Consultor de Plantão")
st.markdown("---")

if "messages" not in st.session_state:
    st.session_state.messages = []

# LÓGICA DO GEMINI
if "docs" in st.session_state and st.session_state.docs:
    # Instruções de Sistema (Sua versão aprimorada)
    SYSTEM_PROMPT = """
    Você é um Consultor Médico de Plantão.
    FONTE: Use APENAS os PDFs anexados.
    SEGURANÇA: Se não estiver no PDF, diga "Não consta nos protocolos".
    FORMATO:
    - Use tabelas para doses.
    - Destaque alertas em > Bloco de Citação.
    - Cite a fonte (Arquivo e Página) no final.
    """
    
    model = genai.GenerativeModel(model_name="gemini-1.5-pro", system_instruction=SYSTEM_PROMPT)
    
    # Mantém o chat ativo
    if "chat" not in st.session_state:
        st.session_state.chat = model.start_chat(history=[
            {"role": "user", "parts": st.session_state.docs + ["Estude estes arquivos."]},
            {"role": "model", "parts": ["Protocolos estudados. Pronto para o plantão."]}
        ])

    # Exibe mensagens antigas
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Campo de Pergunta
    if prompt := st.chat_input("Qual a conduta para..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Consultando protocolos..."):
                response = st.session_state.chat.send_message(prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
else:
    st.info("👈 Faça o upload dos protocolos na barra lateral para começar.")
