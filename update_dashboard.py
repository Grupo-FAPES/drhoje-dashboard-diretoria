import os
import requests
import pandas as pd
import json
from datetime import datetime

# 1. Definições de Acesso e Credenciais
BASE_URL = "http://drhoje.salustech.com.br:8082"
LOGIN_URL = f"{BASE_URL}/sgc/logar.jsp"
DATA_URL = f"{BASE_URL}/sgc/carregarJson/carregarGenerico.jsp"

credentials = {
    "usuario": os.environ.get("SALUSTECH_USER", "BI"),
    "senha": os.environ.get("SALUSTECH_PASS", "drhoje123456"),
    "cd_empresa": os.environ.get("SALUSTECH_COMPANY", "DRHOJE")
}

print("Iniciando login no Salustech...")
session = requests.Session()
login_response = session.post(LOGIN_URL, data=credentials)
print("Status do Login:", login_response.status_code)

params = {
    "search": "",
    "order": "asc",
    "tabela": "VW_REL_CONTRATO_ANALITICO",
    "campo": "tipo_contrato,tipo_plano,nm_convenio,nm_plano,codplano,grupo_contratual,tipo_descricao,nm_entidade,no_proposta,nome,cpf_contratante,email_contratante,telefone_contratante,id_ben,nome_segurado,total_geral,matricula,sexo_segurado,dtativacao,mae_segurado,tipo_cliente,descr_parentesco,cpf_segurado,carteirinha,dtnasc_segurado,idade,faixa_preco_ans,tipo_segurado,status_proposta_desc,qtdsegurado,dtacao,descr_status,dtcadastro,dtpedido,dtvigencia_benef,mes_ano_inclusao,dtinativacao,mes_ano_inativacao,reajuste_por_contrato,motivo_exclusao,descr_motivo_exclusao,reprlegal_nome,reprlegal_cpf,cep,endereco,endnum,complemento,bairro,cidade,uf,email_segurado,telefone_segurado,regional,supervisor,corretora",
    "condicao": "1 = 1"
}

# Fetch data with retry mechanism
max_retries = 3
df_contratos = None
for i in range(max_retries):
    try:
        print(f"Tentando buscar registros (tentativa {i+1})...")
        response = session.get(DATA_URL, params=params, timeout=120)
        if response.status_code == 200:
            data_json = response.json()
            df_contratos = pd.DataFrame(data_json)
            print(f"Sucesso! {len(df_contratos)} registros recuperados.")
            break
    except Exception as e:
        print(f"Erro na tentativa {i+1}: {e}")
        if i == max_retries - 1:
            raise e

if df_contratos is None or len(df_contratos) == 0:
    print("Nenhum dado recuperado. Encerrando.")
    exit(1)

# Clean up encoding issues in key columns
if 'tipo_contrato' in df_contratos.columns:
    df_contratos['tipo_contrato'] = df_contratos['tipo_contrato'].astype(str).str.upper()
    df_contratos['tipo_contrato'] = df_contratos['tipo_contrato'].apply(lambda x: 'ADESÃO' if 'ADE' in x else x)

if 'tipo_descricao' in df_contratos.columns:
    df_contratos['tipo_descricao'] = df_contratos['tipo_descricao'].astype(str).str.upper()
    df_contratos['tipo_descricao'] = df_contratos['tipo_descricao'].str.replace('SADE', 'SAÚDE').str.replace('BENEFCIOS', 'BENEFÍCIOS')

if 'motivo_exclusao' in df_contratos.columns:
    df_contratos['motivo_exclusao'] = df_contratos['motivo_exclusao'].astype(str).str.upper()
    df_contratos['motivo_exclusao'] = df_contratos['motivo_exclusao'].str.replace('SOLICITAO', 'SOLICITAÇÃO').str.replace('CONTRATAO', 'CONTRATAÇÃO')

