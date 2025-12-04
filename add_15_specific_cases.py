#!/usr/bin/env python3
"""
Adicionar 15 casos específicos com IDs e títulos da imagem
TODOS com status PENDENTE
SEM apagar os 110 casos existentes
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from pathlib import Path
from dotenv import load_dotenv
import uuid
from datetime import datetime, timezone

# Load environment
ROOT_DIR = Path('backend')
load_dotenv(ROOT_DIR / '.env')

# Casos específicos da imagem
CASOS_ESPECIFICOS = [
    {
        "jira_id": "S2GSS-10712",
        "title": "Campo Protecionais e PPCI não abrem para inclusão de informação",
        "seguradora": "AVLA"
    },
    {
        "jira_id": "S2GSS-10717",
        "title": "Saneamento de usuários Daycoval Seguros",
        "seguradora": "DAYCOVAL"
    },
    {
        "jira_id": "S2GSS-10716",
        "title": "Saneamento de usuários Daycoval Seguros",
        "seguradora": "DAYCOVAL"
    },
    {
        "jira_id": "S2GSS-10715",
        "title": "Saneamento de usuários Daycoval Seguros",
        "seguradora": "DAYCOVAL"
    },
    {
        "jira_id": "S2GSS-10714",
        "title": "URGENTE - EMISSÃO SEM BOLETO - 10149020255100132182.",
        "seguradora": "AVLA"
    },
    {
        "jira_id": "S2GSS-10702",
        "title": "DADOS ESSOR NOS BOLETOS",
        "seguradora": "ESSOR"
    },
    {
        "jira_id": "S2GSS-10678",
        "title": "NOVA LEI DE SEGUROS - OBSERVACÃO.",
        "seguradora": "AVLA"
    },
    {
        "jira_id": "S2GSS-10671",
        "title": "ADEQUACAO NOVA LEI DO SEGURO - OBSERVAÇÕES",
        "seguradora": "AVLA"
    },
    {
        "jira_id": "S2GSS-10670",
        "title": "ADEQUACAO NOVA LEI DO SEGURO - OBSERVAÇÕES",
        "seguradora": "AVLA"
    },
    {
        "jira_id": "S2GSS-10669",
        "title": "ADEQUAÇÃO NOVA LEI DO SEGURO - Inclusão de disclaimer.",
        "seguradora": "AVLA"
    },
    {
        "jira_id": "S2GSS-10668",
        "title": "ADEQUAÇÃO NOVA LEI DO SEGURO - Numero das cotações | preservação de cotação.",
        "seguradora": "AVLA"
    },
    {
        "jira_id": "S2GSS-10660",
        "title": "COSEGURADO INTERNACIONAL",
        "seguradora": "AVLA"
    },
    {
        "jira_id": "S2GSS-10524",
        "title": "URGENTE - PDF COM ERRO - 10149020255100130003",
        "seguradora": "AVLA"
    },
    {
        "jira_id": "S2GSS-10437",
        "title": "CAIXINHA - VOCÊ SABIA?",
        "seguradora": "AVLA"
    },
    {
        "jira_id": "S2GSS-9650",
        "title": "AJUSTE ENDOSSO DE PRORROGAÇÃO.",
        "seguradora": "AVLA"
    }
]

async def add_specific_cases():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("=" * 80)
    print("➕ ADICIONANDO 15 CASOS ESPECÍFICOS (SEM APAGAR NADA)")
    print("=" * 80)
    
    # Buscar usuário admin para usar como creator
    admin_user = await db.users.find_one({'role': 'administrador'})
    if not admin_user:
        print("❌ Nenhum usuário admin encontrado.")
        return
    
    creator_id = admin_user['id']
    print(f"✅ Usuário admin encontrado: {admin_user['email']}")
    
    # Verificar casos existentes (NÃO vamos apagar)
    existing_count = await db.cases.count_documents({})
    print(f"📊 Casos existentes no banco: {existing_count}")
    
    print("\n📝 ADICIONANDO 15 CASOS ESPECÍFICOS...")
    print("-" * 80)
    
    added_count = 0
    skipped_count = 0
    
    for caso_data in CASOS_ESPECIFICOS:
        # Verificar se já existe
        existing = await db.cases.find_one({'jira_id': caso_data['jira_id']})
        
        if existing:
            print(f"⚠️  {caso_data['jira_id']} - Já existe, pulando...")
            skipped_count += 1
            continue
        
        caso = {
            "id": str(uuid.uuid4()),
            "jira_id": caso_data['jira_id'],
            "title": caso_data['title'],
            "description": f"Caso específico: {caso_data['title']}",
            "status": "Pendente",
            "responsible": "Equipe Suporte",
            "seguradora": caso_data['seguradora'],
            "category": "Técnico",
            "priority": "Alta",
            "creator_id": creator_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.cases.insert_one(caso)
        print(f"✅ {caso_data['jira_id']} - {caso_data['title'][:60]}...")
        added_count += 1
    
    # Resumo final
    print("\n" + "=" * 80)
    print("📊 RESUMO DA ADIÇÃO")
    print("=" * 80)
    
    # Contar todos os casos agora
    total_now = await db.cases.count_documents({})
    concluidos = await db.cases.count_documents({"status": "Concluído"})
    pendentes = await db.cases.count_documents({"status": "Pendente"})
    aguardando = await db.cases.count_documents({"status": "Aguardando resposta"})
    em_dev = await db.cases.count_documents({"status": "Em Desenvolvimento"})
    
    print(f"\n  ➕ Casos adicionados: {added_count}")
    print(f"  ⚠️  Casos pulados (já existiam): {skipped_count}")
    print(f"  📈 Total de casos no banco: {total_now}")
    print(f"     🟢 Concluídos: {concluidos}")
    print(f"     🟡 Pendentes: {pendentes}")
    print(f"     🔵 Em Desenvolvimento: {em_dev}")
    print(f"     🟠 Aguardando resposta: {aguardando}")
    
    # Distribuição por seguradora
    print(f"\n  📊 Casos por seguradora:")
    seguradoras = ["AVLA", "ESSOR", "DAYCOVAL"]
    for seg in seguradoras:
        count = await db.cases.count_documents({"seguradora": seg})
        print(f"    • {seg}: {count} casos")
    
    # Taxa de conclusão
    completion_rate = round((concluidos / total_now * 100), 1) if total_now > 0 else 0
    print(f"\n  ✅ Taxa de conclusão: {completion_rate}%")
    
    print("\n✅ ADIÇÃO DOS 15 CASOS CONCLUÍDA COM SUCESSO!")
    print("=" * 80)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(add_specific_cases())
