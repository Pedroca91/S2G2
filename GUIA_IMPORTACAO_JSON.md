# 📥 Guia de Importação de Casos via JSON

## ✅ Correções Implementadas

### Problema Original
O sistema estava identificando arquivos JSON como imagens e tentando processar via OCR, resultando no erro:
> "Nenhum chamado identificado na imagem. Tente uma imagem mais clara ou use JSON"

### Solução Aplicada
1. **Verificação de extensão priorizada**: Agora o sistema verifica primeiro a extensão `.json` antes de checar o MIME type
2. **Logs de debug**: Adicionados logs no console para facilitar diagnóstico
3. **Mensagens de erro melhoradas**: Mensagens mais claras sobre o formato esperado
4. **Validação aprimorada**: Verifica se o arquivo tem a estrutura correta antes de processar

---

## 📄 Formato do Arquivo JSON

O arquivo JSON deve seguir esta estrutura:

```json
{
  "export_date": "2025-12-02T15:30:00",
  "total_cases": 11,
  "cases": [
    {
      "jira_id": "SGSS-N012",
      "title": "Título do chamado",
      "description": "Descrição detalhada do problema",
      "status": "Pendente",
      "responsible": "Nome do Responsável",
      "seguradora": "Nome da Seguradora",
      "category": "Categoria",
      "priority": "Alta"
    }
  ]
}
```

### Campos Obrigatórios
- ✅ `cases`: Array contendo os chamados (obrigatório)
- ✅ `jira_id`: ID único do chamado (obrigatório)
- ✅ `title`: Título do chamado (obrigatório)

### Campos Opcionais
- `description`: Descrição detalhada
- `status`: Pendente | Em Desenvolvimento | Aguardando resposta do cliente | Concluído
- `responsible`: Nome do responsável
- `seguradora`: Nome da seguradora (AVLA, ESSOR, DAYCOVAL, etc)
- `category`: Categoria do chamado
- `priority`: Baixa | Média | Alta | Crítica
- `export_date`: Data da exportação
- `total_cases`: Total de casos no arquivo

---

## 🚀 Como Usar

### 1. Preparar o Arquivo JSON
- Certifique-se que o arquivo tem extensão `.json`
- Valide o JSON em um validador online (jsonlint.com)
- Use o arquivo de exemplo em `/app/exemplo_importacao.json`

### 2. Importar no Sistema
1. Faça login como **administrador** (função de import é admin-only)
2. Vá para a página **Chamados**
3. Clique no botão **"Importar"** (ícone de upload)
4. Selecione seu arquivo `.json`
5. Aguarde a mensagem de confirmação

### 3. Resultado
O sistema irá:
- ✅ Verificar duplicados por `jira_id`
- ✅ Criar apenas casos novos
- ✅ Mostrar quantos foram importados e quantos foram ignorados
- ✅ Recarregar a lista automaticamente

---

## 🔍 Troubleshooting

### Erro: "Arquivo JSON inválido"
**Causa**: Estrutura do JSON não está correta
**Solução**: 
- Verifique se existe a propriedade `cases`
- Verifique se `cases` é um array
- Use um validador de JSON

### Erro: "Nenhum chamado encontrado"
**Causa**: Array `cases` está vazio
**Solução**: Adicione pelo menos um chamado no array

### Erro: "Erro ao processar JSON"
**Causa**: JSON mal formatado (syntax error)
**Solução**: 
- Remova vírgulas extras
- Verifique aspas e colchetes
- Use um formatador de JSON

### Casos não aparecem após importar
**Causa**: Todos os `jira_id` já existem no sistema
**Solução**: 
- Use `jira_id` únicos
- Ou delete os casos existentes antes de reimportar

---

## 📊 Arquivo de Exemplo

Um arquivo de exemplo com 11 casos está disponível em:
```
/app/exemplo_importacao.json
```

Para baixar e usar:
1. Abra o arquivo
2. Copie o conteúdo
3. Cole em um novo arquivo `.json` no seu computador
4. Importe no sistema

---

## 💡 Dicas Importantes

1. **Sempre use extensão .json**: Não renomeie arquivos .txt para .json
2. **Valide antes de importar**: Use jsonlint.com ou similar
3. **IDs únicos**: Cada `jira_id` deve ser único
4. **Backup**: Use a função "Exportar Todos" antes de importações grandes
5. **Teste com poucos casos primeiro**: Importe 2-3 casos de teste antes de importar muitos

---

## 🎯 Status Válidos

- `Pendente` (padrão)
- `Em Desenvolvimento`
- `Aguardando resposta do cliente`
- `Concluído`

---

## 📧 Suporte

Se encontrar problemas:
1. Verifique o console do navegador (F12)
2. Veja os logs detalhados
3. Verifique se é administrador
4. Tente com o arquivo de exemplo primeiro