if 'total_geral' in df_contratos.columns:
    df_contratos['total_geral'] = pd.to_numeric(df_contratos['total_geral'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0.0)

# Save raw data to CSV locally for backup/audit
df_contratos.to_csv("contratos_analitico.csv", index=False, encoding="utf-8-sig")

# --- DATA MANIPULATION & CALCULATIONS ---
today = datetime.now()
current_month = today.month
current_year = today.year

month_names_pt = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho", 
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
]
month_abbr_pt = [
    "Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"
]
month_abbr_caps = [
    "JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"
]

months_keys = []
labels_pivot = []
labels_abbr = []
labels_evo = []

for m in range(1, current_month + 1):
    month_str = f"{m:02d}/2026"
    months_keys.append(month_str)
    labels_pivot.append(f"{month_names_pt[m-1]}-26")
    labels_abbr.append(month_abbr_caps[m-1])
    if m == current_month:
        labels_evo.append(f"{month_abbr_caps[m-1]}/26 (até {today.strftime('%d/%m')})")
    else:
        labels_evo.append(f"{month_abbr_caps[m-1]}/26")

active_df = df_contratos[df_contratos['descr_status'].astype(str).str.upper() == 'ATIVO']
vidas_ativas = len(active_df)
empresarial = len(active_df[active_df['tipo_contrato'] == 'EMPRESARIAL'])
adesao = len(active_df[active_df['tipo_contrato'] == 'ADESÃO'])
empresarial_pct = round((empresarial / vidas_ativas) * 100, 1) if vidas_ativas > 0 else 0.0
adesao_pct = round((adesao / vidas_ativas) * 100, 1) if vidas_ativas > 0 else 0.0

# Current period (last two months, e.g. June + July 2026)
current_period_keys = [months_keys[-2], months_keys[-1]] if len(months_keys) >= 2 else [months_keys[-1]]
current_period_inclusions = df_contratos[df_contratos['mes_ano_inclusao'].isin(current_period_keys)]
inclusoes_junho = len(current_period_inclusions)

obs_period_name = f"{month_names_pt[len(months_keys)-2].capitalize()}+{month_names_pt[len(months_keys)-1].capitalize()}" if len(months_keys) >= 2 else month_names_pt[len(months_keys)-1].capitalize()
inclusoes_junho_obs = f"{obs_period_name}/2026 (até {today.strftime('%d/%m')})"

# Inclusoes por dia no periodo
daily_df = current_period_inclusions.copy()
daily_df['date_parsed'] = pd.to_datetime(daily_df['dtvigencia_benef'], format='%d/%m/%Y', errors='coerce')
daily_df = daily_df.dropna(subset=['date_parsed'])
daily_grouped = daily_df.groupby('date_parsed').size().reset_index(name='valor')
daily_grouped = daily_grouped.sort_values('date_parsed')
daily_grouped['dia'] = daily_grouped['date_parsed'].dt.strftime('%d/%m')
inclusoes_por_dia_junho = daily_grouped[['dia', 'valor']].to_dict('records')

# Inclusões por mês / tipo
inc_2026 = df_contratos[df_contratos['mes_ano_inclusao'].isin(months_keys)]
adesao_list = []
empresarial_list = []
total_list = []
for m_key in months_keys:
    m_df = inc_2026[inc_2026['mes_ano_inclusao'] == m_key]
    ad_count = len(m_df[m_df['tipo_contrato'] == 'ADESÃO'])
    emp_count = len(m_df[m_df['tipo_contrato'] == 'EMPRESARIAL'])
    adesao_list.append(ad_count)
    empresarial_list.append(emp_count)
    total_list.append(ad_count + emp_count)

inclusoes_por_mes_tipo = {
    "meses": labels_pivot,
    "adesao": adesao_list,
    "adesao_total": sum(adesao_list),
    "empresarial": empresarial_list,
    "empresarial_total": sum(empresarial_list),
    "total": total_list,
    "total_geral": sum(total_list)
}

