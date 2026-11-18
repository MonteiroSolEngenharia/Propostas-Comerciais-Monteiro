import pandas as pd
import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image as RLImage
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate
from num2words import num2words
from datetime import date, datetime
import gspread
from google.oauth2.service_account import Credentials
import os
import io
import json

# ─────────────────────────────────────────────
LOGO_PATH        = "logo-monteiro.jpg"
NOME_PLANILHA    = "Propostas_Monteiro"

COR_PRINCIPAL  = colors.HexColor("#1A3E6F")
COR_SECUNDARIA = colors.HexColor("#2E86C1")
COR_DESTAQUE   = colors.HexColor("#F39C12")
COR_FUNDO_TAB  = colors.HexColor("#EAF4FB")
COR_BRANCO     = colors.white
COR_TEXTO      = colors.HexColor("#2C3E50")

EMPRESA = {
    "nome":   "Monteiro Projetos de Engenharia",
    "eng":    "Eng. Civil Luciano Monteiro",
    "crea":   "CREA 5061119966",
    "email":  "monteiro_projetos@yahoo.com.br",
    "tel":    "(16) 99194-6578",
    "cidade": "Região Sudeste do Brasil",
    "cnpj":   "05.013.900/0001-97",
}

BANCOS = {
    "C6 Bank — Conta Corrente": {
        "banco":      "336 - Banco C6 S.A.",
        "agencia":    "0001",
        "conta":      "30139206-4",
        "tipo":       "Conta Corrente",
        "pix":        "05.013.900/0001-97",
        "favorecido": "MONTEIRO PROJ DE CONSTR. CIVIL LTDA",
    },
    "Bradesco — Conta Corrente": {
        "banco":      "237 - Banco Bradesco S.A.",
        "agencia":    "0003",
        "conta":      "0262722-1",
        "tipo":       "Conta Corrente",
        "pix":        "05.013.900/0001-97",
        "favorecido": "MONTEIRO PROJ DE CONSTR. CIVIL LTDA",
    },
    "PIX Celular": {
        "banco":      "—",
        "agencia":    "—",
        "conta":      "—",
        "tipo":       "PIX",
        "pix":        "+55 (11) 97793-0283",
        "favorecido": "MONTEIRO PROJ DE CONSTR. CIVIL LTDA",
    },
    "Bradesco — CPF Luciano Monteiro": {
        "banco":      "237 - Banco Bradesco S.A.",
        "agencia":    "0003",
        "conta":      "260022-6",
        "tipo":       "Conta Corrente",
        "pix":        "199.607.698-10",
        "favorecido": "Luciano Monteiro - CPF 199.607.698-10",
    },
}

MANUAIS_BONUS = {
"atp": {
    "titulo": "Manual de Avaliação Técnica de Projetos (ATP) — Estruturas de Concreto e Fundações",
    "resumo": (
        "Resumo institucional do procedimento interno do escritório para avaliação técnica de "
        "projetos estruturais e de fundações, com base na ABECE 002:2015 e normas ABNT correlatas. "
        "Aborda fases de recebimento documental, auditoria de premissas, modelagem independente, "
        "verificações ELU/ELS, gestão de achados e critérios de emissão de parecer."
    ),
},
"estrutural": {
    "titulo": "Manual Técnico — Projeto Estrutural",
    "resumo": (
        "Material educativo e institucional sobre o que é um projeto estrutural, quando ele é "
        "necessário, fundações e investigação geotécnica, responsabilidades técnicas, execução, "
        "controle de qualidade e checklist para o cliente antes de construir, ampliar ou reformar."
    ),
},
}

CATALOGO_SERVICOS = {
    "1.1": {"descricao": "Inspeção Visual e Mapeamento de Anomalias",               "preco": 2500.00, "fase": "Diagnóstico e Investigação"},
    "1.2": {"descricao": "Ensaio de Esclerometria (Resistência Superficial)",       "preco": 1500.00, "fase": "Diagnóstico e Investigação"},
    "1.3": {"descricao": "Ensaio de Pacometria (Mapeamento de Armadura)",           "preco": 1500.00, "fase": "Diagnóstico e Investigação"},
    "1.4": {"descricao": "Verificação de Corrosão Potencial (Carbonatação)",        "preco": 1200.00, "fase": "Diagnóstico e Investigação"},
    "1.5": {"descricao": "Inspeção Não-Destrutiva — Pilares, Vigas e Lajes",        "preco": 4900.00, "fase": "Diagnóstico e Investigação"},
    "1.6": {"descricao": "Ensaio de Pacometria e Esclerometria — 30 pontos",        "preco": 2900.00, "fase": "Diagnóstico e Investigação"},
    "1.7": {"descricao": "Investigação de Fundações com Poço de Inspeção",          "preco": 3000.00, "fase": "Diagnóstico e Investigação"},
    "1.8": {"descricao": "Análise Detalhada de Fissuras e Trincas",                 "preco":  900.00, "fase": "Diagnóstico e Investigação"},
    "1.9": {"descricao": "Levantamento Geométrico de Área",                         "preco": 3500.00, "fase": "Diagnóstico e Investigação"},
    "2.1": {"descricao": "Projeto de Fundações",                                    "preco": 5000.00, "fase": "Projetos e Soluções"},
    "2.2": {"descricao": "Projeto de Estrutura de Concreto Armado",                 "preco": 8000.00, "fase": "Projetos e Soluções"},
    "2.3": {"descricao": "Projeto de Estrutura Metálica",                           "preco": 7500.00, "fase": "Projetos e Soluções"},
    "2.4": {"descricao": "Projeto de Reforço e Recuperação Estrutural",             "preco": 6500.00, "fase": "Projetos e Soluções"},
    "2.5": {"descricao": "Projeto de Regularização",                                "preco": 2800.00, "fase": "Projetos e Soluções"},
    "3.1": {"descricao": "Verificação de Projeto de Terceiros (ATP)",               "preco": 4000.00, "fase": "Consultoria e Verificação"},
    "3.2": {"descricao": "Acompanhamento Técnico de Obra (por visita)",             "preco": 1200.00, "fase": "Consultoria e Verificação"},
    "3.3": {"descricao": "Consultoria Técnica (por hora)",                          "preco":  350.00, "fase": "Consultoria e Verificação"},
    "4.1": {"descricao": "Laudo de Vistoria Cautelar",                              "preco": 1800.00, "fase": "Laudos e Perícias"},
    "4.2": {"descricao": "Laudo de Avaliação de Imóvel (ABNT NBR 14653)",           "preco": 2500.00, "fase": "Laudos e Perícias"},
    "4.3": {"descricao": "Laudo Técnico de Patologias",                             "preco": 2200.00, "fase": "Laudos e Perícias"},
    "4.4": {"descricao": "Laudo de Insalubridade e Periculosidade",                 "preco": 2000.00, "fase": "Laudos e Perícias"},
    "4.5": {"descricao": "Laudo de Conformidade Estrutural",                        "preco": 3000.00, "fase": "Laudos e Perícias"},
    "4.6": {"descricao": "Inspeção Predial (ABNT NBR 5674)",                        "preco": 1900.00, "fase": "Laudos e Perícias"},
    "4.7": {"descricao": "Parecer Técnico de Engenharia",                           "preco": 9500.00, "fase": "Laudos e Perícias"},
    "4.8": {"descricao": "Levantamento Planialtimétrico",                           "preco": 1700.00, "fase": "Laudos e Perícias"},
}

