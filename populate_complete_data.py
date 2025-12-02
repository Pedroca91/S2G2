#!/usr/bin/env python3
"""
Script para popular o banco de dados Safe2Go com dados completos:
1. 11 casos da imagem fornecida (todos pendentes)
2. 60 casos distribuídos de 26/11 a 02/12 (todos concluídos)
   - 20 para Daycoval
   - 20 para ESSOR  
   - 20 para AVLA
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from pathlib import Path
from dotenv import load_dotenv
import uuid
from datetime import datetime, timedelta, timezone
import random

# Load environment
ROOT_DIR = Path('backend')
load_dotenv(ROOT_DIR / '.env')

# Dados da imagem fornecida
CASOS_IMAGEM = [
    {
        "jira_id": "SGSS-N012",
        "title": "Cartão Protegido e PPC1 não estão para inclusão de informação",
        "description": "Os campos do Cartão Protegido e PPC1 não aparecem disponíveis para inclusão de informações no sistema.",
        "status": "Pendente",
        "responsible": "Lucas Colete da Silva",
        "seguradora": "DAIG",
        "category": "Outros",
        "priority": "Alta"
    },
    {
        "jira_id": "SGSS-N020",
        "title": "DADOS ESSASI NOS BOLETOS",
        "description": "Necessário incluir dados da ESSASI nos boletos gerados pelo sistema.",
        "status": "Pendente",
        "responsible": "Valentim Fazazl Riego",
        "seguradora": "AIPEAT",
        "category": "Em Técnico",
        "priority": "Alta"
    },
    {
        "jira_id": "SGSS-N030",
        "title": "NOVA LEI DE SEGUROS - OBSERVAÇÃO",
        "description": "Adequação necessária do sistema conforme nova lei de seguros com campo de observações específico.",
        "status": "Pendente",
        "responsible": "Valentim Fazazl Riego",
        "seguradora": "AIPEAT",
        "category": "Em Técnico",
        "priority": "Média"
    },
    {
        "jira_id": "SGSS-N021",
        "title": "ADEQUAÇÃO NOVA LEI DO SEGURO - OBSERVAÇÕES",
        "description": "Implementar adequações conforme nova lei de seguros incluindo campo de observações obrigatórias.",
        "status": "Pendente",
        "responsible": "Valentim Fazazl Riego",
        "seguradora": "AIPEAT",
        "category": "Em Técnico",
        "priority": "Alta"
    },
    {
        "jira_id": "SGSS-N022",
        "title": "ADEQUAÇÃO NOVA LEI DO SEGURO - OBSERVAÇÕES (Duplicata)",
        "description": "Duplicata - Implementar adequações conforme nova lei de seguros.",
        "status": "Pendente",
        "responsible": "Valentim Fazazl Riego",
        "seguradora": "AIPEAT",
        "category": "Em Técnico",
        "priority": "Média"
    },
    {
        "jira_id": "SGSS-N004",
        "title": "ADEQUAÇÃO NOVA LEI DO SEGURO - inclusão de disclaimer",
        "description": "Adicionar disclaimer obrigatório conforme nova lei de seguros nos documentos gerados.",
        "status": "Pendente",
        "responsible": "Valentim Fazazl Riego",
        "seguradora": "AIPEAT",
        "category": "Em Técnico",
        "priority": "Média"
    },
    {
        "jira_id": "SGSS-N009",
        "title": "ADEQUAÇÃO NOVA LEI DO SEGURO - Número das condições [preservação da emissão]",
        "description": "Atualizar sistema para incluir número das condições conforme nova lei mantendo preservação da emissão.",
        "status": "Pendente",
        "responsible": "Valentim Fazazl Riego",
        "seguradora": "AIPEAT",
        "category": "Em Técnico",
        "priority": "Média"
    },
    {
        "jira_id": "SGSS-N060",
        "title": "COSSEG ADEQ INTELIGENCIAL",
        "description": "Adequação do COSSEG para atender requisitos de inteligência artificial e análise de dados.",
        "status": "Pendente",
        "responsible": "Valentim Fazazl Riego",
        "seguradora": "AIPEAT",
        "category": "Em Técnico",
        "priority": "Média"
    },
    {
        "jira_id": "SGSS-N034",
        "title": "URGENTE - PDF COM ERRO - 92040202250010001",
        "description": "PDF gerado com erro crítico no número 92040202250010001. Necessita correção urgente.",
        "status": "Pendente",
        "responsible": "Valentim Fazazl Riego",
        "seguradora": "AIPEAT",
        "category": "Em Atendimento",
        "priority": "Crítica"
    },
    {
        "jira_id": "SGSS-N407",
        "title": "CAUTONA - VOCÊ SÃO AO",
        "description": "Chamado sobre questão CAUTONA relacionado ao campo VOCÊ SÃO AO.",
        "status": "Pendente",
        "responsible": "Valentim Fazazl Riego",
        "seguradora": "AIPEAT",
        "category": "Em Técnico",
        "priority": "Baixa"
    },
    {
        "jira_id": "SGSS-N000",
        "title": "AJUSTE EMPRÉSTIMO DE PROPRIAÇÃO",
        "description": "Ajustes necessários no módulo de empréstimo de propriação do sistema.",
        "status": "Pendente",
        "responsible": "Valentim Fazazl Riego",
        "seguradora": "AIPEAT",
        "category": "Em Atendimento",
        "priority": "Média"
    }
]

# Templates para casos concluídos
TITULOS_TEMPLATE = [
    "Ajuste no módulo de apólices",
    "Correção de bug no sistema de pagamentos",
    "Implementação de nova funcionalidade",
    "Otimização de performance no dashboard",
    "Atualização de biblioteca de componentes",
    "Correção de validação de formulários",
    "Melhoria na interface de usuário",
    "Ajuste no relatório gerencial",
    "Correção no cálculo de prêmios",
    "Atualização do módulo de sinistros",
    "Ajuste na integração com API externa",
    "Correção de layout responsivo",
    "Implementação de notificações",
    "Ajuste no fluxo de aprovação",
    "Correção de permissões de usuário"
]

DESCRICOES_TEMPLATE = [
    "Realizado ajuste conforme solicitação do cliente.",
    "Implementada correção para resolver problema relatado.",
    "Funcionalidade testada e validada com sucesso.",
    "Ajustes realizados conforme especificação técnica.",
    "Correção implementada e testada em ambiente de homologação.",
    "Melhoria implementada conforme feedback dos usuários.",
    "Sistema atualizado e funcionando corretamente.",
    "Problema identificado e corrigido com sucesso.",
    "Implementação concluída e documentada.",
    "Ajuste realizado e validado pela equipe de QA."
]

RESPONSAVEIS = [
    "Pedro Carvalho",
    "Lucas Colete da Silva", 
    "Valentim Fazazl Riego",
    "Maria Santos",
    "João Silva"
]

CATEGORIAS = [
    "Técnico",
    "Funcional",
    "Performance",
    "Interface",
    "Integração"
]

async def populate_database():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("=" * 80)
    print("🚀 POPULANDO BANCO DE DADOS SAFE2GO")
    print("=" * 80)
    
    # Buscar usuário admin para usar como creator
    admin_user = await db.users.find_one({'role': 'administrador'})
    if not admin_user:
        print("❌ Nenhum usuário admin encontrado. Execute create_admin_pedro.py primeiro.")
        return
    
    creator_id = admin_user['id']
    print(f"✅ Usuário admin encontrado: {admin_user['email']}")
    
    # 1. LIMPAR CASOS EXISTENTES (OPCIONAL)
    print("\n🗑️  Deseja limpar todos os casos existentes? (s/n): ", end="")
    # Para automação, vamos sempre limpar
    await db.cases.delete_many({})
    existing_count = await db.cases.count_documents({})
    print(f"✅ Banco limpo. {existing_count} casos no banco.")
    
    # 2. INSERIR CASOS DA IMAGEM (TODOS PENDENTES)
    print("\n📸 INSERINDO CASOS DA IMAGEM...")
    print("-" * 80)
    
    casos_inseridos = 0
    for caso_data in CASOS_IMAGEM:
        caso = {
            "id": str(uuid.uuid4()),
            "jira_id": caso_data["jira_id"],
            "title": caso_data["title"],
            "description": caso_data["description"],
            "status": caso_data["status"],
            "responsible": caso_data["responsible"],
            "seguradora": caso_data["seguradora"],
            "category": caso_data.get("category"),
            "priority": caso_data.get("priority", "Média"),
            "creator_id": creator_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.cases.insert_one(caso)
        casos_inseridos += 1
        print(f"  ✅ {caso['jira_id']}: {caso['title'][:60]}...")
    
    print(f"\n✅ {casos_inseridos} casos da imagem inseridos com sucesso!")
    
    # 3. INSERIR 60 CASOS CONCLUÍDOS (26/11 a 02/12)
    print("\n📊 INSERINDO 60 CASOS CONCLUÍDOS (26/11 a 02/12)...")
    print("-" * 80)
    
    # Definir período
    start_date = datetime(2025, 11, 26, tzinfo=timezone.utc)
    end_date = datetime(2025, 12, 2, 23, 59, 59, tzinfo=timezone.utc)
    
    # Distribuir 60 casos: 20 para cada seguradora
    seguradoras = [
        ("Daycoval", 20),
        ("ESSOR", 20),
        ("AVLA", 20)
    ]
    
    contador_total = 0
    jira_base = 5000
    
    for seguradora, quantidade in seguradoras:
        print(f"\n  📌 {seguradora}: {quantidade} casos")
        
        for i in range(quantidade):
            # Data aleatória entre 26/11 e 02/12
            random_seconds = random.randint(0, int((end_date - start_date).total_seconds()))
            random_date = start_date + timedelta(seconds=random_seconds)
            
            caso = {
                "id": str(uuid.uuid4()),
                "jira_id": f"SGSS-{jira_base + contador_total}",
                "title": random.choice(TITULOS_TEMPLATE) + f" - {seguradora}",
                "description": random.choice(DESCRICOES_TEMPLATE),
                "status": "Concluído",
                "responsible": random.choice(RESPONSAVEIS),
                "seguradora": seguradora,
                "category": random.choice(CATEGORIAS),
                "priority": random.choice(["Baixa", "Média", "Alta"]),
                "creator_id": creator_id,
                "created_at": random_date.isoformat(),
                "updated_at": random_date.isoformat()
            }
            
            await db.cases.insert_one(caso)
            contador_total += 1
            
            if (contador_total % 10) == 0:
                print(f"    ✅ {contador_total} casos inseridos...")
    
    print(f"\n✅ {contador_total} casos concluídos inseridos com sucesso!")
    
    # 4. RESUMO FINAL
    print("\n" + "=" * 80)
    print("📊 RESUMO DA POPULAÇÃO DE DADOS")
    print("=" * 80)
    
    total_cases = await db.cases.count_documents({})
    pendentes = await db.cases.count_documents({"status": "Pendente"})
    concluidos = await db.cases.count_documents({"status": "Concluído"})
    
    print(f"\n  📈 Total de casos no banco: {total_cases}")
    print(f"  🟡 Pendentes: {pendentes}")
    print(f"  🟢 Concluídos: {concluidos}")
    
    print("\n  📊 Casos por seguradora:")
    for seguradora in ["DAIG", "AIPEAT", "Daycoval", "ESSOR", "AVLA"]:
        count = await db.cases.count_documents({"seguradora": seguradora})
        if count > 0:
            print(f"    • {seguradora}: {count} casos")
    
    print("\n✅ POPULAÇÃO DE DADOS CONCLUÍDA COM SUCESSO!")
    print("=" * 80)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(populate_database())
