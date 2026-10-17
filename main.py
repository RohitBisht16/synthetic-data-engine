from io import BytesIO
import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from pypdf import PdfReader

# Import existing core modules
from evaluator import evaluate_fidelity
from generator import generate_synthetic_data
from scrubber import scrub_pii

app = FastAPI(title="Synthetic Data & Privacy Engine")


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(pdf_bytes))
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    # Serves your exact dark-mode dashboard UI with added File Upload & Export functionality
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Synthetic Data & Privacy Engine</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            body { background-color: #0b0f19; color: #f8fafc; padding: 20px; }
            
            .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #1e293b; padding-bottom: 15px; }
            .header h1 { color: #38bdf8; font-size: 22px; font-weight: 700; }
            .header p { color: #64748b; font-size: 13px; margin-top: 4px; }
            .status-badge { background-color: #064e3b; color: #34d399; border: 1px solid #059669; padding: 6px 14px; border-radius: 20px; font-weight: 600; font-size: 12px; }

            .main-container { display: grid; grid-template-columns: 360px 1fr; gap: 20px; }

            /* Left Panel Styles */
            .left-panel { display: flex; flex-direction: column; gap: 20px; }
            .panel-card { background-color: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 20px; }
            .panel-card h3 { color: #38bdf8; font-size: 14px; margin-bottom: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }

            .file-upload-box { border: 2px dashed #334155; border-radius: 6px; padding: 15px; text-align: center; background: #1e293b; cursor: pointer; transition: 0.2s; }
            .file-upload-box:hover { border-color: #38bdf8; }
            .file-upload-box input { display: none; }
            .file-upload-box label { cursor: pointer; color: #94a3b8; font-size: 13px; display: block; }
            .file-name-display { margin-top: 8px; font-size: 12px; color: #38bdf8; font-weight: 600; }

            .btn-action { width: 100%; padding: 12px; border: none; border-radius: 6px; font-weight: 700; font-size: 14px; cursor: pointer; transition: 0.2s; margin-top: 10px; }
            .btn-yellow { background-color: #eab308; color: #0f172a; }
            .btn-yellow:hover { background-color: #ca8a04; }
            .btn-blue { background-color: #2563eb; color: #ffffff; }
            .btn-blue:hover { background-color: #1d4ed8; }

            .slider-group { margin-bottom: 15px; }
            .slider-group label { display: flex; justify-content: space-between; font-size: 13px; color: #cbd5e1; margin-bottom: 6px; }
            .slider-group input[type="range"] { width: 100%; accent-color: #38bdf8; }

            /* Right Panel Styles */
            .right-panel { display: flex; flex-direction: column; gap: 20px; }
            .top-bar { display: flex; justify-content: space-between; align-items: center; }
            .tabs { display: flex; gap: 8px; }
            .tab-btn { background-color: #1e293b; color: #94a3b8; border: 1px solid #334155; padding: 8px 16px; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer; }
            .tab-btn.active { background-color: #2563eb; color: #ffffff; border-color: #2563eb; }

            .btn-export { background-color: #10b981; color: #ffffff; border: none; padding: 8px 18px; border-radius: 6px; font-weight: 700; font-size: 13px; cursor: pointer; display: none; transition: 0.2s; }
            .btn-export:hover { background-color: #059669; }

            .table-container { background-color: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 15px; height: 320px; overflow: auto; }
            table { width: 100%; border-collapse: collapse; text-align: left; font-size: 13px; }
            th { background-color: #1e293b; color: #38bdf8; padding: 10px; font-weight: 600; position: sticky; top: 0; }
            td { padding: 10px; border-bottom: 1px solid #1e293b; color: #cbd5e1; white-space: nowrap; }
            pre { color: #cbd5e1; font-size: 13px; white-space: pre-wrap; word-wrap: break-word; }

            .chart-card { background-color: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 20px; height: 260px; }
            .chart-card h4 { color: #38bdf8; font-size: 14px; margin-bottom: 10px; font-weight: 600; }
        </style>
    </head>
    <body>

    <div class="header">
        <div>
            <h1>Synthetic Data & Privacy Engine</h1>
            <p>Enterprise PII Masking, CTGAN Synthesis & Differential Privacy Evaluation Studio</p>
        </div>
        <div class="status-badge">System Status: Active</div>
    </div>

    <div class="main-container">
        <!-- LEFT CONTROL PANEL -->
        <div class="left-panel">
            
            <!-- 1. Custom File Upload -->
            <div class="panel-card">
                <h3>1. Select or Upload Dataset</h3>
                <div class="file-upload-box" onclick="document.getElementById('fileInput').click()">
                    <label>Click or Drop Custom <b>.csv</b> or <b>.pdf</b></label>
                    <input type="file" id="fileInput" accept=".csv, .pdf" onchange="updateFileName(this)">
                    <div id="fileName" class="file-name-display">No file selected</div>
                </div>
            </div>

            <!-- 2. PII Scrubber Engine -->
            <div class="panel-card">
                <h3>2. PII Scrubber Engine</h3>
                <p style="font-size: 12px; color: #64748b; margin-bottom: 10px;">Scrub names, emails, and phone numbers using SpaCy NLP pattern matchers.</p>
                <button class="btn-action btn-yellow" onclick="triggerProcess('scrub')">Execute PII Anonymization</button>
            </div>

            <!-- 3. DP-CTGAN Generator -->
            <div class="panel-card">
                <h3>3. DP-CTGAN Generator</h3>
                
                <div class="slider-group">
                    <label><span>Training Epochs:</span> <b id="epochsVal">20</b></label>
                    <input type="range" id="epochs" min="5" max="100" value="20" oninput="document.getElementById('epochsVal').textContent=this.value">
                </div>

                <div class="slider-group">
                    <label><span>Synthetic Sample Rows:</span> <b id="samplesVal">10</b></label>
                    <input type="range" id="samples" min="5" max="500" value="10" oninput="document.getElementById('samplesVal').textContent=this.value">
                </div>

                <div class="slider-group">
                    <label><span>Differential Privacy (&epsilon;):</span> <b id="epsilonVal">1.5</b></label>
                    <input type="range" id="epsilon" min="0.1" max="10.0" step="0.1" value="1.5" oninput="document.getElementById('epsilonVal').textContent=this.value">
                </div>

                <button class="btn-action btn-blue" onclick="triggerProcess('generate')">Train & Generate Synthetic Data</button>
            </div>

        </div>

        <!-- RIGHT DISPLAY PANEL -->
        <div class="right-panel">
            
            <div class="top-bar">
                <div class="tabs">
                    <button class="tab-btn active" id="tab-raw" onclick="switchTab('raw')">Raw Production Data</button>
                    <button class="tab-btn" id="tab-anonymized" onclick="switchTab('anonymized')">Anonymized Output</button>
                    <button class="tab-btn" id="tab-synthetic" onclick="switchTab('synthetic')">Synthetic Data Output</button>
                </div>
                <button class="btn-export" id="exportBtn" onclick="exportData()">↓ Export CSV / TXT</button>
            </div>

            <div class="table-container" id="tableDisplay">
                <p style="color: #64748b; text-align: center; margin-top: 100px;">Upload a .csv or .pdf file and execute an action to preview results...</p>
            </div>

            <div class="chart-card">
                <h4>Statistical Fidelity Metrics (Kolmogorov-Smirnov Test)</h4>
                <div style="height: 180px;">
                    <canvas id="fidelityChart"></canvas>
                </div>
            </div>

        </div>
    </div>

    <script>
        let currentRawCSV = "";
        let currentExportFilename = "output.csv";
        let fidelityChartInstance = null;

        function updateFileName(input) {
            if (input.files && input.files[0]) {
                document.getElementById('fileName').textContent = input.files[0].name;
            }
        }

        function switchTab(tab) {
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.getElementById(`tab-${tab}`).classList.add('active');
        }

        async function triggerProcess(mode) {
            const fileInput = document.getElementById('fileInput');
            if (!fileInput.files[0]) {
                alert("Please select a .csv or .pdf file first!");
                return;
            }

            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            formData.append('mode', mode);
            formData.append('epochs', document.getElementById('epochs').value);
            formData.append('num_samples', document.getElementById('samples').value);

            const display = document.getElementById('tableDisplay');
            display.innerHTML = '<p style="color: #38bdf8; text-align: center; margin-top: 100px;">Processing data through engine... Please wait.</p>';

            try {
                const res = await fetch('/api/process', { method: 'POST', body: formData });
                const data = await res.json();

                if (!res.ok) throw new Error(data.detail);

                if (data.file_type === 'pdf') {
                    display.innerHTML = `<pre>${data.scrubbed_text}</pre>`;
                    currentRawCSV = data.scrubbed_text;
                    currentExportFilename = "redacted_document.txt";
                    switchTab('anonymized');
                } else {
                    currentRawCSV = data.csv_raw;
                    currentExportFilename = mode === 'generate' ? "synthetic_data.csv" : "anonymized_data.csv";
                    renderTable(data.data);
                    switchTab(mode === 'generate' ? 'synthetic' : 'anonymized');

                    if (data.fidelity_scores) {
                        updateChart(data.fidelity_scores);
                    }
                }

                document.getElementById('exportBtn').style.display = 'block';

            } catch (err) {
                display.innerHTML = `<p style="color: #ef4444; text-align: center; margin-top: 100px;">Error: ${err.message}</p>`;
            }
        }

        function renderTable(records) {
            if (!records || records.length === 0) return;
            const headers = Object.keys(records[0]);
            let html = '<table><thead><tr>' + headers.map(h => `<th>${h}</th>`).join('') + '</tr></thead><tbody>';
            records.forEach(row => {
                html += '<tr>' + headers.map(h => `<td>${row[h]}</td>`).join('') + '</tr>';
            });
            html += '</tbody></table>';
            document.getElementById('tableDisplay').innerHTML = html;
        }

        function updateChart(scores) {
            const labels = Object.keys(scores);
            const values = labels.map(k => scores[k].p_value || 0.5);

            const ctx = document.getElementById('fidelityChart').getContext('2d');
            if (fidelityChartInstance) fidelityChartInstance.destroy();

            fidelityChartInstance = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Distribution Similarity (P-Value)',
                        data: values,
                        backgroundColor: '#2563eb',
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { beginAtZero: true, max: 1.0, grid: { color: '#1e293b' } },
                        x: { grid: { color: '#1e293b' } }
                    },
                    plugins: { legend: { labels: { color: '#cbd5e1' } } }
                }
            });
        }

        function exportData() {
            if (!currentRawCSV) return;
            const mimeType = currentExportFilename.endsWith('.csv') ? 'text/csv' : 'text/plain';
            const blob = new Blob([currentRawCSV], { type: mimeType });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = currentExportFilename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        }
    </script>
    </body>
    </html>
    """


@app.post("/api/process")
async def process_dataset(
    file: UploadFile = File(...),
    mode: str = Form("scrub"),
    epochs: int = Form(20),
    num_samples: int = Form(10),
):
    filename = file.filename.lower()
    contents = await file.read()

    # Handle PDF Files
    if filename.endswith(".pdf"):
        if mode == "generate":
            raise HTTPException(
                status_code=400,
                detail="PDF files contain unstructured text and only support PII Scrubbing. Upload a CSV for CTGAN generation.",
            )

        raw_text = extract_text_from_pdf(contents)
        scrubbed_text = scrub_pii(raw_text)

        return JSONResponse(
            {
                "file_type": "pdf",
                "filename": file.filename,
                "scrubbed_text": scrubbed_text,
            }
        )

    # Handle CSV Files
    elif filename.endswith(".csv"):
        df = pd.read_csv(BytesIO(contents))

        if mode == "scrub":
            for col in df.select_dtypes(include=["object"]).columns:
                df[col] = df[col].astype(str).apply(lambda val: scrub_pii(val, column_name=col))

            return JSONResponse(
                {
                    "file_type": "csv",
                    "mode": "scrub",
                    "data": df.to_dict(orient="records"),
                    "csv_raw": df.to_csv(index=False),
                }
            )

        elif mode == "generate":
            synthetic_df = generate_synthetic_data(
                df, num_samples=num_samples, epochs=epochs
            )
            fidelity_scores = evaluate_fidelity(df, synthetic_df)

            return JSONResponse(
                {
                    "file_type": "csv",
                    "mode": "generate",
                    "data": synthetic_df.to_dict(orient="records"),
                    "fidelity_scores": fidelity_scores,
                    "csv_raw": synthetic_df.to_csv(index=False),
                }
            )

    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported format. Please upload a .csv or .pdf file.",
        )