IMPOSTOS = {
    "ISS":    0.05,
    "PIS":    0.0065,
    "COFINS": 0.03,
    "IRPJ":   0.048,
    "CSLL":   0.0288,
}

# Normas ABNT/ABECE aplicáveis, por fase/categoria de serviço do catálogo
NORMAS_POR_FASE = {
    "Diagnóstico e Investigação": [
        "ABNT NBR 6118 (seção 5) — Projeto de estruturas de concreto",
        "ABNT NBR 7680 — Extração e ensaio de testemunhos",
        "ABNT NBR 5674 — Manutenção de edificações",
    ],
    "Projetos e Soluções": [
        "ABNT NBR 6118 — Projeto de estruturas de concreto",
        "ABNT NBR 6120 — Ações para o cálculo de estruturas",
        "ABNT NBR 6122 — Projeto e execução de fundações",
        "ABNT NBR 6123 — Forças devidas ao vento",
        "ABNT NBR 8681 — Ações e segurança nas estruturas",
        "ABNT NBR 8036 / NBR 6484 — Sondagens (quando aplicável)",
    ],
    "Consultoria e Verificação": [
        "ABECE 002:2015 — Avaliação Técnica de Projeto (ATP)",
        "ABNT NBR 6118 — Projeto de estruturas de concreto",
    ],
    "Laudos e Perícias": [
        "ABNT NBR 14653 — Avaliação de bens",
        "ABNT NBR 5674 — Manutenção de edificações",
        "ABNT NBR 15575 — Edificações habitacionais, desempenho",
    ],
}

# Exclusões e despesas padrão (editável por proposta na interface)
EXCLUSOES_PADRAO = [
    "Taxas, emolumentos e despachantes para aprovação em órgãos públicos;",
    "Sondagens, topografia e levantamentos não previstos expressamente no escopo;",
    "Projetos complementares não estruturais (elétrico, hidráulico, arquitetônico, paisagismo);",
    "Acompanhamento de obra, salvo quando contratado separadamente;",
    "Despesas de deslocamento para fora da Região Sudeste do Brasil;",
    "Alterações de escopo solicitadas após o início dos trabalhos (sujeitas a nova negociação).",
]

STATUS_OPCOES = ["Emitida", "Em Negociação", "Aprovada", "Recusada", "Cancelada"]

STATUS_CORES = {
    "Emitida":       "🔵",
    "Em Negociação": "🟡",
    "Aprovada":      "🟢",
    "Recusada":      "🔴",
    "Cancelada":     "⚫",
}

CABECALHO_PLANILHA = [
    "Nº Proposta", "Data Emissão", "Revisão", "Cliente",
    "Local do Serviço", "Objeto", "Subtotal (R$)",
    "Desconto (R$)", "Total Geral (R$)", "Banco",
    "Condição Pagamento", "Status", "Observações", "Serviços",
    "Data Registro"
]

# ─────────────────────────────────────────────
# GOOGLE SHEETS — usando st.secrets (Streamlit Cloud)
# ─────────────────────────────────────────────
@st.cache_resource
def conectar_sheets():
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        info  = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(info, scopes=scopes)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"❌ Erro ao conectar com Google Sheets: {e}")
        return None

def obter_aba(client) -> gspread.Worksheet | None:
    try:
        planilha = client.open(NOME_PLANILHA)
        try:
            aba = planilha.worksheet("Propostas")
        except gspread.WorksheetNotFound:
            aba = planilha.add_worksheet(title="Propostas", rows=1000, cols=20)
            aba.append_row(CABECALHO_PLANILHA)
            aba.format("A1:O1", {
                "backgroundColor": {"red": 0.10, "green": 0.24, "blue": 0.44},
                "textFormat": {"foregroundColor": {"red": 1, "green": 1, "blue": 1},
                               "bold": True},
                "horizontalAlignment": "CENTER"
            })
        return aba
    except Exception as e:
        st.error(f"❌ Erro ao acessar a planilha: {e}")
        return None

def salvar_proposta_sheets(client, dados: dict, subtotal: float,
                            desconto: float, total: float):
    aba = obter_aba(client)
    if not aba:
        return False
    try:
        servicos_txt = " | ".join(
            [f"{s['cod']} - {s['nome']} (x{s['qtd']})" for s in dados["servicos"]]
        )
        linha = [
            dados["numero_proposta"],
            dados["data_emissao"],
            dados.get("revisao", "Rev.00"),
            dados["cliente_nome"],
            dados["local_servico"],
            dados["objeto"],
            f"{subtotal:.2f}",
            f"{desconto:.2f}",
            f"{total:.2f}",
            dados["banco"]["banco"],
            dados.get("condicao_pagamento", ""),
            "Emitida",
            dados.get("obs_personalizada", ""),
            servicos_txt,
            datetime.now().strftime("%d/%m/%Y %H:%M"),
        ]
        aba.append_row(linha)
        return True
    except Exception as e:
        st.error(f"❌ Erro ao salvar proposta: {e}")
        return False

def listar_propostas(client) -> list[dict]:
    aba = obter_aba(client)
    if not aba:
        return []
    try:
        registros = aba.get_all_records()
        return registros
    except Exception as e:
        st.error(f"❌ Erro ao listar propostas: {e}")
        return []

def atualizar_status(client, numero_proposta: str, novo_status: str,
                      obs_extra: str = ""):
    aba = obter_aba(client)
    if not aba:
        return False
    try:
        col_proposta = CABECALHO_PLANILHA.index("Nº Proposta") + 1
        col_status   = CABECALHO_PLANILHA.index("Status") + 1
        col_obs      = CABECALHO_PLANILHA.index("Observações") + 1
        celulas      = aba.col_values(col_proposta)
        for i, val in enumerate(celulas):
            if val == numero_proposta:
                linha = i + 1
                aba.update_cell(linha, col_status, novo_status)
                if obs_extra:
                    obs_atual = aba.cell(linha, col_obs).value or ""
                    aba.update_cell(linha, col_obs,
                        f"{obs_atual}\n[{datetime.now().strftime('%d/%m/%Y %H:%M')}] {obs_extra}".strip())
                return True
        st.warning("⚠️ Proposta não encontrada na planilha.")
        return False
    except Exception as e:
        st.error(f"❌ Erro ao atualizar status: {e}")
        return False

# ─────────────────────────────────────────────
# FUNÇÕES AUXILIARES
# ─────────────────────────────────────────────
def valor_extenso(valor: float) -> str:
    reais    = int(valor)
    centavos = round((valor - reais) * 100)
    texto    = num2words(reais, lang="pt_BR").capitalize()
    if centavos:
        texto += f" reais e {num2words(centavos, lang='pt_BR')} centavos"
    else:
        texto += " reais"
    return texto

