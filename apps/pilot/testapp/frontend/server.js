/**
 * Simple Hello World Frontend
 * Replace this with your actual frontend application
 */
const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

app.get('/', (req, res) => {
  res.send(`
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Azure App Template</title>
      <style>
        body {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
          max-width: 800px;
          margin: 50px auto;
          padding: 20px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
        }
        .container {
          background: rgba(255, 255, 255, 0.1);
          padding: 40px;
          border-radius: 20px;
          backdrop-filter: blur(10px);
          box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        }
        h1 { margin-top: 0; font-size: 3em; }
        .success { color: #4ade80; }
        .status {
          background: rgba(255, 255, 255, 0.2);
          padding: 20px;
          border-radius: 10px;
          margin: 20px 0;
        }
        button {
          background: white;
          color: #667eea;
          border: none;
          padding: 15px 30px;
          font-size: 16px;
          border-radius: 8px;
          cursor: pointer;
          font-weight: bold;
          margin: 10px 5px;
        }
        button:hover { transform: scale(1.05); transition: transform 0.2s; }
        #response {
          background: rgba(0, 0, 0, 0.3);
          padding: 15px;
          border-radius: 8px;
          margin-top: 20px;
          font-family: monospace;
          word-wrap: break-word;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>🚀 Azure App Template</h1>
        <p class="success">✅ Successfully deployed to Azure!</p>

        <div class="status">
          <h3>📊 Status</h3>
          <p><strong>Frontend:</strong> Running on port ${PORT}</p>
          <p><strong>Backend:</strong> ${BACKEND_URL}</p>
          <p><strong>Environment:</strong> ${process.env.ENVIRONMENT || 'dev'}</p>
        </div>

        <h3>🧪 Test Backend Connection</h3>
        <button onclick="testBackend('/')">Test Root Endpoint</button>
        <button onclick="testBackend('/health')">Health Check</button>
        <button onclick="testBackend('/api/info')">API Info</button>

        <div id="response"></div>

        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.3);">
          <h3>🎯 Next Steps</h3>
          <ol>
            <li>Replace <code>backend/main.py</code> with your backend code</li>
            <li>Replace <code>frontend/</code> with your React/Vue/Angular app</li>
            <li>Update <code>app-config.yml</code> with your settings</li>
            <li>Push to main branch to redeploy</li>
          </ol>
        </div>
      </div>

      <script>
        async function testBackend(endpoint) {
          const responseDiv = document.getElementById('response');
          responseDiv.innerHTML = '<p>⏳ Loading...</p>';

          try {
            const response = await fetch('${BACKEND_URL}' + endpoint);
            const data = await response.json();
            responseDiv.innerHTML = '<p><strong>✅ Response from ' + endpoint + ':</strong></p><pre>' +
              JSON.stringify(data, null, 2) + '</pre>';
          } catch (error) {
            responseDiv.innerHTML = '<p><strong>❌ Error:</strong></p><pre>' + error.message + '</pre>';
          }
        }
      </script>
    </body>
    </html>
  `);
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy', frontend: 'running' });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Frontend server running on port ${PORT}`);
  console.log(`Backend URL: ${BACKEND_URL}`);
});
