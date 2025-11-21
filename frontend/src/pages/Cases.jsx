import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Plus, Search, Edit, Trash2, Filter } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const Cases = () => {
  const [cases, setCases] = useState([]);
  const [filteredCases, setFilteredCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingCase, setEditingCase] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [responsibleFilter, setResponsibleFilter] = useState('all');
  const [formData, setFormData] = useState({
    jira_id: '',
    title: '',
    description: '',
    responsible: '',
    status: 'Pendente',
  });

  useEffect(() => {
    fetchCases();
  }, []);

  useEffect(() => {
    filterCases();
  }, [cases, searchTerm, statusFilter, responsibleFilter]);

  const fetchCases = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/cases`);
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

    setFilteredCases(filtered);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingCase) {
        await axios.put(`${API}/cases/${editingCase.id}`, formData);
        toast.success('Caso atualizado com sucesso!');
      } else {
        await axios.post(`${API}/cases`, formData);
        toast.success('Caso criado com sucesso!');
      }
      setDialogOpen(false);
      resetForm();
      fetchCases();
    } catch (error) {
      console.error('Erro ao salvar caso:', error);
      toast.error('Erro ao salvar caso');
    }
  };

  const handleEdit = (caseItem) => {
    setEditingCase(caseItem);
    setFormData({
      jira_id: caseItem.jira_id,
      title: caseItem.title,
      description: caseItem.description,
      responsible: caseItem.responsible,
      status: caseItem.status,
    });
    setDialogOpen(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Tem certeza que deseja deletar este caso?')) {
      try {
        await axios.delete(`${API}/cases/${id}`);
        toast.success('Caso deletado com sucesso!');
        fetchCases();
      } catch (error) {
        console.error('Erro ao deletar caso:', error);
        toast.error('Erro ao deletar caso');
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
    });
    setEditingCase(null);
  };

  const uniqueResponsibles = [...new Set(cases.map((c) => c.responsible))];

  return (
    <div className="page-container">
      <div className="page-header flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="page-title" data-testid="cases-title">Casos</h1>
          <p className="page-subtitle">Gerencie todos os casos de suporte</p>
        </div>
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
              Novo Caso
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{editingCase ? 'Editar Caso' : 'Novo Caso'}</DialogTitle>
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
                  placeholder="Título do caso"
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
                  placeholder="Descreva o caso"
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
                <Label htmlFor="status">Status</Label>
                <Select
                  value={formData.status}
                  onValueChange={(value) => setFormData({ ...formData, status: value })}
                >
                  <SelectTrigger data-testid="status-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Pendente">Pendente</SelectItem>
                    <SelectItem value="Concluído">Concluído</SelectItem>
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

      {/* Filters */}
      <div className="card mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
                <SelectItem value="Pendente">Pendente</SelectItem>
                <SelectItem value="Concluído">Concluído</SelectItem>
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
        </div>
      </div>

      {/* Cases List */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Carregando...</div>
        </div>
      ) : filteredCases.length === 0 ? (
        <div className="card text-center py-12" data-testid="no-cases-message">
          <p className="text-gray-500">Nenhum caso encontrado</p>
        </div>
      ) : (
        <div className="grid gap-4" data-testid="cases-list">
          {filteredCases.map((caseItem) => (
            <div
              key={caseItem.id}
              data-testid={`case-item-${caseItem.id}`}
              className="card hover:shadow-lg transition-shadow"
            >
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-sm font-medium text-purple-600 bg-purple-50 px-3 py-1 rounded-lg">
                      {caseItem.jira_id}
                    </span>
                    <span
                      className={`badge ${
                        caseItem.status === 'Concluído' ? 'badge-success' : 'badge-pending'
                      }`}
                      data-testid={`case-status-${caseItem.id}`}
                    >
                      {caseItem.status}
                    </span>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">{caseItem.title}</h3>
                  <p className="text-sm text-gray-600 mb-2">{caseItem.description}</p>
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    <span>Responsável: <strong>{caseItem.responsible}</strong></span>
                    <span>Aberto: {new Date(caseItem.opened_date).toLocaleDateString('pt-BR')}</span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleEdit(caseItem)}
                    data-testid={`edit-case-${caseItem.id}`}
                  >
                    <Edit className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDelete(caseItem.id)}
                    data-testid={`delete-case-${caseItem.id}`}
                    className="text-red-600 hover:bg-red-50"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
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