def calcular_impostos(subtotal: float) -> dict:
    resultado = {}
    for nome, aliq in IMPOSTOS.items():
        resultado[nome] = subtotal * aliq
    resultado["Total Impostos"] = sum(resultado.values())
    resultado["Total Geral"]    = subtotal + resultado["Total Impostos"]
    return resultado

def fmt_brl(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def criar_estilos():
    def E(name, **kw):
        return ParagraphStyle(name, **kw)
    return {
        "titulo":     E("Titulo",   fontSize=20, textColor=COR_BRANCO,
                         alignment=TA_CENTER, fontName="Helvetica-Bold", leading=26),
        "subtitulo":  E("Sub",      fontSize=11, textColor=COR_BRANCO,
                         alignment=TA_CENTER, fontName="Helvetica", leading=16),
        "secao":      E("Secao",    fontSize=12, textColor=COR_BRANCO,
                         fontName="Helvetica-Bold", leading=16,
                         spaceBefore=10, spaceAfter=4),
        "normal":     E("Normal",   fontSize=9,  textColor=COR_TEXTO,
                         fontName="Helvetica", leading=14,
                         spaceBefore=2, spaceAfter=2),
        "normalJ":    E("NormalJ",  fontSize=9,  textColor=COR_TEXTO,
                         fontName="Helvetica", leading=14,
                         alignment=TA_JUSTIFY, spaceBefore=2, spaceAfter=2),
        "bold":       E("Bold",     fontSize=9,  textColor=COR_TEXTO,
                         fontName="Helvetica-Bold", leading=14),
        "cabTab":     E("CabTab",   fontSize=9,  textColor=COR_BRANCO,
                         fontName="Helvetica-Bold",
                         alignment=TA_CENTER, leading=12),
        "rodape":     E("Rodape",   fontSize=7.5, textColor=colors.grey,
                         alignment=TA_CENTER, fontName="Helvetica", leading=11),
        "destaque":   E("Destaque", fontSize=10, textColor=COR_DESTAQUE,
                         fontName="Helvetica-Bold", leading=15),
        "info":       E("Info",     fontSize=8,  textColor=colors.grey,
                         fontName="Helvetica", alignment=TA_CENTER, leading=12),
        "ass":        E("Ass",      fontSize=8.5, textColor=COR_TEXTO,
                         alignment=TA_CENTER, fontName="Helvetica", leading=13),
        "desconto":   E("Desconto", fontSize=9,  textColor=colors.HexColor("#C0392B"),
                         fontName="Helvetica-Bold", leading=14),
        "obs_titulo": E("ObsTit",   fontSize=9,  textColor=COR_PRINCIPAL,
                         fontName="Helvetica-Bold", leading=14),
        "obs_corpo":  E("ObsCorp",  fontSize=9,  textColor=COR_TEXTO,
                         fontName="Helvetica", leading=14,
                         alignment=TA_JUSTIFY),
    }

# ─────────────────────────────────────────────
# RODAPÉ
# ─────────────────────────────────────────────
def rodape_paginas(canvas, doc):
    canvas.saveState()
    largura, altura = A4
    canvas.setStrokeColor(COR_SECUNDARIA)
    canvas.setLineWidth(0.8)
    canvas.line(2*cm, 1.4*cm, largura - 2*cm, 1.4*cm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.grey)
    texto_rodape = (
        f"{EMPRESA['nome']}  |  {EMPRESA['eng']}  |  {EMPRESA['crea']}  |  "
        f"{EMPRESA['email']}  |  {EMPRESA['tel']}  |  CNPJ: {EMPRESA['cnpj']}"
    )
    canvas.drawCentredString(largura / 2, 0.95*cm, texto_rodape)
    canvas.setFont("Helvetica-Bold", 7.5)
    canvas.setFillColor(COR_PRINCIPAL)
    canvas.drawCentredString(largura / 2, 0.55*cm, f"Página {doc.page}")
    canvas.restoreState()

# ─────────────────────────────────────────────
# SEÇÃO: MATERIAL TÉCNICO COMPLEMENTAR (BÔNUS)
# ─────────────────────────────────────────────
def montar_secao_bonus(story, chaves_bonus, S, cab):
    if not chaves_bonus:
        return
    story.append(cab("10. MATERIAL TÉCNICO COMPLEMENTAR (BÔNUS)"))
    story.append(Spacer(1, 0.25 * cm))
    story.append(Paragraph(
        "Como cortesia informativa, esta proposta inclui acesso ao(s) seguinte(s) material(is) "
        "técnico(s) institucional(is) do escritório. Trata-se de conteúdo educativo e orientativo, "
        "que não substitui laudo, projeto, memorial de cálculo, vistoria ou análise específica, e "
        "não amplia nem altera o escopo contratado nesta proposta.",
        S["normalJ"]))
    story.append(Spacer(1, 0.2 * cm))
    for chave in chaves_bonus:
        item = MANUAIS_BONUS.get(chave)
        if not item:
            continue
        story.append(Paragraph(f"<b>• {item['titulo']}</b>", S["obs_titulo"]))
        story.append(Paragraph(item["resumo"], S["obs_corpo"]))
        story.append(Spacer(1, 0.15 * cm))
    story.append(Spacer(1, 0.3 * cm))

# ─────────────────────────────────────────────
# SEÇÃO: DOCUMENTOS RECEBIDOS (NOVO)
# ─────────────────────────────────────────────
def montar_secao_documentos(story, docs, S, cab):
    if not docs:
        return
    story.append(cab("9. DOCUMENTOS RECEBIDOS PARA ELABORAÇÃO"))
    story.append(Spacer(1, 0.25 * cm))
    header = [[
        Paragraph("<b>Código</b>", S["cabTab"]),
        Paragraph("<b>Título/Descrição</b>", S["cabTab"]),
        Paragraph("<b>Rev.</b>", S["cabTab"]),
        Paragraph("<b>Data</b>", S["cabTab"]),
        Paragraph("<b>Formato</b>", S["cabTab"]),
        Paragraph("<b>Observação</b>", S["cabTab"]),
    ]]
    linhas = [[
        d["Código"], Paragraph(str(d["Título/Descrição"]), S["normal"]),
        d["Rev."], d["Data"], d["Formato"],
        Paragraph(str(d["Observação"]), S["normal"]),
    ] for d in docs]
    t = Table(
        header + linhas,
        colWidths=[2.2 * cm, 6.3 * cm, 1.3 * cm, 2 * cm, 1.8 * cm, 3.4 * cm]
    )
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COR_SECUNDARIA),
        ("TEXTCOLOR", (0, 0), (-1, 0), COR_BRANCO),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COR_BRANCO, COR_FUNDO_TAB]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B0BEC5")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.4 * cm))

