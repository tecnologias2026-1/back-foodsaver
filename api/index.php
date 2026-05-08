<?php
// Enable error reporting
error_reporting(E_ALL);
ini_set('display_errors', 1);

// Set headers
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');
header('Content-Type: application/json; charset=utf-8');

// Handle preflight requests
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
  http_response_code(200);
  exit();
}

// Autoload classes
spl_autoload_register(function ($class) {
  $file = str_replace('\\', '/', $class) . '.php';
  if (file_exists($file)) {
    require_once $file;
  }
});

// Get request method and path
$method = $_SERVER['REQUEST_METHOD'];
$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
if (strpos($path, '/api') === 0) {
  $path = substr($path, 4);
}
if ($path === '') {
  $path = '/';
}

// Route requests
if (strpos($path, '/usuarios') === 0) {
  require_once 'routes/user.routes.php';
  handleUserRoutes($method, $path);
} elseif ($path === '/') {
  http_response_code(200);
  echo json_encode(['message' => 'Servidor backend activo']);
} else {
  http_response_code(404);
  echo json_encode(['error' => 'Ruta no encontrada']);
}
?>
