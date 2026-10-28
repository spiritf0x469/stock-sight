import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid,
  ResponsiveContainer, ReferenceDot,
} from "recharts";
import { stockApi, authApi } from "../api";

export default function Dashboard() {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem("user")) || null; }
    catch { return null; }
  });
  const [tickers, setTickers] = useState([]);
  const [form, setForm] = useState({ ticker: "", amount: 10000, horizon_days: 30 });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const nav = useNavigate();

  useEffect(() => {
    (async () => {
      try {
        const [{ data: t }, { data: m }] = await Promise.all([
          stockApi.tickers(),
          authApi.me(),
        ]);
        setTickers(t.tickers);
        setUser(m.user);
        if (!form.ticker && t.tickers[0]) setForm((f) => ({ ...f, ticker: t.tickers[0].symbol }));
      } catch {
        nav("/login");
      }
    })();
    // eslint-disable-next-line
  }, []);

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    nav("/login");
  };

  const submit = async (e) => {
    e.preventDefault();
    setErr("");
    setResult(null);
    setLoading(true);
    try {
      const { data } = await stockApi.predict({
        ticker: form.ticker,
        amount: Number(form.amount),
        horizon_days: Number(form.horizon_days),
      });
      setResult(data);
    } catch (e) {
      setErr(e.response?.data?.error || "Prediction failed");
    } finally {
      setLoading(false);
    }
  };

  // Build chart data: history + predicted point
  const chartData = useMemo(() => {
    if (!result) return [];
    const hist = result.history.map((r) => ({ date: r.Date, close: r.Close, predicted: null }));
    const last = hist[hist.length - 1];
    if (last) last.predicted = result.prediction.current_price;
    hist.push({
      date: `+${result.used_model_horizon_days}d`,
      close: null,
      predicted: result.prediction.predicted_price,
    });
    return hist;
  }, [result]);

  const badgeClass =
    result?.decision.action === "BUY" ? "badge buy"
    : result?.decision.action === "AVOID" ? "badge avoid"
    : "badge hold";

  return (
    <div className="dash">
      <header className="dash-header">
        <div>
          <h1>StockSight</h1>
          <p className="sub">Intelligent Stock Price Prediction</p>
        </div>
        <div className="user-box">
          <span>{user?.username}</span>
          <button className="ghost" onClick={logout}>Logout</button>
        </div>
      </header>

      <form className="controls" onSubmit={submit}>
        <label>
          Stock
          <select
            value={form.ticker}
            onChange={(e) => setForm({ ...form, ticker: e.target.value })}
          >
            {tickers.map((t) => (
              <option key={t.symbol} value={t.symbol}>
                {t.name} ({t.symbol})
              </option>
            ))}
          </select>
        </label>

        <label>
          Investment Amount (₹)
          <input
  type="number"
  min="1"
  step="any"
  inputMode="numeric"
  value={form.amount}
  onChange={(e) => setForm({ ...form, amount: e.target.value })}
/>
        </label>

        <label>
          Holding Period (days)
          <input
  type="number"
  min="1"
  max="365"
  step="1"
  value={form.horizon_days}
  onChange={(e) => setForm({ ...form, horizon_days: e.target.value })}
/>
        </label>

        <button disabled={loading}>{loading ? "Predicting..." : "Predict"}</button>
      </form>

      {err && <div className="error">{err}</div>}

      {result && (
        <>
          <div className="result-grid">
            <div className="card">
              <p className="label">Current Price</p>
              <p className="big">₹{result.prediction.current_price.toLocaleString()}</p>
              <p className="muted">As of {result.prediction.as_of_date}</p>
            </div>
            <div className="card">
              <p className="label">Predicted Price</p>
              <p className="big">₹{result.prediction.predicted_price.toLocaleString()}</p>
              <p className="muted">Horizon: {result.used_model_horizon_days}d</p>
            </div>
            <div className="card">
              <p className="label">Future Value</p>
              <p className="big">₹{result.investment.future_value.toLocaleString()}</p>
              <p className="muted">Invested ₹{result.investment.invested.toLocaleString()}</p>
            </div>
            <div className="card">
              <p className="label">Profit / Loss</p>
              <p className={`big ${result.investment.profit_loss >= 0 ? "pos" : "neg"}`}>
                {result.investment.profit_loss >= 0 ? "+" : ""}
                ₹{result.investment.profit_loss.toLocaleString()}
              </p>
              <p className="muted">
                Return: {result.investment.return_pct}%
              </p>
            </div>
          </div>

          <div className="decision-box">
            <span className={badgeClass}>{result.decision.action}</span>
            <span>{result.decision.reason}</span>
          </div>

          <div className="chart-card">
            <h3>Price History + Prediction</h3>
            <ResponsiveContainer width="100%" height={360}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} minTickGap={40} />
                <YAxis domain={["auto", "auto"]} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Line
                  type="monotone" dataKey="close" stroke="#2563eb"
                  strokeWidth={2} dot={false} name="Historical Close"
                />
                <Line
                  type="monotone" dataKey="predicted" stroke="#dc2626"
                  strokeWidth={2} dot={{ r: 4 }} connectNulls name="Predicted"
                />
                <ReferenceDot
                  x={`+${result.used_model_horizon_days}d`}
                  y={result.prediction.predicted_price}
                  r={6} fill="#dc2626" stroke="#fff"
                />
              </LineChart>
            </ResponsiveContainer>
            <p className="muted small">
              Model: <b>{result.model_info.name}</b> ·
              RMSE {result.model_info.metrics.RMSE} ·
              R² {result.model_info.metrics.R2}
            </p>
          </div>

          <p className="disclaimer">
            ⚠️ Predictions are estimates only and not financial advice.
          </p>
        </>
      )}
    </div>
  );
}