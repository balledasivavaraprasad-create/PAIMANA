import React, { useState, useEffect } from 'react';
import GlassCard from '../components/GlassCard';
import { fetchUsersList, fetchAuditLogs } from '../lib/api';

const DEFAULT_USERS = [
  {
    id: 'USR-001',
    name: 'National Director (MoSPI)',
    email: 'admin@paimana.gov.in',
    role: 'ADMIN',
    ministry: 'Ministry of Statistics & Programme Implementation',
    designation: 'MoSPI Lead Director',
    status: 'Active',
    lastLogin: 'Just now'
  },
  {
    id: 'USR-002',
    name: 'Lead Infrastructure Risk Analyst',
    email: 'analyst@paimana.gov.in',
    role: 'ANALYST',
    ministry: 'MoSPI Early Warning Unit',
    designation: 'Principal Risk Analyst',
    status: 'Active',
    lastLogin: 'Today, 13:45'
  },
  {
    id: 'USR-003',
    name: 'Balleda Siva Vara Prasad',
    email: 'balledasivavaraprasad@gmail.com',
    role: 'PROJECT_OFFICER',
    ministry: 'Ministry of Housing & Urban Affairs',
    designation: 'Project Officer',
    status: 'Active',
    lastLogin: 'Just now'
  }
];

const DEFAULT_AUDIT_LOGS = [
  {
    id: 'EVT-9021',
    action: 'Risk Alert Evaluated',
    actor: 'System / n8n Webhook',
    target: 'Project 617321 (Varanasi Expressway)',
    detail: 'DPHIS risk scored at 85.0. Automated notification dispatched.',
    time: '12 mins ago'
  },
  {
    id: 'EVT-9020',
    action: 'User Session Authenticated',
    actor: 'Balleda Siva Vara Prasad',
    target: 'Auth Subsystem',
    detail: 'Successful login session created for balledasivavaraprasad@gmail.com.',
    time: '28 mins ago'
  },
  {
    id: 'EVT-9019',
    action: 'Project Details Updated',
    actor: 'Project Officer',
    target: 'Project N28000157',
    detail: 'Physical progress milestone synchronized with ministry repository.',
    time: '1 hour ago'
  }
];

export default function UsersAudit() {
  const [users, setUsers] = useState<any[]>(DEFAULT_USERS);
  const [auditEvents, setAuditEvents] = useState<any[]>(DEFAULT_AUDIT_LOGS);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    Promise.all([
      fetchUsersList(),
      fetchAuditLogs(50)
    ]).then(([uList, logs]) => {
      if (!isMounted) return;
      if (uList && uList.length > 0) {
        setUsers(uList);
      }
      if (logs && logs.length > 0) {
        setAuditEvents(logs);
      }
      setLoading(false);
    }).catch(() => {
      if (isMounted) setLoading(false);
    });

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="space-y-6 sm:space-y-8 pt-16 sm:pt-20 pb-16 px-4 sm:px-8 md:px-12 max-w-7xl mx-auto">
      {/* Header */}
      <GlassCard variant="hero" padding={24} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <h2 className="text-xl sm:text-2xl md:text-3xl font-bold font-display text-white">
              Users, Access Governance &amp; Audit Trail
            </h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">
              ADMIN ONLY
            </span>
          </div>
          <p className="text-xs sm:text-sm md:text-base text-white/80 leading-relaxed">
            Live database registry of authorized ministry officers, role privileges, and system audit trail events
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <span className="px-3.5 py-1.5 rounded-xl bg-white/10 text-white font-mono text-xs font-bold border border-white/20">
            {users.length} Authorized {users.length === 1 ? 'Account' : 'Accounts'}
          </span>
        </div>
      </GlassCard>

      {/* Authorized Officers & Users Table */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-mono font-bold uppercase tracking-wider text-white/70">
            Authorized Ministry Officers &amp; Analysts ({users.length})
          </h3>
          {loading && (
            <span className="text-[11px] font-mono text-white/50 animate-pulse">Syncing database...</span>
          )}
        </div>

        <div className="overflow-x-auto rounded-xl border border-white/15 bg-black/40 backdrop-blur-md">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-white/15 bg-[#0B0F17]">
                <th className="p-4 text-white/80 font-mono text-[10px] uppercase">User ID</th>
                <th className="p-4 text-white/80 font-mono text-[10px] uppercase">Officer Name</th>
                <th className="p-4 text-white/80 font-mono text-[10px] uppercase">Role</th>
                <th className="p-4 text-white/80 font-mono text-[10px] uppercase">Ministry / Department</th>
                <th className="p-4 text-white/80 font-mono text-[10px] uppercase">Designation</th>
                <th className="p-4 text-white/80 font-mono text-[10px] uppercase">Status</th>
                <th className="p-4 text-white/80 font-mono text-[10px] uppercase">Last Active</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {users.map(u => (
                <tr key={u.id} className="hover:bg-white/5 transition-colors">
                  <td className="p-4 font-mono font-bold text-white">{u.id}</td>
                  <td className="p-4">
                    <div className="font-semibold text-white">{u.name}</div>
                    <div className="text-[11px] text-white/60 font-mono">{u.email}</div>
                  </td>
                  <td className="p-4">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                      u.role === 'ADMIN' 
                        ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                        : u.role === 'ANALYST'
                        ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                        : 'bg-white/10 text-white border border-white/20'
                    }`}>
                      {u.role}
                    </span>
                  </td>
                  <td className="p-4 text-white/80">{u.ministry}</td>
                  <td className="p-4 text-white/80">{u.designation}</td>
                  <td className="p-4">
                    <span className="text-emerald-400 font-mono font-bold text-xs flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                      <span>{u.status}</span>
                    </span>
                  </td>
                  <td className="p-4 font-mono text-white/70">{u.lastLogin}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* System Audit Log */}
      <div className="space-y-3">
        <h3 className="text-sm font-mono font-bold uppercase tracking-wider text-white/70">
          Recent System Audit Actions ({auditEvents.length})
        </h3>

        <div className="space-y-2.5">
          {auditEvents.map(evt => (
            <div key={evt.id} className="oled-solid-card p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-white px-2 py-0.5 rounded bg-white/10">{evt.id}</span>
                  <span className="font-bold text-white">{evt.action}</span>
                  <span className="text-white/50">•</span>
                  <span className="text-white/70">by {evt.actor}</span>
                </div>
                <p className="text-white/80">{evt.detail}</p>
              </div>

              <div className="font-mono text-white/50 text-[11px] shrink-0">
                {evt.time}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
