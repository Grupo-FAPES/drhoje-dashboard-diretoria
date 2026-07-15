import os
import pandas as pd
import requests

# 1. Definições de Acesso e Credenciais
BASE_URL = "http://drhoje.salustech.com.br:8082"
LOGIN_URL = f"{BASE_URL}/sgc/logar.jsp"
DATA_URL = f"{BASE_URL}/sgc/carregarJson/carregarGenerico.jsp"

# Tenta carregar variáveis do arquivo .env se ele existir localmente
if os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()

credentials = {
    "usuario": os.environ.get("SALUSTECH_USER", ""),
    "senha": os.environ.get("SALUSTECH_PASS", ""),
    "cd_empresa": os.environ.get("SALUSTECH_COMPANY", "")
}


# 2. Login e armazenamento da sessão
print("Tentando efetuar login em:", LOGIN_URL)
session = requests.Session()
login_response = session.post(LOGIN_URL, data=credentials)

print("Status do Login (HTTP):", login_response.status_code)
print("Cookies obtidos:", session.cookies.get_dict())

# Parâmetros para buscar os registros
params = {
    "search": "",
    "order": "asc",
    "tabela": "VW_REL_CONTRATO_ANALITICO",
    "campo": "TIPO_CONTRATO,TIPO_PLANO,NM_CONVENIO,NM_PLANO,CODPLANO,GRUPO_CONTRATUAL,TIPO_DESCRICAO,NM_ENTIDADE,NO_PROPOSTA,NOME,CPF_CONTRATANTE,EMAIL_CONTRATANTE,TELEFONE_CONTRATANTE,ID_BEN,NOME_SEGURADO,TOTAL_GERAL,MATRICULA,SEXO_SEGURADO,DTATIVACAO,MAE_SEGURADO,TIPO_CLIENTE,DESCR_PARENTESCO,CPF_SEGURADO,CARTEIRINHA,DTNASC_SEGURADO,IDADE,FAIXA_PRECO_ANS,TIPO_SEGURADO,STATUS_PROPOSTA_DESC,QTDSEGURADO,DTACAO,DESCR_STATUS,DTCADASTRO,DTPEDIDO,DTVIGENCIA_BENEF,MES_ANO_INCLUSAO,DTINATIVACAO,MES_ANO_INATIVACAO,REAJUSTE_POR_CONTRATO,MOTIVO_EXCLUSAO,DESCR_MOTIVO_EXCLUSAO,REPRLEGAL_NOME,REPRLEGAL_CPF,CEP,ENDERECO,ENDNUM,COMPLEMENTO,BAIRRO,CIDADE,UF,EMAIL_SEGURADO,TELEFONE_SEGURADO,REGIONAL,SUPERVISOR,CORRETORA",
    "condicao": "1 = 1"
}

# 3. Requisição de dados
print("Tentando buscar os dados de:", DATA_URL)
response = session.get(DATA_URL, params=params)

print("Status da Busca (HTTP):", response.status_code)

try:
    data_json = response.json()
    print("Sucesso ao decodificar JSON.")
    
    # 4. Criação do DataFrame
    df_contratos = pd.DataFrame(data_json)
    print("DataFrame criado com sucesso!")
    print("Total de registros recuperados:", len(df_contratos))
    
    # Salva os dados extraídos em CSV para validação
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "contratos_analitico.csv")
    df_contratos.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"Dados extraídos salvos com sucesso em: {csv_path}")
    
    # Mostrar as primeiras 3 linhas para conferência
    if len(df_contratos) > 0:
        print("\nPrimeiros 3 registros encontrados:")
        print(df_contratos[["nome", "matricula", "tipo_contrato"]].head(3))
    else:
        print("A tabela retornou vazia.")
except Exception as e:
    print("Erro ao decodificar os dados ou ao criar o DataFrame:", e)
    # Exibe parte da resposta bruta se falhar
    print("Resposta bruta (primeiros 500 caracteres):")
    print(response.text[:500])