# ─────────────────────────────────────────────
# SEÇÃO: FIGURAS / ANEXOS FOTOGRÁFICOS (estilo grid, como na proposta 092)
# ─────────────────────────────────────────────
def montar_secao_imagens(story, imagens, S, cab):
    if not imagens:
        return
    story.append(cab("REGISTRO FOTOGRÁFICO / ANEXOS"))
    story.append(Spacer(1, 0.3 * cm))

    estilo_card = TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#B0BEC5")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ])

    linhas = []
    linha_atual = []
    for i, arq in enumerate(imagens, start=1):
        try:
            img_bytes = io.BytesIO(arq.getvalue())
            img = RLImage(img_bytes, width=7.6 * cm, height=5.6 * cm, kind="proportional")
        except Exception:
            continue
        legenda = Paragraph(f"Figura {i}: {arq.name}", S["info"])
        celula = Table(
            [[img], [Spacer(1, 0.12 * cm)], [legenda]],
            colWidths=[7.8 * cm]
        )
        celula.setStyle(estilo_card)
        linha_atual.append(celula)
        if len(linha_atual) == 2:
            linhas.append(linha_atual)
            linha_atual = []
    if linha_atual:
        linha_atual.append("")
        linhas.append(linha_atual)

    if linhas:
        t_grid = Table(linhas, colWidths=[8.3 * cm, 8.3 * cm])
        t_grid.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(t_grid)
    story.append(Spacer(1, 0.4 * cm))


# ─────────────────────────────────────────────
# SEÇÃO: NORMAS TÉCNICAS APLICÁVEIS
# ─────────────────────────────────────────────
def montar_secao_normas(story, servicos, S, cab):
    if not servicos:
        return
    fases_presentes = []
    for s in servicos:
        fase = CATALOGO_SERVICOS.get(s["cod"], {}).get("fase")
        if fase and fase not in fases_presentes:
            fases_presentes.append(fase)
    normas = []
    for fase in fases_presentes:
        for n in NORMAS_POR_FASE.get(fase, []):
            if n not in normas:
                normas.append(n)
    if not normas:
        return
    story.append(cab("11. NORMAS TÉCNICAS APLICÁVEIS"))
    story.append(Spacer(1, 0.25 * cm))
    story.append(Paragraph(
        "As edições vigentes de cada norma serão confirmadas no Catálogo ABNT na data de "
        "execução do serviço. A lista abaixo é referência técnica usual para o escopo contratado:",
        S["normalJ"]))
    story.append(Spacer(1, 0.15 * cm))
    for n in normas:
        story.append(Paragraph(f"• {n}", S["normal"]))
    story.append(Spacer(1, 0.3 * cm))

# ─────────────────────────────────────────────
# SEÇÃO: EXCLUSÕES E DESPESAS NÃO INCLUÍDAS
# ─────────────────────────────────────────────
def montar_secao_exclusoes(story, exclusoes_personalizadas, S, cab):
    story.append(cab("12. EXCLUSÕES E DESPESAS NÃO INCLUÍDAS"))
    story.append(Spacer(1, 0.25 * cm))
    for item in EXCLUSOES_PADRAO:
        story.append(Paragraph(f"• {item}", S["normal"]))
    texto = (exclusoes_personalizadas or "").strip()
    if texto:
        story.append(Spacer(1, 0.1 * cm))
        story.append(Paragraph("<b>Exclusões específicas desta proposta:</b>", S["obs_titulo"]))
        for linha in texto.split("\n"):
            if linha.strip():
                story.append(Paragraph(f"• {linha.strip()}", S["obs_corpo"]))
    story.append(Spacer(1, 0.3 * cm))

# ─────────────────────────────────────────────
# SEÇÃO: PRAZO POR ETAPA
# ─────────────────────────────────────────────
def montar_secao_prazos(story, prazos, S, cab):
    if not prazos:
        return
    story.append(cab("13. PRAZO DETALHADO POR ETAPA"))
    story.append(Spacer(1, 0.25 * cm))
    header = [[
        Paragraph("<b>Etapa</b>", S["cabTab"]),
        Paragraph("<b>Prazo</b>", S["cabTab"]),
    ]]
    linhas = [[
        Paragraph(str(p.get("Etapa", "")), S["normal"]),
        Paragraph(str(p.get("Prazo", "")), S["normal"]),
    ] for p in prazos if p.get("Etapa")]
    if not linhas:
        return
    t = Table(header + linhas, colWidths=[9 * cm, 8 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COR_SECUNDARIA),
        ("TEXTCOLOR", (0, 0), (-1, 0), COR_BRANCO),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COR_BRANCO, COR_FUNDO_TAB]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B0BEC5")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.4 * cm))


