import { BrowserRouter as Router, Route, Routes } from "react-router-dom";

import Home from "@/pages/Home";
import { TokenResearch } from "@/pages/FetResearch";
import { TokenPositionsPage } from "@/pages/TokenPositionsPlaceholder";

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/tokens/:symbol" element={<TokenResearch />} />
        <Route path="/tokens/:symbol/positions" element={<TokenPositionsPage />} />
      </Routes>
    </Router>
  );
}