# Valores de inclusões por mês / tipo
adesao_val_list = []
empresarial_val_list = []
total_val_list = []
for m_key in months_keys:
    m_df = inc_2026[inc_2026['mes_ano_inclusao'] == m_key]
    ad_val = float(m_df[m_df['tipo_contrato'] == 'ADESÃO']['total_geral'].sum())
    emp_val = float(m_df[m_df['tipo_contrato'] == 'EMPRESARIAL']['total_geral'].sum())
    adesao_val_list.append(round(ad_val, 1))
    empresarial_val_list.append(round(emp_val, 1))
    total_val_list.append(round(ad_val + emp_val, 1))

valores_inclusoes_por_mes_tipo = {
    "meses": labels_pivot,
    "adesao": adesao_val_list,
    "adesao_total": round(sum(adesao_val_list), 1),
    "empresarial": empresarial_val_list,
    "empresarial_total": round(sum(empresarial_val_list), 1),
    "total": total_val_list,
    "total_geral": round(sum(total_val_list), 1)
}

# Vendas adesão por produto
adesao_2026 = inc_2026[inc_2026['tipo_contrato'] == 'ADESÃO'].copy()
adesao_2026['tipo_descricao'] = adesao_2026['tipo_descricao'].fillna('Outros')
top_products = adesao_2026['tipo_descricao'].value_counts().index.tolist()
products_data = []
for prod in top_products:
    prod_df = adesao_2026[adesao_2026['tipo_descricao'] == prod]
    monthly_vals = []
    for m_key in months_keys:
        monthly_vals.append(len(prod_df[prod_df['mes_ano_inclusao'] == m_key]))
    products_data.append({
        "produto": prod,
        "valores": monthly_vals,
        "total": sum(monthly_vals)
    })
products_data = sorted(products_data, key=lambda x: x['total'], reverse=True)

vendas_adesao_por_produto = {
    "meses": labels_abbr,
    "produtos": products_data,
    "total": adesao_list,
    "total_geral": sum(adesao_list)
}

# Ranking vendas
ranking_vendas = []
total_adesao_lives = sum(adesao_list)
if len(products_data) > 2:
    ranking_vendas.append({
        "posicao": 1,
        "produto": products_data[0]['produto'],
        "vidas": products_data[0]['total'],
        "pct": round((products_data[0]['total'] / total_adesao_lives) * 100, 1) if total_adesao_lives > 0 else 0.0
    })
    ranking_vendas.append({
        "posicao": 2,
        "produto": products_data[1]['produto'],
        "vidas": products_data[1]['total'],
        "pct": round((products_data[1]['total'] / total_adesao_lives) * 100, 1) if total_adesao_lives > 0 else 0.0
    })
    others_total = sum(p['total'] for p in products_data[2:])
    ranking_vendas.append({
        "posicao": 3,
        "produto": "Demais produtos",
        "vidas": others_total,
        "pct": round((others_total / total_adesao_lives) * 100, 1) if total_adesao_lives > 0 else 0.0
    })
else:
    for idx, p in enumerate(products_data):
        ranking_vendas.append({
            "posicao": idx + 1,
            "produto": p['produto'],
            "vidas": p['total'],
            "pct": round((p['total'] / total_adesao_lives) * 100, 1) if total_adesao_lives > 0 else 0.0
        })

max_adesao_idx = adesao_list.index(max(adesao_list))
melhor_mes = {
    "mes": month_names_pt[max_adesao_idx].capitalize(),
    "inclusoes": max(adesao_list)
}
media_mensal = round(sum(adesao_list) / len(adesao_list), 1)
acumulado_2026 = sum(adesao_list)

# Vendas por consultor
adesao_2026['regional'] = adesao_2026['regional'].fillna('Venda Direta (Site)')
consultor_counts = adesao_2026['regional'].value_counts()
vendas_por_consultor = []
total_vendas_consultor = len(adesao_2026)
for c_name, count in consultor_counts.items():
    vendas_por_consultor.append({
        "consultor": str(c_name),
        "vendas": int(count),
        "pct": round((count / total_vendas_consultor) * 100, 1) if total_vendas_consultor > 0 else 0.0
    })