# ─────────────────────────────────────────────
# GERAÇÃO DO PDF
# ─────────────────────────────────────────────
def gerar_pdf(dados: dict) -> bytes:
    buffer = io.BytesIO()
    doc = BaseDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=1.2*cm, bottomMargin=2.2*cm,
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin,
                  doc.width, doc.height, id="normal")
    template = PageTemplate(id="comRodape", frames=[frame], onPage=rodape_paginas)
    doc.addPageTemplates([template])

    S     = criar_estilos()
    story = []

    def cab(texto):
        t = Table([[Paragraph(f"  {texto}", S["secao"])]],
                  colWidths=[17*cm], rowHeights=[0.75*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), COR_PRINCIPAL),
            ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ]))
        return t

    if os.path.exists(LOGO_PATH):
        logo_cell = RLImage(LOGO_PATH, width=3.8*cm, height=2.0*cm)
    else:
        logo_cell = Paragraph(EMPRESA["nome"], S["titulo"])

    t_logo = Table([[logo_cell]], colWidths=[17*cm], rowHeights=[2.5*cm])
    t_logo.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), COR_PRINCIPAL),
        ("ALIGN",      (0,0), (-1,-1), "CENTER"),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(t_logo)
    story.append(Table([[""]], colWidths=[17*cm], rowHeights=[0.22*cm],
        style=[("BACKGROUND",(0,0),(-1,-1), COR_DESTAQUE)]))
    story.append(Spacer(1, 0.3*cm))

    t_titulo = Table([[Paragraph("PROPOSTA TECNICA COMERCIAL", S["titulo"])]],
                     colWidths=[17*cm], rowHeights=[1.0*cm])
    t_titulo.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), COR_SECUNDARIA),
        ("ALIGN",      (0,0), (-1,-1), "CENTER"),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(t_titulo)
    story.append(Spacer(1, 0.3*cm))

    revisao_txt = dados.get("revisao", "Rev.00")
    story.append(Paragraph(
        f"<b>Proposta No:</b> {dados['numero_proposta']}  &nbsp;|&nbsp; "
        f"<b>Data:</b> {dados['data_emissao']}  &nbsp;|&nbsp; "
        f"<b>Revisão:</b> {revisao_txt}  &nbsp;|&nbsp; "
        f"<b>Validade:</b> {dados.get('validade_dias', 10)} dias corridos", S["info"]))
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=0.8, color=COR_SECUNDARIA))
    story.append(Spacer(1, 0.35*cm))

    story.append(cab("1. APRESENTACAO INSTITUCIONAL"))
    story.append(Spacer(1, 0.25*cm))
    story.append(Paragraph(
        "A <b>Monteiro Projetos de Engenharia</b> atua na area de pericias, vistorias e laudos "
        "tecnicos, com registro ativo no CREA e atuacao na <b>Região Sudeste do Brasil</b>. "
        "Nossos servicos sao pautados nas normas ABNT vigentes, com rigor "
        "tecnico, imparcialidade e responsabilidade civil do engenheiro responsavel.",
        S["normalJ"]))
    story.append(Spacer(1, 0.4*cm))

    story.append(cab("2. DADOS DO CONTRATANTE"))
    story.append(Spacer(1, 0.25*cm))
    linhas_cliente = [
        [Paragraph("<b>Campo</b>", S["cabTab"]),
         Paragraph("<b>Informacao</b>", S["cabTab"])],
        ["Nome / Razao Social", dados["cliente_nome"]],
    ]
    if dados.get("cliente_doc"):     linhas_cliente.append(["CPF / CNPJ", dados["cliente_doc"]])
    if dados.get("cliente_end"):     linhas_cliente.append(["Endereco",   dados["cliente_end"]])
    if dados.get("cliente_contato"): linhas_cliente.append(["Contato",    dados["cliente_contato"]])
    if dados.get("cliente_email"):   linhas_cliente.append(["E-mail",     dados["cliente_email"]])
    t_cli = Table(linhas_cliente, colWidths=[4.5*cm, 12.5*cm])
    t_cli.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  COR_SECUNDARIA),
        ("TEXTCOLOR",     (0,0), (-1,0),  COR_BRANCO),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [COR_BRANCO, COR_FUNDO_TAB]),
        ("GRID",          (0,0), (-1,-1), 0.4, colors.HexColor("#B0BEC5")),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING",   (0,0), (-1,-1), 7),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(t_cli)
    story.append(Spacer(1, 0.4*cm))

    story.append(cab("3. ESCOPO DOS SERVICOS"))
    story.append(Spacer(1, 0.25*cm))
    story.append(Paragraph(f"<b>Local do Servico:</b> {dados['local_servico']}", S["normal"]))
    story.append(Paragraph(f"<b>Objeto:</b> {dados['objeto']}", S["normal"]))
    story.append(Spacer(1, 0.25*cm))
    t_serv_header = [[
        Paragraph("<b>Cod.</b>",       S["cabTab"]),
        Paragraph("<b>Servico</b>",    S["cabTab"]),
        Paragraph("<b>Qtd.</b>",       S["cabTab"]),
        Paragraph("<b>Unit. (R$)</b>", S["cabTab"]),
        Paragraph("<b>Total (R$)</b>", S["cabTab"]),
    ]]
    subtotal = 0.0
    t_serv_rows = []
    for s in dados["servicos"]:
        total_item = s["qtd"] * s["valor"]
        subtotal  += total_item
        t_serv_rows.append([
            s["cod"],
            Paragraph(s["nome"], S["normal"]),
            str(s["qtd"]),
            fmt_brl(s["valor"]),
            fmt_brl(total_item),
        ])
    t_serv = Table(t_serv_header + t_serv_rows,
                   colWidths=[1.2*cm, 8.8*cm, 1.5*cm, 2.8*cm, 2.7*cm])
    t_serv.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  COR_SECUNDARIA),
        ("TEXTCOLOR",     (0,0), (-1,0),  COR_BRANCO),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [COR_BRANCO, COR_FUNDO_TAB]),
        ("GRID",          (0,0), (-1,-1), 0.4, colors.HexColor("#B0BEC5")),
        ("ALIGN",         (0,0), (0,-1),  "CENTER"),
        ("ALIGN",         (2,0), (-1,-1), "CENTER"),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING",   (0,0), (-1,-1), 5),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(t_serv)
    story.append(Spacer(1, 0.4*cm))

    # NOVO: Figuras/Fotos anexadas (estilo grid, logo após o escopo — igual à proposta 092)
    montar_secao_imagens(story, dados.get("imagens_anexas", []), S, cab)

    # Documentos Recebidos (apenas arquivos não-imagem: PDF, DWG, etc.)
    montar_secao_documentos(story, dados.get("documentos_recebidos", []), S, cab)

    # Material técnico complementar (bônus) — opcional
    montar_secao_bonus(story, dados.get("bonus_manuais", []), S, cab)

    # Normas técnicas aplicáveis, conforme os serviços selecionados
    montar_secao_normas(story, dados.get("servicos", []), S, cab)

    # Exclusões e despesas não incluídas
    montar_secao_exclusoes(story, dados.get("exclusoes_personalizadas", ""), S, cab)

    # Prazo detalhado por etapa
    montar_secao_prazos(story, dados.get("prazos_etapas", []), S, cab)

    story.append(cab("4. METODOLOGIA DE TRABALHO"))
    story.append(Spacer(1, 0.25*cm))
    for titulo_met, descricao_met in [
        ("FASE DE CAMPO", "Visita tecnica ao local para coleta de dados, registro fotografico e medicoes in loco."),
        ("FASE DE LABORATORIO / ESCRITORIO", "Processamento das informacoes coletadas, analise tecnica e elaboracao dos documentos."),
        ("FASE DE ENTREGA", "Emissao do laudo/projeto em formato PDF e, se necessario, reuniao de apresentacao dos resultados."),
        ("ACOMPANHAMENTO POS-ENTREGA", "Suporte tecnico por 30 dias apos a entrega para esclarecimento de duvidas sobre o documento emitido."),
    ]:
        story.append(Paragraph(f"<b>{titulo_met}:</b> {descricao_met}", S["normal"]))
        story.append(Spacer(1, 0.15*cm))
    story.append(Spacer(1, 0.25*cm))

    story.append(cab("5. RESUMO FINANCEIRO"))
    story.append(Spacer(1, 0.25*cm))
    desconto_valor        = dados.get("desconto_valor", 0.0)
    subtotal_com_desconto = subtotal - desconto_valor
    imp = calcular_impostos(subtotal_com_desconto)
    linhas_fin = [
        [Paragraph("<b>Descricao</b>", S["cabTab"]),
         Paragraph("<b>Valor</b>",     S["cabTab"])],
        ["Subtotal dos Servicos", fmt_brl(subtotal)],
    ]
    if desconto_valor > 0:
        desconto_pct_pdf = (desconto_valor / subtotal * 100) if subtotal > 0 else 0
        linhas_fin.append([
            Paragraph(f"<b>Desconto Negociado ({desconto_pct_pdf:.1f}%)</b>", S["desconto"]),
            Paragraph(f"<b>- {fmt_brl(desconto_valor)}</b>",                  S["desconto"]),
        ])
        linhas_fin.append(["Subtotal com Desconto", fmt_brl(subtotal_com_desconto)])
    linhas_fin += [
        ["ISS (5,00%)",    fmt_brl(imp["ISS"])],
        ["PIS (0,65%)",    fmt_brl(imp["PIS"])],
        ["COFINS (3,00%)", fmt_brl(imp["COFINS"])],
        ["IRPJ (4,80%)",   fmt_brl(imp["IRPJ"])],
        ["CSLL (2,88%)",   fmt_brl(imp["CSLL"])],
        [Paragraph("<b>TOTAL GERAL</b>", S["bold"]),
         Paragraph(f"<b>{fmt_brl(imp['Total Geral'])}</b>", S["bold"])],
    ]
    t_fin = Table(linhas_fin, colWidths=[10*cm, 7*cm])
    t_fin.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),  (-1,0),  COR_SECUNDARIA),
        ("TEXTCOLOR",     (0,0),  (-1,0),  COR_BRANCO),
        ("FONTSIZE",      (0,0),  (-1,-1), 9),
        ("ROWBACKGROUNDS",(0,1),  (-1,-2), [COR_BRANCO, COR_FUNDO_TAB]),
        ("BACKGROUND",    (0,-1), (-1,-1), COR_DESTAQUE),
        ("TEXTCOLOR",     (0,-1), (-1,-1), COR_BRANCO),
        ("GRID",          (0,0),  (-1,-1), 0.4, colors.HexColor("#B0BEC5")),
        ("ALIGN",         (1,0),  (1,-1),  "CENTER"),
        ("VALIGN",        (0,0),  (-1,-1), "MIDDLE"),
        ("LEFTPADDING",   (0,0),  (-1,-1), 7),
        ("TOPPADDING",    (0,0),  (-1,-1), 4),
        ("BOTTOMPADDING", (0,0),  (-1,-1), 4),
    ]))
    story.append(t_fin)
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        f"<b>Valor por extenso:</b> {valor_extenso(imp['Total Geral'])}", S["normal"]))
    story.append(Spacer(1, 0.4*cm))

    story.append(cab("6. CONDICOES DE PAGAMENTO"))
    story.append(Spacer(1, 0.25*cm))
    cond = dados.get("condicao_pagamento", "50% na assinatura do contrato e 50% na entrega.")
    story.append(Paragraph(f"<b>Condicao:</b> {cond}", S["normal"]))
    story.append(Spacer(1, 0.25*cm))
    banco_info   = dados["banco"]
    linhas_banco = [
        [Paragraph("<b>Dados Bancarios</b>", S["cabTab"]),
         Paragraph("<b>Informacao</b>",      S["cabTab"])],
        ["Favorecido", banco_info["favorecido"]],
        ["Banco",      banco_info["banco"]],
        ["Agencia",    banco_info["agencia"]],
        ["Conta",      banco_info["conta"]],
        ["Tipo",       banco_info["tipo"]],
        ["Chave PIX",  banco_info["pix"]],
    ]
    t_banco = Table(linhas_banco, colWidths=[4.5*cm, 12.5*cm])
    t_banco.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  COR_PRINCIPAL),
        ("TEXTCOLOR",     (0,0), (-1,0),  COR_BRANCO),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [COR_BRANCO, COR_FUNDO_TAB]),
        ("GRID",          (0,0), (-1,-1), 0.4, colors.HexColor("#B0BEC5")),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING",   (0,0), (-1,-1), 7),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(t_banco)
    story.append(Spacer(1, 0.4*cm))

    story.append(cab("7. OBSERVACOES GERAIS"))
    story.append(Spacer(1, 0.25*cm))
    for obs in [
        f"Esta proposta tem validade de {dados.get('validade_dias', 10)} dias corridos a partir da data de emissao.",
        "Os valores nao incluem despesas de deslocamento para municipios fora da Regiao Sudeste do Brasil.",
        "O prazo de entrega sera definido em contrato apos aprovacao desta proposta.",
        "Os laudos e relatorios serao emitidos em conformidade com as normas ABNT vigentes.",
        "A ART (Anotacao de Responsabilidade Tecnica) esta inclusa no valor proposto.",
    ]:
        story.append(Paragraph(f"• {obs}", S["normal"]))
        story.append(Spacer(1, 0.1*cm))
    obs_personalizada = dados.get("obs_personalizada", "").strip()
    if obs_personalizada:
        story.append(Spacer(1, 0.15*cm))
        story.append(Paragraph("<b>Observações Específicas desta Proposta:</b>", S["obs_titulo"]))
        story.append(Spacer(1, 0.1*cm))
        for linha in obs_personalizada.split("\n"):
            if linha.strip():
                story.append(Paragraph(f"• {linha.strip()}", S["obs_corpo"]))
                story.append(Spacer(1, 0.08*cm))
    story.append(Spacer(1, 0.3*cm))

    story.append(cab("8. ACEITE DA PROPOSTA"))
    story.append(Spacer(1, 0.25*cm))
    story.append(Paragraph(
        f"Declaro que li e aceito os termos desta proposta — "
        f"<b>Proposta Nº {dados['numero_proposta']} / {revisao_txt}</b>.", S["normal"]))
    story.append(Spacer(1, 0.6*cm))
    t_aceite = Table([[
        Paragraph("_______________________________<br/><b>Contratante</b><br/>Data: ___/___/______", S["ass"]),
        Paragraph(f"_______________________________<br/><b>{EMPRESA['eng']}</b><br/>{EMPRESA['crea']}", S["ass"]),
    ]], colWidths=[8.5*cm, 8.5*cm])
    t_aceite.setStyle(TableStyle([
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0), (-1,-1), 12),
        ("BOTTOMPADDING", (0,0), (-1,-1), 12),
    ]))
    story.append(t_aceite)

    doc.build(story)
    return buffer.getvalue()


