import express from 'express';
import analyze from './api/analyze.js';

const app = express();
app.disable('x-powered-by');
app.use(express.json({ limit: '2mb' }));

app.get('/health', (_req, res) => {
  res.json({ ok: true, service: 'securely-server' });
});

function wrap(handler) {
  return (req, res, next) => Promise.resolve(handler(req, res)).catch(next);
}

app.post('/api/analyze', wrap(analyze));

const port = parseInt(process.env.PORT || '3000', 10);
app.listen(port, () => {
  console.log(`securely-server listening on port ${port}`);
});

