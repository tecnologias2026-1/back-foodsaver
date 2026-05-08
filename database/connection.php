<?php
// Database connection
define('DB_HOST', getenv('DB_HOST') ?: 'sql202.infinityfree.com');
define('DB_USER', getenv('DB_USER') ?: 'if0_41710395');
define('DB_PASSWORD', getenv('DB_PASSWORD') ?: 'bgCGG87D4RDlBz');
define('DB_NAME', getenv('DB_NAME') ?: 'if0_41710395_mula');
define('DB_PORT', getenv('DB_PORT') ?: 3306);

// Create connection
$conn = new mysqli(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT);

// Check connection
if ($conn->connect_error) {
  die(json_encode(['error' => 'Error conectando a la base de datos: ' . $conn->connect_error]));
}

// Set charset
$conn->set_charset('utf8');

echo "Conectado a la base de datos\n";

/*$conn->close();*/
?>
