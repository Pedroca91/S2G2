import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Plus, Search, Trash2, Filter, Eye, Info, Download, Upload, FileText } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Checkbox } from '../components/ui/checkbox';
import { toast } from 'sonner';
import jsPDF from 'jspdf';
import 'jspdf-autotable';
import { createWorker } from 'tesseract.js';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const Cases = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [cases, setCases] = useState([]);
  const [filteredCases, setFilteredCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingCase, setEditingCase] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [responsibleFilter, setResponsibleFilter] = useState('all');
  const [seguradoraFilter, setSeguradoraFilter] = useState('all');
  const isAdmin = user?.role === 'administrador';
  const [selectedCases, setSelectedCases] = useState([]);
  const [selectMode, setSelectMode] = useState(false);
  const [ocrProcessing, setOcrProcessing] = useState(false);
  const fileInputRef = useRef(null);
  const [formData, setFormData] = useState({
    jira_id: '',
    title: '',
    description: '',
    responsible: '',
    status: 'Pendente',
    seguradora: '',
  });

  useEffect(() => {
    fetchCases();
    
    // Aplicar filtros da URL se existirem
    const statusFromUrl = searchParams.get('status');
    const seguradoraFromUrl = searchParams.get('seguradora');
    
    if (statusFromUrl) {
      setStatusFilter(statusFromUrl);
      toast.info(`Filtrando por status: ${statusFromUrl}`);
    }
    
    if (seguradoraFromUrl) {
      setSeguradoraFilter(seguradoraFromUrl);
      toast.success(`📊 Mostrando casos da ${seguradoraFromUrl}`, {
        duration: 3000
      });
    }
  }, []);

  // Recarregar casos quando a página receber foco
  useEffect(() => {
    const handleFocus = () => {
      fetchCases();
    };
    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, []);

  useEffect(() => {
    filterCases();
  }, [cases, searchTerm, statusFilter, responsibleFilter, seguradoraFilter]);

  const fetchCases = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/cases`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCases(response.data);
    } catch (error) {
      console.error('Erro ao carregar casos:', error);
      toast.error('Erro ao carregar casos');
    } finally {
      setLoading(false);
    }
  };

  const filterCases = () => {
    let filtered = [...cases];

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(
        (c) =>
          c.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
          c.jira_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
          c.responsible.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter((c) => c.status === statusFilter);
    }

    // Responsible filter
    if (responsibleFilter !== 'all') {
      filtered = filtered.filter((c) => c.responsible === responsibleFilter);
    }

    // Seguradora filter
    if (seguradoraFilter !== 'all') {
      if (seguradoraFilter === 'Não especificada') {
        // Filtrar casos sem seguradora (null, undefined, ou string vazia)
        filtered = filtered.filter((c) => !c.seguradora || c.seguradora === 'Não especificada');
      } else {
        filtered = filtered.filter((c) => c.seguradora === seguradoraFilter);
      }
    }

    setFilteredCases(filtered);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      
      if (editingCase) {
        await axios.put(`${API}/cases/${editingCase.id}`, formData, { headers });
        toast.success('✅ Caso atualizado e salvo no banco de dados!');
      } else {
        await axios.post(`${API}/cases`, formData, { headers });
        toast.success('Caso criado com sucesso!');
      }
      setDialogOpen(false);
      resetForm();
      fetchCases();
    } catch (error) {
      console.error('Erro ao salvar caso:', error);
      toast.error('Erro ao salvar caso: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleStatusChange = async (caseId, newStatus) => {
    try {
      const token = localStorage.getItem('token');
      await axios.put(
        `${API}/cases/${caseId}`,
        { status: newStatus },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Status atualizado com sucesso!');
      fetchCases();
    } catch (error) {
      console.error('Erro ao atualizar status:', error);
      toast.error('Erro ao atualizar status');
    }
  };

  // Função para selecionar/desselecionar chamado
  const toggleCaseSelection = (caseId) => {
    setSelectedCases(prev => 
      prev.includes(caseId) 
        ? prev.filter(id => id !== caseId)
        : [...prev, caseId]
    );
  };

  // Selecionar todos os chamados visíveis
  const selectAllCases = () => {
    if (selectedCases.length === filteredCases.length) {
      setSelectedCases([]);
    } else {
      setSelectedCases(filteredCases.map(c => c.id));
    }
  };

  // Gerar PDF dos chamados selecionados
  const generatePDF = () => {
    if (selectedCases.length === 0) {
      toast.error('Selecione pelo menos um chamado para gerar o relatório');
      return;
    }

    const selectedData = cases.filter(c => selectedCases.includes(c.id));
    
    const doc = new jsPDF();
    
    // Título
    doc.setFontSize(18);
    doc.text('Relatório de Chamados - Safe2Go', 14, 20);
    
    doc.setFontSize(11);
    doc.text(`Gerado em: ${new Date().toLocaleString('pt-BR')}`, 14, 28);
    doc.text(`Total de chamados: ${selectedData.length}`, 14, 34);
    
    // Tabela resumida
    const tableData = selectedData.map(c => [
      c.jira_id || c.id.substring(0, 8),
      c.title.substring(0, 40) + (c.title.length > 40 ? '...' : ''),
      c.status,
      c.seguradora || '-',
      c.responsible || 'Não atribuído',
      new Date(c.created_at).toLocaleDateString('pt-BR')
    ]);
    
    doc.autoTable({
      startY: 40,
      head: [['ID', 'Título', 'Status', 'Seguradora', 'Responsável', 'Data']],
      body: tableData,
      theme: 'grid',
      headStyles: { fillColor: [147, 51, 234] }, // Purple
      styles: { fontSize: 9 }
    });
    
    // Detalhes de cada chamado
    let yPos = doc.lastAutoTable.finalY + 15;
    
    selectedData.forEach((caseItem, index) => {
      if (yPos > 250) {
        doc.addPage();
        yPos = 20;
      }
      
      doc.setFontSize(12);
      doc.setFont(undefined, 'bold');
      doc.text(`Chamado ${index + 1}: ${caseItem.jira_id || caseItem.id.substring(0, 8)}`, 14, yPos);
      
      doc.setFontSize(10);
      doc.setFont(undefined, 'normal');
      yPos += 7;
      
      doc.text(`Título: ${caseItem.title}`, 14, yPos);
      yPos += 7;
      
      doc.text(`Status: ${caseItem.status}`, 14, yPos);
      yPos += 7;
      
      if (caseItem.seguradora) {
        doc.text(`Seguradora: ${caseItem.seguradora}`, 14, yPos);
        yPos += 7;
      }
      
      doc.text(`Responsável: ${caseItem.responsible || 'Não atribuído'}`, 14, yPos);
      yPos += 7;
      
      doc.text(`Data de abertura: ${new Date(caseItem.created_at).toLocaleString('pt-BR')}`, 14, yPos);
      yPos += 7;
      
      // Descrição com quebra de linha
      const descLines = doc.splitTextToSize(`Descrição: ${caseItem.description}`, 180);
      doc.text(descLines, 14, yPos);
      yPos += (descLines.length * 5) + 10;
    });
    
    // Salvar PDF
    doc.save(`chamados_safe2go_${new Date().toISOString().split('T')[0]}.pdf`);
    toast.success(`PDF gerado com ${selectedData.length} chamado(s)!`);
    setSelectMode(false);
    setSelectedCases([]);
  };

  // Exportar todos os chamados em JSON
  const exportAllCases = () => {
    const dataToExport = {
      export_date: new Date().toISOString(),
      total_cases: cases.length,
      cases: cases
    };
    
    const blob = new Blob([JSON.stringify(dataToExport, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `chamados_backup_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    toast.success(`${cases.length} chamados exportados com sucesso!`);
  };

  // Processar imagem com OCR
  const processImageWithOCR = async (file) => {
    setOcrProcessing(true);
    toast.info('🔍 Processando imagem com OCR... Aguarde, isso pode levar alguns segundos...');
    
    try {
      console.log('🖼️ Iniciando OCR para arquivo:', file.name, 'Tamanho:', file.size);
      
      // Criar worker com português e configurações otimizadas
      const worker = await createWorker('por', 1, {
        logger: m => console.log('OCR:', m)
      });
      
      // Configurar reconhecimento para melhor performance com tabelas
      await worker.setParameters({
        tessedit_pageseg_mode: '6', // Assume uniform block of text
      });
      
      console.log('🔄 Reconhecendo texto...');
      const { data: { text, confidence } } = await worker.recognize(file);
      await worker.terminate();
      
      console.log('✅ OCR Completo! Confiança:', confidence);
      console.log('📝 Texto extraído completo:', text);
      
      // Processar texto extraído e criar chamados
      const extractedCases = parseTextToCases(text);
      
      if (extractedCases.length === 0) {
        console.error('❌ Nenhum caso foi extraído após o parsing');
        toast.error('Nenhum chamado identificado na imagem. Verifique se a imagem está clara e contém IDs de casos (ex: SGSS-N012).');
        setOcrProcessing(false);
        return;
      }
      
      console.log(`✅ ${extractedCases.length} casos prontos para criar:`, extractedCases);
      
      // Criar chamados extraídos
      const token = localStorage.getItem('token');
      let successCount = 0;
      let duplicateCount = 0;
      
      toast.info(`📊 Encontrados ${extractedCases.length} chamado(s) na imagem. Criando...`);
      
      for (const caseData of extractedCases) {
        try {
          // Verificar se já existe
          const existing = cases.find(c => c.jira_id === caseData.jira_id);
          
          if (!existing) {
            await axios.post(`${API}/cases`, caseData, {
              headers: { Authorization: `Bearer ${token}` }
            });
            successCount++;
            console.log(`✅ Criado: ${caseData.jira_id}`);
          } else {
            duplicateCount++;
            console.log(`⚠️ Já existe: ${caseData.jira_id}`);
          }
        } catch (err) {
          console.error('❌ Erro ao criar caso da imagem:', caseData.jira_id, err);
        }
      }
      
      if (successCount > 0) {
        toast.success(`✅ ${successCount} chamado(s) criado(s) da imagem!${duplicateCount > 0 ? ` (${duplicateCount} já existiam)` : ''}`);
      } else if (duplicateCount > 0) {
        toast.warning(`⚠️ Todos os ${duplicateCount} chamados já existem no sistema.`);
      } else {
        toast.error('Nenhum chamado pôde ser criado. Verifique os logs.');
      }
      
      fetchCases();
      
    } catch (error) {
      console.error('❌ Erro no OCR:', error);
      toast.error('Erro ao processar imagem: ' + error.message);
    } finally {
      setOcrProcessing(false);
    }
  };

  // Parser de texto para extrair chamados
  const parseTextToCases = (text) => {
    console.log('🔍 Iniciando parse do texto OCR...');
    console.log('📝 Texto completo (primeiros 500 chars):', text.substring(0, 500));
    
    const cases = [];
    const lines = text.split('\n').filter(line => line.trim());
    
    console.log(`📊 Total de linhas: ${lines.length}`);
    
    // Padrões melhorados para IDs de casos Jira
    const jiraIdPatterns = [
      /\b(SGSS[-\s]?N?\d+)\b/i,           // SGSS-N012, SGSS N012, SGSS-0012
      /\b([A-Z]{2,5}[-\s]\d{3,6})\b/i,    // WEB-732303, etc
      /\b([A-Z]+\d+[-\s]\d+)\b/i,         // Outros padrões
    ];
    
    let currentCase = null;
    let lineBuffer = '';
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line || line.length < 3) continue;
      
      // Tentar encontrar ID do Jira
      let foundId = null;
      for (const pattern of jiraIdPatterns) {
        const match = line.match(pattern);
        if (match) {
          foundId = match[1].replace(/\s/g, '-').toUpperCase();
          break;
        }
      }
      
      if (foundId) {
        // Salvar caso anterior se existir
        if (currentCase && currentCase.jira_id && currentCase.title) {
          cases.push(currentCase);
          console.log(`✅ Caso encontrado: ${currentCase.jira_id} - ${currentCase.title.substring(0, 50)}`);
        }
        
        // Extrair título (tudo depois do ID na mesma linha)
        let title = line.replace(foundId, '').trim();
        // Remover caracteres especiais e múltiplos espaços
        title = title.replace(/[|]/g, ' ').replace(/\s{2,}/g, ' ').trim();
        
        // Se não tem título na mesma linha, pegar próxima linha
        if (!title && i + 1 < lines.length) {
          title = lines[i + 1].trim();
          i++; // Pular próxima linha já que usamos ela
        }
        
        // Detectar status na linha
        let status = 'Pendente';
        if (/aguardando\s*suporte/i.test(line)) {
          status = 'Aguardando resposta';
        } else if (/aguardando\s*configura[çc][ãa]o/i.test(line)) {
          status = 'Aguardando Configuração';
        } else if (/em\s*atendimento/i.test(line)) {
          status = 'Em Desenvolvimento';
        } else if (/conclu[íi]do/i.test(line)) {
          status = 'Concluído';
        }
        
        // Detectar responsável
        let responsible = user?.name || 'Não atribuído';
        const namePatterns = [
          /(?:Lucas|Valentim|Pedro|João|Maria)\s+[A-Za-zÀ-ÿ\s]+/i
        ];
        for (const pattern of namePatterns) {
          const nameMatch = line.match(pattern);
          if (nameMatch) {
            responsible = nameMatch[0].trim();
            break;
          }
        }
        
        // Detectar organização/categoria
        let category = null;
        if (/AVLA|ESSOR|DAYCOVAL/i.test(line)) {
          const catMatch = line.match(/AVLA|ESSOR|DAYCOVAL/i);
          if (catMatch) category = catMatch[0].toUpperCase();
        }
        
        currentCase = {
          jira_id: foundId,
          title: title || 'Sem título',
          description: `Importado via OCR da imagem`,
          status: status,
          responsible: responsible,
          seguradora: category || null,
          category: category || null,
          priority: 'Média'
        };
        
      } else if (currentCase && line.length > 10) {
        // Acumular informações adicionais para o caso atual
        
        // Se ainda não tem título bom, atualizar
        if (currentCase.title === 'Sem título' || currentCase.title.length < 10) {
          currentCase.title = line.substring(0, 200);
        }
        
        // Atualizar descrição com mais contexto
        if (currentCase.description === 'Importado via OCR da imagem') {
          currentCase.description = line.substring(0, 500);
        }
        
        // Buscar status se ainda não encontrou
        if (currentCase.status === 'Pendente') {
          if (/aguardando\s*suporte/i.test(line)) {
            currentCase.status = 'Aguardando resposta';
          } else if (/em\s*atendimento/i.test(line)) {
            currentCase.status = 'Em Desenvolvimento';
          }
        }
      }
    }
    
    // Adicionar último caso
    if (currentCase && currentCase.jira_id && currentCase.title && currentCase.title !== 'Sem título') {
      cases.push(currentCase);
      console.log(`✅ Caso encontrado: ${currentCase.jira_id} - ${currentCase.title.substring(0, 50)}`);
    }
    
    console.log(`📊 Total de casos extraídos: ${cases.length}`);
    
    // Validar e limpar casos
    const validCases = cases.filter(c => {
      const isValid = c.jira_id && c.title && c.title !== 'Sem título' && c.title.length >= 5;
      if (!isValid) {
        console.warn(`⚠️ Caso inválido removido: ${c.jira_id}`);
      }
      return isValid;
    }).map(c => ({
      ...c,
      title: c.title.substring(0, 200).trim(),
      description: c.description.substring(0, 500).trim()
    }));
    
    console.log(`✅ Casos válidos finais: ${validCases.length}`);
    
    return validCases;
  };

  // Importar chamados de JSON ou Imagem
  const importCases = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    // Verificar extensão do arquivo primeiro (mais confiável que MIME type)
    const fileName = file.name.toLowerCase();
    const isJsonFile = fileName.endsWith('.json');
    const isImageFile = fileName.match(/\.(jpg|jpeg|png|gif|bmp|webp)$/i);
    
    console.log('📁 Arquivo selecionado:', {
      name: fileName,
      type: file.type,
      size: file.size,
      isJsonFile,
      isImageFile
    });
    
    // Se é imagem, processar com OCR
    if (isImageFile || (!isJsonFile && file.type.startsWith('image/'))) {
      console.log('🖼️ Processando como imagem com OCR');
      await processImageWithOCR(file);
      
      // Limpar input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      return;
    }
    
    // Processar JSON
    try {
      console.log('📄 Processando como arquivo JSON');
      const text = await file.text();
      console.log('📝 Conteúdo do arquivo (primeiros 200 chars):', text.substring(0, 200));
      const data = JSON.parse(text);
      console.log('✅ JSON parseado com sucesso:', {
        hasCases: !!data.cases,
        casesCount: data.cases?.length,
        structure: Object.keys(data)
      });
      
      if (!data.cases || !Array.isArray(data.cases)) {
        toast.error('Arquivo JSON inválido! O arquivo deve conter um objeto com a propriedade "cases" contendo um array de chamados.');
        console.error('Estrutura do arquivo:', data);
        return;
      }
      
      if (data.cases.length === 0) {
        toast.warning('Nenhum chamado encontrado no arquivo JSON.');
        return;
      }
      
      const token = localStorage.getItem('token');
      let successCount = 0;
      let errorCount = 0;
      
      toast.info(`Importando ${data.cases.length} chamados...`);
      
      for (const caseData of data.cases) {
        try {
          // Verificar se já existe pelo jira_id
          const existing = cases.find(c => c.jira_id === caseData.jira_id);
          
          if (!existing) {
            await axios.post(`${API}/cases`, caseData, {
              headers: { Authorization: `Bearer ${token}` }
            });
            successCount++;
          } else {
            errorCount++; // Já existe, pular
          }
        } catch (err) {
          errorCount++;
          console.error('Erro ao importar caso:', err);
        }
      }
      
      toast.success(`Importação concluída! ${successCount} novos, ${errorCount} ignorados.`);
      fetchCases();
      
      // Limpar input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      
    } catch (error) {
      console.error('Erro ao importar:', error);
      if (error instanceof SyntaxError) {
        toast.error('Erro ao processar JSON! Verifique se o arquivo está em formato JSON válido.');
      } else {
        toast.error('Erro ao processar arquivo: ' + error.message);
      }
    } finally {
      // Limpar input em caso de erro também
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Tem certeza que deseja deletar este caso?')) {
      try {
        const token = localStorage.getItem('token');
        await axios.delete(`${API}/cases/${id}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Caso deletado com sucesso!');
        fetchCases();
      } catch (error) {
        console.error('Erro ao deletar caso:', error);
        toast.error('Erro ao deletar caso: ' + (error.response?.data?.detail || error.message));
      }
    }
  };

  const resetForm = () => {
    setFormData({
      jira_id: '',
      title: '',
      description: '',
      responsible: '',
      status: 'Pendente',
      seguradora: '',
    });
    setEditingCase(null);
  };

  const uniqueResponsibles = [...new Set(cases.map((c) => c.responsible))];

  return (
    <div className="page-container">
      <div className="page-header flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="flex-1">
          <h1 className="page-title" data-testid="cases-title">Chamados</h1>
          <p className="page-subtitle">Gerencie todos os chamados de suporte</p>
        </div>

        {isAdmin && (
          <div className="flex gap-2 flex-wrap">
            {/* Botões de Export/Import */}
            <Button
              variant="outline"
              onClick={() => setSelectMode(!selectMode)}
              className="flex items-center gap-2"
            >
              <FileText className="w-4 h-4" />
              {selectMode ? 'Cancelar Seleção' : 'Gerar Relatório PDF'}
            </Button>

            {selectMode && (
              <Button
                onClick={generatePDF}
                className="bg-red-600 hover:bg-red-700 text-white flex items-center gap-2"
                disabled={selectedCases.length === 0}
              >
                <FileText className="w-4 h-4" />
                Gerar PDF ({selectedCases.length})
              </Button>
            )}

            <Button
              variant="outline"
              onClick={exportAllCases}
              className="flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              Exportar Todos
            </Button>

            <label htmlFor="import-file">
              <Button
                variant="outline"
                className="flex items-center gap-2"
                onClick={() => fileInputRef.current?.click()}
                type="button"
                disabled={ocrProcessing}
              >
                <Upload className="w-4 h-4" />
                {ocrProcessing ? 'Processando...' : 'Importar'}
              </Button>
            </label>
            <input
              ref={fileInputRef}
              type="file"
              accept=".json,image/*"
              onChange={importCases}
              className="hidden"
              id="import-file"
              disabled={ocrProcessing}
            />

            <Dialog open={dialogOpen} onOpenChange={(open) => {
              setDialogOpen(open);
              if (!open) resetForm();
            }}>
              <DialogTrigger asChild>
              <Button
                data-testid="add-case-btn"
                className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white shadow-lg"
              >
                <Plus className="w-4 h-4 mr-2" />
                Novo Chamado
              </Button>
              </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{editingCase ? 'Editar Chamado' : 'Novo Chamado'}</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4 mt-4">
              <div>
                <Label htmlFor="jira_id">ID do Jira</Label>
                <Input
                  id="jira_id"
                  data-testid="jira-id-input"
                  value={formData.jira_id}
                  onChange={(e) => setFormData({ ...formData, jira_id: e.target.value })}
                  required
                  placeholder="Ex: SUP-123"
                />
              </div>
              <div>
                <Label htmlFor="title">Título</Label>
                <Input
                  id="title"
                  data-testid="title-input"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  required
                  placeholder="Título do chamado"
                />
              </div>
              <div>
                <Label htmlFor="description">Descrição</Label>
                <Textarea
                  id="description"
                  data-testid="description-input"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  required
                  placeholder="Descreva o chamado"
                  rows={4}
                />
              </div>
              <div>
                <Label htmlFor="responsible">Responsável</Label>
                <Input
                  id="responsible"
                  data-testid="responsible-input"
                  value={formData.responsible}
                  onChange={(e) => setFormData({ ...formData, responsible: e.target.value })}
                  required
                  placeholder="Nome do responsável"
                />
              </div>
              <div>
                <Label htmlFor="seguradora">Seguradora</Label>
                <Select
                  value={formData.seguradora}
                  onValueChange={(value) => setFormData({ ...formData, seguradora: value })}
                >
                  <SelectTrigger data-testid="seguradora-select">
                    <SelectValue placeholder="Selecione a seguradora" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="AVLA">AVLA</SelectItem>
                    <SelectItem value="DAYCOVAL">DAYCOVAL</SelectItem>
                    <SelectItem value="ESSOR">ESSOR</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="status">Status</Label>
                <Select
                  value={formData.status}
                  onValueChange={(value) => setFormData({ ...formData, status: value })}
                >
                  <SelectTrigger data-testid="status-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Pendente">🟡 Pendente</SelectItem>
                    <SelectItem value="Em Desenvolvimento">🔵 Em Desenvolvimento</SelectItem>
                    <SelectItem value="Aguardando resposta">🟠 Aguardando resposta</SelectItem>
                    <SelectItem value="Aguardando Configuração">⚙️ Aguardando Configuração</SelectItem>
                    <SelectItem value="Concluído">🟢 Concluído</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex gap-2 justify-end">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setDialogOpen(false);
                    resetForm();
                  }}
                  data-testid="cancel-btn"
                >
                  Cancelar
                </Button>
                <Button type="submit" data-testid="save-case-btn">
                  {editingCase ? 'Atualizar' : 'Criar'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
          </div>
        )}
      </div>

      {/* Banner informativo para clientes */}
      {!isAdmin && (
        <div className="mb-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <Info className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="font-semibold text-blue-900 mb-1">Meus Chamados</h3>
              <p className="text-sm text-blue-800">
                Aqui você pode ver todos os seus chamados e acompanhar o andamento. 
                Para abrir um novo chamado, clique no botão &quot;Abrir Chamado&quot; no topo da página.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="card mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <Label htmlFor="search" className="flex items-center gap-2 mb-2">
              <Search className="w-4 h-4" />
              Buscar
            </Label>
            <Input
              id="search"
              data-testid="search-input"
              placeholder="Buscar por título, ID ou responsável"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div>
            <Label htmlFor="status-filter" className="flex items-center gap-2 mb-2">
              <Filter className="w-4 h-4" />
              Status
            </Label>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger id="status-filter" data-testid="status-filter">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos</SelectItem>
                <SelectItem value="Pendente">🟡 Pendente</SelectItem>
                <SelectItem value="Em Desenvolvimento">🔵 Em Desenvolvimento</SelectItem>
                <SelectItem value="Aguardando resposta">🟠 Aguardando resposta</SelectItem>
                <SelectItem value="Aguardando Configuração">⚙️ Aguardando Configuração</SelectItem>
                    <SelectItem value="Concluído">🟢 Concluído</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label htmlFor="responsible-filter" className="flex items-center gap-2 mb-2">
              <Filter className="w-4 h-4" />
              Responsável
            </Label>
            <Select value={responsibleFilter} onValueChange={setResponsibleFilter}>
              <SelectTrigger id="responsible-filter" data-testid="responsible-filter">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todos</SelectItem>
                {uniqueResponsibles.map((resp) => (
                  <SelectItem key={resp} value={resp}>
                    {resp}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label htmlFor="seguradora-filter" className="flex items-center gap-2 mb-2">
              <Filter className="w-4 h-4" />
              Seguradora
            </Label>
            <Select value={seguradoraFilter} onValueChange={setSeguradoraFilter}>
              <SelectTrigger id="seguradora-filter" data-testid="seguradora-filter">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todas</SelectItem>
                <SelectItem value="AVLA">AVLA</SelectItem>
                <SelectItem value="ESSOR">ESSOR</SelectItem>
                <SelectItem value="DAYCOVAL">DAYCOVAL</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      {/* Indicador de Filtro Ativo */}
      {seguradoraFilter !== 'all' && (
        <div className="mb-4 bg-purple-50 border border-purple-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-purple-700 font-medium">
                📊 Filtrando por: {seguradoraFilter}
              </span>
              <span className="text-purple-600 text-sm">
                ({filteredCases.length} {filteredCases.length === 1 ? 'caso' : 'casos'})
              </span>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setSeguradoraFilter('all');
                setSearchParams({});
                toast.success('Filtro removido');
              }}
              className="text-purple-600 border-purple-300 hover:bg-purple-100"
            >
              Limpar Filtro
            </Button>
          </div>
        </div>
      )}

      {/* Cases List */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Carregando...</div>
        </div>
      ) : filteredCases.length === 0 ? (
        <div className="card text-center py-12" data-testid="no-cases-message">
          <p className="text-gray-500">Nenhum chamado encontrado</p>
        </div>
      ) : (
        <div className="grid gap-4" data-testid="cases-list">
          {/* Botão Selecionar Todos - Apenas no modo seleção */}
          {selectMode && isAdmin && (
            <div className="card bg-purple-50 border-purple-200">
              <div className="flex items-center gap-3">
                <Checkbox
                  checked={selectedCases.length === filteredCases.length && filteredCases.length > 0}
                  onCheckedChange={selectAllCases}
                  id="select-all"
                />
                <Label htmlFor="select-all" className="cursor-pointer font-semibold text-purple-900">
                  {selectedCases.length === filteredCases.length && filteredCases.length > 0
                    ? `Desselecionar Todos (${filteredCases.length})`
                    : `Selecionar Todos (${filteredCases.length})`
                  }
                </Label>
              </div>
            </div>
          )}

          {filteredCases.map((caseItem) => (
            <div
              key={caseItem.id}
              data-testid={`case-item-${caseItem.id}`}
              className={`card hover:shadow-lg transition-shadow ${
                selectedCases.includes(caseItem.id) ? 'ring-2 ring-purple-500 bg-purple-50' : ''
              }`}
            >
              <div>
                {/* Header do card com badges */}
                <div className="flex items-center gap-3 mb-2 flex-wrap">
                  {selectMode && isAdmin && (
                    <Checkbox
                      checked={selectedCases.includes(caseItem.id)}
                      onCheckedChange={() => toggleCaseSelection(caseItem.id)}
                      id={`select-${caseItem.id}`}
                    />
                  )}
                  <span className="text-sm font-medium text-purple-600 bg-purple-50 px-3 py-1 rounded-lg">
                    {caseItem.jira_id}
                  </span>
                  <span
                    className={`badge ${
                      caseItem.status === 'Concluído' 
                        ? 'badge-success' 
                        : caseItem.status === 'Aguardando resposta'
                        ? 'badge-waiting'
                        : caseItem.status === 'Em Desenvolvimento'
                        ? 'bg-blue-100 text-blue-700'
                        : caseItem.status === 'Aguardando Configuração'
                        ? 'bg-cyan-100 text-cyan-700'
                        : 'badge-pending'
                    }`}
                    data-testid={`case-status-${caseItem.id}`}
                  >
                    {caseItem.status}
                  </span>
                  {caseItem.category && (
                    <span className="text-xs font-medium text-blue-600 bg-blue-50 px-2 py-1 rounded-md border border-blue-200">
                      📂 {caseItem.category}
                    </span>
                  )}
                  {caseItem.seguradora && (
                    <span className="inline-flex items-center px-2 py-1 bg-purple-100 text-purple-700 rounded-md text-xs font-medium">
                      {caseItem.seguradora}
                    </span>
                  )}
                </div>
                
                {/* Título e descrição */}
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{caseItem.title}</h3>
                <p className="text-sm text-gray-600 mb-3 line-clamp-2">{caseItem.description}</p>
                
                {/* Footer com info e ações */}
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    <span>Responsável: <strong>{caseItem.responsible}</strong></span>
                    <span>Aberto: {new Date(caseItem.created_at).toLocaleDateString('pt-BR')}</span>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    {/* Seletor rápido de status */}
                    <Select
                      value={caseItem.status}
                      onValueChange={(value) => handleStatusChange(caseItem.id, value)}
                    >
                      <SelectTrigger className="h-9 text-sm w-[180px]">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Pendente">🟡 Pendente</SelectItem>
                        <SelectItem value="Em Desenvolvimento">🔵 Em Desenvolvimento</SelectItem>
                        <SelectItem value="Aguardando resposta">🟠 Aguardando</SelectItem>
                        <SelectItem value="Aguardando Configuração">⚙️ Aguardando Configuração</SelectItem>
                    <SelectItem value="Concluído">🟢 Concluído</SelectItem>
                      </SelectContent>
                    </Select>
                    
                    <Button
                      variant="default"
                      size="sm"
                      onClick={() => navigate(`/cases/${caseItem.id}`)}
                      data-testid={`view-case-${caseItem.id}`}
                      className="bg-purple-600 hover:bg-purple-700"
                    >
                      <Eye className="w-4 h-4 mr-1" />
                      Ver Detalhes
                    </Button>
                    
                    {isAdmin && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDelete(caseItem.id)}
                        data-testid={`delete-case-${caseItem.id}`}
                        className="text-red-600 hover:bg-red-50"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Cases;