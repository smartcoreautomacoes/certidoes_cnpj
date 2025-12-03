import streamlit as st
import requests
import time
import re
import base64
from io import BytesIO
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

# ==============================================================================
# CONFIGURAÇÃO VISUAL & CSS (Visual Minimalista e Moderno)
# ==============================================================================
st.set_page_config(
    page_title="Hub de Certidões Corporativas",
    page_icon="⚖️",
    layout="wide"
)

st.markdown("""
    <style>
    /* Limpeza geral */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Inputs e Botões */
    .stTextInput > div > div > input { border-radius: 8px; border: 1px solid #ced4da; }
    .stButton > button {
        border-radius: 8px; font-weight: 600;
        transition: all 0.2s ease-in-out;
    }
    
    /* Card da Empresa */
    .company-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 25px; border-radius: 12px;
        border-left: 6px solid #2c3e50;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 25px;
        color: #2c3e50;
    }
    
    /* Card do Documento */
    .doc-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        transition: transform 0.2s;
    }
    .doc-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    .doc-header {
        font-size: 1.1rem; font-weight: bold; color: #34495e;
        margin-bottom: 10px; border-bottom: 2px solid #f1f2f6; padding-bottom: 5px;
    }
    
    /* Botão Link Externo */
    .external-link {
        display: inline-block;
        text-decoration: none;
        background-color: #27ae60;
        color: white !important;
        padding: 8px 16px;
        border-radius: 6px;
        font-size: 0.9rem;
        margin-top: 10px;
        text-align: center;
        width: 100%;
    }
    .external-link:hover { background-color: #219150; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# MAPEAMENTO DE FONTES OFICIAIS
# ==============================================================================
OFFICIAL_SOURCES = {
    "CND Tributos Federais": {
        "url": "https://servicos.receitafederal.gov.br/servico/certidoes/#/home/cnpj",
        "desc": "Receita Federal"
    },
    "CND Trabalhista (TST)": {
        "url": "https://www.tst.jus.br/certidao1",
        "desc": "Tribunal Superior do Trabalho"
    },
    "FGTS (Caixa)": {
        "url": "https://consulta-crf.caixa.gov.br/consultacrf/pages/consultaEmpregador.jsf",
        "desc": "Caixa Econômica Federal"
    },
    "Cartão CNPJ": {
        "url": "https://solucoes.receita.fazenda.gov.br/Servicos/cnpjreva/Cnpjreva_Solicitacao.asp",
        "desc": "Receita Federal"
    }
}

# ==============================================================================
# BACKEND (API & PDF)
# ==============================================================================

class CNPJService:
    @staticmethod
    def get_real_data(cnpj: str):
        clean_cnpj = re.sub(r'\D', '', cnpj)
        try:
            response = requests.get(f"https://brasilapi.com.br/api/cnpj/v1/{clean_cnpj}", timeout=10)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return {"error": "CNPJ não encontrado na base oficial."}
            else:
                return {"error": f"Erro na API: {response.status_code}"}
        except Exception as e:
            return {"error": f"Erro de conexão: {str(e)}"}

class PDFGenerator:
    @staticmethod
    def create(company_data: dict, doc_type: str) -> BytesIO:
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        
        # Design Profissional
        c.setStrokeColor("#2c3e50")
        c.setLineWidth(1)
        c.rect(20, 20, 555, 800)
        
        # Logo (Tentativa Segura)
        try:
            logo_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/2/21/Bras%C3%A3o_da_Rep%C3%BAblica_Federativa_do_Brasil.svg/1200px-Bras%C3%A3o_da_Rep%C3%BAblica_Federativa_do_Brasil.svg.png"
            headers = {'User-Agent': 'Mozilla/5.0'} 
            img_response = requests.get(logo_url, headers=headers, timeout=3)
            if img_response.status_code == 200:
                img = ImageReader(BytesIO(img_response.content))
                c.drawImage(img, 270, 750, width=50, height=50, mask='auto')
        except:
            pass # Falha silenciosa no logo para não parar o app
        
        c.setFillColor("#2c3e50")
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(297, 730, "REPÚBLICA FEDERATIVA DO BRASIL")
        c.setFont("Helvetica", 10)
        c.drawCentredString(297, 715, "SISTEMA CENTRALIZADO DE CERTIDÕES")
        
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(297, 670, doc_type.upper())
        
        c.setStrokeColor("#bdc3c7")
        c.line(40, 650, 555, 650)
        
        # Dados da Empresa
        y = 620
        c.setFont("Helvetica-Bold", 11)
        c.drawString(40, y, "DADOS DO CONTRIBUINTE:")
        
        c.setFont("Helvetica", 10)
        c.setFillColor("black")
        y -= 25
        c.drawString(40, y, f"CNPJ: {company_data.get('cnpj_fmt', 'N/A')}")
        y -= 15
        c.drawString(40, y, f"Razão Social: {company_data.get('razao_social', '')[:65]}")
        y -= 15
        c.drawString(40, y, f"Fantasia: {company_data.get('nome_fantasia', '')[:65]}")
        y -= 15
        
        end = f"{company_data.get('logradouro','')}, {company_data.get('numero','')} - {company_data.get('bairro','')}"
        c.drawString(40, y, f"Endereço: {end[:75]}")
        y -= 15
        c.drawString(40, y, f"Local: {company_data.get('municipio','')}/{company_data.get('uf','')}")
        
        # Área de Status
        y -= 45
        c.setFillColor("#ecf0f1") # Fundo cinza claro
        c.rect(40, y-10, 515, 25, fill=1, stroke=0)
        c.setFillColor("black")
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y-4, f"SITUAÇÃO CADASTRAL ATUAL: {company_data.get('descricao_situacao_cadastral', 'ATIVA')}")
        
        # Texto Legal (Simulação)
        y -= 50
        c.setFont("Helvetica", 10)
        text_lines = [
            "Este documento é uma representação consolidada dos dados públicos disponíveis.",
            "A emissão oficial definitiva deve ser validada nos sites governamentais competentes.",
            "Certificamos que, até o momento da consulta, os dados cadastrais acima conferem",
            "com a base da Receita Federal do Brasil."
        ]
        
        for line in text_lines:
            c.drawString(40, y, line)
            y -= 15
            
        # Rodapé
        c.setFont("Helvetica-Oblique", 8)
        c.setFillColor("#7f8c8d")
        c.drawString(40, 40, f"Gerado via Hub Python em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        c.drawString(40, 30, f"Hash de Controle: {hash(time.time())}")
        
        c.save()
        buffer.seek(0)
        return buffer

# ==============================================================================
# FRONTEND (VIEW)
# ==============================================================================

def main():
    # Sidebar
    st.sidebar.title("🛠️ Painel")
    st.sidebar.markdown("**Modo de Operação:**")
    st.sidebar.info("✅ Consulta API Brasil (Online)\n✅ Geração de PDF (Local)\n✅ Links Oficiais (Gov.br)")
    
    # Header
    st.title("Hub de Regularidade Fiscal")
    st.markdown("#### Central de emissão e verificação de certidões via CNPJ")
    
    # Session State Init
    if 'company_data' not in st.session_state:
        st.session_state['company_data'] = {}
    if 'search_done' not in st.session_state:
        st.session_state['search_done'] = False

    # Input Area
    with st.container():
        col1, col2 = st.columns([3, 1])
        with col1:
            cnpj_input = st.text_input("Insira o CNPJ da empresa:", placeholder="00.000.000/0000-00", max_chars=18)
        with col2:
            st.write("")
            st.write("")
            btn_buscar = st.button("🔍 Buscar CNPJ", use_container_width=True)

    # Lógica de Busca
    if btn_buscar and cnpj_input:
        with st.spinner('Validando CNPJ na base da Receita...'):
            data = CNPJService.get_real_data(cnpj_input)
            
            if "error" in data:
                st.error(f"❌ {data['error']}")
                st.session_state['search_done'] = False
            else:
                # Formatando
                raw_cnpj = data['cnpj']
                data['cnpj_fmt'] = f"{raw_cnpj[:2]}.{raw_cnpj[2:5]}.{raw_cnpj[5:8]}/{raw_cnpj[8:12]}-{raw_cnpj[12:]}"
                
                st.session_state['company_data'] = data
                st.session_state['search_done'] = True

    # Exibição dos Resultados
    if st.session_state['search_done'] and st.session_state['company_data']:
        data = st.session_state['company_data']
        
        # 1. Card Principal da Empresa
        st.markdown(f"""
        <div class="company-card">
            <h2 style="margin:0; color:#2c3e50">{data.get('razao_social')}</h2>
            <p style="margin:5px 0; color:#7f8c8d">{data.get('nome_fantasia', '')}</p>
            <hr style="border:0; border-top:1px solid #bdc3c7; margin:15px 0;">
            <div style="display:flex; justify-content:space-between; flex-wrap:wrap;">
                <div><strong>CNPJ:</strong> {data.get('cnpj_fmt')}</div>
                <div><strong>Abertura:</strong> {data.get('data_inicio_atividade')}</div>
                <div><strong>Situação:</strong> <span style="background:#27ae60; color:white; padding:2px 8px; border-radius:4px;">{data.get('descricao_situacao_cadastral')}</span></div>
            </div>
            <p style="margin-top:10px;"><strong>Endereço:</strong> {data.get('logradouro')}, {data.get('numero')} - {data.get('bairro')}, {data.get('municipio')}/{data.get('uf')}</p>
        </div>
        """, unsafe_allow_html=True)

        # 2. Área de Certidões
        st.subheader("📂 Certidões Disponíveis")
        
        # Filtros
        docs_list = list(OFFICIAL_SOURCES.keys())
        selected_docs = st.multiselect("Filtrar documentos:", docs_list, default=docs_list)
        
        if selected_docs:
            st.markdown("<br>", unsafe_allow_html=True)
            # Layout Grid
            cols = st.columns(2)
            
            for idx, doc_name in enumerate(selected_docs):
                col = cols[idx % 2]
                
                # Gera PDF Interno (Representação)
                pdf_buffer = PDFGenerator.create(data, doc_name)
                b64_pdf = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
                
                source_info = OFFICIAL_SOURCES.get(doc_name, {})
                
                with col:
                    # Renderiza Card HTML
                    st.markdown(f"""
                    <div class="doc-card">
                        <div class="doc-header">{doc_name}</div>
                        <p style="font-size:0.85rem; color:#7f8c8d; margin-bottom:10px;">
                            Fonte Oficial: <strong>{source_info.get('desc')}</strong>
                        </p>
                        
                        <!-- Preview do PDF -->
                        <iframe src="data:application/pdf;base64,{b64_pdf}#toolbar=0&view=FitH" width="100%" height="250" style="border:1px solid #eee; border-radius:4px;"></iframe>
                        
                        <!-- Botão Link Oficial (O "Pulo do Gato") -->
                        <a href="{source_info.get('url')}" target="_blank" class="external-link">
                            🌐 Emitir no Site Oficial ({source_info.get('desc')})
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Botão Download Python (Separado para manter funcionalidade nativa do Streamlit)
                    st.download_button(
                        label="⬇️ Baixar Prévia (PDF)",
                        data=pdf_buffer,
                        file_name=f"{doc_name.replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        key=f"btn_{idx}",
                        use_container_width=True
                    )

if __name__ == "__main__":
    main()