import { useEffect, useState } from "react";

const API_URL = "https://ai-crm-vazc.onrender.com";

function DealTable() {
  const [deals, setDeals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchDeals = async () => {
    try {
      setLoading(true);

      const response = await fetch(`${API_URL}/api/deals`);

      if (!response.ok) {
        throw new Error("Failed to fetch deals");
      }

      const data = await response.json();

      setDeals(data.deals);
      setError("");
    } catch (error) {
      console.error(error);
      setError("Could not load deals.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDeals();
  }, []);

  const getStatusClass = (status) => {
    return `status status-${status.toLowerCase()}`;
  };

  if (loading) {
    return <div className="loading">Loading deals...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  return (
    <section className="card">
      <div className="section-header">
        <div>
          <h2>Deals</h2>
          <p>{deals.length} deals</p>
        </div>

        <button className="refresh-button" onClick={fetchDeals}>
          Refresh
        </button>
      </div>

      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Customer</th>
              <th>Deal</th>
              <th>Amount</th>
              <th>Status</th>
              <th>Salesperson</th>
              <th>Last Updated</th>
            </tr>
          </thead>

          <tbody>
            {deals.map((deal) => (
              <tr key={deal.id}>
                <td>#{deal.id}</td>

                <td>
                  <strong>{deal.customer_name}</strong>
                  <small>{deal.company}</small>
                </td>

                <td>{deal.title}</td>

                <td>
                  ${Number(deal.amount).toLocaleString()}
                </td>

                <td>
                  <span className={getStatusClass(deal.status)}>
                    {deal.status}
                  </span>
                </td>

                <td>{deal.salesperson}</td>

                <td>{deal.last_updated}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default DealTable;