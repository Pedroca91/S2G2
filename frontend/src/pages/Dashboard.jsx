import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { FileText, CheckCircle2, Clock, TrendingUp, Download } from 'lucide-react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Button } from '../components/ui/button';
import { toast } from 'sonner';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const Dashboard = () => {
  const [stats, setStats] = useState({
    total_cases: 0,
    completed_cases: 0,
    pending_cases: 0,
    completion_percentage: 0,
  });
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const [statsRes, chartsRes] = await Promise.all([
        axios.get(`${API}/dashboard/stats`),
        axios.get(`${API}/dashboard/charts`),
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

  const generatePDF = async () => {
    try {
      toast.info('Gerando PDF...');
      
      const pdf = new jsPDF('p', 'mm', 'a4');
      const pageWidth = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();
      
      // Header
      pdf.setFillColor(147, 51, 234);
      pdf.rect(0, 0, pageWidth, 40, 'F');
      pdf.setTextColor(255, 255, 255);
      pdf.setFontSize(24);
      pdf.setFont('helvetica', 'bold');
      pdf.text('Relatório Semanal - Safe2Go', pageWidth / 2, 20, { align: 'center' });
      
      pdf.setFontSize(12);
      pdf.setFont('helvetica', 'normal');
      const today = new Date().toLocaleDateString('pt-BR');
      pdf.text(`Data de Emissão: ${today}`, pageWidth / 2, 30, { align: 'center' });
      
      // Stats Section
      pdf.setTextColor(30, 41, 59);
      pdf.setFontSize(16);
      pdf.setFont('helvetica', 'bold');
      pdf.text('Estatísticas Gerais', 20, 55);
      
      pdf.setFontSize(12);
      pdf.setFont('helvetica', 'normal');
      pdf.text(`Total de Casos: ${stats.total_cases}`, 20, 70);
      pdf.text(`Casos Concluídos: ${stats.completed_cases}`, 20, 80);
      pdf.text(`Casos Pendentes: ${stats.pending_cases}`, 20, 90);
      pdf.text(`Taxa de Conclusão: ${stats.completion_percentage}%`, 20, 100);
      
      // Chart capture
      const chartElement = document.getElementById('dashboard-charts');
      if (chartElement) {
        const canvas = await html2canvas(chartElement, {
          scale: 2,
          backgroundColor: '#ffffff',
        });
        const imgData = canvas.toDataURL('image/png');
        const imgWidth = pageWidth - 40;
        const imgHeight = (canvas.height * imgWidth) / canvas.width;
        
        pdf.addPage();
        pdf.setFontSize(16);
        pdf.setFont('helvetica', 'bold');
        pdf.text('Gráficos da Última Semana', 20, 20);
        pdf.addImage(imgData, 'PNG', 20, 30, imgWidth, imgHeight);
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
        <div>
          <h1 className="page-title" data-testid="dashboard-title">Dashboard</h1>
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
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="stat-card" data-testid="total-cases-card">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-purple-100 rounded-xl">
              <FileText className="w-6 h-6 text-purple-600" />
            </div>
            <TrendingUp className="w-5 h-5 text-gray-400" />
          </div>
          <p className="text-sm text-gray-600 mb-1">Total de Casos</p>
          <p className="text-3xl font-bold text-gray-900">{stats.total_cases}</p>
        </div>

        <div className="stat-card" data-testid="completed-cases-card">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-green-100 rounded-xl">
              <CheckCircle2 className="w-6 h-6 text-green-600" />
            </div>
          </div>
          <p className="text-sm text-gray-600 mb-1">Casos Concluídos</p>
          <p className="text-3xl font-bold text-green-600">{stats.completed_cases}</p>
        </div>

        <div className="stat-card" data-testid="pending-cases-card">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-yellow-100 rounded-xl">
              <Clock className="w-6 h-6 text-yellow-600" />
            </div>
          </div>
          <p className="text-sm text-gray-600 mb-1">Casos Pendentes</p>
          <p className="text-3xl font-bold text-yellow-600">{stats.pending_cases}</p>
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

      {/* Charts */}
      <div id="dashboard-charts" className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bar Chart */}
        <div className="card" data-testid="bar-chart-container">
          <h3 className="text-lg font-semibold mb-4">Casos por Dia (Últimos 7 Dias)</h3>
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