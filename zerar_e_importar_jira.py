#!/usr/bin/env python3
"""
Script para ZERAR o banco e importar TODOS os casos do Jira
Total: 18 casos (5 Pendentes + 5 Aguardando Cliente + 8 Configuração de Produtos)
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

# TODOS OS 18 CASOS DO JIRA
TODOS_CASOS_JIRA = [
    # ========== FILA: PENDENTES S2G (5 casos) ==========
    {
        "jira_id": "S2GSS-10808",
        "title": "URGENTE - DUVIDA.",
        "responsible": "Yasmin Fazani Rego",
        "status": "Pendente",  # AGUARDANDO SUPORTE
        "seguradora": "ESSOR",  # AXPERT → ESSOR
        "priority": "Alta",
        "created_date": "13/jan/26"
    },
    {
        "jira_id": "S2GSS-10806",
        "title": "erro campos do item ao clonar cotação",
        "responsible": "Penhor Rural",
        "status": "Em Desenvolvimento",  # EM ATENDIMENTO
        "seguradora": "ESSOR",
        "priority": "Média",
        "created_date": "13/jan/26"
    },
    {
        "jira_id": "S2GSS-10723",
        "title": "PDFs das apólices não estão trazendo os dados das coberturas",
        "responsible": "julio.cruz@essor.com.br",
        "status": "Pendente",  # AGUARDANDO SUPORTE
        "seguradora": "ESSOR",
        "priority": "Alta",
        "created_date": "22/jan/26"
    },
    {
        "jira_id": "S2GSS-10524",
        "title": "URGENTE - PDF COM ERRO - 10149020255100130003",
        "responsible": "Yasmin Fazani Rego",
        "status": "Em Desenvolvimento",  # EM ATENDIMENTO
        "seguradora": "ESSOR",  # AXPERT → ESSOR
        "priority": "Crítica",
        "created_date": "24/out/25"
    },
    {
        "jira_id": "S2GSS-10437",
        "title": "CAIXINHA - VOCÊ SABIA?",
        "responsible": "Yasmin Fazani Rego",
        "status": "Pendente",  # AGUARDANDO SUPORTE
        "seguradora": "ESSOR",  # AXPERT → ESSOR
        "priority": "Baixa",
        "created_date": "06/out/25"
    },
    
    # ========== FILA: AGUARDANDO CLIENTE (5 casos) ==========
    {
        "jira_id": "S2GSS-10610",
        "title": "Alteração/Inclusão Cobertura - Nova Lei (Urgente/Obrigatoriedade)",
        "responsible": "NICCOLLAS DAMASCENO PEIXOTO",
        "status": "Aguardando resposta",  # AGUARDANDO CLIENTE
        "seguradora": "ESSOR",  # AXPERT → ESSOR
        "priority": "Crítica",
        "created_date": "03/nov/25"
    },
    {
        "jira_id": "S2GSS-10613",
        "title": "Alterações RD Eventos- Nova Lei",
        "responsible": "NICCOLLAS DAMASCENO PEIXOTO",
        "status": "Aguardando resposta",
        "seguradora": "ESSOR",  # AXPERT → ESSOR
        "priority": "Alta",
        "created_date": "03/nov/25"
    },
    {
        "jira_id": "S2GSS-10728",
        "title": "ajuste de critério de subscrição de itens aceitos automaticamente (penhor rural e benfeitorias)",
        "responsible": "luiz filipe barreiros nunes",
        "status": "Aguardando resposta",
        "seguradora": "ESSOR",
        "priority": "Média",
        "created_date": "09/dez/25"
    },
    {
        "jira_id": "S2GSS-10751",
        "title": "Melhoria na planilha de carga de equipamentos nos produtos Riscos Especiais (Penhor Rural e Benfeitoria)",
        "responsible": "julio.cruz@essor.com.br",
        "status": "Aguardando resposta",
        "seguradora": "ESSOR",
        "priority": "Média",
        "created_date": "15/dez/25"
    },
    {
        "jira_id": "S2GSS-10781",
        "title": "aplicar juros e multas para pedido de reprogramação de parcela, usando API e ERP da Seguradora.",
        "responsible": "luiz filipe barreiros nunes",
        "status": "Aguardando resposta",
        "seguradora": "ESSOR",
        "priority": "Média",
        "created_date": "26/dez/25"
    },
    
    # ========== FILA: CONFIGURAÇÃO DE PRODUTOS (8 casos) ==========
    {
        "jira_id": "S2GSS-10842",
        "title": "Fiera Milano- Atualização Logo e Custos",
        "responsible": "NICOLLAS DAMASCENO PEIXOTO",
        "status": "Configuração",  # AGUARDANDO CONFIGURAÇÃO
        "seguradora": "ESSOR",  # Sem org, padrão ESSOR
        "priority": "Média",
        "created_date": "26/jan/26"
    },
    {
        "jira_id": "S2GSS-10822",
        "title": "URGENTE - COBERTURA DE OBJETOS PESSOAIS DE TERCEIROS.",
        "responsible": "Yasmin Fazani Rego",
        "status": "Configuração",
        "seguradora": "ESSOR",
        "priority": "Alta",
        "created_date": "19/jan/26"
    },
    {
        "jira_id": "S2GSS-10757",
        "title": "Inclusão de uma nova coluna na planilha de extração",
        "responsible": "rodrigo.menegassi@essor.com.br",
        "status": "Configuração",
        "seguradora": "ESSOR",
        "priority": "Média",
        "created_date": "16/dez/25"
    },
    {
        "jira_id": "S2GSS-10743",
        "title": "AJUSTE ABRAPE",
        "responsible": "Yasmin Fazani Rego",
        "status": "Configuração",
        "seguradora": "ESSOR",
        "priority": "Média",
        "created_date": "12/dez/25"
    },
    {
        "jira_id": "S2GSS-10668",
        "title": "ADEQUAÇÃO NOVA LEI DO SEGURO - Numero das cotações | preservação de cotação.",
        "responsible": "Yasmin Fazani Rego",
        "status": "Configuração",
        "seguradora": "ESSOR",
        "priority": "Alta",
        "created_date": "10/nov/25"
    },
    {
        "jira_id": "S2GSS-10660",
        "title": "COSSEGURADO INTERNACIONAL",
        "responsible": "Yasmin Fazani Rego",
        "status": "Configuração",
        "seguradora": "ESSOR",
        "priority": "Média",
        "created_date": "05/nov/25"
    },
    {
        "jira_id": "S2GSS-9650",
        "title": "AJUSTE ENDOSSO DE PRORROGAÇÃO.",
        "responsible": "Yasmin Fazani Rego",
        "status": "Configuração",
        "seguradora": "ESSOR",
        "priority": "Média",
        "created_date": "14/ago/25"
    },
    {
        "jira_id": "S2GSS-8419",
        "title": "complemento solicitação S2GSS-7695",
        "responsible": "Yasmin Fazani Rego",
        "status": "Configuração",
        "seguradora": "ESSOR",
        "priority": "Baixa",
        "created_date": "08/mai/25"
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
    
    return datetime(ano, mes, dia, 10, 0, 0)

async def zerar_banco():
    """Remove TODOS os casos do sistema"""
    print("\n" + "="*70)
    print("🗑️  ZERANDO BANCO DE DADOS")
    print("="*70)
    
    casos_removidos = await db.cases.delete_many({})
    comentarios_removidos = await db.comments.delete_many({})
    notificacoes_removidas = await db.notifications.delete_many({})
    atividades_removidas = await db.activities.delete_many({})
    
    print(f"  ❌ {casos_removidos.deleted_count} casos removidos")
    print(f"  ❌ {comentarios_removidos.deleted_count} comentários removidos")
    print(f"  ❌ {notificacoes_removidas.deleted_count} notificações removidas")
    print(f"  ❌ {atividades_removidas.deleted_count} atividades removidas")
    print("\n  ✅ Banco zerado!")

async def importar_casos():
    """Importa todos os 18 casos do Jira"""
    print("\n" + "="*70)
    print("📥 IMPORTANDO 18 CASOS DO JIRA")
    print("="*70)
    
    # Pegar um usuário admin como creator
    admin_user = await db.users.find_one({"role": "administrador"})
    creator_id = admin_user['id'] if admin_user else str(uuid.uuid4())
    
    casos_criados = 0
    
    for caso_data in TODOS_CASOS_JIRA:
        case_id = str(uuid.uuid4())
        created_date = parse_date(caso_data["created_date"])
        
        caso = {
            "id": case_id,
            "jira_id": caso_data["jira_id"],
            "title": caso_data["title"],
            "description": f"Caso importado do Jira - {caso_data['title']}",
            "status": caso_data["status"],
            "priority": caso_data["priority"],
            "category": "Suporte",
            "seguradora": caso_data["seguradora"],
            "responsible": caso_data["responsible"],
            "creator_id": creator_id,
            "created_at": created_date.isoformat() + "Z",
            "updated_at": created_date.isoformat() + "Z"
        }
        
        await db.cases.insert_one(caso)
        casos_criados += 1
        print(f"  ✅ {caso_data['jira_id']} - {caso_data['status']}")
    
    print(f"\n  📊 Total importado: {casos_criados} casos")

async def mostrar_resumo():
    """Mostra resumo final do sistema"""
    print("\n" + "="*70)
    print("📊 RESUMO FINAL DO SISTEMA")
    print("="*70)
    
    total = await db.cases.count_documents({})
    pendentes = await db.cases.count_documents({"status": "Pendente"})
    aguardando = await db.cases.count_documents({"status": "Aguardando resposta"})
    em_dev = await db.cases.count_documents({"status": "Em Desenvolvimento"})
    config = await db.cases.count_documents({"status": "Configuração"})
    
    print(f"\n  📊 CASOS POR STATUS:")
    print(f"    • Total: {total}")
    print(f"    • Pendentes: {pendentes}")
    print(f"    • Aguardando resposta: {aguardando}")
    print(f"    • Em Desenvolvimento: {em_dev}")
    print(f"    • Configuração: {config}")
    
    print(f"\n  📋 CASOS POR FILA:")
    print(f"    • Pendentes S2G: 5 casos")
    print(f"    • Aguardando Cliente: 5 casos")
    print(f"    • Configuração de Produtos: 8 casos")
    
    print("\n" + "="*70)
    print("✅ IMPORTAÇÃO CONCLUÍDA COM SUCESSO!")
    print("="*70 + "\n")

async def main():
    print("\n" + "="*70)
    print("🚀 ZERAR E IMPORTAR CASOS DO JIRA")
    print("="*70)
    
    # Passo 1: Zerar banco
    await zerar_banco()
    
    # Passo 2: Importar casos
    await importar_casos()
    
    # Passo 3: Mostrar resumo
    await mostrar_resumo()

if __name__ == "__main__":
    asyncio.run(main())
