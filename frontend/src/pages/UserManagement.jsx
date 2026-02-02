import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Users, CheckCircle, XCircle, Edit, Trash2, Clock, Building, Phone, Mail, UserPlus } from 'lucide-react';
import { toast } from 'sonner';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const UserManagement = () => {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [pendingUsers, setPendingUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState('pending');

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const [allUsersRes, pendingRes] = await Promise.all([
        axios.get(`${API}/users`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/users/pending`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      setUsers(allUsersRes.data);
      setPendingUsers(pendingRes.data);
    } catch (error) {
      console.error('Erro ao carregar usuários:', error);
      toast.error('Erro ao carregar usuários');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (userId, status) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/users/${userId}/approve`,
        { status },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      toast.success(`Usuário ${status === 'aprovado' ? 'aprovado' : 'rejeitado'} com sucesso!`);
      fetchUsers();
    } catch (error) {
      console.error('Erro ao aprovar usuário:', error);
      toast.error('Erro ao processar aprovação');
    }
  };

  const handleDelete = async (userId) => {
    if (!window.confirm('Tem certeza que deseja deletar este usuário?')) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/users/${userId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast.success('Usuário deletado com sucesso!');
      fetchUsers();
    } catch (error) {
      console.error('Erro ao deletar usuário:', error);
      toast.error(error.response?.data?.detail || 'Erro ao deletar usuário');
    }
  };

  // Estado e funções para edição de usuário
  const [editingUser, setEditingUser] = useState(null);
  const [editFormData, setEditFormData] = useState({
    name: '',
    email: '',
    phone: '',
    company: '',
    role: '',
    status: ''
  });
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);

  const openEditDialog = (user) => {
    setEditingUser(user);
    setEditFormData({
      name: user.name || '',
      email: user.email || '',
      phone: user.phone || '',
      company: user.company || '',
      role: user.role || 'cliente',
      status: user.status || 'pendente'
    });
    setIsEditDialogOpen(true);
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    
    if (!editFormData.name || !editFormData.email) {
      toast.error('Nome e email são obrigatórios');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.put(
        `${API}/users/${editingUser.id}`,
        editFormData,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      toast.success('Usuário atualizado com sucesso!');
      setIsEditDialogOpen(false);
      fetchUsers();
    } catch (error) {
      console.error('Erro ao atualizar usuário:', error);
      toast.error(error.response?.data?.detail || 'Erro ao atualizar usuário');
    }
  };

  const UserCard = ({ user, showActions = true }) => {
    const statusColors = {
      pendente: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      aprovado: 'bg-green-100 text-green-800 border-green-300',
      rejeitado: 'bg-red-100 text-red-800 border-red-300'
    };

    const roleColors = {
      administrador: 'bg-purple-100 text-purple-800 border-purple-300',
      cliente: 'bg-blue-100 text-blue-800 border-blue-300'
    };

    return (
      <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-blue-500 rounded-full flex items-center justify-center text-white font-bold text-lg">
                {user.name.charAt(0).toUpperCase()}
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{user.name}</h3>
                <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium border ${roleColors[user.role]}`}>
                  {user.role === 'administrador' ? '👑 Administrador' : '👤 Cliente'}
                </span>
              </div>
            </div>
          </div>
          
          <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium border ${statusColors[user.status]}`}>
            {user.status.charAt(0).toUpperCase() + user.status.slice(1)}
          </span>
        </div>

        <div className="space-y-2 mb-4">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Mail className="w-4 h-4" />
            <span>{user.email}</span>
          </div>
          
          {user.phone && (
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Phone className="w-4 h-4" />
              <span>{user.phone}</span>
            </div>
          )}
          
          {user.company && (
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Building className="w-4 h-4" />
              <span>{user.company}</span>
            </div>
          )}
          
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <Clock className="w-3 h-3" />
            <span>Cadastrado em {new Date(user.created_at).toLocaleDateString('pt-BR')}</span>
          </div>
        </div>

        {showActions && user.id !== currentUser?.id && (
          <div className="flex gap-2 pt-4 border-t">
            {user.status === 'pendente' && (
              <>
                <Button
                  onClick={() => handleApprove(user.id, 'aprovado')}
                  className="flex-1 bg-green-600 hover:bg-green-700 text-white"
                  size="sm"
                >
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Aprovar
                </Button>
                <Button
                  onClick={() => handleApprove(user.id, 'rejeitado')}
                  variant="outline"
                  className="flex-1 border-red-300 text-red-600 hover:bg-red-50"
                  size="sm"
                >
                  <XCircle className="w-4 h-4 mr-2" />
                  Rejeitar
                </Button>
              </>
            )}
            
            {/* Botão Editar - disponível para todos os usuários */}
            <Button
              onClick={() => openEditDialog(user)}
              variant="outline"
              className="flex-1 border-blue-300 text-blue-600 hover:bg-blue-50"
              size="sm"
            >
              <Edit className="w-4 h-4 mr-2" />
              Editar
            </Button>
            
            {user.status !== 'pendente' && (
              <Button
                onClick={() => handleDelete(user.id)}
                variant="outline"
                className="flex-1 border-red-300 text-red-600 hover:bg-red-50"
                size="sm"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Deletar
              </Button>
            )}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Carregando...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title flex items-center gap-3">
            <Users className="w-8 h-8" />
            Gerenciamento de Usuários
          </h1>
          <p className="page-subtitle">Aprovar cadastros e gerenciar acessos</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="card mb-6">
        <div className="flex gap-2 border-b">
          <button
            onClick={() => setSelectedTab('pending')}
            className={`px-4 py-3 font-medium transition-colors relative ${
              selectedTab === 'pending'
                ? 'text-purple-600 border-b-2 border-purple-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Pendentes
            {pendingUsers.length > 0 && (
              <span className="ml-2 inline-flex items-center justify-center w-6 h-6 text-xs font-bold text-white bg-red-500 rounded-full">
                {pendingUsers.length}
              </span>
            )}
          </button>
          <button
            onClick={() => setSelectedTab('all')}
            className={`px-4 py-3 font-medium transition-colors relative ${
              selectedTab === 'all'
                ? 'text-purple-600 border-b-2 border-purple-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Todos os Usuários
            <span className="ml-2 text-xs text-gray-500">({users.length})</span>
          </button>
        </div>
      </div>

      {/* Content */}
      {selectedTab === 'pending' && (
        <div>
          {pendingUsers.length === 0 ? (
            <div className="card text-center py-12">
              <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Nenhum cadastro pendente
              </h3>
              <p className="text-gray-600">
                Todos os cadastros foram processados!
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {pendingUsers.map((user) => (
                <UserCard key={user.id} user={user} />
              ))}
            </div>
          )}
        </div>
      )}

      {selectedTab === 'all' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {users.map((user) => (
            <UserCard key={user.id} user={user} showActions={true} />
          ))}
        </div>
      )}

      {/* Modal de Edição de Usuário */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Edit className="w-5 h-5" />
              Editar Usuário
            </DialogTitle>
          </DialogHeader>

          <form onSubmit={handleEditSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              {/* Nome */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nome Completo *
                </label>
                <input
                  type="text"
                  value={editFormData.name}
                  onChange={(e) => setEditFormData({ ...editFormData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                  required
                />
              </div>

              {/* Email */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email *
                </label>
                <input
                  type="email"
                  value={editFormData.email}
                  onChange={(e) => setEditFormData({ ...editFormData, email: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                  required
                />
              </div>

              {/* Telefone */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Telefone
                </label>
                <input
                  type="tel"
                  value={editFormData.phone}
                  onChange={(e) => setEditFormData({ ...editFormData, phone: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="(11) 99999-9999"
                />
              </div>

              {/* Empresa/Seguradora */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Empresa/Seguradora
                </label>
                <select
                  value={editFormData.company}
                  onChange={(e) => setEditFormData({ ...editFormData, company: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="">Selecione...</option>
                  <option value="AVLA">AVLA</option>
                  <option value="ESSOR">ESSOR</option>
                  <option value="DAYCOVAL">DAYCOVAL</option>
                  <option value="Safe2Go">Safe2Go</option>
                  <option value="Outro">Outro</option>
                </select>
              </div>

              {/* Role */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tipo de Usuário *
                </label>
                <select
                  value={editFormData.role}
                  onChange={(e) => setEditFormData({ ...editFormData, role: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                  required
                >
                  <option value="cliente">👤 Cliente</option>
                  <option value="administrador">👑 Administrador</option>
                </select>
              </div>

              {/* Status */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Status *
                </label>
                <select
                  value={editFormData.status}
                  onChange={(e) => setEditFormData({ ...editFormData, status: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                  required
                >
                  <option value="pendente">🟡 Pendente</option>
                  <option value="aprovado">🟢 Aprovado</option>
                  <option value="rejeitado">🔴 Rejeitado</option>
                </select>
              </div>
            </div>

            {/* Botões de Ação */}
            <div className="flex justify-end gap-3 pt-4 border-t">
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsEditDialogOpen(false)}
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                className="bg-purple-600 hover:bg-purple-700 text-white"
              >
                Salvar Alterações
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default UserManagement;
