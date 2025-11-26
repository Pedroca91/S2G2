# 🔗 Navegação por Seguradora - Dashboard → Casos

## ✅ Funcionalidade Implementada

### **O que foi adicionado:**

Agora você pode clicar na quantidade de casos de cada seguradora no Dashboard e ser redirecionado automaticamente para a página de Casos com o filtro já aplicado.

---

## 🎯 **Como Usar**

### **1. No Dashboard**

Na seção **"Casos por Seguradora"**, você verá cards como:

```
┌─────────────────────────────┐
│  AVLA                    → │
│  13 casos                   │
└─────────────────────────────┘

┌─────────────────────────────┐
│  ESSOR                   → │
│  27 casos                   │
└─────────────────────────────┘

┌─────────────────────────────┐
│  DAYCOVAL                → │
│  6 casos                    │
└─────────────────────────────┘
```

### **2. Clique em Qualquer Card**

- Card tem **efeito hover** (aumenta levemente ao passar o mouse)
- **Seta →** indica que é clicável
- Tooltip: "Clique para ver todos os casos da [SEGURADORA]"

### **3. Redirecionamento Automático**

Ao clicar, você será levado para:
```
/cases?seguradora=AVLA
```

A página de Casos irá:
- ✅ Aplicar filtro automaticamente
- ✅ Mostrar toast: "📊 Mostrando casos da AVLA"
- ✅ Exibir banner de filtro ativo
- ✅ Mostrar apenas casos daquela seguradora

---

## 📊 **Interface na Página de Casos**

### **Banner de Filtro Ativo**

Quando filtrado por seguradora, aparece um banner roxo:

```
┌─────────────────────────────────────────────────┐
│ 📊 Filtrando por: AVLA  (13 casos)             │
│                         [Limpar Filtro] ───────┤
└─────────────────────────────────────────────────┘
```

### **Novo Filtro de Seguradora**

Adicionado um 4º filtro na página de Casos:

```
┌────────┬─────────┬────────────┬────────────┐
│ Buscar │ Status  │ Responsável│ Seguradora │
└────────┴─────────┴────────────┴────────────┘
```

**Opções:**
- Todas
- AVLA
- ESSOR
- DAYCOVAL

---

## 🎨 **Melhorias Visuais**

### **Cards Interativos no Dashboard**

**Antes:**
```
AVLA
13
```

**Depois:**
```
┌─────────────────────────────┐
│  AVLA              ╭───╮   │
│  13 casos          │ → │   │  ← Hover: aumenta e adiciona sombra
│                    ╰───╯   │
└─────────────────────────────┘
```

**Características:**
- Cursor pointer (mão)
- Hover: `scale-105` (aumenta 5%)
- Hover: `shadow-lg` (sombra maior)
- Transição suave (200ms)
- Círculo roxo com seta →

---

## 🔄 **Fluxo Completo**

```
1. Usuário no Dashboard
   ↓
2. Vê "AVLA: 13 casos"
   ↓
3. Clica no card da AVLA
   ↓
4. Navegação para /cases?seguradora=AVLA
   ↓
5. Página de Casos detecta parâmetro na URL
   ↓
6. Aplica filtro automaticamente
   ↓
7. Toast: "📊 Mostrando casos da AVLA"
   ↓
8. Banner de filtro ativo aparece
   ↓
9. Mostra apenas 13 casos da AVLA
```

---

## 🛠️ **Implementação Técnica**

### **Dashboard.jsx**

```javascript
// Card clicável
<div 
  onClick={() => navigate(`/cases?seguradora=${seguradora}`)}
  className="cursor-pointer hover:scale-105 transition-all"
>
  <p>{seguradora}</p>
  <p>{count} casos</p>
  <span>→</span>
</div>
```

### **Cases.jsx**

#### **1. Captura parâmetro da URL:**
```javascript
useEffect(() => {
  const seguradoraFromUrl = searchParams.get('seguradora');
  if (seguradoraFromUrl) {
    setSeguradoraFilter(seguradoraFromUrl);
    toast.success(`📊 Mostrando casos da ${seguradoraFromUrl}`);
  }
}, []);
```

