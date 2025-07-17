import React, { useEffect, useState, useRef } from "react";
import Plot from "react-plotly.js";
import axios from "axios";
const API_URL = process.env.REACT_APP_API_URL;

const PITCH_TYPE_MAP = {
  FF: "Four-Seam Fastball",
  SL: "Slider",
  CH: "Changeup",
  CU: "Curveball",
  FC: "Cutter",
  SI: "Sinker",
  FS: "Splitter",
  KN: "Knuckleball"
};

export default function UmapChart({ userPoint, onDotClick }) {
  const [data, setData] = useState([]);
  const [customDataMap, setCustomDataMap] = useState({});
  const plotRef = useRef();

  useEffect(() => {
    axios.get(`${API_URL}/umap_data`).then((response) => {
      const df = response.data;
      const grouped = {};
      const customDataMapTemp = {};

      // Group by pitch type for color separation
      df.forEach((row, idx) => {
        const key = row.pitch_type;
        if (!grouped[key]) {
          grouped[key] = {
            x: [],
            y: [],
            mode: "markers",
            type: "scatter",
            name: PITCH_TYPE_MAP[key] || key,
            marker: {
              size: 7,
              opacity: 0.7
            },
            text: [],
            hoverinfo: "text",
            customdata: []
          };
        }
        grouped[key].x.push(row.umap_1);
        grouped[key].y.push(row.umap_2);
        grouped[key].text.push(`${row.name} (${row.year})<br>${PITCH_TYPE_MAP[key] || key}`);
        grouped[key].customdata.push(row); // Attach full row for click
      });

      const plotData = Object.values(grouped);

      // Overlay the user's point as a large white dot in the foreground
      if (userPoint) {
        plotData.push({
          x: [userPoint.umap_1],
          y: [userPoint.umap_2],
          mode: "markers",
          type: "scatter",
          name: "Your Pitch",
          marker: {
            color: "white",
            size: 14,
            opacity: 1,
            line: {
              color: "black",
              width: 4
            }
          },
          text: ["Your Input"],
          hoverinfo: "text",
          customdata: [{}]
        });
      }

      setData(plotData);
    });
  }, [userPoint]);

  // Set up layout, optionally zoom to user's point
  let layout = {
    width: 700,
    height: 500,
    title: "UMAP of Pitch Types",
    xaxis: { title: "UMAP 1" },
    yaxis: { title: "UMAP 2" },
    plot_bgcolor: "#1e293b",
    paper_bgcolor: "#1e293b",
    font: { color: "#ffffff" },
    showlegend: true,
    dragmode: "zoom"
  };

  // Handle dot click
  const handleClick = (event) => {
    if (!onDotClick) return;
    // event.points is an array of clicked points (usually length 1)
    const pt = event.points && event.points[0];
    if (pt && pt.customdata) {
      onDotClick(pt.customdata);
    }
  };

  return (
    <div className="mt-12">
      <h2 className="text-2xl font-bold mb-4 text-emerald-400 text-center">
        Pitch UMAP Visualization
      </h2>
      <Plot
        data={data}
        layout={layout}
        style={{ margin: "0 auto" }}
        onClick={handleClick}
        ref={plotRef}
        config={{ displayModeBar: false }}
      />
    </div>
  );
}
