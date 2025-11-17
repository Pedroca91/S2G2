import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Play, Square, Clock, User } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const SupportPanel = () => {
  const [currentActivities, setCurrentActivities] = useState([]);
  const [recentActivities, setRecentActivities] = useState([]);
  const [formData, setFormData] = useState({
    responsible: '',
    activity: '',
    case_id: '',
    notes: '',
    time_spent: 0,
  });

  useEffect(() => {
    fetchActivities();
    const interval = setInterval(fetchActivities, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchActivities = async () => {
    try {
      const [currentRes, recentRes] = await Promise.all([
        axios.get(`${API}/activities/current`),
        axios.get(`${API}/activities?limit=20`),
      ]);
      setCurrentActivities(currentRes.data);
      setRecentActivities(recentRes.data);
    } catch (error) {
      console.error('Erro ao carregar atividades:', error);
    }
  };

  const handleStartActivity = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/activities`, {
        ...formData,
        is_current: true,
      });
      toast.success('Atividade iniciada!');
      setFormData({
        responsible: formData.responsible,
        activity: '',
        case_id: '',
        notes: '',
        time_spent: 0,
      });
      fetchActivities();
    } catch (error) {
      console.error('Erro ao iniciar atividade:', error);
      toast.error('Erro ao iniciar atividade');
    }
  };

  const handleStopActivity = async (activityId) => {
    try {
      await axios.put(`${API}/activities/${activityId}/stop`);
      toast.success('Atividade finalizada!');
      fetchActivities();
    } catch (error) {
      console.error('Erro ao parar atividade:', error);
      toast.error('Erro ao parar atividade');
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title" data-testid="support-panel-title">Painel do Suporte</h1>
        <p className="page-subtitle">Registre e acompanhe suas atividades</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Start Activity Form */}
        <Card>
          <CardHeader>
            <CardTitle>Iniciar Nova Atividade</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleStartActivity} className="space-y-4">
              <div>
                <Label htmlFor="responsible">Seu Nome</Label>
                <Input
                  id="responsible"
                  data-testid="responsible-name-input"
                  value={formData.responsible}
                  onChange={(e) => setFormData({ ...formData, responsible: e.target.value })}
                  required
                  placeholder="Nome do responsável"
                />
              </div>
              <div>
                <Label htmlFor="activity">O que você está fazendo?</Label>
                <Input
                  id="activity"
                  data-testid="activity-input"
                  value={formData.activity}
                  onChange={(e) => setFormData({ ...formData, activity: e.target.value })}
                  required
                  placeholder="Ex: Analisando problema de login"
                />
              </div>
              <div>
                <Label htmlFor="case_id">ID do Caso (Opcional)</Label>
                <Input
                  id="case_id"
                  data-testid="case-id-input"
                  value={formData.case_id}
                  onChange={(e) => setFormData({ ...formData, case_id: e.target.value })}
                  placeholder="ID do caso relacionado"
                />
              </div>
              <div>
                <Label htmlFor="notes">Notas (Opcional)</Label>
                <Textarea
                  id="notes"
                  data-testid="notes-input"
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  placeholder="Anotações sobre a atividade"
                  rows={3}
                />
              </div>
              <Button
                type="submit"
                data-testid="start-activity-btn"
                className="w-full bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800"
              >
                <Play className="w-4 h-4 mr-2" />
                Iniciar Atividade
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Current Activities */}
        <Card>
          <CardHeader>
            <CardTitle>Atividades em Andamento</CardTitle>
          </CardHeader>
          <CardContent>
            {currentActivities.length === 0 ? (
              <div className="text-center py-8 text-gray-500" data-testid="no-current-activities">
                Nenhuma atividade em andamento
              </div>
            ) : (
              <div className="space-y-3" data-testid="current-activities-list">
                {currentActivities.map((activity) => (
                  <div
                    key={activity.id}
                    data-testid={`current-activity-${activity.id}`}
                    className="p-4 bg-green-50 border border-green-200 rounded-lg"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <User className="w-4 h-4 text-green-600" />
                        <span className="font-medium text-green-900">{activity.responsible}</span>
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleStopActivity(activity.id)}
                        data-testid={`stop-activity-${activity.id}`}
                        className="text-red-600 hover:bg-red-50"
                      >
                        <Square className="w-3 h-3 mr-1" />
                        Parar
                      </Button>
                    </div>
                    <p className="text-sm text-gray-700 mb-1">{activity.activity}</p>
                    {activity.case_id && (
                      <p className="text-xs text-gray-500">Caso: {activity.case_id}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Activities */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Histórico de Atividades</CardTitle>
        </CardHeader>
        <CardContent>
          {recentActivities.length === 0 ? (
            <div className="text-center py-8 text-gray-500" data-testid="no-recent-activities">
              Nenhuma atividade registrada
            </div>
          ) : (
            <div className="space-y-3" data-testid="recent-activities-list">
              {recentActivities.map((activity) => (
                <div
                  key={activity.id}
                  data-testid={`activity-${activity.id}`}
                  className="p-4 bg-gray-50 rounded-lg border border-gray-200"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <User className="w-4 h-4 text-gray-600" />
                      <span className="font-medium text-gray-900">{activity.responsible}</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <Clock className="w-3 h-3" />
                      {new Date(activity.created_at).toLocaleString('pt-BR')}
                    </div>
                  </div>
                  <p className="text-sm text-gray-700 mb-1">{activity.activity}</p>
                  {activity.case_id && (
                    <p className="text-xs text-blue-600 mb-1">Caso: {activity.case_id}</p>
                  )}
                  {activity.notes && (
                    <p className="text-xs text-gray-500 italic">{activity.notes}</p>
                  )}
                  {activity.time_spent > 0 && (
                    <p className="text-xs text-gray-500 mt-1">
                      Tempo gasto: {activity.time_spent} minutos
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default SupportPanel;