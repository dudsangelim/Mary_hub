"use client";

import { useEffect, useMemo, useState } from "react";

import { Header } from "@/components/layout/Header";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { useStudents } from "@/hooks/useStudents";
import { apiFetch } from "@/lib/api";
import type { ProviderAccount, ProviderSyncLog, ProviderSyncTriggerResponse } from "@/lib/types";

type FormState = {
  student_id: string;
  username: string;
  password: string;
  student_login_id: string;
  link_code: string;
};

const initialForm: FormState = {
  student_id: "",
  username: "",
  password: "",
  student_login_id: "",
  link_code: "",
};

export default function IntegrationsPage() {
  const { students, loading: studentsLoading } = useStudents();
  const [accounts, setAccounts] = useState<ProviderAccount[]>([]);
  const [logsByAccount, setLogsByAccount] = useState<Record<string, ProviderSyncLog[]>>({});
  const [form, setForm] = useState<FormState>(initialForm);
  const [loadingAccounts, setLoadingAccounts] = useState(true);
  const [saving, setSaving] = useState(false);
  const [syncingAccountId, setSyncingAccountId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const sortedStudents = useMemo(() => students.slice().sort((a, b) => a.name.localeCompare(b.name, "pt-BR")), [students]);

  useEffect(() => {
    if (!form.student_id && sortedStudents.length > 0) {
      setForm((current) => ({ ...current, student_id: sortedStudents[0].id }));
    }
  }, [form.student_id, sortedStudents]);

  useEffect(() => {
    async function loadAccounts() {
      setLoadingAccounts(true);
      try {
        const providerAccounts = await apiFetch<ProviderAccount[]>("/providers/accounts");
        setAccounts(providerAccounts);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao carregar integrações");
      } finally {
        setLoadingAccounts(false);
      }
    }

    loadAccounts();
  }, []);

  async function loadLogs(accountId: string) {
    const logs = await apiFetch<ProviderSyncLog[]>(`/providers/accounts/${accountId}/logs`);
    setLogsByAccount((current) => ({ ...current, [accountId]: logs }));
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setMessage(null);
    setError(null);

    try {
      const account = await apiFetch<ProviderAccount>("/providers/plurall/accounts", {
        method: "POST",
        body: JSON.stringify({
          ...form,
          student_login_id: form.student_login_id || null,
          link_code: form.link_code || null,
        }),
      });

      setAccounts((current) => {
        const next = current.filter((item) => item.id !== account.id);
        return [account, ...next];
      });
      setMessage("Conta Plurall vinculada. Se você trocar a senha depois, será preciso atualizar a conexão aqui.");
      setForm((current) => ({ ...current, password: "" }));
      await loadLogs(account.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao vincular conta Plurall");
    } finally {
      setSaving(false);
    }
  }

  async function handleSync(accountId: string) {
    setSyncingAccountId(accountId);
    setMessage(null);
    setError(null);

    try {
      const response = await apiFetch<ProviderSyncTriggerResponse>(`/providers/accounts/${accountId}/sync`, {
        method: "POST",
      });

      setAccounts((current) =>
        current.map((account) => (account.id === response.provider_account.id ? response.provider_account : account))
      );
      setLogsByAccount((current) => ({
        ...current,
        [accountId]: [response.sync_log, ...(current[accountId] ?? [])],
      }));
      setMessage(response.message);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao sincronizar Plurall");
    } finally {
      setSyncingAccountId(null);
    }
  }

  return (
    <main className="space-y-6">
      <Header title="Integrações" subtitle="Conecte a conta do aluno no Plurall e dispare sync manual para importar o snapshot atual do portal." />

      <section className="rounded-[2rem] bg-white p-6 shadow-sm">
        <h3 className="text-xl font-semibold text-slate-900">Conectar Plurall</h3>
        <p className="mt-2 text-sm text-slate-600">
          O sync atual usa login do portal. Se a senha mudar, atualize a conexão aqui para o Mary conseguir autenticar de novo.
        </p>
        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <Select value={form.student_id} onChange={(event) => setForm((current) => ({ ...current, student_id: event.target.value }))} disabled={studentsLoading}>
            {!form.student_id ? <option value="">Selecione o aluno</option> : null}
            {sortedStudents.map((student) => (
              <option key={student.id} value={student.id}>
                {student.name}
              </option>
            ))}
          </Select>
          <div className="grid gap-4 md:grid-cols-2">
            <Input
              placeholder="Usuário do Plurall"
              value={form.username}
              onChange={(event) => setForm((current) => ({ ...current, username: event.target.value }))}
            />
            <Input
              type="password"
              placeholder="Senha do Plurall"
              value={form.password}
              onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
            />
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <Input
              placeholder="ID do aluno no Plurall"
              value={form.student_login_id}
              onChange={(event) => setForm((current) => ({ ...current, student_login_id: event.target.value }))}
            />
            <Input
              placeholder="Código de vínculo"
              value={form.link_code}
              onChange={(event) => setForm((current) => ({ ...current, link_code: event.target.value }))}
            />
          </div>
          {message ? <p className="rounded-2xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{message}</p> : null}
          {error ? <p className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p> : null}
          <Button type="submit" disabled={saving || !form.student_id || !form.username || !form.password}>
            {saving ? "Salvando conexão..." : "Salvar conexão"}
          </Button>
        </form>
      </section>

      <section className="space-y-4">
        <div className="rounded-[2rem] bg-white p-6 shadow-sm">
          <h3 className="text-xl font-semibold text-slate-900">Contas conectadas</h3>
          <p className="mt-2 text-sm text-slate-600">Nesta fase, o sync ainda é manual e importa o snapshot atual do portal do aluno.</p>
        </div>

        {loadingAccounts ? (
          <div className="rounded-[2rem] bg-white p-6 text-sm text-slate-600 shadow-sm">Carregando integrações...</div>
        ) : accounts.length === 0 ? (
          <div className="rounded-[2rem] bg-white p-6 text-sm text-slate-600 shadow-sm">Nenhuma conta conectada ainda.</div>
        ) : (
          accounts.map((account) => {
            const student = students.find((item) => item.id === account.student_id);
            const logs = logsByAccount[account.id] ?? [];

            return (
              <article key={account.id} className="rounded-[2rem] bg-white p-6 shadow-sm">
                <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-[0.25em] text-slate-500">{account.provider_name}</p>
                    <h3 className="mt-1 text-xl font-semibold text-slate-900">{student?.name ?? "Aluno"}</h3>
                    <p className="mt-2 text-sm text-slate-600">
                      Tipo: {account.provider_type} · Credencial salva: {account.has_credentials ? "sim" : "não"}
                    </p>
                    <p className="mt-1 text-sm text-slate-600">
                      Último sync: {account.last_sync_at ? new Date(account.last_sync_at).toLocaleString("pt-BR") : "ainda não executado"}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="secondary" onClick={() => loadLogs(account.id)}>
                      Ver logs
                    </Button>
                    <Button onClick={() => handleSync(account.id)} disabled={syncingAccountId === account.id}>
                      {syncingAccountId === account.id ? "Sincronizando..." : "Sincronizar agora"}
                    </Button>
                  </div>
                </div>
                {logs.length > 0 ? (
                  <div className="mt-4 space-y-3">
                    {logs.slice(0, 5).map((log) => (
                      <div key={log.id} className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-700">
                        <p>
                          {new Date(log.started_at).toLocaleString("pt-BR")} · status: <strong>{log.status}</strong>
                        </p>
                        {log.error_message ? <p className="mt-1 text-slate-600">{log.error_message}</p> : null}
                      </div>
                    ))}
                  </div>
                ) : null}
              </article>
            );
          })
        )}
      </section>
    </main>
  );
}
