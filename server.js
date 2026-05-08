const http = require('http');
const url = require('url');
const querystring = require('querystring');

// Import routes
const userRoutes = require('./routes/user.routes');

// Get environment variables
const PORT = process.env.PORT || 3000;

// Create server
const server = http.createServer((req, res) => {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Content-Type', 'application/json');

  // Handle preflight requests
  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  // Parse URL
  const parsedUrl = url.parse(req.url, true);
  const pathname = parsedUrl.pathname;

  // Route requests
  if (pathname.startsWith('/api/users')) {
    userRoutes(req, res, pathname, parsedUrl.query);
  } else if (pathname === '/') {
    res.writeHead(200);
    res.end(JSON.stringify({ message: 'Servidor backend activo' }));
  } else {
    res.writeHead(404);
    res.end(JSON.stringify({ error: 'Ruta no encontrada' }));
  }
});

// Start server
server.listen(PORT, () => {
  console.log(`Servidor ejecutándose en puerto ${PORT}`);
  console.log(`http://localhost:${PORT}`);
});

module.exports = server;