#### **2. Aplica filtro:**
```javascript
const filterCases = () => {
  let filtered = [...cases];
  
  if (seguradoraFilter !== 'all') {
    filtered = filtered.filter((c) => c.seguradora === seguradoraFilter);
  }
  
  setFilteredCases(filtered);
};
```

#### **3. Mostra banner:**
```javascript
{seguradoraFilter !== 'all' && (
  <div className="bg-purple-50 border border-purple-200">
    <span>📊 Filtrando por: {seguradoraFilter}</span>
    <Button onClick={() => setSeguradoraFilter('all')}>
      Limpar Filtro
    </Button>
  </div>
)}
```

---

## 📱 **Responsividade**

### **Desktop:**
```
Grid: 4 colunas (Buscar | Status | Responsável | Seguradora)
```

### **Tablet:**
```
Grid: 2 colunas
[Buscar]        [Status]
[Responsável]   [Seguradora]
```

### **Mobile:**
```
Grid: 1 coluna
[Buscar]
[Status]
[Responsável]
[Seguradora]
```

---

## 🔍 **Casos de Uso**

### **1. Gestor de AVLA**
- Acessa Dashboard
- Clica em "AVLA: 13 casos"
- Vê apenas casos da AVLA
- Pode focar apenas em sua seguradora

### **2. Análise Rápida**
- "Quantos casos a ESSOR tem pendentes?"
- Clica em ESSOR
- Filtra por Status: Pendente
- Vê número exato

### **3. Compartilhar Link**
- Pode compartilhar link direto:
  ```
  https://safe2go.com/cases?seguradora=DAYCOVAL
  ```
- Colega abre e já vê filtrado

---

## 🎯 **Benefícios**

✅ **1 clique** para ver casos de uma seguradora
✅ **Visual claro** de cards clicáveis
✅ **Filtro automático** ao chegar na página
✅ **Banner informativo** mostra filtro ativo
✅ **Fácil remover** filtro com botão "Limpar"
✅ **URL compartilhável** com filtro aplicado
✅ **Compatível** com outros filtros

---

## 🧪 **Como Testar**

### **Teste 1: Click no Card**
1. Acesse o Dashboard
2. Role até "Casos por Seguradora"
3. Passe o mouse sobre um card (deve aumentar)
4. Clique no card
5. ✅ Deve ir para /cases com filtro aplicado

### **Teste 2: Banner de Filtro**
1. Após clicar no card
2. ✅ Deve aparecer banner roxo no topo
3. ✅ Toast: "📊 Mostrando casos da [SEGURADORA]"
4. ✅ Contador de casos correto

### **Teste 3: Limpar Filtro**
1. Com filtro ativo
2. Clique em "Limpar Filtro"
3. ✅ Mostra todos os casos novamente
4. ✅ URL volta para /cases
5. ✅ Banner desaparece

### **Teste 4: Combinar Filtros**
1. Filtre por seguradora AVLA
2. Adicione filtro de Status: Pendente
3. ✅ Deve mostrar apenas casos AVLA pendentes

### **Teste 5: URL Direta**
1. Cole na barra de endereço:
   ```
   /cases?seguradora=ESSOR
   ```
2. ✅ Deve aplicar filtro automaticamente

---

## 📝 **Notas**

- Filtro persiste ao navegar pela página
- Compatível com filtros existentes (Status, Responsável, Busca)
- URL é atualizada para permitir bookmark/compartilhamento
- Banner só aparece quando filtro está ativo
- Animações suaves para melhor UX

---

## 🔧 **Arquivos Modificados**

1. **`/app/frontend/src/pages/Dashboard.jsx`**
   - Cards clicáveis com navegação
   - Hover effects
   - Seta indicadora

2. **`/app/frontend/src/pages/Cases.jsx`**
   - Novo filtro de seguradora
   - Captura parâmetro da URL
   - Banner de filtro ativo
   - Botão limpar filtro
   - Grid 4 colunas

---

**Última atualização:** 26 de Novembro de 2025
**Versão:** 3.2 - Navegação Inteligente por Seguradora
