import React, { useState, useEffect, useRef } from 'react';
import {
  Database,
  RefreshCw,
  Download,
  Upload,
  Calendar,
  Clock,
  Bell,
  HardDrive,
  Plus,
  Trash2,
  CheckCircle,
  AlertTriangle,
  Play,
  FileSpreadsheet,
  FileArchive,
  Code,
  Copy,
  Check,
} from 'lucide-react';
import {
  SettingsData,
  RecurringTask,
  RecurringTaskForm,
  NotificationSettings,
} from '../types';
import {
  fetchSettings,
  createBackup,
  restoreBackup,
  uploadAndRestoreBackup,
  createRecurringTask,
  updateRecurringTask,
  deleteRecurringTask,
  triggerRecurringGeneration,
  fetchNotificationSettings,
  testNotification,
} from '../api';

const WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

export function SettingsView() {
  const [activeTab, setActiveTab] = useState<'backups' | 'recurring' | 'export' | 'notifications' | 'system'>('backups');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Settings & Backups state
  const [settings, setSettings] = useState<SettingsData | null>(null);
  const [isBackingUp, setIsBackingUp] = useState(false);
  const [restoreConfirmName, setRestoreConfirmName] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Recurring Tasks state
  const [isNewRecurringOpen, setIsNewRecurringOpen] = useState(false);
  const [recurringForm, setRecurringForm] = useState<RecurringTaskForm>({
    title: '',
    rule: 'daily',
    start_date: new Date().toISOString().split('T')[0],
    priority: 'medium',
    category: 'work',
    estimated_min: 30,
    weekday: 0,
    day_of_month: 1,
    end_date: '',
  });
  const [isGenerating, setIsGenerating] = useState(false);

  // Notifications state
  const [notifSettings, setNotifSettings] = useState<NotificationSettings | null>(null);
  const [testingNotif, setTestingNotif] = useState<'morning' | 'evening' | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [sData, nData] = await Promise.all([
        fetchSettings(),
        fetchNotificationSettings(),
      ]);
      setSettings(sData);
      setNotifSettings(nData);
    } catch (err: any) {
      setError(err.message || 'Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const notifySuccess = (msg: string) => {
    setSuccessMsg(msg);
    setTimeout(() => setSuccessMsg(null), 4000);
  };

  // ---------------------------------------------------------------------------
  // Backup Handlers
  // ---------------------------------------------------------------------------
  const handleCreateBackup = async () => {
    try {
      setIsBackingUp(true);
      const res = await createBackup();
      notifySuccess(`Backup created successfully: ${res.filename}`);
      await loadData();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsBackingUp(false);
    }
  };

  const handleConfirmRestore = async (filename: string) => {
    try {
      setLoading(true);
      const res = await restoreBackup(filename);
      setRestoreConfirmName(null);
      notifySuccess(res.message);
      await loadData();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.name.endsWith('.db')) {
      setError('Please select a valid SQLite .db database file.');
      return;
    }
    if (!confirm(`Restore database from file "${file.name}"? Current state will be safely snapshotted.`)) {
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }
    try {
      setLoading(true);
      const res = await uploadAndRestoreBackup(file);
      notifySuccess(res.message);
      await loadData();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  // ---------------------------------------------------------------------------
  // Recurring Handlers
  // ---------------------------------------------------------------------------
  const handleCreateRecurring = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!recurringForm.title.trim()) return;
    try {
      setLoading(true);
      await createRecurringTask({
        ...recurringForm,
        title: recurringForm.title.trim(),
        estimated_min: recurringForm.estimated_min ? Number(recurringForm.estimated_min) : null,
        weekday: recurringForm.rule === 'weekly' ? Number(recurringForm.weekday) : null,
        day_of_month: recurringForm.rule === 'monthly' ? Number(recurringForm.day_of_month) : null,
        end_date: recurringForm.end_date || null,
      });
      setIsNewRecurringOpen(false);
      setRecurringForm({
        title: '',
        rule: 'daily',
        start_date: new Date().toISOString().split('T')[0],
        priority: 'medium',
        category: 'work',
        estimated_min: 30,
        weekday: 0,
        day_of_month: 1,
        end_date: '',
      });
      notifySuccess('Recurring task rule created!');
      await loadData();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleRecurringActive = async (task: RecurringTask) => {
    try {
      const nextActive = task.active === 1 ? 0 : 1;
      await updateRecurringTask(task.id, { active: nextActive });
      notifySuccess(`Recurring rule "${task.title}" is now ${nextActive === 1 ? 'active' : 'inactive'}.`);
      await loadData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDeleteRecurring = async (task: RecurringTask) => {
    if (!confirm(`Delete recurring rule "${task.title}"? Existing task instances will be preserved.`)) return;
    try {
      await deleteRecurringTask(task.id);
      notifySuccess('Recurring rule deleted.');
      await loadData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleGenerateToday = async () => {
    try {
      setIsGenerating(true);
      const res = await triggerRecurringGeneration();
      notifySuccess(`Generator ran: ${res.generated_count} task(s) created for today!`);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsGenerating(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Notification Test & Copy Handlers
  // ---------------------------------------------------------------------------
  const handleTestNotification = async (mode: 'morning' | 'evening') => {
    try {
      setTestingNotif(mode);
      const res = await testNotification(mode);
      notifySuccess(`Notification sent: "${res.title}" — ${res.message}`);
      await loadData();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setTestingNotif(null);
    }
  };

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2500);
  };

  if (loading && !settings) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh', color: '#94a3b8' }}>
        <RefreshCw size={28} className="animate-spin" style={{ marginRight: '12px' }} />
        <span>Loading system settings...</span>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '1.875rem', fontWeight: '800', color: '#f8fafc', letterSpacing: '-0.025em' }}>
            ⚙️ System & Settings
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginTop: '0.25rem' }}>
            Production management for database snapshots, recurring task rules, portable data exports, and Windows desktop notifications.
          </p>
        </div>

        {/* Global Alert Banners */}
        {successMsg && (
          <div
            style={{
              padding: '0.75rem 1.25rem',
              borderRadius: '10px',
              backgroundColor: 'rgba(16, 185, 129, 0.15)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              color: '#34d399',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              fontSize: '0.9rem',
              fontWeight: '600',
            }}
          >
            <CheckCircle size={18} />
            <span>{successMsg}</span>
          </div>
        )}

        {error && (
          <div
            style={{
              padding: '0.75rem 1.25rem',
              borderRadius: '10px',
              backgroundColor: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: '#f87171',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              fontSize: '0.9rem',
              fontWeight: '600',
            }}
          >
            <AlertTriangle size={18} />
            <span>{error}</span>
            <button
              onClick={() => setError(null)}
              style={{ background: 'none', border: 'none', color: '#f87171', cursor: 'pointer', marginLeft: '8px' }}
            >
              ✕
            </button>
          </div>
        )}
      </div>

      {/* Modern Navigation Tabs */}
      <div
        style={{
          display: 'flex',
          gap: '0.5rem',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          paddingBottom: '0.5rem',
          overflowX: 'auto',
        }}
      >
        {[
          { id: 'backups', label: 'Snapshots & Backups', icon: Database },
          { id: 'recurring', label: 'Recurring Automation', icon: RefreshCw },
          { id: 'export', label: 'Data Export & Portability', icon: Download },
          { id: 'notifications', label: 'Desktop Notifications', icon: Bell },
          { id: 'system', label: 'Diagnostics & Info', icon: HardDrive },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.6rem 1.1rem',
                borderRadius: '10px',
                border: 'none',
                background: isActive ? 'linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(59, 130, 246, 0.2))' : 'transparent',
                color: isActive ? '#38bdf8' : '#94a3b8',
                fontWeight: isActive ? '700' : '500',
                fontSize: '0.9rem',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                borderBottom: isActive ? '2px solid #06b6d4' : '2px solid transparent',
              }}
            >
              <Icon size={16} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* ===================================================================== */}
      {/* TAB 1: SNAPSHOTS & BACKUPS */}
      {/* ===================================================================== */}
      {activeTab === 'backups' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Action Header Card */}
          <div className="bento-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: '700', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Database size={20} color="#06b6d4" />
                SQLite Database Snapshots
              </h2>
              <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginTop: '0.25rem' }}>
                Create point-in-time consistent backups via SQLite Backup API. Restores automatically create safety snapshots.
              </p>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileUpload}
                accept=".db"
                style={{ display: 'none' }}
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="btn-secondary"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.65rem 1.25rem',
                  borderRadius: '10px',
                  cursor: 'pointer',
                  fontSize: '0.875rem',
                }}
              >
                <Upload size={16} />
                <span>Upload & Restore .db</span>
              </button>

              <button
                onClick={handleCreateBackup}
                disabled={isBackingUp}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.65rem 1.25rem',
                  borderRadius: '10px',
                  border: 'none',
                  background: 'linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%)',
                  color: '#fff',
                  fontWeight: '700',
                  fontSize: '0.875rem',
                  cursor: isBackingUp ? 'not-allowed' : 'pointer',
                  boxShadow: '0 4px 14px rgba(6, 182, 212, 0.3)',
                }}
              >
                <Plus size={16} />
                <span>{isBackingUp ? 'Creating Backup...' : 'Create Instant Backup'}</span>
              </button>
            </div>
          </div>

          {/* Backup Catalog */}
          <div className="bento-card">
            <h3 style={{ fontSize: '1rem', fontWeight: '700', color: '#f1f5f9', marginBottom: '1rem' }}>
              Available Snapshots ({settings?.backups.length || 0})
            </h3>

            {(!settings?.backups || settings.backups.length === 0) ? (
              <div style={{ textAlign: 'center', padding: '2.5rem', color: '#64748b' }}>
                <Database size={36} style={{ margin: '0 auto 0.75rem auto', opacity: 0.4 }} />
                <p>No snapshots found in backup directory.</p>
                <p style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>Click "Create Instant Backup" above to generate your first snapshot.</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {settings.backups.map((b) => (
                  <div
                    key={b.name}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '0.85rem 1.2rem',
                      borderRadius: '10px',
                      backgroundColor: 'rgba(255, 255, 255, 0.02)',
                      border: '1px solid rgba(255, 255, 255, 0.06)',
                      transition: 'border-color 0.15s ease',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                      <div
                        style={{
                          width: '36px',
                          height: '36px',
                          borderRadius: '8px',
                          backgroundColor: 'rgba(6, 182, 212, 0.1)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: '#06b6d4',
                        }}
                      >
                        <Database size={18} />
                      </div>
                      <div>
                        <div style={{ color: '#f8fafc', fontWeight: '600', fontSize: '0.9rem' }}>{b.name}</div>
                        <div style={{ color: '#64748b', fontSize: '0.75rem', marginTop: '2px' }}>
                          Created: {b.created} • Size: {b.size_mb} MB
                        </div>
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                      <a
                        href={`/api/backups/${b.name}/download`}
                        download={b.name}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.35rem',
                          padding: '0.45rem 0.85rem',
                          borderRadius: '8px',
                          backgroundColor: 'rgba(255, 255, 255, 0.05)',
                          color: '#94a3b8',
                          fontSize: '0.8rem',
                          textDecoration: 'none',
                          fontWeight: '600',
                          border: '1px solid rgba(255, 255, 255, 0.08)',
                        }}
                      >
                        <Download size={14} />
                        <span>Download</span>
                      </a>

                      <button
                        onClick={() => setRestoreConfirmName(b.name)}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.35rem',
                          padding: '0.45rem 0.85rem',
                          borderRadius: '8px',
                          backgroundColor: 'rgba(239, 68, 68, 0.1)',
                          color: '#f87171',
                          fontSize: '0.8rem',
                          fontWeight: '600',
                          border: '1px solid rgba(239, 68, 68, 0.2)',
                          cursor: 'pointer',
                        }}
                      >
                        <RefreshCw size={14} />
                        <span>Restore</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Restore Confirmation Modal */}
          {restoreConfirmName && (
            <div
              style={{
                position: 'fixed',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                backdropFilter: 'blur(8px)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                zIndex: 1000,
                padding: '1rem',
              }}
            >
              <div
                className="bento-card"
                style={{
                  maxWidth: '480px',
                  width: '100%',
                  border: '1px solid rgba(239, 68, 68, 0.4)',
                  boxShadow: '0 20px 40px rgba(0, 0, 0, 0.6)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: '#f87171', marginBottom: '1rem' }}>
                  <AlertTriangle size={24} />
                  <h3 style={{ fontSize: '1.2rem', fontWeight: '700' }}>Confirm Database Restore</h3>
                </div>

                <p style={{ color: '#cbd5e1', fontSize: '0.9rem', lineHeight: '1.5', marginBottom: '1rem' }}>
                  Are you sure you want to restore the database from snapshot <strong style={{ color: '#fff' }}>"{restoreConfirmName}"</strong>?
                </p>

                <div
                  style={{
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    border: '1px solid rgba(16, 185, 129, 0.2)',
                    padding: '0.75rem',
                    borderRadius: '8px',
                    fontSize: '0.8rem',
                    color: '#34d399',
                    marginBottom: '1.5rem',
                  }}
                >
                  ✓ A safety backup of your current database will automatically be saved prior to restoring.
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                  <button
                    onClick={() => setRestoreConfirmName(null)}
                    className="btn-secondary"
                    style={{ padding: '0.6rem 1.2rem', borderRadius: '8px', cursor: 'pointer' }}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => handleConfirmRestore(restoreConfirmName)}
                    style={{
                      padding: '0.6rem 1.2rem',
                      borderRadius: '8px',
                      border: 'none',
                      backgroundColor: '#ef4444',
                      color: '#fff',
                      fontWeight: '700',
                      cursor: 'pointer',
                    }}
                  >
                    Yes, Restore Now
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ===================================================================== */}
      {/* TAB 2: RECURRING TASK AUTOMATION */}
      {/* ===================================================================== */}
      {activeTab === 'recurring' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Action Bar */}
          <div className="bento-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: '700', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <RefreshCw size={20} color="#3b82f6" />
                Recurring Task Schedules
              </h2>
              <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginTop: '0.25rem' }}>
                Automatically populate your daily agenda with Daily, Weekdays, Weekly, and Monthly task routines.
              </p>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
              <button
                onClick={handleGenerateToday}
                disabled={isGenerating}
                className="btn-secondary"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.65rem 1.25rem',
                  borderRadius: '10px',
                  cursor: isGenerating ? 'not-allowed' : 'pointer',
                  fontSize: '0.875rem',
                }}
              >
                <Play size={15} color="#3b82f6" />
                <span>{isGenerating ? 'Evaluating Rules...' : 'Run Scheduler for Today'}</span>
              </button>

              <button
                onClick={() => setIsNewRecurringOpen(true)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.65rem 1.25rem',
                  borderRadius: '10px',
                  border: 'none',
                  background: 'linear-gradient(135deg, #3b82f6 0%, #6366f1 100%)',
                  color: '#fff',
                  fontWeight: '700',
                  fontSize: '0.875rem',
                  cursor: 'pointer',
                  boxShadow: '0 4px 14px rgba(59, 130, 246, 0.3)',
                }}
              >
                <Plus size={16} />
                <span>New Recurring Rule</span>
              </button>
            </div>
          </div>

          {/* Recurring Rules Catalog */}
          <div className="bento-card">
            <h3 style={{ fontSize: '1rem', fontWeight: '700', color: '#f1f5f9', marginBottom: '1rem' }}>
              Configured Recurring Rules ({settings?.recurring_tasks.length || 0})
            </h3>

            {(!settings?.recurring_tasks || settings.recurring_tasks.length === 0) ? (
              <div style={{ textAlign: 'center', padding: '2.5rem', color: '#64748b' }}>
                <Clock size={36} style={{ margin: '0 auto 0.75rem auto', opacity: 0.4 }} />
                <p>No recurring rules configured yet.</p>
                <p style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>Create rules for daily standups, weekly reviews, or monthly routines.</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {settings.recurring_tasks.map((r) => (
                  <div
                    key={r.id}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '0.9rem 1.2rem',
                      borderRadius: '10px',
                      backgroundColor: r.active === 1 ? 'rgba(255, 255, 255, 0.02)' : 'rgba(255, 255, 255, 0.008)',
                      border: r.active === 1 ? '1px solid rgba(255, 255, 255, 0.08)' : '1px solid rgba(255, 255, 255, 0.03)',
                      opacity: r.active === 1 ? 1 : 0.6,
                      transition: 'all 0.15s ease',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                      <button
                        onClick={() => handleToggleRecurringActive(r)}
                        title={r.active === 1 ? 'Click to Pause Rule' : 'Click to Enable Rule'}
                        style={{
                          width: '40px',
                          height: '22px',
                          borderRadius: '11px',
                          backgroundColor: r.active === 1 ? '#06b6d4' : 'rgba(255, 255, 255, 0.1)',
                          position: 'relative',
                          border: 'none',
                          cursor: 'pointer',
                          transition: 'background-color 0.2s',
                        }}
                      >
                        <div
                          style={{
                            width: '16px',
                            height: '16px',
                            borderRadius: '50%',
                            backgroundColor: '#fff',
                            position: 'absolute',
                            top: '3px',
                            left: r.active === 1 ? '21px' : '3px',
                            transition: 'left 0.2s',
                          }}
                        />
                      </button>

                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                          <span style={{ color: '#f8fafc', fontWeight: '600', fontSize: '0.95rem' }}>{r.title}</span>
                          <span
                            style={{
                              padding: '2px 8px',
                              borderRadius: '6px',
                              fontSize: '0.7rem',
                              fontWeight: '700',
                              textTransform: 'uppercase',
                              backgroundColor:
                                r.rule === 'daily'
                                  ? 'rgba(6, 182, 212, 0.15)'
                                  : r.rule === 'weekdays'
                                  ? 'rgba(59, 130, 246, 0.15)'
                                  : r.rule === 'weekly'
                                  ? 'rgba(168, 85, 247, 0.15)'
                                  : 'rgba(245, 158, 11, 0.15)',
                              color:
                                r.rule === 'daily'
                                  ? '#38bdf8'
                                  : r.rule === 'weekdays'
                                  ? '#60a5fa'
                                  : r.rule === 'weekly'
                                  ? '#c084fc'
                                  : '#fbbf24',
                            }}
                          >
                            {r.rule === 'weekly' && r.weekday !== null && r.weekday !== undefined
                              ? `Weekly on ${WEEKDAYS[r.weekday]}`
                              : r.rule === 'monthly' && r.day_of_month
                              ? `Monthly on Day ${r.day_of_month}`
                              : r.rule}
                          </span>
                        </div>

                        <div style={{ color: '#64748b', fontSize: '0.75rem', marginTop: '4px', display: 'flex', gap: '0.75rem' }}>
                          <span>Category: <strong style={{ color: '#cbd5e1' }}>{r.category}</strong></span>
                          <span>Priority: <strong style={{ color: '#cbd5e1' }}>{r.priority}</strong></span>
                          {r.estimated_min && <span>Est: <strong style={{ color: '#cbd5e1' }}>{r.estimated_min}m</strong></span>}
                          <span>Started: <strong style={{ color: '#cbd5e1' }}>{r.start_date}</strong></span>
                        </div>
                      </div>
                    </div>

                    <button
                      onClick={() => handleDeleteRecurring(r)}
                      title="Delete Recurring Rule"
                      style={{
                        background: 'none',
                        border: 'none',
                        color: '#64748b',
                        cursor: 'pointer',
                        padding: '6px',
                        borderRadius: '6px',
                        transition: 'color 0.15s ease',
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.color = '#f87171')}
                      onMouseLeave={(e) => (e.currentTarget.style.color = '#64748b')}
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Create Recurring Modal */}
          {isNewRecurringOpen && (
            <div
              style={{
                position: 'fixed',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                backdropFilter: 'blur(8px)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                zIndex: 1000,
                padding: '1rem',
              }}
            >
              <form
                onSubmit={handleCreateRecurring}
                className="bento-card"
                style={{
                  maxWidth: '520px',
                  width: '100%',
                  border: '1px solid rgba(59, 130, 246, 0.4)',
                  boxShadow: '0 20px 40px rgba(0, 0, 0, 0.6)',
                }}
              >
                <h3 style={{ fontSize: '1.25rem', fontWeight: '700', color: '#f8fafc', marginBottom: '1rem' }}>
                  Create Recurring Task Rule
                </h3>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.25rem' }}>
                      Task Title *
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Daily Standup & Planning"
                      value={recurringForm.title}
                      onChange={(e) => setRecurringForm({ ...recurringForm, title: e.target.value })}
                      style={{
                        width: '100%',
                        padding: '0.65rem 0.85rem',
                        borderRadius: '8px',
                        backgroundColor: 'rgba(255, 255, 255, 0.05)',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        color: '#fff',
                        outline: 'none',
                      }}
                    />
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.25rem' }}>
                        Recurrence Pattern *
                      </label>
                      <select
                        value={recurringForm.rule}
                        onChange={(e) => setRecurringForm({ ...recurringForm, rule: e.target.value as any })}
                        style={{
                          width: '100%',
                          padding: '0.65rem 0.85rem',
                          borderRadius: '8px',
                          backgroundColor: '#1e293b',
                          border: '1px solid rgba(255, 255, 255, 0.1)',
                          color: '#fff',
                          outline: 'none',
                        }}
                      >
                        <option value="daily">Daily (Every Day)</option>
                        <option value="weekdays">Weekdays (Mon-Fri)</option>
                        <option value="weekly">Weekly</option>
                        <option value="monthly">Monthly</option>
                      </select>
                    </div>

                    {recurringForm.rule === 'weekly' && (
                      <div>
                        <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.25rem' }}>
                          Day of Week
                        </label>
                        <select
                          value={recurringForm.weekday || 0}
                          onChange={(e) => setRecurringForm({ ...recurringForm, weekday: Number(e.target.value) })}
                          style={{
                            width: '100%',
                            padding: '0.65rem 0.85rem',
                            borderRadius: '8px',
                            backgroundColor: '#1e293b',
                            border: '1px solid rgba(255, 255, 255, 0.1)',
                            color: '#fff',
                            outline: 'none',
                          }}
                        >
                          {WEEKDAYS.map((w, idx) => (
                            <option key={w} value={idx}>{w}</option>
                          ))}
                        </select>
                      </div>
                    )}

                    {recurringForm.rule === 'monthly' && (
                      <div>
                        <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.25rem' }}>
                          Day of Month (1-31)
                        </label>
                        <input
                          type="number"
                          min="1"
                          max="31"
                          value={recurringForm.day_of_month || 1}
                          onChange={(e) => setRecurringForm({ ...recurringForm, day_of_month: Number(e.target.value) })}
                          style={{
                            width: '100%',
                            padding: '0.65rem 0.85rem',
                            borderRadius: '8px',
                            backgroundColor: 'rgba(255, 255, 255, 0.05)',
                            border: '1px solid rgba(255, 255, 255, 0.1)',
                            color: '#fff',
                            outline: 'none',
                          }}
                        />
                      </div>
                    )}
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.75rem' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.25rem' }}>
                        Priority
                      </label>
                      <select
                        value={recurringForm.priority}
                        onChange={(e) => setRecurringForm({ ...recurringForm, priority: e.target.value as any })}
                        style={{
                          width: '100%',
                          padding: '0.65rem 0.85rem',
                          borderRadius: '8px',
                          backgroundColor: '#1e293b',
                          border: '1px solid rgba(255, 255, 255, 0.1)',
                          color: '#fff',
                          outline: 'none',
                        }}
                      >
                        <option value="high">High</option>
                        <option value="medium">Medium</option>
                        <option value="low">Low</option>
                      </select>
                    </div>

                    <div>
                      <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.25rem' }}>
                        Category
                      </label>
                      <select
                        value={recurringForm.category}
                        onChange={(e) => setRecurringForm({ ...recurringForm, category: e.target.value as any })}
                        style={{
                          width: '100%',
                          padding: '0.65rem 0.85rem',
                          borderRadius: '8px',
                          backgroundColor: '#1e293b',
                          border: '1px solid rgba(255, 255, 255, 0.1)',
                          color: '#fff',
                          outline: 'none',
                        }}
                      >
                        <option value="work">Work</option>
                        <option value="learning">Learning</option>
                        <option value="personal">Personal</option>
                      </select>
                    </div>

                    <div>
                      <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.25rem' }}>
                        Est. Minutes
                      </label>
                      <input
                        type="number"
                        min="5"
                        step="5"
                        value={recurringForm.estimated_min || ''}
                        onChange={(e) => setRecurringForm({ ...recurringForm, estimated_min: Number(e.target.value) })}
                        style={{
                          width: '100%',
                          padding: '0.65rem 0.85rem',
                          borderRadius: '8px',
                          backgroundColor: 'rgba(255, 255, 255, 0.05)',
                          border: '1px solid rgba(255, 255, 255, 0.1)',
                          color: '#fff',
                          outline: 'none',
                        }}
                      />
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                    <div>
                      <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.25rem' }}>
                        Start Date *
                      </label>
                      <input
                        type="date"
                        required
                        value={recurringForm.start_date}
                        onChange={(e) => setRecurringForm({ ...recurringForm, start_date: e.target.value })}
                        style={{
                          width: '100%',
                          padding: '0.65rem 0.85rem',
                          borderRadius: '8px',
                          backgroundColor: 'rgba(255, 255, 255, 0.05)',
                          border: '1px solid rgba(255, 255, 255, 0.1)',
                          color: '#fff',
                          outline: 'none',
                        }}
                      />
                    </div>

                    <div>
                      <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.25rem' }}>
                        End Date (Optional)
                      </label>
                      <input
                        type="date"
                        value={recurringForm.end_date || ''}
                        onChange={(e) => setRecurringForm({ ...recurringForm, end_date: e.target.value })}
                        style={{
                          width: '100%',
                          padding: '0.65rem 0.85rem',
                          borderRadius: '8px',
                          backgroundColor: 'rgba(255, 255, 255, 0.05)',
                          border: '1px solid rgba(255, 255, 255, 0.1)',
                          color: '#fff',
                          outline: 'none',
                        }}
                      />
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
                  <button
                    type="button"
                    onClick={() => setIsNewRecurringOpen(false)}
                    className="btn-secondary"
                    style={{ padding: '0.6rem 1.2rem', borderRadius: '8px', cursor: 'pointer' }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    style={{
                      padding: '0.6rem 1.2rem',
                      borderRadius: '8px',
                      border: 'none',
                      background: 'linear-gradient(135deg, #3b82f6 0%, #6366f1 100%)',
                      color: '#fff',
                      fontWeight: '700',
                      cursor: 'pointer',
                    }}
                  >
                    Save Recurring Rule
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>
      )}

      {/* ===================================================================== */}
      {/* TAB 3: DATA EXPORT & PORTABILITY */}
      {/* ===================================================================== */}
      {activeTab === 'export' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div className="bento-card">
            <h2 style={{ fontSize: '1.25rem', fontWeight: '700', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Download size={20} color="#10b981" />
              1-Click Data Exports
            </h2>
            <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginTop: '0.25rem' }}>
              Download your productivity metrics and logs in universal formats (CSV, ZIP, JSON) for spreadsheet analysis or external backup.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
            {/* Tasks CSV */}
            <div className="bento-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                  <div style={{ padding: '8px', borderRadius: '8px', backgroundColor: 'rgba(16, 185, 129, 0.1)', color: '#10b981' }}>
                    <FileSpreadsheet size={20} />
                  </div>
                  <h3 style={{ color: '#f8fafc', fontWeight: '700', fontSize: '1.05rem' }}>Tasks Export (CSV)</h3>
                </div>
                <p style={{ color: '#94a3b8', fontSize: '0.8rem', lineHeight: '1.4' }}>
                  All backlog, planned, and completed tasks including priorities, categories, time estimates, and timestamps.
                </p>
              </div>
              <a
                href="/api/export/csv?table=tasks"
                download
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem',
                  marginTop: '1.25rem',
                  padding: '0.65rem 1rem',
                  borderRadius: '8px',
                  backgroundColor: 'rgba(16, 185, 129, 0.15)',
                  color: '#34d399',
                  border: '1px solid rgba(16, 185, 129, 0.3)',
                  textDecoration: 'none',
                  fontWeight: '600',
                  fontSize: '0.85rem',
                }}
              >
                <Download size={16} />
                <span>Download Tasks CSV</span>
              </a>
            </div>

            {/* Learning Sessions CSV */}
            <div className="bento-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                  <div style={{ padding: '8px', borderRadius: '8px', backgroundColor: 'rgba(168, 85, 247, 0.1)', color: '#a855f7' }}>
                    <FileSpreadsheet size={20} />
                  </div>
                  <h3 style={{ color: '#f8fafc', fontWeight: '700', fontSize: '1.05rem' }}>Learning Sessions (CSV)</h3>
                </div>
                <p style={{ color: '#94a3b8', fontSize: '0.8rem', lineHeight: '1.4' }}>
                  Complete study log records with date, skill resource, duration in minutes, confidence ratings, and takeaways.
                </p>
              </div>
              <a
                href="/api/export/csv?table=sessions"
                download
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem',
                  marginTop: '1.25rem',
                  padding: '0.65rem 1rem',
                  borderRadius: '8px',
                  backgroundColor: 'rgba(168, 85, 247, 0.15)',
                  color: '#c084fc',
                  border: '1px solid rgba(168, 85, 247, 0.3)',
                  textDecoration: 'none',
                  fontWeight: '600',
                  fontSize: '0.85rem',
                }}
              >
                <Download size={16} />
                <span>Download Sessions CSV</span>
              </a>
            </div>

            {/* Daily Updates CSV */}
            <div className="bento-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                  <div style={{ padding: '8px', borderRadius: '8px', backgroundColor: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6' }}>
                    <Calendar size={20} />
                  </div>
                  <h3 style={{ color: '#f8fafc', fontWeight: '700', fontSize: '1.05rem' }}>Daily Updates (CSV)</h3>
                </div>
                <p style={{ color: '#94a3b8', fontSize: '0.8rem', lineHeight: '1.4' }}>
                  Historical record of your daily closures: completed summaries, learned highlights, blockers, tomorrow's focus, and 1-5 ratings.
                </p>
              </div>
              <a
                href="/api/export/csv?table=updates"
                download
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem',
                  marginTop: '1.25rem',
                  padding: '0.65rem 1rem',
                  borderRadius: '8px',
                  backgroundColor: 'rgba(59, 130, 246, 0.15)',
                  color: '#60a5fa',
                  border: '1px solid rgba(59, 130, 246, 0.3)',
                  textDecoration: 'none',
                  fontWeight: '600',
                  fontSize: '0.85rem',
                }}
              >
                <Download size={16} />
                <span>Download Updates CSV</span>
              </a>
            </div>

            {/* Complete Tables ZIP Archive */}
            <div className="bento-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                  <div style={{ padding: '8px', borderRadius: '8px', backgroundColor: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b' }}>
                    <FileArchive size={20} />
                  </div>
                  <h3 style={{ color: '#f8fafc', fontWeight: '700', fontSize: '1.05rem' }}>Complete Bundle (ZIP)</h3>
                </div>
                <p style={{ color: '#94a3b8', fontSize: '0.8rem', lineHeight: '1.4' }}>
                  Zipped archive containing individual CSV files for every SQLite table in the schema.
                </p>
              </div>
              <a
                href="/api/export/zip"
                download
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem',
                  marginTop: '1.25rem',
                  padding: '0.65rem 1rem',
                  borderRadius: '8px',
                  backgroundColor: 'rgba(245, 158, 11, 0.15)',
                  color: '#fbbf24',
                  border: '1px solid rgba(245, 158, 11, 0.3)',
                  textDecoration: 'none',
                  fontWeight: '600',
                  fontSize: '0.85rem',
                }}
              >
                <Download size={16} />
                <span>Download Tables ZIP</span>
              </a>
            </div>

            {/* Full Database JSON */}
            <div className="bento-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gridColumn: 'span 2' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                  <div style={{ padding: '8px', borderRadius: '8px', backgroundColor: 'rgba(6, 182, 212, 0.1)', color: '#06b6d4' }}>
                    <Code size={20} />
                  </div>
                  <h3 style={{ color: '#f8fafc', fontWeight: '700', fontSize: '1.05rem' }}>Structured JSON Database Dump</h3>
                </div>
                <p style={{ color: '#94a3b8', fontSize: '0.8rem', lineHeight: '1.4' }}>
                  Export the complete database structure and records in clean, formatted JSON. Ideal for custom scripts, LLM analysis, and cross-platform migrations.
                </p>
              </div>
              <a
                href="/api/export/json"
                download
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem',
                  marginTop: '1.25rem',
                  padding: '0.65rem 1rem',
                  borderRadius: '8px',
                  backgroundColor: 'rgba(6, 182, 212, 0.15)',
                  color: '#38bdf8',
                  border: '1px solid rgba(6, 182, 212, 0.3)',
                  textDecoration: 'none',
                  fontWeight: '600',
                  fontSize: '0.85rem',
                }}
              >
                <Download size={16} />
                <span>Download Full JSON Dump</span>
              </a>
            </div>
          </div>
        </div>
      )}

      {/* ===================================================================== */}
      {/* TAB 4: DESKTOP NOTIFICATIONS & AUTOMATION */}
      {/* ===================================================================== */}
      {activeTab === 'notifications' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div className="bento-card">
            <h2 style={{ fontSize: '1.25rem', fontWeight: '700', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Bell size={20} color="#f59e0b" />
              Windows Native Reminders & Automation
            </h2>
            <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginTop: '0.25rem' }}>
              FLUX includes scheduled notification triggers via Windows Task Scheduler. Test desktop toast popups directly from here.
            </p>
          </div>

          {/* Test Buttons Card */}
          <div className="bento-card">
            <h3 style={{ fontSize: '1rem', fontWeight: '700', color: '#f1f5f9', marginBottom: '0.75rem' }}>
              Direct Windows Toast Verification
            </h3>
            <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginBottom: '1.25rem' }}>
              Click either test button to trigger a live Windows desktop toast notification on your PC right now:
            </p>

            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
              <button
                onClick={() => handleTestNotification('morning')}
                disabled={testingNotif !== null}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.75rem 1.5rem',
                  borderRadius: '10px',
                  border: 'none',
                  background: 'linear-gradient(135deg, #f59e0b 0%, #ea580c 100%)',
                  color: '#fff',
                  fontWeight: '700',
                  fontSize: '0.875rem',
                  cursor: testingNotif ? 'not-allowed' : 'pointer',
                  boxShadow: '0 4px 14px rgba(245, 158, 11, 0.3)',
                }}
              >
                <Bell size={16} />
                <span>{testingNotif === 'morning' ? 'Triggering...' : '☀️ Test Morning Reminder (9:00 AM)'}</span>
              </button>

              <button
                onClick={() => handleTestNotification('evening')}
                disabled={testingNotif !== null}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.75rem 1.5rem',
                  borderRadius: '10px',
                  border: 'none',
                  background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
                  color: '#fff',
                  fontWeight: '700',
                  fontSize: '0.875rem',
                  cursor: testingNotif ? 'not-allowed' : 'pointer',
                  boxShadow: '0 4px 14px rgba(99, 102, 241, 0.3)',
                }}
              >
                <Bell size={16} />
                <span>{testingNotif === 'evening' ? 'Triggering...' : '🌙 Test Evening Reminder (9:00 PM)'}</span>
              </button>
            </div>
          </div>

          {/* Windows Task Scheduler Automation Commands */}
          <div className="bento-card">
            <h3 style={{ fontSize: '1rem', fontWeight: '700', color: '#f1f5f9', marginBottom: '0.5rem' }}>
              Automatic Setup via Windows Task Scheduler
            </h3>
            <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginBottom: '1rem' }}>
              To receive notifications automatically even when your browser is closed, run the following commands in an elevated PowerShell or Command Prompt:
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {/* Morning Command */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                  <span style={{ fontSize: '0.8rem', color: '#cbd5e1', fontWeight: '600' }}>
                    1. Morning Plan Reminder (Every Day at 09:00 AM)
                  </span>
                  <button
                    onClick={() => copyToClipboard(notifSettings?.schtasks_morning_cmd || '', 'morning_cmd')}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.35rem',
                      background: 'none',
                      border: 'none',
                      color: copiedKey === 'morning_cmd' ? '#34d399' : '#38bdf8',
                      cursor: 'pointer',
                      fontSize: '0.75rem',
                      fontWeight: '600',
                    }}
                  >
                    {copiedKey === 'morning_cmd' ? <Check size={14} /> : <Copy size={14} />}
                    <span>{copiedKey === 'morning_cmd' ? 'Copied!' : 'Copy Command'}</span>
                  </button>
                </div>
                <pre
                  style={{
                    backgroundColor: 'rgba(0, 0, 0, 0.5)',
                    padding: '0.75rem 1rem',
                    borderRadius: '8px',
                    fontSize: '0.8rem',
                    color: '#94a3b8',
                    overflowX: 'auto',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-all',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                  }}
                >
                  {notifSettings?.schtasks_morning_cmd || 'Loading command...'}
                </pre>
              </div>

              {/* Evening Command */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                  <span style={{ fontSize: '0.8rem', color: '#cbd5e1', fontWeight: '600' }}>
                    2. Evening Close-Day Reminder (Every Day at 21:00 / 9:00 PM)
                  </span>
                  <button
                    onClick={() => copyToClipboard(notifSettings?.schtasks_evening_cmd || '', 'evening_cmd')}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.35rem',
                      background: 'none',
                      border: 'none',
                      color: copiedKey === 'evening_cmd' ? '#34d399' : '#38bdf8',
                      cursor: 'pointer',
                      fontSize: '0.75rem',
                      fontWeight: '600',
                    }}
                  >
                    {copiedKey === 'evening_cmd' ? <Check size={14} /> : <Copy size={14} />}
                    <span>{copiedKey === 'evening_cmd' ? 'Copied!' : 'Copy Command'}</span>
                  </button>
                </div>
                <pre
                  style={{
                    backgroundColor: 'rgba(0, 0, 0, 0.5)',
                    padding: '0.75rem 1rem',
                    borderRadius: '8px',
                    fontSize: '0.8rem',
                    color: '#94a3b8',
                    overflowX: 'auto',
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-all',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                  }}
                >
                  {notifSettings?.schtasks_evening_cmd || 'Loading command...'}
                </pre>
              </div>
            </div>
          </div>

          {/* Recent Notification Logs */}
          {notifSettings?.recent_logs && notifSettings.recent_logs.length > 0 && (
            <div className="bento-card">
              <h3 style={{ fontSize: '1rem', fontWeight: '700', color: '#f1f5f9', marginBottom: '0.75rem' }}>
                Notification Log Excerpt ({notifSettings.log_file})
              </h3>
              <div
                style={{
                  backgroundColor: 'rgba(0, 0, 0, 0.4)',
                  padding: '0.75rem 1rem',
                  borderRadius: '8px',
                  fontFamily: 'monospace',
                  fontSize: '0.75rem',
                  color: '#94a3b8',
                  maxHeight: '180px',
                  overflowY: 'auto',
                }}
              >
                {notifSettings.recent_logs.map((log, i) => (
                  <div key={i} style={{ padding: '2px 0' }}>{log}</div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ===================================================================== */}
      {/* TAB 5: SYSTEM & DIAGNOSTICS */}
      {/* ===================================================================== */}
      {activeTab === 'system' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div className="bento-card">
            <h2 style={{ fontSize: '1.25rem', fontWeight: '700', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <HardDrive size={20} color="#06b6d4" />
              System Diagnostics & Runtime Environment
            </h2>
            <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginTop: '0.25rem' }}>
              Live metrics from your SQLite database engine, Python virtual environment, and active file paths.
            </p>
          </div>

          {/* Diagnostics Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
            <div className="bento-card">
              <div style={{ color: '#94a3b8', fontSize: '0.8rem', fontWeight: '600' }}>SQLITE VERSION</div>
              <div style={{ color: '#38bdf8', fontSize: '1.5rem', fontWeight: '800', marginTop: '0.5rem' }}>
                v{settings?.system_info.sqlite_version || '3.x'}
              </div>
              <div style={{ color: '#64748b', fontSize: '0.75rem', marginTop: '0.25rem' }}>ACID Compliant Local DB</div>
            </div>

            <div className="bento-card">
              <div style={{ color: '#94a3b8', fontSize: '0.8rem', fontWeight: '600' }}>TOTAL TASKS</div>
              <div style={{ color: '#f8fafc', fontSize: '1.5rem', fontWeight: '800', marginTop: '0.5rem' }}>
                {settings?.system_info.table_counts.tasks ?? 0}
              </div>
              <div style={{ color: '#64748b', fontSize: '0.75rem', marginTop: '0.25rem' }}>Across todo, done, dropped</div>
            </div>

            <div className="bento-card">
              <div style={{ color: '#94a3b8', fontSize: '0.8rem', fontWeight: '600' }}>STUDY SESSIONS LOGGED</div>
              <div style={{ color: '#c084fc', fontSize: '1.5rem', fontWeight: '800', marginTop: '0.5rem' }}>
                {settings?.system_info.table_counts.sessions ?? 0}
              </div>
              <div style={{ color: '#64748b', fontSize: '0.75rem', marginTop: '0.25rem' }}>Linked learning entries</div>
            </div>

            <div className="bento-card">
              <div style={{ color: '#94a3b8', fontSize: '0.8rem', fontWeight: '600' }}>ACTIVE GOALS</div>
              <div style={{ color: '#34d399', fontSize: '1.5rem', fontWeight: '800', marginTop: '0.5rem' }}>
                {settings?.system_info.table_counts.goals ?? 0}
              </div>
              <div style={{ color: '#64748b', fontSize: '0.75rem', marginTop: '0.25rem' }}>Tracked targets</div>
            </div>

            <div className="bento-card">
              <div style={{ color: '#94a3b8', fontSize: '0.8rem', fontWeight: '600' }}>DAILY CLOSURES</div>
              <div style={{ color: '#fbbf24', fontSize: '1.5rem', fontWeight: '800', marginTop: '0.5rem' }}>
                {settings?.system_info.table_counts.updates ?? 0}
              </div>
              <div style={{ color: '#64748b', fontSize: '0.75rem', marginTop: '0.25rem' }}>Historical updates</div>
            </div>

            <div className="bento-card">
              <div style={{ color: '#94a3b8', fontSize: '0.8rem', fontWeight: '600' }}>RECURRING RULES</div>
              <div style={{ color: '#60a5fa', fontSize: '1.5rem', fontWeight: '800', marginTop: '0.5rem' }}>
                {settings?.system_info.table_counts.recurring ?? 0}
              </div>
              <div style={{ color: '#64748b', fontSize: '0.75rem', marginTop: '0.25rem' }}>Templates configured</div>
            </div>
          </div>

          {/* Paths Card */}
          <div className="bento-card">
            <h3 style={{ fontSize: '1rem', fontWeight: '700', color: '#f1f5f9', marginBottom: '1rem' }}>
              Environment Locations
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.85rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                <span style={{ color: '#94a3b8' }}>Database Path:</span>
                <span style={{ color: '#f8fafc', fontFamily: 'monospace' }}>{settings?.system_info.database_path}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                <span style={{ color: '#94a3b8' }}>Backup Directory:</span>
                <span style={{ color: '#f8fafc', fontFamily: 'monospace' }}>{settings?.system_info.backup_dir}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                <span style={{ color: '#94a3b8' }}>Python Virtualenv Executable:</span>
                <span style={{ color: '#f8fafc', fontFamily: 'monospace' }}>{notifSettings?.python_exe}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0' }}>
                <span style={{ color: '#94a3b8' }}>Project Workspace Root:</span>
                <span style={{ color: '#f8fafc', fontFamily: 'monospace' }}>{notifSettings?.project_root}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