# Inclusões por consultor no mês de referência
current_period_inclusions_copy = current_period_inclusions.copy()
current_period_inclusions_copy['consultor_clean'] = current_period_inclusions_copy['regional'].fillna('Venda Direta (Site)')
consultor_period = current_period_inclusions_copy.groupby(['consultor_clean', 'tipo_contrato']).agg(
    inclusoes=('tipo_contrato', 'size'),
    valor=('total_geral', 'sum')
).reset_index()
consultor_period['pct'] = (consultor_period['inclusoes'] / len(current_period_inclusions) * 100).round(1)
consultor_period['valor'] = consultor_period['valor'].round(1)
consultor_period = consultor_period.sort_values(by='inclusoes', ascending=False)

inclusoes_junho_por_consultor_items = []
for row in consultor_period.to_dict('records'):
    inclusoes_junho_por_consultor_items.append({
        "consultor": row['consultor_clean'],
        "tipo": row['tipo_contrato'],
        "inclusoes": int(row['inclusoes']),
        "pct": row['pct'],
        "valor": row['valor']
    })
inclusoes_junho_por_consultor = {
    "mes_ref": inclusoes_junho_obs,
    "itens": inclusoes_junho_por_consultor_items,
    "total": len(current_period_inclusions),
    "valor_total": round(current_period_inclusions['total_geral'].sum(), 1)
}

# Detalhe de inclusões
detail_items = []
for row in current_period_inclusions.to_dict('records'):
    detail_items.append({
        "tipo": row['tipo_contrato'],
        "vigencia": row['dtvigencia_benef'],
        "contratante": row['nome'],
        "consultor": "null" if pd.isna(row['regional']) and row['tipo_contrato'] == 'ADESÃO' else (row['regional'] if pd.notna(row['regional']) else "Venda Direta (Site)"),
        "tipo_descricao": row['tipo_descricao'],
        "tipo_beneficiario": row['tipo_segurado'],
        "beneficiario": row['nome_segurado'],
        "cpf_cnpj": row['cpf_segurado'],
        "valor": round(row['total_geral'], 1)
    })
def parse_vig_date(item):
    try:
        return datetime.strptime(item['vigencia'], '%d/%m/%Y')
    except:
        return datetime.min
detail_items = sorted(detail_items, key=parse_vig_date)

inclusoes_junho_detalhe = {
    "mes_ref": inclusoes_junho_obs,
    "itens": detail_items
}

pagina1_data = {
    "titulo": "VISÃO EXECUTIVA - CARTEIRA DE BENEFICIÁRIOS",
    "kpis": {
        "vidas_ativas": vidas_ativas,
        "empresarial": empresarial,
        "empresarial_pct": empresarial_pct,
        "adesao": adesao,
        "adesao_pct": adesao_pct,
        "inclusoes_junho": inclusoes_junho,
        "inclusoes_junho_obs": inclusoes_junho_obs
    },
    "composicao_carteira": {
        "empresarial": empresarial,
        "empresarial_pct": empresarial_pct,
        "adesao": adesao,
        "adesao_pct": adesao_pct
    },
    "inclusoes_por_dia_junho": inclusoes_por_dia_junho,
    "destaques_periodo": [
        {
            "data": "Acompanhamento Mensal",
            "texto": f"Inclusões no período de {obs_period_name}: {inclusoes_junho} vidas registradas."
        }
    ],
    "inclusoes_por_mes_tipo": inclusoes_por_mes_tipo,
    "valores_inclusoes_por_mes_tipo": valores_inclusoes_por_mes_tipo,
    "vendas_adesao_por_produto": vendas_adesao_por_produto,
    "ranking_vendas": ranking_vendas,
    "melhor_mes": melhor_mes,
    "media_mensal": media_mensal,
    "acumulado_2026": acumulado_2026,
    "vendas_por_consultor": vendas_por_consultor,
    "vendas_por_consultor_total": total_vendas_consultor,
    "inclusoes_junho_por_consultor": inclusoes_junho_por_consultor,
    "inclusoes_junho_detalhe": inclusoes_junho_detalhe,
    "mensagem_diretoria": f"A DR. HOJE finaliza o período com {vidas_ativas} vidas ativas na carteira (Adesão: {adesao} | PJ: {empresarial})."
}

