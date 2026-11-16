
USE library_lab4;

INSERT INTO AUTHOR (author_id, name, country)
VALUES
(1, 'Dodo', 'Egypt'),
(2, 'Mohamed Bory', 'Egypt'),
(3, 'Eng Basem', 'UK'),
(4, 'Mohamed Ashraf', 'USA'),
(5, 'Mohab Mohamed', 'Italy');


INSERT INTO PUBLISHER (publisher_id, name, country)
VALUES
(1, 'Nile House', 'Egypt'),
(2, 'Cambridge Press', 'UK'),
(3, 'Global Books', 'USA');


INSERT INTO CATEGORY (category_id, name)
VALUES
(1, 'Database'),
(2, 'Programming'),
(3, 'Artificial Intelligence');


INSERT INTO MEMBER (member_id, name, email, join_date)
VALUES
(1, 'Abdelrahman Waleed', 'boda@gmail.com', '2026-01-10'),
(2, 'Abdelrahman Hazem', 'Zengo@gmail.com', '2026-02-15'),
(3, 'Omar Adel', 'omar@gmail.com', '2026-03-20'),
(4, 'Mohamed Elragal', 'elragal@gmail.com', '2026-04-12'),
(5, 'Mahmoud Elragal', 'mahelragal@gmail.com', '2026-05-05'),
(6, 'Omar Elsayed', 'elsayed@gmail.com', '2026-06-01');


INSERT INTO BOOK
(book_id, title, price, publish_year, author_id, publisher_id, category_id)
VALUES
(1, 'Database Basics', 17.50, 2023, 1, 1, 1),
(2, 'SQL Made Easy', 25.00, 2024, 1, 1, 1),
(3, 'Python for Beginners', 30.00, 2022, 2, 2, 2),
(4, 'Advanced Python', 45.00, 2025, 2, 3, 2),
(5, 'Introduction to AI', 40.00, 2023, 3, 2, 3),
(6, 'Machine Learning Basics', 55.00, 2024, 3, 2, 3),
(7, 'Data Science Guide', 35.00, 2022, 4, 3, 3),
(8, 'Web Development', 28.00, 2023, 2, 1, 2),
(9, 'Database Design', 32.00, 2025, 1, 1, 1),
(10, 'Future of Technology', 60.00, 2026, 4, 3, 3);


INSERT INTO LOAN
(loan_id, book_id, member_id, loan_date, return_date)
VALUES
(1, 1, 1, '2026-01-08', '2026-01-15'),
(2, 2, 2, '2026-02-03', '2026-02-07'),
(3, 3, 3, '2026-04-01', '2026-04-10'),
(4, 4, 1, '2026-04-12', '2026-04-20'),
(5, 5, 4, '2026-05-05', '2026-05-15'),
(6, 6, 2, '2026-06-01', '2026-06-12'),
(7, 7, 5, '2026-07-03', '2026-07-15'),
(8, 8, 3, '2026-08-02', '2026-08-09'),
(9, 9, 1, '2026-09-01', '2026-09-11'),
(10, 1, 2, '2026-02-10', '2026-02-18'),
(11, 2, 4, '2026-03-05', '2026-03-09'),
(12, 1, 1, '2026-10-01', NULL);
