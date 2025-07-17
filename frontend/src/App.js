import React, { useState } from "react";
import axios from "axios";
import UmapChart from "./UmapChart";
import mlbLogo from "./mlb-logo.svg";

const API_URL = process.env.REACT_APP_API_URL;

// Modal for UMAP dot details
function PitchModal({ data, onClose }) {
  if (!data) return null;
  return (
    <div
      style={{
        position: "fixed",
        top: 0, left: 0, right: 0, bottom: 0,
        background: "rgba(0,0,0,0.5)",
        display: "flex", alignItems: "center", justifyContent: "center",
        zIndex: 1000
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: "#fff",
          color: "#222",
          padding: 24,
          borderRadius: 8,
          minWidth: 320,
          maxWidth: 400,
          boxShadow: "0 2px 16px rgba(0,0,0,0.2)"
        }}
        onClick={e => e.stopPropagation()}
      >
        <h3>
          {data.name} ({data.pitch_type}, {data.year})
        </h3>
        <ul style={{ listStyle: "none", padding: 0 }}>
          {Object.entries(data).map(([key, value]) => {
            if (
              ["name", "pitch_type", "year", "umap_1", "umap_2", "final_working_URL"].includes(key)
            )
              return null;
            return (
              <li key={key}>
                <strong>
  {key.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}:
</strong> {value}
              </li>
            );
          })}
        </ul>
        {data.final_working_URL && (
          <a
            href={data.final_working_URL}
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: "#0077cc", textDecoration: "underline", display: "block", marginTop: 12 }}
          >
            View on Baseball Savant
          </a>
        )}
        <button
          onClick={onClose}
          style={{
            marginTop: 16,
            background: "#0077cc",
            color: "#fff",
            border: "none",
            borderRadius: 4,
            padding: "8px 16px",
            cursor: "pointer"
          }}
        >
          Close
        </button>
      </div>
    </div>
  );
}

