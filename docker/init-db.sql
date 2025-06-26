-- Création des extensions nécessaires
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Insertion des offres de tickets par défaut
INSERT INTO ticket_offers (tickets_amount, price_euros, name, created_at, updated_at) VALUES
(1, 2.0, '1 Ticket', NOW(), NOW()),
(10, 15.0, '10 Tickets', NOW(), NOW()),
(20, 20.0, '20 Tickets', NOW(), NOW())
ON CONFLICT DO NOTHING;

-- Insertion de jeux d'exemple
INSERT INTO games (nom, description, min_players, max_players, ticket_cost, created_at, updated_at) VALUES
('Street Fighter', 'Jeu de combat classique', 1, 2, 1, NOW(), NOW()),
('Pac-Man', 'Jeu d''arcade emblématique', 1, 1, 1, NOW(), NOW()),
('Tekken', 'Jeu de combat en 3D', 1, 2, 1, NOW(), NOW()),
('Space Invaders', 'Shoot''em up spatial', 1, 1, 1, NOW(), NOW())
ON CONFLICT DO NOTHING;

-- Insertion de bornes d'arcade d'exemple
INSERT INTO arcades (nom, description, api_key, localisation, latitude, longitude, created_at, updated_at) VALUES
('Arcade Central', 'Borne principale du centre-ville', 'arcade_key_central_123', 'Centre-ville Toulouse', 43.6047, 1.4442, NOW(), NOW()),
('Arcade Campus', 'Borne du campus universitaire', 'arcade_key_campus_456', 'Campus Université Toulouse', 43.5615, 1.4679, NOW(), NOW())
ON CONFLICT DO NOTHING;

-- Association des jeux aux bornes (2 jeux par borne)
INSERT INTO arcade_games (arcade_id, game_id, slot_number, created_at, updated_at) VALUES
(1, 1, 1, NOW(), NOW()), -- Street Fighter sur borne 1, slot 1
(1, 2, 2, NOW(), NOW()), -- Pac-Man sur borne 1, slot 2
(2, 3, 1, NOW(), NOW()), -- Tekken sur borne 2, slot 1
(2, 4, 2, NOW(), NOW())  -- Space Invaders sur borne 2, slot 2
ON CONFLICT DO NOTHING;