# --- PAGE 2 ---
inclusoes_2026 = len(inc_2026)
excl_2026 = df_contratos[df_contratos['mes_ano_inativacao'].isin(months_keys)]
exclusoes_2026 = len(excl_2026)
saldo_liquido = inclusoes_2026 - exclusoes_2026
obs_s1_saude = len(inc_2026[inc_2026['tipo_descricao'] == 'PLUS'])

evolucao_mensal_list = []
for idx, m_key in enumerate(months_keys):
    inc_count = total_list[idx]
    excl_count = len(df_contratos[df_contratos['mes_ano_inativacao'] == m_key])
    evolucao_mensal_list.append({
        "mes": labels_evo[idx],
        "inclusoes": inc_count,
        "exclusoes": excl_count,
        "saldo": inc_count - excl_count
    })

# Inclusões por produto (top 4 and DEMAIS)
product_inc = inc_2026['tipo_descricao'].value_counts()
inclusoes_por_produto_items = []
top_4_prods = product_inc.index.tolist()[:4]
for prod in top_4_prods:
    count = product_inc[prod]
    inclusoes_por_produto_items.append({
        "produto": str(prod).upper(),
        "vidas": int(count),
        "pct": round((count / inclusoes_2026) * 100, 1) if inclusoes_2026 > 0 else 0.0
    })
others_count = sum(product_inc[p] for p in product_inc.index if p not in top_4_prods)
if others_count > 0:
    inclusoes_por_produto_items.append({
        "produto": "DEMAIS PRODUTOS",
        "vidas": int(others_count),
        "pct": round((others_count / inclusoes_2026) * 100, 1) if inclusoes_2026 > 0 else 0.0
    })

# Motivos de exclusão (categories order)
excl_reasons = excl_2026.copy()
excl_reasons['motivo_clean'] = excl_reasons['motivo_exclusao'].fillna('')
def map_motivo(m):
    m = str(m).strip().upper()
    if 'EMPRESA' in m: return 'SOLICITAÇÃO DA EMPRESA'
    elif 'INADIMPL' in m: return 'INADIMPLÊNCIA'
    elif 'SOLUTIONS' in m or 'MIGRAD' in m: return 'MIGRAÇÃO PARA SOLUTIONS'
    elif 'CLIENTE' in m: return 'SOLICITAÇÃO DO CLIENTE'
    else: return 'DEMAIS MOTIVOS'
excl_reasons['categoria'] = excl_reasons['motivo_clean'].apply(map_motivo)
cat_counts = excl_reasons['categoria'].value_counts()
motivos_exclusao_items = []
categories_order = ['SOLICITAÇÃO DA EMPRESA', 'INADIMPLÊNCIA', 'MIGRAÇÃO PARA SOLUTIONS', 'SOLICITAÇÃO DO CLIENTE', 'DEMAIS MOTIVOS']
for cat in categories_order:
    count = cat_counts.get(cat, 0)
    motivos_exclusao_items.append({
        "motivo": cat,
        "vidas": int(count),
        "pct": round((count / exclusoes_2026) * 100, 1) if exclusoes_2026 > 0 else 0.0
    })

