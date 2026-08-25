import CustomerTable from "./components/CustomerTable";
import DealTable from "./components/DealTable";
import Chat from "./components/Chat";
import "./App.css";

function App() {
  return (
    <div className="app">
      <header className="topbar">
        <div>
          <h1>AI CRM</h1>
          <p>Intelligent Customer Relationship Management</p>
        </div>

        <div className="backend-status">
          <span></span>
          Backend Connected
        </div>
      </header>

      <main className="dashboard">
        <div className="top-grid">
          <CustomerTable />
          <Chat />
        </div>

        <DealTable />
      </main>
    </div>
  );
}

export default App;