export default function App() {
  const [mode, setMode] = useState("player");
  const [pitcherName, setPitcherName] = useState("");
  const [pitchType, setPitchType] = useState("FF");
  const [year, setYear] = useState("");
  const [features, setFeatures] = useState({
    avg_speed: "",
    avg_spin: "",
    avg_break_x: "",
    avg_break_z: "",
    avg_break_z_induced: "",
    avg_break: "",
    range_speed: "",
    usage_pct: ""
  });
  const [results, setResults] = useState([]);
  const [error, setError] = useState(null);
  const [userUmapPoint, setUserUmapPoint] = useState(null);


  // For UMAP modal
  const [umapModalData, setUmapModalData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const pitchTypeLabels = {
    FF: "Four-Seam Fastball",
    SL: "Slider",
    CH: "Changeup",
    CU: "Curveball",
    FC: "Cutter",
    SI: "Sinker",
    FS: "Splitter",
    KN: "Knuckleball"
  };

  const FEATURE_LABELS = {
    avg_speed: "Average Speed (MPH)",
    avg_spin: "Average Spin (RPM)",
    avg_break_x: "Average Break X (Inches)",
    avg_break_z: "Average Break Z (Inches)",
    avg_break_z_induced: "Average Induced Break Z (Inches)",
    avg_break: "Average Break (Inches)",
    range_speed: "Range Speed (MPH)",
    usage_pct: "Usage %"
  };

  const handleFeatureChange = (e) => {
    setFeatures({ ...features, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setResults([]);
    setUserUmapPoint(null);
    setIsLoading(true);

    try {
  if (mode === "player") {
    const res = await axios.post(`${API_URL}/compare_by_player`, {
      name: pitcherName,
      pitch_type: pitchType,
      year: year ? parseInt(year) : undefined
    });
    setResults(res.data);

    if (res.data.length > 0) {
      setUserUmapPoint({
        umap_1: res.data[0].umap_1,
        umap_2: res.data[0].umap_2
      });
    }
  } else {
    const filtered = {};
    Object.keys(features).forEach((key) => {
      if (features[key] !== "") filtered[key] = parseFloat(features[key]);
    });

    if (Object.keys(filtered).length < 2) {
      setError("Please provide at least two features.");
      return;
    }

    const [compareRes, umapRes] = await Promise.all([
      axios.post(`${API_URL}/compare_by_features`, filtered),
      axios.post(`${API_URL}/project_umap`, filtered)
    ]);

    setResults(compareRes.data);
    setUserUmapPoint(umapRes.data);
  }
} catch (err) {
  setError("No results found or an error occurred.");
  console.error(err);
} finally {
  setIsLoading(false);
}
  };

  const getDistanceColor = (dist) => {
    if (dist < 0.4) return "text-green-400";
    if (dist < 0.7) return "text-yellow-400";
    return "text-red-400";
  };

  return (
    <div className="min-h-screen bg-slate-900 text-white py-10 px-4 font-sans">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-4xl font-extrabold text-center text-emerald-400 mb-8">
          ⚾ PitchDNA
        </h1>
        <p className="text-center text-slate-300 mb-6 text-lg">
          A Pitch Similarity Engine — Choose Between Comparing MLB Pitchers With Each Other, Or Your Own Pitch Data
        </p>

        <div className="flex justify-center space-x-4 mb-8">
          <button
            onClick={() => setMode("player")}
            className={`px-4 py-2 rounded-md font-medium transition ${
              mode === "player" ? "bg-emerald-500 text-white" : "bg-slate-700 hover:bg-slate-600"
            }`}
          >
            Compare Pitchers
          </button>
          <button
            onClick={() => setMode("features")}
            className={`px-4 py-2 rounded-md font-medium transition ${
              mode === "features" ? "bg-emerald-500 text-white" : "bg-slate-700 hover:bg-slate-600"
            }`}
          >
            Find Your MLB Comparison
          </button>
        </div>

        <form onSubmit={handleSubmit} className="bg-slate-800 p-6 rounded-lg space-y-4 shadow-lg">
          {mode === "player" ? (
            <>
              <div>
                <label className="block text-sm font-semibold mb-1">Pitcher Name</label>
                <input
                  type="text"
                  value={pitcherName}
                  onChange={(e) => setPitcherName(e.target.value)}
                  className="w-full px-3 py-2 rounded bg-slate-700 text-white border border-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  placeholder="e.g. Shohei Ohtani"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold mb-1">Pitch Type</label>
                <select
                  value={pitchType}
                  onChange={(e) => setPitchType(e.target.value)}
                  className="w-full px-3 py-2 rounded bg-slate-700 text-white border border-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                >
                  {Object.keys(pitchTypeLabels).map((type) => (
                    <option key={type} value={type}>
                      {pitchTypeLabels[type]}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-semibold mb-1">Year</label>
                <select
                  value={year}
                  onChange={(e) => setYear(e.target.value)}
                  className="w-full px-3 py-2 rounded bg-slate-700 text-white border border-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                >
                  <option value="">Any Year</option>
                  {[...Array(2025 - 2015).keys()].map(i => {
                    const y = 2015 + i;
                    return <option key={y} value={y}>{y}</option>;
                  })}
                </select>
              </div>
            </>
          ) : (
            <>
              {Object.keys(features).map((key) => (
                <div key={key}>
                  <label className="block text-sm font-semibold mb-1">
                    {FEATURE_LABELS[key]}
                  </label>
                  <input
                    type="number"
                    name={key}
                    value={features[key]}
                    onChange={handleFeatureChange}
                    className="w-full px-3 py-2 rounded bg-slate-700 text-white border border-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    step="any"
                  />
                </div>
              ))}
              <p className="text-xs text-slate-400">
                Fill in at least 2 fields to get accurate results.
              </p>
            </>
          )}

          <button
            type="submit"
            className="w-full bg-emerald-600 hover:bg-emerald-700 text-white py-2 px-4 rounded transition font-semibold"
          >
            Find Similar Pitches
          </button>
        </form>
        
        {isLoading && (
  <div className="flex justify-center mt-6">
    <div className="loader"></div>
  </div>
)}


        {error && (
          <div className="mt-4 text-red-400 text-center font-semibold">
            {error}
          </div>
        )}

        {results.length > 0 && (
          <div className="mt-10">
            <h2 className="text-2xl font-bold text-emerald-300 mb-4">Top Matches</h2>
            <p className="text-sm text-slate-400 mb-2 italic">
              Distance is a similarity metric (lower = more similar).{" "}
              <span title="Distance is a Euclidean score based on pitch characteristics like speed, spin, and movement. Lower scores mean higher similarity.">
                Hover to learn more.
              </span>
            </p>
            <ul className="space-y-4">
              {results.map((item, idx) => (
                <li key={idx} className="bg-slate-800 p-4 rounded-lg shadow border border-slate-700">
                  <div><strong>Pitcher:</strong> {item.name}</div>
                  <div><strong>Pitch Type:</strong> {pitchTypeLabels[item.pitch_type] || item.pitch_type}</div>
                  <div><strong>Year:</strong> {item.year}</div>
                  <div className={getDistanceColor(item.distance)}>
                    <strong>Distance:</strong> {item.distance.toFixed(3)}
                  </div>
                  {item.video_url && (
  <div className="mt-2 flex items-center space-x-2">
    <a
      href={item.video_url}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center text-blue-400 underline"
    >
      <img src={mlbLogo} alt="MLB" className="w-5 h-5 mr-1" />
      Watch on Baseball Savant
    </a>
  </div>
)}
                  {item.matched_name && (
                    <div><strong>Matched Input:</strong> {item.matched_name}</div>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* UMAP Chart with modal integration */}
        <UmapChart userPoint={userUmapPoint} onDotClick={setUmapModalData} />

        <div className="mt-10 text-center">
          <a href="https://www.mlb.com" target="_blank" rel="noopener noreferrer">
            <img src={mlbLogo} alt="MLB Logo" className="mx-auto h-12" />
          </a>
        </div>


        {/* Modal for UMAP dot details */}
        <PitchModal data={umapModalData} onClose={() => setUmapModalData(null)} />
      </div>
    </div>
  );
}