# Top 5 Empresas
pj_active_counts = active_df[active_df['tipo_contrato'] == 'EMPRESARIAL']['nome'].value_counts()
top5_empresas_items = []
total_pj_active = len(active_df[active_df['tipo_contrato'] == 'EMPRESARIAL'])
for idx, (company, count) in enumerate(pj_active_counts.head(5).items()):
    top5_empresas_items.append({
        "posicao": idx + 1,
        "empresa": str(company),
        "vidas": int(count),
        "pct_empresarial": round((count / total_pj_active) * 100, 1) if total_pj_active > 0 else 0.0
    })
top5_total_vidas = sum(x['vidas'] for x in top5_empresas_items)
top5_pct_base_empresarial = round((top5_total_vidas / total_pj_active) * 100, 1) if total_pj_active > 0 else 0.0
top5_vidas_acima_demais = top5_total_vidas - (total_pj_active - top5_total_vidas)

pagina2_data = {
    "titulo": "VISÃO EXECUTIVA 02 - EVOLUÇÃO E MOVIMENTAÇÃO DA CARTEIRA",
    "kpis": {
        "inclusoes_2026": inclusoes_2026,
        "exclusoes_2026": exclusoes_2026,
        "saldo_liquido": saldo_liquido,
        "base_atual": vidas_ativas,
        "concentracao_empresarial_pct": empresarial_pct,
        "obs_s1_saude": obs_s1_saude
    },
    "evolucao_mensal": evolucao_mensal_list,
    "inclusoes_acumuladas": inclusoes_2026,
    "exclusoes_acumuladas": exclusoes_2026,
    "saldo_liquido_2026": saldo_liquido,
    "inclusoes_por_produto": inclusoes_por_produto_items,
    "inclusoes_por_produto_total": inclusoes_2026,
    "motivos_exclusao": motivos_exclusao_items,
    "motivos_exclusao_total": exclusoes_2026,
    "top5_empresas": top5_empresas_items,
    "top5_total_vidas": top5_total_vidas,
    "top5_pct_base_empresarial": top5_pct_base_empresarial,
    "top5_vidas_acima_demais": top5_vidas_acima_demais,
    "resumo_executivo": [
        {
            "titulo": "SALDO LÍQUIDO 2026",
            "texto": f"A carteira acumula um saldo de {saldo_liquido} vidas em 2026 ({inclusoes_2026} inclusões e {exclusoes_2026} exclusões)."
        }
    ],
    "mensagem_diretoria": f"Acumulado 2026: {inclusoes_2026} inclusões e {exclusoes_2026} exclusões. Saldo líquido de {saldo_liquido} vidas."
}

# --- PAGE 3 ---
adesao_active = active_df[active_df['tipo_contrato'] == 'ADESÃO']
adesao_active_counts = list(adesao_active['tipo_descricao'].value_counts().items())
distribuicao_adesao = [{
    "produto": "TOTAL ADESÃO",
    "vidas": len(adesao_active),
    "pct": 100.0,
    "destaque": True
}]
for prod, count in adesao_active_counts:
    distribuicao_adesao.append({
        "produto": str(prod).upper(),
        "vidas": int(count),
        "pct": round((count / len(adesao_active)) * 100, 1) if len(adesao_active) > 0 else 0.0
    })

donut_adesao_items = []
for prod, count in adesao_active_counts[:4]:
    donut_adesao_items.append({
        "produto": str(prod).upper(),
        "vidas": int(count),
        "pct": round((count / len(adesao_active)) * 100, 1) if len(adesao_active) > 0 else 0.0
    })
others_adesao_count = sum(count for prod, count in adesao_active_counts[4:])
if others_adesao_count > 0:
    donut_adesao_items.append({
        "produto": "DEMAIS PRODUTOS",
        "vidas": int(others_adesao_count),
        "pct": round((others_adesao_count / len(adesao_active)) * 100, 1) if len(adesao_active) > 0 else 0.0
    })