# ─────────────────────────────────────────────
# TELA: GESTÃO DE PROPOSTAS
# ─────────────────────────────────────────────
def tela_gestao(client):
    st.header("📊 Gestão de Propostas")
    propostas = listar_propostas(client)

    if not propostas:
        st.info("📭 Nenhuma proposta registrada ainda.")
        return

    st.subheader("🔍 Filtros")
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        filtro_status = st.multiselect(
            "Status", options=STATUS_OPCOES, default=STATUS_OPCOES)
    with fc2:
        filtro_cliente = st.text_input("Buscar por cliente")
    with fc3:
        filtro_numero = st.text_input("Buscar por Nº Proposta")

    filtradas = [
        p for p in propostas
        if p.get("Status", "") in filtro_status
        and filtro_cliente.lower() in p.get("Cliente", "").lower()
        and filtro_numero.lower() in p.get("Nº Proposta", "").lower()
    ]

    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    total_geral = sum(
        float(str(p.get("Total Geral (R$)", "0")).replace(",", "."))
        for p in filtradas
    )
    aprovadas = sum(1 for p in filtradas if p.get("Status") == "Aprovada")
    em_neg    = sum(1 for p in filtradas if p.get("Status") == "Em Negociação")

    m1.metric("📋 Total Filtrado",      len(filtradas))
    m2.metric("✅ Aprovadas",            aprovadas)
    m3.metric("🟡 Em Negociação",        em_neg)
    m4.metric("💰 Volume (Total Geral)", fmt_brl(total_geral))

    st.divider()

    for idx, p in enumerate(filtradas):
        status  = p.get("Status", "Emitida")
        icone   = STATUS_CORES.get(status, "⚪")
        num     = p.get("Nº Proposta", "—")
        cliente = p.get("Cliente", "—")
        total   = p.get("Total Geral (R$)", "0")
        data    = p.get("Data Emissão", "—")
        revisao = p.get("Revisão", "—")

        key_base = f"{idx}_{str(num).replace('/', '-')}"

        with st.expander(f"{icone} {num} | {cliente} | {fmt_brl(float(str(total).replace(',', '.')))} | {status}"):
            d1, d2 = st.columns(2)
            with d1:
                st.markdown(f"**📅 Data:** {data}  |  **🔄 Revisão:** {revisao}")
                st.markdown(f"**📍 Local:** {p.get('Local do Serviço', '—')}")
                st.markdown(f"**📌 Objeto:** {p.get('Objeto', '—')}")
                st.markdown(f"**💳 Banco:** {p.get('Banco', '—')}")
                st.markdown(f"**💼 Pagamento:** {p.get('Condição Pagamento', '—')}")
            with d2:
                st.markdown(f"**🔧 Serviços:** {p.get('Serviços', '—')}")
                st.markdown(f"**📝 Obs:** {p.get('Observações', '—') or '—'}")
                st.markdown(f"**🕐 Registrado em:** {p.get('Data Registro', '—')}")

            st.divider()
            st.markdown("**🔄 Atualizar Status desta Proposta:**")
            nc1, nc2, nc3 = st.columns([2, 2, 1])
            with nc1:
                novo_status = st.selectbox(
                    "Novo Status", options=STATUS_OPCOES,
                    index=STATUS_OPCOES.index(status) if status in STATUS_OPCOES else 0,
                    key=f"status_{key_base}"
                )
            with nc2:
                obs_upd = st.text_input(
                    "Observação (opcional)", key=f"obs_upd_{key_base}",
                    placeholder="Ex: Cliente solicitou desconto adicional"
                )
            with nc3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("💾 Salvar", key=f"btn_{key_base}"):
                    if atualizar_status(client, num, novo_status, obs_upd):
                        st.success(f"✅ Status atualizado para **{novo_status}**!")
                        st.rerun()


