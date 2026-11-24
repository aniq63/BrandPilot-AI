import { Route, Routes } from "react-router-dom";

import Footer from "./components/Footer";
import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";
import Campaign from "./pages/Campaign";
import Dashboard from "./pages/Dashboard";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import NewProject from "./pages/NewProject";
import ProjectRun from "./pages/ProjectRun";
import Signup from "./pages/Signup";

export default function App() {
  return (
    <div className="app-shell">
      <Navbar />
      <main className="app-main">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/login" element={<Login />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/projects/new"
            element={
              <ProtectedRoute>
                <NewProject />
              </ProtectedRoute>
            }
          />
          <Route
            path="/runs/:projectId"
            element={
              <ProtectedRoute>
                <ProjectRun />
              </ProtectedRoute>
            }
          />
          <Route
            path="/campaigns/:campaignId"
            element={
              <ProtectedRoute>
                <Campaign />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Landing />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}
