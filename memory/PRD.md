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

### Notas de Resolução (02/02/2026)
- [x] Modal solicita descrição da solução ao concluir caso
- [x] Funciona na página de detalhes do caso (CaseDetails.jsx)
- [x] Funciona no dropdown de status rápido na lista (Cases.jsx)
- [x] Campos salvos: solution, solved_by, solved_by_id
- [x] Seção verde exibe notas na página de detalhes do caso concluído
- [x] Base de conhecimento para resolver problemas similares

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
│       └── test_resolution_notes.py
├── frontend/
│   ├── .env (REACT_APP_BACKEND_URL)
│   └── src/
│       ├── pages/
│       │   ├── Dashboard.jsx
│       │   ├── Cases.jsx (com modal de resolução)
│       │   ├── CaseDetails.jsx (com modal de resolução)
│       │   ├── Settings.jsx
│       │   └── UserManagement.jsx
│       └── components/
└── memory/
    └── PRD.md
```

## Endpoints Principais
- `POST /api/login` - Autenticação
- `GET /api/dashboard/stats` - Estatísticas do dashboard
- `GET /api/cases` - Listar casos
- `GET/PUT /api/cases/{id}` - Detalhes/atualizar caso (aceita campos solution, solved_by, solved_by_id)
- `POST /api/cases/{id}/comments` - Adicionar comentário
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
- [ ] Página de Base de Conhecimento (pesquisa de soluções anteriores)

## Notas Técnicas
- **Jira Project Key**: S2GSS (tickets antigos usam SGSS)
- **Webhook não protegido**: O endpoint `/api/webhooks/jira` precisa de token secreto
- **ObjectId MongoDB**: Sempre excluir `_id` das respostas JSON