# ─────────────────────────────────────────────
# INTERFACE STREAMLIT — MAIN
# ─────────────────────────────────────────────
def main():
    st.set_page_config(
        page_title="Monteiro Engenharia — Propostas",
        page_icon="📋",
        layout="wide"
    )

    st.markdown("""
        <style>
        .main { background-color: #f0f4f8; }
        h1, h2, h3 { color: #1A3E6F; }
        .stNumberInput input { background-color: #fffbea; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

    client = conectar_sheets()

    aba_prop, aba_gest = st.tabs(["📄 Nova Proposta", "📊 Gestão de Propostas"])

    with aba_prop:
        st.title("📋 Gerador de Proposta Tecnica")
        st.markdown("**Monteiro Projetos de Engenharia** — Sistema de Emissao de Propostas")
        st.divider()

        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("📌 Dados da Proposta")
            numero_proposta = st.text_input("Numero da Proposta", value="001/2026")
            data_emissao    = st.date_input("Data de Emissao", value=date.today())
            revisao = st.selectbox(
                "Revisão da Proposta",
                options=["Rev.00", "Rev.01", "Rev.02", "Rev.03", "Rev.04", "Rev.05"],
                index=0
            )
            local_servico = st.text_input("Local do Servico",
                                placeholder="Ex: Rua das Flores, 100 — Salto/SP")
            objeto = st.text_area("Objeto do Servico", height=80,
                                placeholder="Ex: Inspecao predial e laudo tecnico de patologias")
            validade_dias = st.number_input(
                "Validade da Proposta (dias corridos)",
                min_value=1, value=10, step=1
            )

            st.subheader("⏱️ Prazo Detalhado por Etapa")
            usar_prazos = st.toggle("Detalhar prazo por etapa nesta proposta", value=False)
            prazos_tabela = []
            if usar_prazos:
                df_prazos = pd.DataFrame([
                    {"Etapa": "Fase de campo / vistoria", "Prazo": "5 dias após liberação"},
                    {"Etapa": "Emissão do laudo/projeto", "Prazo": "15 dias após a fase de campo"},
                ])
                df_prazos_editado = st.data_editor(
                    df_prazos, num_rows="dynamic", use_container_width=True,
                    key="editor_prazos"
                )
                prazos_tabela = df_prazos_editado.to_dict("records")

            st.subheader("🚫 Exclusões Específicas desta Proposta")
            exclusoes_personalizadas = st.text_area(
                "Exclusões adicionais (opcional — some às exclusões padrão)", height=80,
                placeholder="Ex: Não inclui prova de carga em estacas."
            )

            st.subheader("👤 Dados do Contratante")
            cliente_nome    = st.text_input("Nome / Razao Social *")
            cliente_doc     = st.text_input("CPF / CNPJ (opcional)")
            cliente_end     = st.text_input("Endereco")
            cliente_contato = st.text_input("Telefone / WhatsApp")
            cliente_email   = st.text_input("E-mail")

            st.subheader("💰 Desconto Negociado")
            usar_desconto = st.toggle("Aplicar desconto nesta proposta", value=False)
            desconto_pct   = 0.0
            desconto_reais = 0.0
            tipo_desconto  = "Percentual (%)"
            if usar_desconto:
                tipo_desconto = st.radio(
                    "Tipo de desconto",
                    options=["Percentual (%)", "Valor fixo (R$)"],
                    horizontal=True
                )
                if tipo_desconto == "Percentual (%)":
                    desconto_pct = st.slider(
                        "Percentual de desconto",
                        min_value=0.0, max_value=50.0,
                        value=5.0, step=0.5, format="%.1f%%"
                    )
                else:
                    desconto_reais = st.number_input(
                        "Valor do desconto (R$)",
                        min_value=0.0, value=0.0,
                        step=100.0, format="%.2f"
                    )

            st.subheader("📝 Observação Personalizada")
            obs_personalizada = st.text_area(
                "Observações específicas (opcional)", height=100,
                placeholder="Ex: O acesso ao local será fornecido pelo contratante."
            )

            st.subheader("🎁 Material Técnico Complementar (Bônus)")
            bonus_atp = st.checkbox(
                "Incluir resumo do Manual de Avaliação Técnica de Projetos (ATP)",
                value=False
            )
            bonus_estrutural = st.checkbox(
                "Incluir resumo do Manual Técnico — Projeto Estrutural",
                value=False
            )
            bonus_manuais = []
            if bonus_atp:
                bonus_manuais.append("atp")
            if bonus_estrutural:
                bonus_manuais.append("estrutural")

            # NOVO: Documentos Recebidos do Cliente
            st.subheader("📎 Documentos Recebidos do Cliente")
            docs_upload = st.file_uploader(
                "Anexe os arquivos recebidos (PDF, DWG, IFC, imagens...)",
                accept_multiple_files=True,
                key="docs_recebidos"
            )

            docs_tabela = []
            imagens_anexas = []
            if docs_upload:
                EXT_IMG = ("png", "jpg", "jpeg")
                imagens_anexas = [
                    arq for arq in docs_upload
                    if arq.name.split(".")[-1].lower() in EXT_IMG
                ]
                docs_nao_imagem = [
                    arq for arq in docs_upload
                    if arq.name.split(".")[-1].lower() not in EXT_IMG
                ]
                if docs_nao_imagem:
                    linhas_default = [{
                        "Código": "",
                        "Título/Descrição": arq.name,
                        "Rev.": "R00",
                        "Data": "",
                        "Formato": arq.name.split(".")[-1].upper(),
                        "Observação": "",
                    } for arq in docs_nao_imagem]
                    df_docs = pd.DataFrame(linhas_default)
                    df_docs_editado = st.data_editor(
                        df_docs, num_rows="fixed", use_container_width=True,
                        key="editor_docs"
                    )
                    docs_tabela = df_docs_editado.to_dict("records")
                if imagens_anexas:
                    st.success(f"📷 {len(imagens_anexas)} imagem(ns) serão anexadas como figuras na proposta.")

        with col2:
            st.subheader("🔧 Selecao de Servicos")
            fases = {}
            for cod, item in CATALOGO_SERVICOS.items():
                fase = item["fase"]
                if fase not in fases:
                    fases[fase] = []
                fases[fase].append((cod, item))

            servicos_selecionados = []
            for fase, itens in fases.items():
                with st.expander(f"📂 {fase}", expanded=False):
                    h1, h2, h3, h4 = st.columns([0.4, 3.2, 1.0, 1.4])
                    h1.markdown("**✔**")
                    h2.markdown("**Serviço**")
                    h3.markdown("**Qtd**")
                    h4.markdown("**Valor (R$)**")
                    st.divider()
                    for cod, item in itens:
                        c1, c2, c3, c4 = st.columns([0.4, 3.2, 1.0, 1.4])
                        with c1:
                            sel = st.checkbox(" ", key=f"chk_{cod}", label_visibility="hidden")
                        with c2:
                            st.markdown(f"`{cod}` {item['descricao']}")
                        with c3:
                            qtd = st.number_input(
                                "Qtd", min_value=1, value=1, step=1,
                                key=f"qtd_{cod}", label_visibility="hidden",
                                disabled=not sel,
                            )
                        with c4:
                            valor_final = st.number_input(
                                "Valor", min_value=0.0,
                                value=float(item["preco"]),
                                step=50.0, format="%.2f",
                                key=f"val_{cod}", label_visibility="hidden",
                                disabled=not sel,
                                help=f"💡 Valor sugerido: {fmt_brl(item['preco'])}",
                            )
                        if sel:
                            servicos_selecionados.append({
                                "cod":   cod,
                                "nome":  item["descricao"],
                                "valor": valor_final,
                                "qtd":   qtd,
                            })

            st.subheader("💳 Dados Bancarios")
            banco_opcao = st.selectbox(
                "Conta para recebimento", options=list(BANCOS.keys()), index=0)

            st.subheader("📋 Condicoes de Pagamento")
            condicao_pagamento = st.selectbox(
                "Forma de pagamento",
                options=[
                    "50% na assinatura do contrato e 50% na entrega.",
                    "100% no ato da assinatura do contrato.",
                    "30% na assinatura, 70% na entrega.",
                    "Parcelado em 3x sem juros.",
                ]
            )

        st.divider()

        if servicos_selecionados:
            subtotal = sum(s["qtd"] * s["valor"] for s in servicos_selecionados)

            if usar_desconto:
                if tipo_desconto == "Percentual (%)":
                    desconto_preview = subtotal * (desconto_pct / 100)
                else:
                    desconto_preview = desconto_reais
                desconto_preview = min(desconto_preview, subtotal)
            else:
                desconto_preview = 0.0

            subtotal_desc = subtotal - desconto_preview
            imp = calcular_impostos(subtotal_desc)

            cols_prev = st.columns(4)
            cols_prev[0].metric("Subtotal",    fmt_brl(subtotal))
            cols_prev[1].metric("Desconto",    f"- {fmt_brl(desconto_preview)}")
            cols_prev[2].metric("Impostos",    fmt_brl(imp["Total Impostos"]))
            cols_prev[3].metric("TOTAL GERAL", fmt_brl(imp["Total Geral"]))
        else:
            st.warning("⚠️ Nenhum serviço selecionado.")

        col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 2])
        with col_btn2:
            gerar = st.button("📄 GERAR PDF", type="primary", use_container_width=True)

        if gerar:
            if not cliente_nome:
                st.error("❌ Informe o nome do contratante.")
            elif not servicos_selecionados:
                st.error("❌ Selecione ao menos um serviço.")
            else:
                subtotal_bruto = sum(s["qtd"] * s["valor"] for s in servicos_selecionados)

                if usar_desconto:
                    if tipo_desconto == "Percentual (%)":
                        desconto_final = subtotal_bruto * (desconto_pct / 100)
                    else:
                        desconto_final = desconto_reais
                    desconto_final = min(desconto_final, subtotal_bruto)
                else:
                    desconto_final = 0.0

                subtotal_liquido = subtotal_bruto - desconto_final
                imp_calc = calcular_impostos(subtotal_liquido)

                dados = {
                    "numero_proposta":      numero_proposta,
                    "data_emissao":         data_emissao.strftime("%d/%m/%Y"),
                    "revisao":              revisao,
                    "local_servico":        local_servico,
                    "objeto":               objeto,
                    "cliente_nome":         cliente_nome,
                    "cliente_doc":          cliente_doc,
                    "cliente_end":          cliente_end,
                    "cliente_contato":      cliente_contato,
                    "cliente_email":        cliente_email,
                    "servicos":             servicos_selecionados,
                    "banco":                BANCOS[banco_opcao],
                    "condicao_pagamento":   condicao_pagamento,
                    "desconto_valor":       desconto_final,
                    "obs_personalizada":    obs_personalizada,
                    "documentos_recebidos": docs_tabela,
                    "imagens_anexas":       imagens_anexas,
                    "validade_dias":        validade_dias,
                    "bonus_manuais":        bonus_manuais,
                    "prazos_etapas":        prazos_tabela,
                    "exclusoes_personalizadas": exclusoes_personalizadas,
                }

                with st.spinner("Gerando PDF..."):
                    pdf_bytes = gerar_pdf(dados)

                if client:
                    with st.spinner("Salvando no Google Sheets..."):
                        salvo = salvar_proposta_sheets(
                            client,
                            dados,
                            subtotal_bruto,
                            desconto_final,
                            imp_calc["Total Geral"]
                        )
                    if salvo:
                        st.success("✅ Proposta salva no Google Sheets!")
                    else:
                        st.error("❌ Falha ao salvar no Google Sheets. Veja o erro acima.")
                else:
                    st.warning("⚠️ Google Sheets não conectado — proposta não foi salva.")

                nome_arquivo = (
                    f"Proposta_{numero_proposta.replace('/', '-')}_"
                    f"{revisao}_{cliente_nome.replace(' ', '_')[:20]}.pdf"
                )
                st.success("✅ PDF gerado com sucesso!")
                st.download_button(
                    label="⬇️ BAIXAR PROPOSTA PDF",
                    data=pdf_bytes,
                    file_name=nome_arquivo,
                    mime="application/pdf",
                    use_container_width=True,
                )

    with aba_gest:
        if client:
            tela_gestao(client)
        else:
            st.error("❌ Não foi possível conectar ao Google Sheets. Verifique as Secrets.")


if __name__ == "__main__":
    main()
