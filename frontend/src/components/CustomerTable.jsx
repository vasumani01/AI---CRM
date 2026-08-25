import { useEffect, useState } from "react";

const API_URL = "https://ai-crm-vazc.onrender.com";

function CustomerTable() {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API_URL}/api/customers`)
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to fetch customers");
        }
        return response.json();
      })
      .then((data) => {
        setCustomers(data.customers);
        setLoading(false);
      })
      .catch((error) => {
        console.error(error);
        setError("Could not load customers.");
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="loading">Loading customers...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  return (
    <section className="card">
      <div className="section-header">
        <div>
          <h2>Customers</h2>
          <p>{customers.length} customers</p>
        </div>
      </div>

      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Company</th>
              <th>Email</th>
              <th>Phone</th>
            </tr>
          </thead>

          <tbody>
            {customers.map((customer) => (
              <tr key={customer.id}>
                <td>#{customer.id}</td>
                <td className="customer-name">{customer.name}</td>
                <td>{customer.company}</td>
                <td>{customer.email}</td>
                <td>{customer.phone}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default CustomerTable;