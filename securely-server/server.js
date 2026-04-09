import express from "express";
import analyzeRouter from "./api/analyze.js"; // adjust if your file path differs

const app = express();

app.use(express.json({ limit: "25mb" }));
app.use(express.urlencoded({ limit: "25mb", extended: true }));

// Routes
app.use("/api/analyze", analyzeRouter);

// Health check
app.get("/health", (req, res) => {
  res.json({ ok: true, service: "securely-server" });
});

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
