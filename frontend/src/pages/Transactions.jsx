import { useEffect, useState } from "react";
import toast from "react-hot-toast";

import api from "../api/client.js";
import Loading from "../components/Loading.jsx";
import TransactionTable from "../components/TransactionTable.jsx";
import { getErrorMessage } from "../utils.js";

export default function Transactions() {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/api/transactions")
      .then((response) => setTransactions(response.data.transactions))
      .catch((error) => toast.error(getErrorMessage(error)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Loading label="Loading transactions..." />;

  return <TransactionTable transactions={transactions} />;
}
