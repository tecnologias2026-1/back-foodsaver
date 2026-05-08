<?php
require_once __DIR__ . '/../database/connection.php';

global $conn;

function getUsersModel() {
  global $conn;
  
  $query = "SELECT * FROM usuario";
  $result = $conn->query($query);
  
  if (!$result) {
    return false;
  }
  
  $users = [];
  while ($row = $result->fetch_assoc()) {
    $users[] = $row;
  }
  
  return $users;
}

function getUserByIdModel($id) {
  global $conn;
  
  $id = intval($id);
  $query = "SELECT * FROM usuario WHERE id = ?";
  
  $stmt = $conn->prepare($query);
  if (!$stmt) {
    return false;
  }
  
  $stmt->bind_param("i", $id);
  $stmt->execute();
  $result = $stmt->get_result();
  
  if (!$result) {
    return false;
  }
  
  $user = $result->fetch_assoc();
  $stmt->close();
  
  return $user;
}

function createUserModel($data) {
  global $conn;
  
  $nombre = $data['nombre'] ?? '';
  $email = $data['email'] ?? '';
  $telefono = $data['telefono'] ?? null;
  
  $query = "INSERT INTO usuario (nombre, cedula, correo) VALUES (?, ?, ?)";
  
  $stmt = $conn->prepare($query);
  if (!$stmt) {
    return false;
  }
  
  $stmt->bind_param("sss", $nombre, $email, $telefono);
  if (!$stmt->execute()) {
    return false;
  }
  
  $id = $conn->insert_id;
  $stmt->close();
  
  return $id;
}

function updateUserModel($id, $data) {
  global $conn;
  
  $id = intval($id);
  $nombre = $data['nombre'] ?? null;
  $email = $data['email'] ?? null;
  $telefono = $data['telefono'] ?? null;
  
  $query = "UPDATE users SET nombre = ?, email = ?, telefono = ? WHERE id = ?";
  
  $stmt = $conn->prepare($query);
  if (!$stmt) {
    return false;
  }
  
  $stmt->bind_param("sssi", $nombre, $email, $telefono, $id);
  if (!$stmt->execute()) {
    return false;
  }
  
  $affected = $stmt->affected_rows;
  $stmt->close();
  
  return $affected;
}

function deleteUserModel($id) {
  global $conn;
  
  $id = intval($id);
  $query = "DELETE FROM users WHERE id = ?";
  
  $stmt = $conn->prepare($query);
  if (!$stmt) {
    return false;
  }
  
  $stmt->bind_param("i", $id);
  if (!$stmt->execute()) {
    return false;
  }
  
  $affected = $stmt->affected_rows;
  $stmt->close();
  
  return $affected;
}
?>
