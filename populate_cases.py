#!/usr/bin/env python3
"""
Script para popular o banco de dados com casos do Jira
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime, timezone, timedelta
import uuid
import bcrypt
import re

ROOT_DIR = Path(__file__).parent / 'backend'
load_dotenv(ROOT_DIR / '.env')

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def categorize_case(title: str, description: str) -> tuple:
    """Categoriza o caso e extrai palavras-chave"""
    title_lower = title.lower()
    desc_lower = description.lower()
    combined = f"{title_lower} {desc_lower}"
    
    # Definir categorias
    if 'reprocessamento' in combined or 'reprocessar' in combined:
        category = 'Reprocessamento'
        keywords = ['reprocessamento', 'reprocessar']
    elif 'erro corretor' in combined:
        category = 'Erro Corretor'
        keywords = ['erro', 'corretor']
    elif 'nova lei' in combined or 'adequação' in combined:
        category = 'Adequação Nova Lei'
        keywords = ['nova lei', 'adequação', 'obrigatoriedade']
    elif 'sumiço' in combined or 'sumiu' in combined:
        category = 'Sumiço de Dados'
        keywords = ['sumiço', 'desapareceu', 'perdido']
    elif 'boleto' in combined:
        category = 'Erro Boleto'
        keywords = ['boleto', 'pagamento']
    elif 'endosso' in combined:
        category = 'Problema Endosso'
        keywords = ['endosso']
    elif 'pdf' in combined or 'relatório' in combined:
        category = 'Problema Documento'
        keywords = ['pdf', 'relatório', 'documento']
    elif 'emissão' in combined:
        category = 'Erro Emissão'
        keywords = ['emissão', 'emitir']
    elif 'cobertura' in combined:
        category = 'Cobertura'
        keywords = ['cobertura']
    elif 'usuário' in combined or 'usuario' in combined:
        category = 'Gestão Usuário'
        keywords = ['usuário', 'acesso']
    else:
        category = 'Outros'
        keywords = []
    
    # Adicionar seguradora como keyword se encontrada
    if 'avla' in combined:
        keywords.append('avla')
    if 'essor' in combined:
        keywords.append('essor')
    if 'daycoval' in combined:
        keywords.append('daycoval')
    
    # Adicionar urgente como keyword
    if 'urgente' in combined:
        keywords.append('urgente')
    
    return category, keywords

def extract_seguradora(responsible: str) -> str:
    """Extrai seguradora do nome do responsável"""
    resp_upper = responsible.upper()
    if 'AVLA' in resp_upper:
        return 'AVLA'
    elif 'ESSOR' in resp_upper:
        return 'ESSOR'
    elif 'DAYCOVAL' in resp_upper:
        return 'DAYCOVAL'
    return None

def parse_date(date_str: str) -> datetime:
    """Converte string de data para datetime"""
    try:
        # Formato: 25/11/2025
        day, month, year = date_str.split('/')
        return datetime(int(year), int(month), int(day), tzinfo=timezone.utc)
    except:
        return datetime.now(timezone.utc)

async def populate_database():
    print("🚀 Iniciando população do banco de dados...\n")
    
    # Conectar ao MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # 1. Criar usuário Pedro Carvalho
    print("👤 Criando usuário Pedro Carvalho...")
    user_id = str(uuid.uuid4())
    user_doc = {
        'id': user_id,
        'name': 'Pedro Carvalho',
        'email': 'pedro.carvalho@safe2go.com.br',
        'password': hash_password('S@muka91'),
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    # Verificar se usuário já existe
    existing_user = await db.users.find_one({'email': user_doc['email']})
    if existing_user:
        print("  ⚠️  Usuário já existe, pulando...")
        user_id = existing_user['id']
    else:
        await db.users.insert_one(user_doc)
        print("  ✅ Usuário criado com sucesso!")
    
    # 2. Preparar casos
    print("\n📋 Preparando casos para inserção...")
    
    cases_data = [
        {
            'jira_id': 'S2GSS-7672',
            'title': 'RELATÓRIO POR MOTIVO',
            'description': 'Solicitação de relatório filtrado por motivo',
            'responsible': 'Mauro ESSOR',
            'status': 'Concluído',
            'opened_date': '25/11/2025'
        },
        {
            'jira_id': 'S2GSS-10696',
            'title': 'Reativar cotação 10149020255100132883',
            'description': 'Solicitação para reativar cotação específica',
            'responsible': 'Pedro ESSOR',
            'status': 'Concluído',
            'opened_date': '25/11/2025'
        },
        {
            'jira_id': 'S2GSS-10695',
            'title': 'Erro corretor',
            'description': 'Sistema de corretor apresentando erro',
            'responsible': 'Pedro AVLA',
            'status': 'Concluído',
            'opened_date': '25/11/2025'
        },
        {
            'jira_id': 'S2GSS-10694',
            'title': 'Reprocessamento AVLA',
            'description': 'Necessidade de reprocessar dados da AVLA',
            'responsible': 'Pedro AVLA',
            'status': 'Concluído',
            'opened_date': '25/11/2025'
        },
        {
            'jira_id': 'S2GSS-10693',
            'title': 'Reprocessamento AVLA',
            'description': 'Necessidade de reprocessar dados da AVLA',
            'responsible': 'Pedro AVLA',
            'status': 'Concluído',
            'opened_date': '25/11/2025'
        },
        {
            'jira_id': 'S2GSS-10692',
            'title': 'Erro na pagina ADM',
            'description': 'Página administrativa apresentando erro',
            'responsible': 'Pedro ESSOR',
            'status': 'Concluído',
            'opened_date': '25/11/2025'
        },
        {
            'jira_id': 'S2GSS-10691',
            'title': 'Erro no cálculo das coberturas',
            'description': 'Sistema calculando coberturas incorretamente',
            'responsible': 'Pedro ESSOR',
            'status': 'Concluído',
            'opened_date': '25/11/2025'
        },
        {
            'jira_id': 'S2GSS-10690',
            'title': 'Reprocessamento AVLA',
            'description': 'Necessidade de reprocessar dados da AVLA',
            'responsible': 'Pedro AVLA',
            'status': 'Concluído',
            'opened_date': '25/11/2025'
        },
        {
            'jira_id': 'S2GSS-10689',
            'title': 'Erro corretor',
            'description': 'Sistema de corretor apresentando erro',
            'responsible': 'Pedro AVLA',
            'status': 'Concluído',
            'opened_date': '25/11/2025'
        },
        {
            'jira_id': 'S2GSS-10688',
            'title': 'Reprocessamento AVLA',
            'description': 'Necessidade de reprocessar dados da AVLA',
            'responsible': 'Pedro AVLA',
            'status': 'Concluído',
            'opened_date': '24/11/2025'
        },
        {
            'jira_id': 'S2GSS-10684',
            'title': 'Reprocessamento AVLA',
            'description': 'Necessidade de reprocessar dados da AVLA',
            'responsible': 'Pedro AVLA',
            'status': 'Concluído',
            'opened_date': '24/11/2025'
        },
        {
            'jira_id': 'S2GSS-10685',
            'title': 'Reprocessamento AVLA',
            'description': 'Necessidade de reprocessar dados da AVLA',
            'responsible': 'Pedro DAYCOVAL',
            'status': 'Concluído',
            'opened_date': '24/11/2025'
        },
        {
            'jira_id': 'S2GSS-10686',
            'title': 'Reprocessamento AVLA',
            'description': 'Necessidade de reprocessar dados da AVLA',
            'responsible': 'Pedro ESSOR',
            'status': 'Concluído',
            'opened_date': '24/11/2025'
        },
        {
            'jira_id': 'S2GSS-10687',
            'title': 'Reprocessamento AVLA',
            'description': 'Necessidade de reprocessar dados da AVLA',
            'responsible': 'Pedro AVLA',
            'status': 'Concluído',
            'opened_date': '24/11/2025'
        },
        {
            'jira_id': 'S2GSS-10683',
            'title': 'Solicitação do Nicolas/ reprocessar cotação',
            'description': 'Reprocessamento de cotação solicitado por Nicolas',
            'responsible': 'Pedro DAYCOVAL',
            'status': 'Concluído',
            'opened_date': '24/11/2025'
        },
        {
            'jira_id': 'S2GSS-10681',
            'title': 'Reprocessar Apólice erro corretor',
            'description': 'Apólice precisa ser reprocessada devido a erro do corretor',
            'responsible': 'Pedro AVLA',
            'status': 'Concluído',
            'opened_date': '24/11/2025'
        },
        {
            'jira_id': 'S2GSS-10613',
            'title': 'Alterações RD Eventos- Nova Lei',
            'description': 'Alterações necessárias em RD Eventos conforme nova lei',
            'responsible': 'Equipe Legal DAYCOVAL',
            'status': 'Aguardando resposta do cliente',
            'opened_date': '21/11/2025'
        },
        {
            'jira_id': 'S2GSS-10610',
            'title': 'Alteração/Inclusão Cobertura - Nova Lei (Urgente/Obrigatoriedade)',
            'description': 'Alteração e inclusão de cobertura conforme nova lei - urgente e obrigatório',
            'responsible': 'Equipe Legal ESSOR',
            'status': 'Aguardando resposta do cliente',
            'opened_date': '21/11/2025'
        },
        {
            'jira_id': 'S2GSS-10512',
            'title': 'ENCONTRAR APÓLICE - E A COMUNICAÇÃO LTDA',
            'description': 'Localização de apólice específica da empresa E A Comunicação LTDA',
            'responsible': 'Equipe Suporte AVLA',
            'status': 'Pendente',
            'opened_date': '21/11/2025'
        },
        {
            'jira_id': 'S2GSS-8419',
            'title': 'complemento solicitação S2GSS-7695',
            'description': 'Complemento da solicitação anterior S2GSS-7695',
            'responsible': 'Equipe Suporte DAYCOVAL',
            'status': 'Aguardando resposta do cliente',
            'opened_date': '21/11/2025'
        },
        {
            'jira_id': 'S2GSS-5732',
            'title': 'NOVO USUARIO APENAS PARA COTAÇÕES DE PARCERIA COM A FACILITYDOC - MENTOR SEGUROS',
            'description': 'Criação de novo usuário exclusivo para cotações em parceria com FacilityDoc - Mentor Seguros',
            'responsible': 'Equipe Comercial ESSOR',
            'status': 'Concluído',
            'opened_date': '21/11/2025'
        },
        {
            'jira_id': 'S2GSS-9650',
            'title': 'AJUSTE ENDOSSO DE PRORROGAÇÃO',
            'description': 'Ajustes necessários no endosso de prorrogação',
            'responsible': 'Equipe Dev AVLA',
            'status': 'Pendente',
            'opened_date': '21/11/2025'
        },
        {
            'jira_id': 'S2GSS-10437',
            'title': 'CAIXINHA - VOCÊ SABIA?',
            'description': 'Implementação da funcionalidade Você Sabia',
            'responsible': 'Equipe Produto DAYCOVAL',
            'status': 'Pendente',
            'opened_date': '21/11/2025'
        },
        {
            'jira_id': 'S2GSS-10467',
            'title': 'OCULTAR COBERTURAS',
            'description': 'Necessidade de ocultar coberturas específicas',
            'responsible': 'Equipe Dev ESSOR',
            'status': 'Concluído',
            'opened_date': '21/11/2025'
        },
        {
            'jira_id': 'S2GSS-10489',
            'title': 'URGENTE - ERRO BOLETO E PAGAMENTO - 10149020255100125952',
            'description': 'Erro no processamento de boleto e pagamento',
            'responsible': 'Mauro ESSOR',
            'status': 'Concluído',
            'opened_date': '21/11/2025'
        },
        {
            'jira_id': 'S2GSS-10499',
            'title': 'URGENTE - ERRO COTAÇÕES - DUPLICAÇÃO DE OBSERVAÇÕES',
            'description': 'Sistema duplicando observações nas cotações',
            'responsible': 'Equipe Dev ESSOR',
            'status': 'Pendente',
            'opened_date': '21/11/2025'
        },
        {
            'jira_id': 'S2GSS-10501',
            'title': 'VERIFICAÇÃO ENDOSSO - 10149020255100128739',
            'description': 'Verificação de endosso específico',
            'responsible': 'Pedro ESSOR',
            'status': 'Concluído',
            'opened_date': '21/11/2025'
        },
        {
            'jira_id': 'S2GSS-10502',
            'title': 'URGENTE - SUMIÇO ENDOSSO - 10149020255100128732 - CCM',
            'description': 'Endosso CCM desapareceu do sistema',
            'responsible': 'Equipe Suporte ESSOR',
            'status': 'Concluído',
            'opened_date': '21/11/2025'
        },
        {
            'jira_id': 'S2GSS-10504',
            'title': 'URGENTE - ENDOSSO SEM BOLETO - 1005103026804',
            'description': 'Endosso criado mas boleto não foi gerado',
            'responsible': 'Mauro ESSOR',
            'status': 'Concluído',
            'opened_date': '21/11/2025'
        },
        {
            'jira_id': 'S2GSS-10524',
            'title': 'URGENTE - PDF COM ERRO - 10149020255100130003',
            'description': 'PDF gerado com erro',
            'responsible': 'Equipe Dev ESSOR',
            'status': 'Pendente',
            'opened_date': '21/11/2025'
        },
        {
            'jira_id': 'S2GSS-10660',
            'title': 'COSSEGURADO INTERNACIONAL',
            'description': 'Questões relacionadas a cossegurado internacional',
            'responsible': 'Equipe Legal ESSOR',
            'status': 'Aguardando resposta do cliente',
            'opened_date': '21/11/2025'
        },
        {
            'jira_id': 'S2GSS-10662',
            'title': 'URGENTE - ERRO - SEM DESCRIÇÃO DO EVENTO',
            'description': 'Sistema não mostra descrição do evento',
            'responsible': 'Equipe Dev ESSOR',
            'status': 'Concluído',
            'opened_date': '21/11/2025'
        },
        {
            'jira_id': 'S2GSS-10665',
            'title': 'URGENTE - ERRO EMISSÃO - 10149020255100132190',
            'description': 'Erro ao emitir apólice',
            'responsible': 'Mauro ESSOR',
            'status': 'Concluído',
            'opened_date': '21/11/2025'
        },
        {
            'jira_id': 'S2GSS-10668',
            'title': 'ADEQUAÇÃO NOVA LEI DO SEGURO - Numero das cotações | preservação de cotação',
            'description': 'Adequação de numeração e preservação de cotações conforme nova lei',
            'responsible': 'Equipe Dev ESSOR',
            'status': 'Pendente',
            'opened_date': '21/11/2025'
        },
        {
            'jira_id': 'S2GSS-10669',
            'title': 'ADEQUAÇÃO NOVA LEI DO SEGURO - inclusão de disclaimer',
            'description': 'Inclusão de disclaimer conforme nova lei',
            'responsible': 'Equipe Legal ESSOR',
            'status': 'Pendente',
            'opened_date': '21/11/2025'
        },
        {
            'jira_id': 'S2GSS-10670',
            'title': 'ADEQUAÇÃO NOVA LEI DO SEGURO - OBSERVAÇÕES',
            'description': 'Observações sobre adequação à nova lei',
            'responsible': 'Equipe Legal ESSOR',
            'status': 'Pendente',
            'opened_date': '21/11/2025'
        },
        {
            'jira_id': 'S2GSS-10671',
            'title': 'ADEQUAÇÃO NOVA LEI DO SEGURO - OBSERVAÇÕES',
            'description': 'Mais observações sobre adequação à nova lei de seguros',
            'responsible': 'Equipe Legal ESSOR',
            'status': 'Pendente',
            'opened_date': '21/11/2025'
        },
        {
            'jira_id': 'S2GSS-10673',
            'title': 'ERRO SISTEMA CORRETOR - PAGAMENTO',
            'description': 'Sistema de corretor com erro no processamento de pagamento',
            'responsible': 'Mauro ESSOR',
            'status': 'Concluído',
            'opened_date': '21/11/2025'
        },
        {
            'jira_id': 'S2GSS-10676',
            'title': 'URGENTE - SUMIÇO ENDOSSO - 1005103025254',
            'description': 'Endosso desapareceu do sistema',
            'responsible': 'Mauro ESSOR',
            'status': 'Concluído',
            'opened_date': '21/11/2025'
        },
        {
            'jira_id': 'S2GSS-10678',
            'title': 'NOVA LEI DE SEGUROS - OBSERVAÇÃO',
            'description': 'Observações sobre adequação à nova lei de seguros',
            'responsible': 'Equipe Legal ESSOR',
            'status': 'Pendente',
            'opened_date': '21/11/2025'
        },
        {
            'jira_id': 'S2GSS-10679',
            'title': 'urgente - facility abrape',
            'description': 'Questões urgentes relacionadas ao facility Abrape',
            'responsible': 'Mauro ESSOR',
            'status': 'Concluído',
            'opened_date': '21/11/2025'
        },
        {
            'jira_id': 'S2GSS-10680',
            'title': 'URGENTE - ERRO PRORROGAÇÕES DE BOLETOS',
            'description': 'Sistema com erro ao processar prorrogações de boletos',
            'responsible': 'Mauro ESSOR',
            'status': 'Concluído',
            'opened_date': '21/11/2025'
        },
        {
            'jira_id': 'S2GSS-10666',
            'title': 'Alteração/Inclusão Cobertura - Nova Lei (Urgente/Obrigatoriedade) - RC EVENTOS',
            'description': 'Alteração de cobertura conforme nova lei para RC Eventos',
            'responsible': 'Equipe Legal ESSOR',
            'status': 'Aguardando resposta do cliente',
            'opened_date': '21/11/2025'
        },
        {
            'jira_id': 'S2GSS-10509',
            'title': 'Adequação da Nova Marca - SAFE2GO - White Label',
            'description': 'Adequação da marca Safe2Go no sistema White Label',
            'responsible': 'Equipe Dev DAYCOVAL',
            'status': 'Pendente',
            'opened_date': '21/11/2025'
        },
        {
            'jira_id': 'S2GSS-10682',
            'title': 'Reprocessamento AVLA',
            'description': 'Necessidade de reprocessar dados da AVLA',
            'responsible': 'Pedro AVLA',
            'status': 'Concluído',
            'opened_date': '24/11/2025'
        },
        {
            'jira_id': 'S2GSS-10697',
            'title': 'Erro corretor - Sistema travado',
            'description': 'Sistema de corretor travando durante uso',
            'responsible': 'Pedro AVLA',
            'status': 'Concluído',
            'opened_date': '25/11/2025'
        },
    ]
    
    print(f"  📊 Total de casos a inserir: {len(cases_data)}")
    
    # 3. Processar e inserir casos
    print("\n💾 Inserindo casos no banco de dados...")
    inserted_count = 0
    skipped_count = 0
    
    for case_data in cases_data:
        # Verificar se caso já existe
        existing = await db.cases.find_one({'jira_id': case_data['jira_id']})
        if existing:
            skipped_count += 1
            continue
        
        # Extrair seguradora
        seguradora = extract_seguradora(case_data['responsible'])
        
        # Categorizar e extrair keywords
        category, keywords = categorize_case(case_data['title'], case_data['description'])
        
        # Criar documento
        case_doc = {
            'id': str(uuid.uuid4()),
            'jira_id': case_data['jira_id'],
            'title': case_data['title'],
            'description': case_data['description'],
            'responsible': case_data['responsible'],
            'status': case_data['status'],
            'seguradora': seguradora,
            'category': category,
            'keywords': keywords,
            'opened_date': parse_date(case_data['opened_date']).isoformat(),
            'closed_date': datetime.now(timezone.utc).isoformat() if case_data['status'] == 'Concluído' else None,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        await db.cases.insert_one(case_doc)
        inserted_count += 1
        
        if inserted_count % 10 == 0:
            print(f"  ✅ {inserted_count} casos inseridos...")
    
    print(f"\n✅ Inserção concluída!")
    print(f"  - Casos inseridos: {inserted_count}")
    print(f"  - Casos pulados (já existentes): {skipped_count}")
    
    # 4. Estatísticas
    print("\n📊 ESTATÍSTICAS FINAIS:")
    total_cases = await db.cases.count_documents({})
    print(f"  - Total de casos no banco: {total_cases}")
    
    # Contar por categoria
    pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    categories = await db.cases.aggregate(pipeline).to_list(100)
    
    print("\n  📋 Casos por categoria:")
    for cat in categories:
        print(f"    • {cat['_id']}: {cat['count']} casos")
    
    # Contar por seguradora
    pipeline_seg = [
        {"$group": {"_id": "$seguradora", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    seguradoras = await db.cases.aggregate(pipeline_seg).to_list(100)
    
    print("\n  🏢 Casos por seguradora:")
    for seg in seguradoras:
        seg_name = seg['_id'] if seg['_id'] else 'Não especificada'
        print(f"    • {seg_name}: {seg['count']} casos")
    
    print("\n✅ POPULAÇÃO DO BANCO DE DADOS CONCLUÍDA COM SUCESSO!")
    print(f"\n🔐 Credenciais de acesso:")
    print(f"  Email: pedro.carvalho@safe2go.com.br")
    print(f"  Senha: S@muka91")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(populate_database())
