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

### Rastreamento de Tempo (02/02/2026)
- [x] Campo `status_history` para registrar mudanças de status
- [x] Seção "Tempo do Caso" na página de detalhes (recolhível)
- [x] Tempo total desde abertura
- [x] Tempo em cada status
- [x] Histórico com linha do tempo (quem alterou, quando)
- [x] Endpoint `/api/cases/{id}/time-metrics` para métricas individuais
- [x] Endpoint `/api/reports/time-metrics` para relatório agregado
- [x] PDF com página de "Métricas de Tempo"
- [x] **Nova página "Relatório de Tempo"** no menu lateral
  - Filtros: data, seguradora, categoria
  - Cards: casos analisados, tempo médio, mais rápido, mais lento
  - Gráfico: Tempo médio por status
  - Gráfico: Distribuição por faixa de tempo
  - Tabela detalhada com todos os casos
  - Exportar para Excel/CSV
  - Paginação

### Paginação na Lista de Casos (Dezembro/2025)
- [x] Controles de paginação no topo (contador, seletor de itens por página)
- [x] Controles de paginação no rodapé (números de página, Primeira/Última)
- [x] Navegação entre páginas (Anterior/Próxima)
- [x] Seletor de itens por página (5, 10, 20, 50)
- [x] Backend: `GET /api/cases?page=X&per_page=Y` retorna paginação

### Anexos de Arquivos (Dezembro/2025)
- [x] Seção "Anexos" na página de detalhes do caso (recolhível)
- [x] Upload de arquivos (drag-and-drop, limite 10MB)
- [x] Download de arquivos anexados
- [x] Exclusão de anexos (admin)
- [x] Validação de tipos de arquivo
- [x] Exibição de anexos nos comentários
- [x] Backend: `POST /api/cases/{id}/attachments` para upload
- [x] Backend: `DELETE /api/cases/{id}/attachments/{att_id}` para remover
- [x] Arquivos servidos via `/api/uploads/`

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
│   ├── uploads/ (arquivos anexados)
│   └── tests/
├── frontend/
│   ├── .env (REACT_APP_BACKEND_URL)
│   └── src/
│       ├── pages/
│       │   ├── Dashboard.jsx
│       │   ├── Cases.jsx (com paginação e modal de resolução)
│       │   ├── CaseDetails.jsx (com anexos e modal de resolução)
│       │   ├── KnowledgeBase.jsx
│       │   ├── TimeReport.jsx
│       │   ├── Settings.jsx
│       │   └── UserManagement.jsx
│       └── components/
│           └── Layout.jsx
└── memory/
    └── PRD.md
```

## Endpoints Principais
- `POST /api/auth/login` - Autenticação
- `GET /api/dashboard/stats` - Estatísticas do dashboard
- `GET /api/cases` - Listar casos (suporta ?page=X&per_page=Y)
- `GET/PUT /api/cases/{id}` - Detalhes/atualizar caso
- `GET /api/cases/{id}/similar` - Buscar casos similares resolvidos
- `POST /api/cases/{id}/attachments` - Upload de anexo
- `DELETE /api/cases/{id}/attachments/{att_id}` - Remover anexo
- `POST /api/cases/{id}/comments` - Adicionar comentário
- `GET /api/knowledge-base` - Buscar notas de resolução
- `GET /api/knowledge-base/stats` - Estatísticas da base
- `GET /api/reports/time-metrics` - Relatório de tempo
- `POST /api/users/create` - Criar usuário (admin)
- `POST /api/webhooks/jira` - Webhook do Jira

## Credenciais de Teste
- **Admin**: pedrohcarvalho1997@gmail.com / S@muka91

## Backlog Priorizado

### P0 (Alta Prioridade)
- [ ] Proteger Webhook do Jira com token secreto

### P1 (Média Prioridade)
- [ ] Notificações por email

### P2 (Baixa Prioridade)
- [ ] Rastreamento de SLA
- [ ] Modo escuro
- [ ] Melhorias na busca da Base de Conhecimento (tags automáticas)

## Notas Técnicas
- **Jira Project Key**: S2GSS (tickets antigos usam SGSS)
- **Webhook URL**: https://s2g-ticketing.preview.emergentagent.com/api/webhooks/jira
- **Mapeamento de Status**: Normalizado (lowercase, sem pontos) para evitar erros
- **ObjectId MongoDB**: Sempre excluir `_id` das respostas JSON
- **Uploads**: Arquivos servidos via `/api/uploads/`, armazenados em `/app/backend/uploads/`
