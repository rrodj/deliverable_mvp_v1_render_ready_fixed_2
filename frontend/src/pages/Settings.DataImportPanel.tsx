import React, { useState } from 'react';
import { uploadSalesCsv, uploadOnhandCsv, runAnalysis, listEvidence } from '../api';

const DataImportPanel: React.FC = () => {
  const [msg, setMsg] = useState<string>('');
  const [evidence, setEvidence] = useState<any[]>([]);
  const [busy, setBusy] = useState(false);

  const doUpload = async (kind: 'sales'|'onhand', file?: File) => {
    if (!file) return; setBusy(true); setMsg('');
    try {
      const res = kind==='sales' ? await uploadSalesCsv(file) : await uploadOnhandCsv(file);
      setMsg(JSON.stringify(res));
    } catch { setMsg('Upload failed'); } finally { setBusy(false); }
  };
  const doScan = async () => {
    setBusy(true); setMsg('');
    try {
      const res = await runAnalysis();
      setMsg(`Scan: alerts=${res.created_alerts}, potential=$${Math.round(res.potential_usd)}`);
      const ev = await listEvidence(); setEvidence(ev.evidence||[]);
    } catch { setMsg('Scan failed'); } finally { setBusy(false); }
  };

  return (
    <div className="card" style={{marginTop:16}}>
      <h3>Data Import & Analysis</h3>
      <div style={{display:'flex', gap:12, alignItems:'center', flexWrap:'wrap'}}>
        <label>Sales CSV <input type="file" onChange={e=>doUpload('sales', e.target.files?.[0])} disabled={busy}/></label>
        <label>On‑hand CSV <input type="file" onChange={e=>doUpload('onhand', e.target.files?.[0])} disabled={busy}/></label>
        <a className="button" href="/reports/roi/html" target="_blank" rel="noreferrer">Open ROI Report</a>
        <button className="button" onClick={doScan} disabled={busy}>Run Analysis</button>
      </div>
      {msg && <div className="alert" style={{marginTop:8}}>{msg}</div>}
      <div style={{marginTop:8}}>
        <strong>Evidence (latest)</strong>
        <table className="table" style={{width:'100%'}}>
          <thead><tr><th>Category</th><th>SKU</th><th>Name</th><th>Amount</th></tr></thead>
          <tbody>
            {evidence.map((e:any)=>(<tr key={e.id}><td>{e.category}</td><td>{e.sku||''}</td><td>{e.item_name||''}</td><td>${Math.round(e.amount_usd||0).toLocaleString()}</td></tr>))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DataImportPanel;
