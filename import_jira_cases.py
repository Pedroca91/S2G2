#!/usr/bin/env python3
"""
Script para:
1. Limpar casos com status "Aguardando resposta" e "Em Desenvolvimento"
2. Criar 21 novos casos do Jira como "Pendente"
3. Substituir AXPERT por ESSOR
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import uuid
import os

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'safe2go_helpdesk')

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Dados dos 21 chamados
CHAMADOS = [
    {
        "jira_id": "S2GSS-10782",
        "title": "Ambiente Admin não está apresentando o valor da cobertura de Furto Simples(Senhor e Benfeitoria)",
        "responsible": "julio.cruz@essor.com.br",
        "created_date": "29/dez/25",
        "seguradora": "ESSOR"
    },
    {
        "jira_id": "S2GSS-10779",
        "title": "Cotador não está concluindo o cálculo.",
        "responsible": "julio.cruz@essor.com.br",
        "created_date": "23/dez/25",
        "seguradora": "ESSOR"
    },
    {
        "jira_id": "S2GSS-10778",
        "title": "Cotador não está disponibilizando a nota fiscal do equipamento para download (Senhor e Benfeitoria)",
        "responsible": "julio.cruz@essor.com.br",
        "created_date": "23/dez/25",
        "seguradora": "ESSOR"
    },
    {
        "jira_id": "S2GSS-10746",
        "title": "Necessário realizar o ajuste da POS e Mínimo de franquia em alguns equipamentos (Senhor e Benfeitoria)",
        "responsible": "julio.cruz@essor.com.br",
        "created_date": "12/dez/25",
        "seguradora": "ESSOR"
    },
    {
        "jira_id": "S2GSS-10737",
        "title": "Botão cancelar não funciona no Admin(Senhor e Benfeitoria)",
        "responsible": "julio.cruz@essor.com.br",
        "created_date": "12/dez/25",
        "seguradora": "ESSOR"
    },
    {
        "jira_id": "S2GSS-10723",
        "title": "PDFs das apólices não estão trazendo os dados das coberturas",
        "responsible": "julio.cruz@essor.com.br",
        "created_date": "12/dez/25",
        "seguradora": "ESSOR"
    },
    {
        "jira_id": "S2GSS-10781",
        "title": "aplicar juros e multas para pedido de reprogramação de parcela, usando API e ERP da Seguradora.",
        "responsible": "luiz filipe barreiros nunes",
        "created_date": "26/dez/25",
        "seguradora": "ESSOR"
    },
    {
        "jira_id": "S2GSS-10756",
        "title": "cotação em moderação pelo campo horímetro",
        "responsible": "luiz filipe barreiros nunes",
        "created_date": "15/dez/25",
        "seguradora": "ESSOR"
    },
    {
        "jira_id": "S2GSS-10750",
        "title": "COBERTURA DE DESPESA COM AÇÃO JUDICIAL SEM A CONTRATAÇÃO DA COBERTURA ADICIONAL DE RC",
        "responsible": "luiz filipe barreiros nunes",
        "created_date": "15/dez/25",
        "seguradora": "ESSOR"
    },
    {
        "jira_id": "S2GSS-10728",
        "title": "ajuste de critério de subscrição de itens aceitos automaticamente (senhor rural e benfeitorias)",
        "responsible": "luiz filipe barreiros nunes",
        "created_date": "09/dez/25",
        "seguradora": "ESSOR"
    },
    {
        "jira_id": "S2GSS-10777",
        "title": "URGENTE - AJUSTE DE FRANQUIAS.",
        "responsible": "Yasmin Fazani Rego",
        "created_date": "23/dez/25",
        "seguradora": "ESSOR"  # Substituído de AXPERT
    },
    {
        "jira_id": "S2GSS-10774",
        "title": "URGENTE - CANCELAMENTO PELA SAFE2GO SEM MOTIVO - 10051003029296",
        "responsible": "Yasmin Fazani Rego",
        "created_date": "22/dez/25",
        "seguradora": "ESSOR"  # Substituído de AXPERT
    },
    {
        "jira_id": "S2GSS-10743",
        "title": "AJUSTE ABRAPE",
        "responsible": "Yasmin Fazani Rego",
        "created_date": "12/dez/25",
        "seguradora": "ESSOR"  # Substituído de AXPERT
    },
    {
        "jira_id": "S2GSS-10740",
        "title": "AJUSTE DE OBSERVAÇÃO PARA EVENTOS MUSICAIS",
        "responsible": "Yasmin Fazani Rego",
        "created_date": "11/dez/25",
        "seguradora": "ESSOR"  # Substituído de AXPERT
    },
    {
        "jira_id": "S2GSS-10702",
        "title": "DADOS ESSOR NOS BOLETOS",
        "responsible": "Yasmin Fazani Rego",
        "created_date": "26/nov/25",
        "seguradora": "ESSOR"  # Substituído de AXPERT
    },
    {
        "jira_id": "S2GSS-10688",
        "title": "ADEQUAÇÃO NOVA LEI DO SEGURO - Numero das cotações | preservação de cotação.",
        "responsible": "Yasmin Fazani Rego",
        "created_date": "10/nov/25",
        "seguradora": "ESSOR"  # Substituído de AXPERT
    },
    {
        "jira_id": "S2GSS-10680",
        "title": "COSSEGURADO INTERNACIONAL",
        "responsible": "Yasmin Fazani Rego",
        "created_date": "05/nov/25",
        "seguradora": "ESSOR"  # Substituído de AXPERT
    },
    {
        "jira_id": "S2GSS-10524",
        "title": "URGENTE - PDF COM ERRO - 10149020255100130003",
        "responsible": "Yasmin Fazani Rego",
        "created_date": "30/out/25",
        "seguradora": "ESSOR"  # Substituído de AXPERT
    },
    {
        "jira_id": "S2GSS-10437",
        "title": "CAIXINHA - VOCÊ SABIA?",
        "responsible": "Yasmin Fazani Rego",
        "created_date": "06/out/25",
        "seguradora": "ESSOR"  # Substituído de AXPERT
    },
    {
        "jira_id": "S2GSS-9650",
        "title": "AJUSTE ENDOSSO DE PRORROGAÇÃO.",
        "responsible": "Yasmin Fazani Rego",
        "created_date": "10/out/25",
        "seguradora": "ESSOR"  # Substituído de AXPERT
    },
    {
        "jira_id": "S2GSS-8419",
        "title": "complemento solicitação S2GSS-7695",
        "responsible": "Yasmin Fazani Rego",
        "created_date": "12/dez/25",
        "seguradora": "ESSOR"  # Substituído de AXPERT
    }
]

def parse_date(date_str):
    """Converte data do formato dd/mmm/yy para datetime"""
    meses = {
        'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4, 'mai': 5, 'jun': 6,
        'jul': 7, 'ago': 8, 'set': 9, 'out': 10, 'nov': 11, 'dez': 12
    }
    
    parts = date_str.replace('/', ' ').split()
    dia = int(parts[0])
    mes = meses[parts[1].lower()]
    ano = 2000 + int(parts[2])
    
    return datetime(ano, mes, dia, 12, 0, 0)

async def limpar_casos_antigos():
    """Remove casos com status Aguardando resposta e Em Desenvolvimento"""
    print("\n🗑️  LIMPANDO CASOS ANTIGOS...")
    print("="*70)
    
    # Deletar casos "Aguardando resposta"
    result1 = await db.cases.delete_many({"status": "Aguardando resposta"})
    print(f"  ✅ Removidos {result1.deleted_count} casos 'Aguardando resposta'")
    
    # Deletar casos "Em Desenvolvimento"
    result2 = await db.cases.delete_many({"status": "Em Desenvolvimento"})
    print(f"  ✅ Removidos {result2.deleted_count} casos 'Em Desenvolvimento'")
    
    total_removidos = result1.deleted_count + result2.deleted_count
    print(f"\n  📊 Total de casos removidos: {total_removidos}")
    
    return total_removidos

async def criar_novos_casos():
    """Cria os 21 novos casos como Pendente"""
    print("\n📝 CRIANDO 21 NOVOS CASOS...")
    print("="*70)
    
    # Pegar um usuário admin como creator
    admin_user = await db.users.find_one({"role": "administrador"})
    creator_id = admin_user['id'] if admin_user else str(uuid.uuid4())
    
    casos_criados = 0
    
    for chamado in CHAMADOS:
        # Verificar se já existe
        existing = await db.cases.find_one({"jira_id": chamado["jira_id"]})
        if existing:
            print(f"  ⚠️  {chamado['jira_id']} já existe, pulando...")
            continue
        
        case_id = str(uuid.uuid4())
        created_date = parse_date(chamado["created_date"])
        
        caso = {
            "id": case_id,
            "jira_id": chamado["jira_id"],
            "title": chamado["title"],
            "description": f"Caso importado do Jira - {chamado['title']}",
            "status": "Pendente",
            "priority": "Alta",
            "category": "Suporte",
            "seguradora": chamado["seguradora"],
            "responsible": chamado["responsible"],
            "creator_id": creator_id,
            "created_at": created_date.isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }
        
        await db.cases.insert_one(caso)
        casos_criados += 1
        print(f"  ✅ {chamado['jira_id']} - {chamado['seguradora']}")
    
    print(f"\n  📊 Total de casos criados: {casos_criados}")
    return casos_criados

async def mostrar_resumo():
    """Mostra resumo final do sistema"""
    print("\n" + "="*70)
    print("📊 RESUMO FINAL DO SISTEMA")
    print("="*70)
    
    total_cases = await db.cases.count_documents({})
    pendentes = await db.cases.count_documents({"status": "Pendente"})
    concluidos = await db.cases.count_documents({"status": "Concluído"})
    
    essor_cases = await db.cases.count_documents({"seguradora": "ESSOR"})
    avla_cases = await db.cases.count_documents({"seguradora": "AVLA"})
    daycoval_cases = await db.cases.count_documents({"seguradora": "DAYCOVAL"})
    
    print(f"\n  📊 CASOS NO SISTEMA:")
    print(f"    • Total: {total_cases}")
    print(f"    • Pendentes: {pendentes}")
    print(f"    • Concluídos: {concluidos}")
    
    print(f"\n  🏢 CASOS POR SEGURADORA:")
    print(f"    • ESSOR: {essor_cases}")
    print(f"    • AVLA: {avla_cases}")
    print(f"    • DAYCOVAL: {daycoval_cases}")
    
    print("\n" + "="*70)
    print("✅ OPERAÇÃO CONCLUÍDA COM SUCESSO!")
    print("="*70 + "\n")

async def main():
    print("\n" + "="*70)
    print("🚀 ATUALIZAÇÃO DE CASOS - JIRA PARA SAFE2GO")
    print("="*70)
    
    # Passo 1: Limpar casos antigos
    removidos = await limpar_casos_antigos()
    
    # Passo 2: Criar novos casos
    criados = await criar_novos_casos()
    
    # Passo 3: Mostrar resumo
    await mostrar_resumo()
    
    print(f"✅ {removidos} casos removidos, {criados} casos criados!")

if __name__ == "__main__":
    asyncio.run(main())
