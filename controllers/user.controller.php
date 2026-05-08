<?php
require_once __DIR__ . '/../models/user.model.php';

function getAllUsers() {
  $users = getUsersModel();
  if ($users === false) {
    http_response_code(500);
    return echo json_encode(['error' => 'Error al obtener usuarios']);
  }
  http_response_code(200);
  echo json_encode($users);
}

function getUserById($id) {
  $user = getUserByIdModel($id);
  if ($user === false) {
    http_response_code(500);
    return echo json_encode(['error' => 'Error al obtener usuario']);
  }
  if (!$user) {
    http_response_code(404);
    return echo json_encode(['error' => 'Usuario no encontrado']);
  }
  http_response_code(200);
  echo json_encode($user);
}

function createUser() {
  $input = json_decode(file_get_contents('php://input'), true);
  
  if (!$input || !isset($input['nombre'], $input['email'])) {
    http_response_code(400);
    return echo json_encode(['error' => 'Datos inválidos']);
  }

  $result = createUserModel($input);
  if ($result === false) {
    http_response_code(500);
    return echo json_encode(['error' => 'Error al crear usuario']);
  }

  http_response_code(201);
  echo json_encode(['message' => 'Usuario creado', 'id' => $result]);
}

function updateUser($id) {
  $input = json_decode(file_get_contents('php://input'), true);
  
  if (!$input) {
    http_response_code(400);
    return echo json_encode(['error' => 'Datos inválidos']);
  }

  $result = updateUserModel($id, $input);
  if ($result === false) {
    http_response_code(500);
    return echo json_encode(['error' => 'Error al actualizar usuario']);
  }
  if ($result === 0) {
    http_response_code(404);
    return echo json_encode(['error' => 'Usuario no encontrado']);
  }

  http_response_code(200);
  echo json_encode(['message' => 'Usuario actualizado']);
}

function deleteUser($id) {
  $result = deleteUserModel($id);
  if ($result === false) {
    http_response_code(500);
    return echo json_encode(['error' => 'Error al eliminar usuario']);
  }
  if ($result === 0) {
    http_response_code(404);
    return echo json_encode(['error' => 'Usuario no encontrado']);
  }

  http_response_code(200);
  echo json_encode(['message' => 'Usuario eliminado']);
}
?>
