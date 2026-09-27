import React from 'react';
import GlassCard from '../components/GlassCard';

export default function UsersAudit() {
  const users = [
    {
      id: 'USR-001',
      name: 'Ramesh Kumar',
      email: 'admin@paimana.gov.in',
      role: 'ADMIN',
      ministry: 'MoSPI Central Coordination',
      designation: 'MoSPI Lead Director',
      status: 'Active',
      lastLogin: 'Today, 14:22'
    },
    {
      id: 'USR-002',
      name: 'Dr. Priya Sharma',
      email: 'analyst@paimana.gov.in',
      role: 'ANALYST',
      ministry: 'MoSPI Early Warning Unit',
      designation: 'Principal Risk Analyst',
      status: 'Active',
      lastLogin: 'Today, 13:45'
    },
    {
      id: 'USR-003',
      name: 'Vikram Singh',
      email: 'morth@paimana.gov.in',
      role: 'PROJECT_OFFICER',
      ministry: 'Ministry of Road Transport and Highways',
      designation: 'Chief Project Engineer',
      status: 'Active',
      lastLogin: 'Yesterday, 18:10'
    },
    {
      id: 'USR-004',
      name: 'Siva Balle',
      email: 'balledasivavaraprasad@gmail.com',
      role: 'PROJECT_OFFICER',
      ministry: 'Ministry of Housing and Urban Affairs',
      designation: 'Executive Project Director',
      status: 'Active',
      lastLogin: 'Just now'
    }
  ];

  const auditEvents = [
    {
      id: 'EVT-9021',
      action: 'Risk Alert Evaluated',
      actor: 'System / n8n Webhook',
      target: 'Project 617321 (Varanasi Expressway)',
      detail: 'DPHIS risk scored at 85.0. Critical alert dispatched to Siva Balle via SMTP.',
      time: '12 mins ago'
    },
    {
      id: 'EVT-9020',
      action: 'User Session Authenticated',
      actor: 'Siva Balle',
      target: 'Auth Subsystem',
      detail: 'Successful OTP verification and JWT session created.',
      time: '28 mins ago'
    },
    {
      id: 'EVT-9019',
      action: 'Project Details Updated',
      actor: 'Vikram Singh',
      target: 'Project N28000157',
      detail: 'Physical progress milestone updated from 32% to 34%.',
      time: '2 hours ago'
    },
    {
      id: 'EVT-9018',
      action: 'Model Manifest Verified',
      actor: 'Dr. Priya Sharma',
      target: 'LightGBM v2.1',
      detail: 'Quantile loss weights and early warning threshold verified against Q2 data.',
      time: '5 hours ago'
    }
  ];

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
            Monitor registered department officers, assign project jurisdictions, and review system-wide audit actions
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <span className="px-3.5 py-1.5 rounded-xl bg-white/10 text-white font-mono text-xs font-bold border border-white/20">
            {users.length} Authorized Accounts
          </span>
        </div>
      </GlassCard>

      {/* Authorized Officers & Users Table */}
      <div className="space-y-3">
        <h3 className="text-sm font-mono font-bold uppercase tracking-wider text-white/70">
          Authorized Ministry Officers &amp; Analysts
        </h3>

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
          Recent System Audit Actions
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
