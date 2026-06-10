-- ФИО: Маколикова Анастасия Александровна
-- Группа: 24-ИС
-- Вариант: 10 (Фитнес-клуб)

-- Задание 1
DROP DATABASE IF EXISTS Variant10_Day5;
CREATE DATABASE Variant10_Day5;
USE Variant10_Day5;

-- Задание 2-5. Создание таблиц

CREATE TABLE Members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    birth_date DATE NOT NULL
);

CREATE TABLE Memberships (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    duration_days INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    visit_limit INT
);

CREATE TABLE MembershipPurchases (
    id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    membership_id INT NOT NULL,
    purchase_date DATE NOT NULL,
    end_date DATE NOT NULL,
    amount_paid DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (member_id) REFERENCES Members(id),
    FOREIGN KEY (membership_id) REFERENCES Memberships(id)
);

CREATE TABLE Trainings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    trainer VARCHAR(100) NOT NULL,
    max_participants INT NOT NULL
);

CREATE TABLE TrainingRegistrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    training_id INT NOT NULL,
    registration_date DATE NOT NULL,
    FOREIGN KEY (member_id) REFERENCES Members(id),
    FOREIGN KEY (training_id) REFERENCES Trainings(id)
);

CREATE TABLE Visits (
    id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    visit_date DATE NOT NULL,
    visit_time TIME NOT NULL,
    FOREIGN KEY (member_id) REFERENCES Members(id)
);

-- Задание 6. Вставить 4 клиента

INSERT INTO Members (full_name, birth_date)
VALUES
('Иванов Иван Иванович', '1990.05.12'),
('Петров Петр Сергеевич', '1988.08.21'),
('Сидорова Анна Викторовна', '1995.11.15'),
('Кузнецов Алексей Павлович', '1992.02.10');

-- Задание 7. Вставить 3 типа абонементов

INSERT INTO Memberships (name, duration_days, price, visit_limit)
VALUES
('Базовый', 30, 3000, 12),
('Стандарт', 90, 8000, 40),
('Безлимит', 365, 25000, NULL);

-- Задание 8. Добавить 2 покупки абонементов

INSERT INTO MembershipPurchases
(member_id, membership_id, purchase_date, end_date, amount_paid)
VALUES
(1, 1, '2025.05.01', '2025.05.31', 3000),
(2, 3, '2025.01.01', '2025.12.31', 25000);

-- Задание 9. Вставить 2 тренировки

INSERT INTO Trainings (title, trainer, max_participants)
VALUES
('Йога', 'Иванов', 15),
('Кроссфит', 'Петров', 10);

-- Задание 10. Создать 3 регистрации

INSERT INTO TrainingRegistrations
(member_id, training_id, registration_date)
VALUES
(1, 1, '2025.05.10'),
(2, 1, '2025.05.11'),
(3, 2, '2025.05.12');

-- Задание 11. Добавить 4 посещения

INSERT INTO Visits
(member_id, visit_date, visit_time)
VALUES
(1, CURDATE(), '09:00:00'),
(1, DATE_SUB(CURDATE(), INTERVAL 2 DAY), '18:00:00'),
(2, CURDATE(), '10:00:00'),
(3, DATE_SUB(CURDATE(), INTERVAL 5 DAY), '17:30:00');

-- Задание 12
-- Все тренировки с тренером Иванов

SELECT *
FROM Trainings
WHERE trainer = 'Иванов';

-- Задание 13
-- Клиенты с активным абонементом

SELECT m.full_name,
       mp.end_date
FROM Members m
JOIN MembershipPurchases mp
    ON m.id = mp.member_id
WHERE mp.end_date > CURDATE();

-- Задание 14
-- Сортировка клиентов по дате рождения

SELECT *
FROM Members
ORDER BY birth_date;

-- Задание 15
-- Посещения за последние 7 дней

SELECT *
FROM Visits
WHERE visit_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY);

-- Задание 16
-- Количество посещений для каждого клиента

SELECT m.full_name,
       COUNT(v.id) AS visit_count
FROM Members m
LEFT JOIN Visits v
    ON m.id = v.member_id
GROUP BY m.id, m.full_name;

-- Задание 17
-- Средняя заполняемость тренировок

SELECT
    AVG(
        registered_count / max_participants
    ) AS avg_occupancy
FROM (
    SELECT
        t.id,
        t.max_participants,
        COUNT(tr.id) AS registered_count
    FROM Trainings t
    LEFT JOIN TrainingRegistrations tr
        ON t.id = tr.training_id
    GROUP BY t.id, t.max_participants
) x;

-- Задание 18
-- Тип абонемента и количество покупок

SELECT
    ms.name,
    COUNT(mp.id) AS purchases_count
FROM Memberships ms
LEFT JOIN MembershipPurchases mp
    ON ms.id = mp.membership_id
GROUP BY ms.id, ms.name;

-- Задание 19
-- Количество участников у тренеров

SELECT
    trainer,
    COUNT(tr.id) AS participants_count
FROM Trainings t
LEFT JOIN TrainingRegistrations tr
    ON t.id = tr.training_id
GROUP BY trainer;

-- Задание 20
-- Клиенты, не посещавшие тренировки

SELECT full_name
FROM Members
WHERE id NOT IN (
    SELECT DISTINCT member_id
    FROM TrainingRegistrations
);

-- Задание 21
-- Увеличить цену абонементов на 10%

UPDATE Memberships
SET price = price * 1.10;

-- Задание 22
-- Удалить тренировку без регистраций

DELETE FROM Trainings
WHERE id NOT IN (
    SELECT DISTINCT training_id
    FROM TrainingRegistrations
);

-- Задание 23
-- Добавить телефон

ALTER TABLE Members
ADD COLUMN phone VARCHAR(20);

-- Задание 24
-- Представление активности клиентов

CREATE VIEW MemberActivity AS
SELECT
    m.id,
    m.full_name,
    COUNT(DISTINCT v.id) AS visits_count,
    COUNT(DISTINCT tr.id) AS trainings_count
FROM Members m
LEFT JOIN Visits v
    ON m.id = v.member_id
LEFT JOIN TrainingRegistrations tr
    ON m.id = tr.member_id
GROUP BY m.id, m.full_name;

-- Проверка представления

SELECT * FROM MemberActivity;

-- Задание 25
-- Сложный запрос

SELECT
    m.full_name,
    ms.name AS membership_type,
    mp.amount_paid,
    COUNT(DISTINCT v.id) AS visits_count,
    COUNT(DISTINCT tr.id) AS trainings_count,
    CASE
        WHEN ms.visit_limit IS NULL THEN 'Без ограничений'
        ELSE CAST(
            ms.visit_limit - COUNT(DISTINCT v.id)
            AS CHAR
        )
    END AS remaining_visits
FROM Members m
LEFT JOIN MembershipPurchases mp
    ON m.id = mp.member_id
LEFT JOIN Memberships ms
    ON mp.membership_id = ms.id
LEFT JOIN Visits v
    ON m.id = v.member_id
LEFT JOIN TrainingRegistrations tr
    ON m.id = tr.member_id
GROUP BY
    m.id,
    m.full_name,
    ms.name,
    mp.amount_paid,
    ms.visit_limit;