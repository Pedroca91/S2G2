import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { FileText, CheckCircle2, Clock, TrendingUp, Download, Wifi } from 'lucide-react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Button } from '../components/ui/button';
import { toast } from 'sonner';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const Dashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    total_cases: 0,
    completed_cases: 0,
    pending_cases: 0,
    in_development_cases: 0,
    waiting_client_cases: 0,
    completion_percentage: 0,
    cases_by_seguradora: {},
  });
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);


  useEffect(() => {
    fetchDashboardData();
    // Recarregar dados a cada 60 segundos
    const interval = setInterval(fetchDashboardData, 60000);
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const [statsRes, chartsRes] = await Promise.all([
        axios.get(`${API}/dashboard/stats`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/dashboard/charts`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
      ]);
      setStats(statsRes.data);
      setChartData(chartsRes.data);
    } catch (error) {
      console.error('Erro ao carregar dados do dashboard:', error);
      toast.error('Erro ao carregar dados do dashboard');
    } finally {
      setLoading(false);
    }
  };

  const handleCardClick = (status) => {
    navigate(`/cases?status=${status}`);
  };

  const generatePDF = async () => {
    try {
      toast.info('Gerando PDF...');
      
      const token = localStorage.getItem('token');
      // Buscar dados de categorias e análise recorrente
      const [categoryResponse, recurrentResponse] = await Promise.all([
        axios.get(`${API}/cases/categories`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/cases/analytics/recurrent`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      const categoryData = categoryResponse.data;
      const recurrentData = recurrentResponse.data;
      
      const pdf = new jsPDF('p', 'mm', 'a4');
      const pageWidth = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();
      
      // ============= PÁGINA 1 =============
      // Header mais compacto
      pdf.setFillColor(147, 51, 234);
      pdf.rect(0, 0, pageWidth, 28, 'F');
      pdf.setTextColor(255, 255, 255);
      pdf.setFontSize(18);
      pdf.setFont('helvetica', 'bold');
      pdf.text('Relatório Semanal - Safe2Go', pageWidth / 2, 14, { align: 'center' });
      
      pdf.setFontSize(9);
      pdf.setFont('helvetica', 'normal');
      const today = new Date().toLocaleDateString('pt-BR');
      pdf.text(`Data de Emissão: ${today}`, pageWidth / 2, 22, { align: 'center' });
      
      // Stats Section - mais compacto
      pdf.setTextColor(30, 41, 59);
      pdf.setFontSize(12);
      pdf.setFont('helvetica', 'bold');
      pdf.text('Estatísticas Gerais', 20, 38);
      
      pdf.setFontSize(9);
      pdf.setFont('helvetica', 'normal');
      pdf.text(`Total: ${stats.total_cases}`, 20, 46);
      pdf.text(`Concluídos: ${stats.completed_cases}`, 20, 52);
      pdf.text(`Pendentes: ${stats.pending_cases}`, 20, 58);
      pdf.text(`Em Desenvolvimento: ${stats.in_development_cases || 0}`, 20, 64);
      pdf.text(`Aguardando: ${stats.waiting_client_cases}`, 20, 70);
      pdf.text(`Taxa de Conclusão: ${stats.completion_percentage}%`, 20, 76);
      
      // Chamados por Seguradora - duas colunas
      pdf.setFontSize(11);
      pdf.setFont('helvetica', 'bold');
      pdf.text('Por Seguradora:', 20, 88);
      pdf.setFontSize(9);
      pdf.setFont('helvetica', 'normal');
      
      let yPos = 95;
      const seguradoras = stats.cases_by_seguradora || {};
      const segKeys = Object.keys(seguradoras);
      segKeys.forEach((seguradora, idx) => {
        const xPos = idx % 2 === 0 ? 20 : 105;
        if (idx % 2 === 0 && idx > 0) yPos += 6;
        pdf.text(`${seguradora}: ${seguradoras[seguradora]}`, xPos, yPos);
      });
      if (segKeys.length % 2 !== 0) yPos += 6;
      
      // Distribuição por Categoria - Top 7 apenas
      yPos += 10;
      pdf.setFontSize(11);
      pdf.setFont('helvetica', 'bold');
      pdf.text('Top 7 Categorias:', 20, yPos);
      yPos += 6;
      
      pdf.setFontSize(7);
      pdf.setFont('helvetica', 'normal');
      
      const maxCount = Math.max(...categoryData.map(c => c.count));
      const barMaxWidth = 70;
      
      categoryData.slice(0, 7).forEach((category, index) => {
        const barWidth = (category.count / maxCount) * barMaxWidth;
        const percentage = ((category.count / stats.total_cases) * 100).toFixed(1);
        
        const colors = [
          [239, 68, 68], [249, 115, 22], [245, 158, 11], [234, 179, 8],
          [132, 204, 22], [34, 197, 94], [20, 184, 166]
        ];
        const color = colors[index % colors.length];
        
        pdf.setTextColor(30, 41, 59);
        pdf.setFont('helvetica', 'normal');
        const categoryName = category.category.length > 18 
          ? category.category.substring(0, 18) + '...' 
          : category.category;
        pdf.text(categoryName, 20, yPos + 2.5);
        
        pdf.setFillColor(...color);
        pdf.rect(80, yPos, barWidth, 3.5, 'F');
        
        pdf.setFont('helvetica', 'bold');
        pdf.text(`${category.count}`, 155, yPos + 2.5);
        pdf.setFont('helvetica', 'normal');
        pdf.text(`(${percentage}%)`, 162, yPos + 2.5);
        
        yPos += 6;
      });
      
      // Chart capture - Gráficos da Última Semana na mesma página se couber
      const chartElement = document.getElementById('dashboard-charts');
      if (chartElement && yPos < 200) {
        yPos += 8;
        pdf.setTextColor(30, 41, 59);
        pdf.setFontSize(11);
        pdf.setFont('helvetica', 'bold');
        pdf.text('Gráficos da Semana:', 20, yPos);
        
        const canvas = await html2canvas(chartElement, {
          scale: 1.5,
          backgroundColor: '#ffffff',
        });
        const imgData = canvas.toDataURL('image/png');
        const imgWidth = pageWidth - 40;
        const imgHeight = Math.min((canvas.height * imgWidth) / canvas.width, 75);
        
        pdf.addImage(imgData, 'PNG', 20, yPos + 3, imgWidth, imgHeight);
      }
      
      // ============= PÁGINA 2 =============
      pdf.addPage();
      
      // Se não coube na página 1, adicionar gráfico aqui
      if (chartElement && yPos >= 200) {
        pdf.setTextColor(30, 41, 59);
        pdf.setFontSize(11);
        pdf.setFont('helvetica', 'bold');
        pdf.text('Gráficos da Última Semana:', 20, 20);
        
        const canvas = await html2canvas(chartElement, {
          scale: 1.5,
          backgroundColor: '#ffffff',
        });
        const imgData = canvas.toDataURL('image/png');
        const imgWidth = pageWidth - 40;
        const imgHeight = Math.min((canvas.height * imgWidth) / canvas.width, 100);
        
        pdf.addImage(imgData, 'PNG', 20, 25, imgWidth, imgHeight);
        yPos = 25 + imgHeight + 10;
      } else {
        yPos = 20;
      }
      
      // Análise de Casos Recorrentes - COMPACTO
      if (recurrentData && recurrentData.length > 0) {
        pdf.setTextColor(30, 41, 59);
        pdf.setFontSize(12);
        pdf.setFont('helvetica', 'bold');
        pdf.text('Análise de Casos Recorrentes', 20, yPos);
        
        pdf.setFontSize(8);
        pdf.setFont('helvetica', 'normal');
        pdf.setTextColor(100, 116, 139);
        pdf.text('Top 3 Categorias Prioritárias', 20, yPos + 6);
        
        yPos += 14;
        
        const top3 = recurrentData.slice(0, 3);
        
        top3.forEach((item, index) => {
          pdf.setFontSize(10);
          pdf.setFont('helvetica', 'bold');
          pdf.setTextColor(147, 51, 234);
          pdf.text(`${index + 1}.`, 20, yPos);
          
          pdf.setTextColor(30, 41, 59);
          pdf.setFontSize(10);
          pdf.text(item.category, 27, yPos);
          
          yPos += 5;
          
          pdf.setFontSize(8);
          pdf.setFont('helvetica', 'normal');
          pdf.setTextColor(71, 85, 105);
          pdf.text(`${item.count} casos (${item.percentage}%)`, 27, yPos);
          
          yPos += 4;
          
          let urgencyText = '';
          let urgencyColor = [0, 0, 0];
          if (item.count >= 9) {
            urgencyText = 'CRÍTICO - Automação URGENTE';
            urgencyColor = [220, 38, 38];
          } else if (item.count >= 5) {
            urgencyText = 'ALTO - Automação recomendada';
            urgencyColor = [234, 88, 12];
          } else {
            urgencyText = 'MÉDIO - Considerar automação';
            urgencyColor = [234, 179, 8];
          }
          
          pdf.setTextColor(...urgencyColor);
          pdf.setFontSize(7);
          pdf.setFont('helvetica', 'bold');
          pdf.text(urgencyText, 27, yPos);
          
          yPos += 4;
          
          let recommendation = '';
          if (item.count >= 9) {
            recommendation = `${item.count} casos recorrentes demandam automação urgente (redução até 80% trabalho manual).`;
          } else if (item.count >= 5) {
            recommendation = `${item.count} casos recorrentes - automação recomendada para otimizar processos.`;
          } else {
            recommendation = `Considerar templates para agilizar ${item.count} casos desta categoria.`;
          }
          
          pdf.setTextColor(71, 85, 105);
          pdf.setFontSize(7);
          pdf.setFont('helvetica', 'normal');
          const lines = pdf.splitTextToSize(recommendation, pageWidth - 55);
          pdf.text(lines, 27, yPos);
          
          yPos += (lines.length * 3) + 6;
        });
        
        yPos += 3;
        if (yPos < pageHeight - 25) {
          pdf.setDrawColor(147, 51, 234);
          pdf.setLineWidth(0.2);
          pdf.line(20, yPos, pageWidth - 20, yPos);
          
          yPos += 5;
          pdf.setTextColor(100, 116, 139);
          pdf.setFontSize(7);
          pdf.setFont('helvetica', 'italic');
          const noteText = 'Nota: Priorize automação das categorias com maior incidência para reduzir carga operacional.';
          const noteLines = pdf.splitTextToSize(noteText, pageWidth - 40);
          pdf.text(noteLines, 20, yPos);
        }
      }
      
      // Footer
      const totalPages = pdf.internal.pages.length - 1;
      for (let i = 1; i <= totalPages; i++) {
        pdf.setPage(i);
        pdf.setFontSize(10);
        pdf.setTextColor(100, 116, 139);
        pdf.text(
          `Página ${i} de ${totalPages}`,
          pageWidth / 2,
          pageHeight - 10,
          { align: 'center' }
        );
      }
      
      pdf.save(`relatorio-safe2go-${today.replace(/\//g, '-')}.pdf`);
      toast.success('PDF gerado com sucesso!');
    } catch (error) {
      console.error('Erro ao gerar PDF:', error);
      toast.error('Erro ao gerar PDF');
    }
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
      <div className="page-header flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="page-title" data-testid="dashboard-title">Dashboard</h1>
          </div>
          <p className="page-subtitle">Visão geral do sistema de suporte</p>
        </div>
        <Button
          onClick={generatePDF}
          data-testid="generate-pdf-btn"
          className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white shadow-lg"
        >
          <Download className="w-4 h-4 mr-2" />
          Gerar Relatório PDF
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6 mb-8">
        <div 
          className="stat-card cursor-pointer" 
          data-testid="total-cases-card"
          onClick={() => navigate('/cases')}
        >
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-purple-100 rounded-xl">
              <FileText className="w-6 h-6 text-purple-600" />
            </div>
            <TrendingUp className="w-5 h-5 text-gray-400" />
          </div>
          <p className="text-sm text-gray-600 mb-1">Total de Chamados</p>
          <p className="text-3xl font-bold text-gray-900">{stats.total_cases}</p>
        </div>

        <div 
          className="stat-card cursor-pointer" 
          data-testid="completed-cases-card"
          onClick={() => handleCardClick('Concluído')}
        >
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-green-100 rounded-xl">
              <CheckCircle2 className="w-6 h-6 text-green-600" />
            </div>
          </div>
          <p className="text-sm text-gray-600 mb-1">Concluídos</p>
          <p className="text-3xl font-bold text-green-600">{stats.completed_cases}</p>
        </div>

        <div 
          className="stat-card cursor-pointer" 
          data-testid="pending-cases-card"
          onClick={() => handleCardClick('Pendente')}
        >
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-yellow-100 rounded-xl">
              <Clock className="w-6 h-6 text-yellow-600" />
            </div>
          </div>
          <p className="text-sm text-gray-600 mb-1">Pendentes</p>
          <p className="text-3xl font-bold text-yellow-600">{stats.pending_cases}</p>
        </div>

        <div 
          className="stat-card cursor-pointer" 
          data-testid="in-development-cases-card"
          onClick={() => handleCardClick('Em Desenvolvimento')}
        >
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-blue-100 rounded-xl">
              <Wifi className="w-6 h-6 text-blue-600" />
            </div>
          </div>
          <p className="text-sm text-gray-600 mb-1">Em Desenvolvimento</p>
          <p className="text-3xl font-bold text-blue-600">{stats.in_development_cases || 0}</p>
        </div>

        <div 
          className="stat-card cursor-pointer" 
          data-testid="waiting-client-cases-card"
          onClick={() => handleCardClick('Aguardando resposta do cliente')}
        >
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-orange-100 rounded-xl">
              <Clock className="w-6 h-6 text-orange-600" />
            </div>
          </div>
          <p className="text-sm text-gray-600 mb-1">Aguardando Cliente</p>
          <p className="text-3xl font-bold text-orange-600">{stats.waiting_client_cases || 0}</p>
        </div>

        <div className="stat-card" data-testid="completion-percentage-card">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-purple-100 rounded-xl">
              <TrendingUp className="w-6 h-6 text-purple-600" />
            </div>
          </div>
          <p className="text-sm text-gray-600 mb-1">Taxa de Conclusão</p>
          <p className="text-3xl font-bold text-purple-600">{stats.completion_percentage}%</p>
        </div>
      </div>

      {/* Alerta de Análise Recorrente */}
      <div 
        className="bg-gradient-to-r from-orange-500 to-red-600 rounded-2xl p-6 mb-8 cursor-pointer hover:shadow-2xl transition-all transform hover:scale-[1.02]"
        onClick={() => navigate('/analytics')}
      >
        <div className="flex items-center justify-between text-white">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-white bg-opacity-20 rounded-lg">
                <TrendingUp className="w-6 h-6" />
              </div>
              <h3 className="text-2xl font-bold">Análise de Chamados Recorrentes</h3>
            </div>
            <p className="text-white text-opacity-90 mb-3">
              Identifique padrões e erros que se repetem para criar automações e melhorar a eficiência da equipe
            </p>
            <div className="flex items-center gap-4 text-sm">
              <span className="bg-white bg-opacity-20 px-3 py-1 rounded-full">
                📊 Análise por Categoria
              </span>
              <span className="bg-white bg-opacity-20 px-3 py-1 rounded-full">
                🔍 Chamados Similares
              </span>
              <span className="bg-white bg-opacity-20 px-3 py-1 rounded-full">
                ⚡ Sugestões de Automação
              </span>
            </div>
          </div>
          <div className="hidden lg:flex items-center">
            <div className="text-right mr-4">
              <p className="text-4xl font-bold">{stats.total_cases}</p>
              <p className="text-sm opacity-90">casos analisados</p>
            </div>
            <div className="w-12 h-12 bg-white bg-opacity-20 rounded-full flex items-center justify-center">
              <span className="text-2xl">→</span>
            </div>
          </div>
        </div>
      </div>

      {/* Chamados por Seguradora */}
      {Object.keys(stats.cases_by_seguradora).length > 0 && (
        <div className="card mb-6" data-testid="seguradoras-stats">
          <h3 className="text-lg font-semibold mb-4">Chamados por Seguradora</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(stats.cases_by_seguradora).map(([seguradora, count]) => (
              <div 
                key={seguradora} 
                className="flex items-center justify-between p-4 bg-gradient-to-r from-purple-50 to-purple-100 rounded-xl cursor-pointer hover:shadow-lg hover:scale-105 transition-all duration-200"
                onClick={() => navigate(`/cases?seguradora=${seguradora}`)}
                title={`Clique para ver todos os chamados da ${seguradora}`}
              >
                <div className="flex-1">
                  <p className="text-sm text-gray-600 font-medium">{seguradora}</p>
                  <p className="text-2xl font-bold text-purple-600">{count} chamados</p>
                </div>
                <div className="ml-4">
                  <div className="w-10 h-10 bg-purple-200 rounded-full flex items-center justify-center">
                    <span className="text-purple-600 font-bold">→</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Charts */}
      <div id="dashboard-charts" className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bar Chart */}
        <div className="card" data-testid="bar-chart-container">
          <h3 className="text-lg font-semibold mb-4">Chamados por Dia (Últimos 7 Dias)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="date" stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                }}
              />
              <Legend />
              <Bar dataKey="completed" fill="#10b981" name="Concluídos" radius={[8, 8, 0, 0]} />
              <Bar dataKey="pending" fill="#f59e0b" name="Pendentes" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Line Chart */}
        <div className="card" data-testid="line-chart-container">
          <h3 className="text-lg font-semibold mb-4">Evolução Semanal</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="date" stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'white',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="completed"
                stroke="#10b981"
                strokeWidth={3}
                name="Concluídos"
                dot={{ fill: '#10b981', r: 5 }}
              />
              <Line
                type="monotone"
                dataKey="pending"
                stroke="#f59e0b"
                strokeWidth={3}
                name="Pendentes"
                dot={{ fill: '#f59e0b', r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;