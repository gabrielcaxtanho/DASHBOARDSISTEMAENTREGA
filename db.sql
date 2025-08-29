CREATE DATABASE maquinas_ti;

USE maquinas_ti;

CREATE TABLE maquinas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patrimonio VARCHAR(50) NOT NULL,
    tipo ENUM('1', '2') NOT NULL,
    setor VARCHAR(100) NOT NULL,
    status ENUM('pendente', 'entregue') DEFAULT 'pendente'
);