emp_active = active_df[active_df['tipo_contrato'] == 'EMPRESARIAL']
emp_active_counts = list(emp_active['tipo_descricao'].value_counts().items())
distribuicao_empresarial = [{
    "produto": "TOTAL EMPRESARIAL",
    "vidas": len(emp_active),
    "pct": 100.0,
    "destaque": True
}]
for prod, count in emp_active_counts:
    distribuicao_empresarial.append({
        "produto": str(prod).upper(),
        "vidas": int(count),
        "pct": round((count / len(emp_active)) * 100, 1) if len(emp_active) > 0 else 0.0
    })

donut_empresarial_items = []
for prod, count in emp_active_counts[:4]:
    donut_empresarial_items.append({
        "produto": str(prod).upper(),
        "vidas": int(count),
        "pct": round((count / len(emp_active)) * 100, 1) if len(emp_active) > 0 else 0.0
    })
others_emp_count = sum(count for prod, count in emp_active_counts[4:])
if others_emp_count > 0:
    donut_empresarial_items.append({
        "produto": "DEMAIS PRODUTOS",
        "vidas": int(others_emp_count),
        "pct": round((others_emp_count / len(emp_active)) * 100, 1) if len(emp_active) > 0 else 0.0
    })

pagina3_data = {
    "titulo": "VIDAS ATIVAS POR PRODUTO – DISTRIBUIÇÃO DE VIDAS POR TIPO E PRODUTO",
    "kpis": {
        "vidas_ativas": vidas_ativas,
        "adesao": adesao,
        "adesao_pct": adesao_pct,
        "empresarial": empresarial,
        "empresarial_pct": empresarial_pct,
        "produtos_disponiveis": active_df['tipo_descricao'].nunique()
    },
    "distribuicao_adesao": distribuicao_adesao,
    "donut_adesao": donut_adesao_items,
    "distribuicao_empresarial": distribuicao_empresarial,
    "donut_empresarial": donut_empresarial_items,
    "destaques": {
        "adesao": "Distribuição detalhada dos planos de Adesão na carteira ativa.",
        "empresarial": "Distribuição detalhada dos planos Empresariais na carteira ativa."
    },
    "resumo_geral": f"A base de vidas ativas totaliza {vidas_ativas} vidas (PJ: {empresarial} e PF: {adesao})."
}

# --- EXTRACT FATURAMENTO FROM EXISTING INDEX.HTML & MERGE ---
html_files = ["index.html", "dashboard_dr_hoje.html"]

for file_path in html_files:
    if not os.path.exists(file_path):
        continue
        
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    start_marker = "const DATA = "
    end_marker = "/* ---------------- helpers ---------------- */"
    
    start_idx = content.find(start_marker) + len(start_marker)
    end_idx = content.find(end_marker)
    
    data_str = content[start_idx:end_idx].strip().rstrip(';')
    existing_data = json.loads(data_str)
    
    # Retain the faturamento section as it was
    faturamento_data = existing_data.get("faturamento", {})
    
    # Update meta dates
    meta_data = {
        "empresa": "DR. HOJE",
        "fonte": "Sistema de Gestão DR. HOJE",
        "posicao_em": today.strftime("%Y-%m-%d"),
        "atualizado_em": today.strftime("%Y-%m-%d"),
        "versao_modelo": "1.0",
        "observacao": "Atualizado de forma automática via GitHub Actions"
    }
    
    # Reassemble new DATA
    new_data = {
        "meta": meta_data,
        "pagina1_visao_executiva": pagina1_data,
        "pagina2_evolucao_movimentacao": pagina2_data,
        "pagina3_carteira_por_produto": pagina3_data,
        "faturamento": faturamento_data
    }
    
    # Serialize with nice formatting
    new_data_str = json.dumps(new_data, ensure_ascii=False, indent=2)
    
    # Write back to file
    new_content = content[:start_idx] + new_data_str + ";\n\n" + content[end_idx:]
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
        
    print(f"Painel {file_path} atualizado com sucesso!")
