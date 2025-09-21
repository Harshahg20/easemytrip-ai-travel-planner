import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Layout from "./Layout";
import Landing from "./pages/Landing";
import TripForm from "./pages/TripForm";
import TripOptions from "./pages/TripOptions";
import TripPlanner from "./pages/TripPlanner";
import MyTrips from "./pages/MyTrips";

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/trip-form" element={<TripForm />} />
          <Route path="/trip-options" element={<TripOptions />} />
          <Route path="/trip-planner" element={<TripPlanner />} />
          <Route path="/my-trips" element={<MyTrips />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
