# Safe2Go Helpdesk - Product Requirements Document

## Descrição do Produto
Sistema de gerenciamento de helpdesk para a Safe2Go, permitindo gestão de casos/tickets de suporte, integração bidirecional com Jira, e gestão de usuários.

## Stack Tecnológico
- **Frontend**: React, Tailwind CSS, Radix UI, Recharts, Axios
- **Backend**: FastAPI (Python), Pydantic, python-jose (JWT), bcrypt
- **Banco de Dados**: MongoDB
- **Integrações**: Jira REST API e Webhooks

## Funcionalidades Implementadas

### Core
- [x] Autenticação de usuários (login/registro)
- [x] Dashboard com estatísticas e gráficos
- [x] Gestão de casos (CRUD completo)
- [x] Sistema de comentários nos casos
- [x] Gestão de usuários (admin)

### Dashboard
- [x] Cards de estatísticas (total, pendentes, em desenvolvimento, etc.)
- [x] Card "Aguardando Configuração"
- [x] Filtro por período de datas
- [x] Filtros de status nos gráficos
- [x] Gráfico expandido com toggle mensal/semanal

### Integração Jira
- [x] Criação de tickets no Jira
- [x] Sincronização bidirecional de comentários
- [x] Webhook para receber atualizações do Jira
- [x] Mapeamento de status normalizado (case-insensitive, remove pontos)

### Base de Conhecimento (02/02/2026)
- [x] Nova página "Base de Conhecimento" no menu lateral
- [x] Busca por palavras-chave (boleto, endosso, corretor, etc.)
- [x] Filtros por categoria e seguradora
- [x] Cards expansíveis com problema e solução
- [x] Modal de resolução com campo de título obrigatório
- [x] Campos: solution, solution_title, solved_by, solved_by_id, solved_at
- [x] Estatísticas por categoria
- [x] **Sugestão de casos similares** na página de detalhes do chamado
- [x] Algoritmo de similaridade (categoria, seguradora, palavras-chave)
- [x] Cards expansíveis mostrando a solução aplicada em casos parecidos

### Outras
- [x] Página de Configurações (Perfil, Segurança, Notificações)
- [x] Criação de usuários pelo admin
- [x] Exportação de relatórios

## Arquitetura de Arquivos
```
/app
├── backend/
│   ├── .env (MONGO_URL, JIRA credentials)
│   ├── server.py (FastAPI app)
│   └── tests/
├── frontend/
│   ├── .env (REACT_APP_BACKEND_URL)
│   └── src/
│       ├── pages/
│       │   ├── Dashboard.jsx
│       │   ├── Cases.jsx (com modal de resolução com título)
│       │   ├── CaseDetails.jsx (com modal de resolução com título)
│       │   ├── KnowledgeBase.jsx (NOVO)
│       │   ├── Settings.jsx
│       │   └── UserManagement.jsx
│       └── components/
│           └── Layout.jsx (menu com Base de Conhecimento)
└── memory/
    └── PRD.md
```

## Endpoints Principais
- `POST /api/auth/login` - Autenticação
- `GET /api/dashboard/stats` - Estatísticas do dashboard
- `GET /api/cases` - Listar casos
- `GET/PUT /api/cases/{id}` - Detalhes/atualizar caso
- `POST /api/cases/{id}/comments` - Adicionar comentário
- `GET /api/knowledge-base` - Buscar notas de resolução
- `GET /api/knowledge-base/stats` - Estatísticas da base
- `POST /api/users/create` - Criar usuário (admin)
- `POST /api/webhooks/jira` - Webhook do Jira

## Credenciais de Teste
- **Admin**: pedrohcarvalho1997@gmail.com / S@muka91

## Backlog Priorizado

### P0 (Alta Prioridade)
- [ ] Proteger Webhook do Jira com token secreto

### P1 (Média Prioridade)
- [ ] Paginação na lista de casos
- [ ] Notificações por email

### P2 (Baixa Prioridade)
- [ ] Anexos de arquivos nos casos
- [ ] Rastreamento de SLA
- [ ] Modo escuro

## Notas Técnicas
- **Jira Project Key**: S2GSS (tickets antigos usam SGSS)
- **Webhook URL**: https://helpdesk-portal-30.preview.emergentagent.com/api/webhooks/jira
- **Mapeamento de Status**: Normalizado (lowercase, sem pontos) para evitar erros
- **ObjectId MongoDB**: Sempre excluir `_id` das respostas JSON
