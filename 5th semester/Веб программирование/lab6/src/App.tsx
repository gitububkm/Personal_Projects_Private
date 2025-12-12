import { Navigate, Route, Routes } from "react-router-dom";

import { Layout } from "./components/Layout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AuthPage } from "./pages/AuthPage";
import { CreateNewsPage } from "./pages/CreateNewsPage";
import { HomePage } from "./pages/HomePage";
import { NewsPage } from "./pages/NewsPage";

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/news/:id" element={<NewsPage />} />
        <Route path="/auth" element={<AuthPage />} />
        <Route
          path="/create-news"
          element={
            <ProtectedRoute roles={["author", "admin"]}>
              <CreateNewsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/edit-news/:id"
          element={
            <ProtectedRoute roles={["author", "admin"]}>
              <CreateNewsPage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}

export default App;

