#!/usr/bin/env python3
"""
Script para adicionar 7 casos como "Aguardando resposta"
Todos os casos são da ESSOR
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

# Dados dos 7 casos
CASOS_AGUARDANDO = [
    {
        "jira_id": "S2GSS-10610",
        "title": "Alteração/Inclusão Cobertura - Nova Lei (Urgente/Obrigatoriedade)",
        "responsible": "NICOLLAS DAMASCENO PEIXOTO",
        "created_date": "03/nov/25"
    },
    {
        "jira_id": "S2GSS-10613",
        "title": "Alterações RD Eventos - Nova Lei",
        "responsible": "NICOLLAS DAMASCENO PEIXOTO",
        "created_date": "03/nov/25"
    },
    {
        "jira_id": "S2GSS-10751",
        "title": "Melhoria na planilha de carga de equipamentos nos produtos Riscos Especiais (Penhor Rural e Benfeitoria)",
        "responsible": "julio.cruz@essor.com.br",
        "created_date": "15/dez/25"
    },
    {
        "jira_id": "S2GSS-10757",
        "title": "Inclusão de uma nova coluna na planilha de extração",
        "responsible": "rodrigo.menegassi@essor.com.br",
        "created_date": "16/dez/25"
    },
    {
        "jira_id": "S2GSS-10761",
        "title": "Solicitação de atualização da lista de bancos presente no campo Beneficiário do cotador.",
        "responsible": "julio.cruz@essor.com.br",
        "created_date": "18/dez/25"
    },
    {
        "jira_id": "S2GSS-10780",
        "title": "Cotador informar que a apólice já emitida, porém ainda não consta no i4pro(proposta 20253000138413)",
        "responsible": "julio.cruz@essor.com.br",
        "created_date": "26/dez/25"
    },
    {
        "jira_id": "S2GSS-10781",
        "title": "aplicar juros e multas para pedido de reprogramação de parcela, usando API e ERP da Seguradora.",
        "responsible": "luiz filipe barreiros nunes",
        "created_date": "26/dez/25"
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

async def criar_casos_aguardando():
    """Cria os 7 casos como Aguardando resposta"""
    print("\n" + "="*70)
    print("📝 CRIANDO 7 CASOS - AGUARDANDO RESPOSTA DO CLIENTE")
    print("="*70)
    
    # Pegar um usuário admin como creator
    admin_user = await db.users.find_one({"role": "administrador"})
    creator_id = admin_user['id'] if admin_user else str(uuid.uuid4())
    
    casos_criados = 0
    casos_atualizados = 0
    
    for caso_data in CASOS_AGUARDANDO:
        # Verificar se já existe
        existing = await db.cases.find_one({"jira_id": caso_data["jira_id"]})
        
        if existing:
            # Atualizar status para Aguardando resposta
            await db.cases.update_one(
                {"jira_id": caso_data["jira_id"]},
                {"$set": {
                    "status": "Aguardando resposta",
                    "updated_at": datetime.utcnow().isoformat() + "Z"
                }}
            )
            print(f"  🔄 {caso_data['jira_id']} - Atualizado para 'Aguardando resposta'")
            casos_atualizados += 1
        else:
            # Criar novo caso
            case_id = str(uuid.uuid4())
            created_date = parse_date(caso_data["created_date"])
            
            caso = {
                "id": case_id,
                "jira_id": caso_data["jira_id"],
                "title": caso_data["title"],
                "description": f"Caso importado do Jira - {caso_data['title']}",
                "status": "Aguardando resposta",
                "priority": "Média",
                "category": "Suporte",
                "seguradora": "ESSOR",
                "responsible": caso_data["responsible"],
                "creator_id": creator_id,
                "created_at": created_date.isoformat() + "Z",
                "updated_at": datetime.utcnow().isoformat() + "Z"
            }
            
            await db.cases.insert_one(caso)
            print(f"  ✅ {caso_data['jira_id']} - Criado com status 'Aguardando resposta'")
            casos_criados += 1
    
    print("\n" + "="*70)
    print(f"📊 RESUMO:")
    print(f"  • Casos criados: {casos_criados}")
    print(f"  • Casos atualizados: {casos_atualizados}")
    print(f"  • Total processado: {casos_criados + casos_atualizados}")
    print("="*70)
    
    return casos_criados, casos_atualizados

async def mostrar_resumo():
    """Mostra resumo final do sistema"""
    print("\n" + "="*70)
    print("📊 ESTADO ATUAL DO SISTEMA")
    print("="*70)
    
    total_cases = await db.cases.count_documents({})
    pendentes = await db.cases.count_documents({"status": "Pendente"})
    aguardando = await db.cases.count_documents({"status": "Aguardando resposta"})
    concluidos = await db.cases.count_documents({"status": "Concluído"})
    em_dev = await db.cases.count_documents({"status": "Em Desenvolvimento"})
    
    essor_cases = await db.cases.count_documents({"seguradora": "ESSOR"})
    avla_cases = await db.cases.count_documents({"seguradora": "AVLA"})
    daycoval_cases = await db.cases.count_documents({"seguradora": "DAYCOVAL"})
    
    print(f"\n  📊 CASOS POR STATUS:")
    print(f"    • Total: {total_cases}")
    print(f"    • Pendentes: {pendentes}")
    print(f"    • Aguardando resposta: {aguardando}")
    print(f"    • Em Desenvolvimento: {em_dev}")
    print(f"    • Concluídos: {concluidos}")
    
    print(f"\n  🏢 CASOS POR SEGURADORA:")
    print(f"    • ESSOR: {essor_cases}")
    print(f"    • AVLA: {avla_cases}")
    print(f"    • DAYCOVAL: {daycoval_cases}")
    
    # Listar os casos aguardando resposta da ESSOR
    print(f"\n  📋 CASOS ESSOR AGUARDANDO RESPOSTA:")
    casos_aguardando = await db.cases.find(
        {"seguradora": "ESSOR", "status": "Aguardando resposta"},
        {"jira_id": 1, "title": 1, "_id": 0}
    ).sort("jira_id", 1).to_list(100)
    
    for i, caso in enumerate(casos_aguardando, 1):
        titulo_curto = caso['title'][:55] + "..." if len(caso['title']) > 55 else caso['title']
        print(f"    {i}. {caso['jira_id']} - {titulo_curto}")
    
    print("\n" + "="*70)
    print("✅ OPERAÇÃO CONCLUÍDA COM SUCESSO!")
    print("="*70 + "\n")

async def main():
    print("\n" + "="*70)
    print("🚀 ADICIONANDO CASOS - AGUARDANDO RESPOSTA DO CLIENTE")
    print("="*70)
    
    # Criar/atualizar casos
    criados, atualizados = await criar_casos_aguardando()
    
    # Mostrar resumo
    await mostrar_resumo()

if __name__ == "__main__":
    asyncio.run(main())
