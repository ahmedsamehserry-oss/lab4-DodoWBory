
USE library_lab4;


-- F2.1
-- Search books by title, price range, and category

-- Example search values
SET @keyword = _utf8mb4'' COLLATE utf8mb4_unicode_ci;
SET @min_price = 0;
SET @max_price = 999999;
SET @category_id = NULL;

-- Available categories for the search form
SELECT category_id, name
FROM CATEGORY
ORDER BY name;

-- Search results
-- NULL category_id means all categories
SELECT
    b.book_id,
    b.title,
    b.price,
    b.publish_year,
    c.name AS category_name
FROM BOOK b
JOIN CATEGORY c
    ON b.category_id = c.category_id
WHERE b.title LIKE CONCAT('%', @keyword, '%')
  AND b.price BETWEEN @min_price AND @max_price
  AND (@category_id IS NULL
       OR b.category_id = @category_id)
ORDER BY b.price ASC, b.book_id ASC;


-- F2.2
-- Catalogue: book, author, publisher, category

SELECT
    b.book_id,
    b.title,
    b.price,
    b.publish_year,
    a.name AS author_name,
    p.name AS publisher_name,
    c.name AS category_name
FROM BOOK b
JOIN AUTHOR a
    ON b.author_id = a.author_id
JOIN PUBLISHER p
    ON b.publisher_id = p.publisher_id
JOIN CATEGORY c
    ON b.category_id = c.category_id
ORDER BY b.title;


-- F2.3 (a)
-- Number of books and average price per category

SELECT
    c.name AS category_name,
    COUNT(b.book_id) AS total_books,
    ROUND(AVG(b.price), 2) AS average_price
FROM CATEGORY c
LEFT JOIN BOOK b
    ON c.category_id = b.category_id
GROUP BY c.category_id, c.name
ORDER BY c.name;


-- F2.3 (b)
-- Authors who wrote at least 2 books

SELECT
    a.name AS author_name,
    COUNT(b.book_id) AS total_books
FROM AUTHOR a
JOIN BOOK b
    ON a.author_id = b.author_id
GROUP BY a.author_id, a.name
HAVING COUNT(b.book_id) >= 2
ORDER BY total_books DESC, a.name;


-- F2.3 (c)
-- Total, minimum and maximum book prices

SELECT
    SUM(price) AS total_price,
    MIN(price) AS minimum_price,
    MAX(price) AS maximum_price
FROM BOOK;


-- F2.4 (a)
-- Loans not returned yet

SELECT
    l.loan_id,
    b.title AS book_title,
    m.name AS member_name,
    l.loan_date,
    l.return_date
FROM LOAN l
JOIN BOOK b
    ON l.book_id = b.book_id
JOIN MEMBER m
    ON l.member_id = m.member_id
WHERE l.return_date IS NULL
ORDER BY l.loan_date;


-- F2.4 (b)
-- Members who never borrowed a book

SELECT
    m.member_id,
    m.name,
    m.email
FROM MEMBER m
LEFT JOIN LOAN l
    ON m.member_id = l.member_id
WHERE l.loan_id IS NULL;


-- F2.4 (c)
-- Books that were never borrowed

SELECT
    b.book_id,
    b.title,
    b.price
FROM BOOK b
LEFT JOIN LOAN l
    ON b.book_id = l.book_id
WHERE l.loan_id IS NULL;


-- F2.5 (a)
-- Top 3 most borrowed books

SELECT
    b.book_id,
    b.title,
    COUNT(l.loan_id) AS loan_count
FROM BOOK b
JOIN LOAN l
    ON b.book_id = l.book_id
GROUP BY b.book_id, b.title
ORDER BY loan_count DESC, b.book_id ASC
LIMIT 3;


-- F2.5 (b)
-- Member with the most loans

SELECT
    m.member_id,
    m.name,
    COUNT(l.loan_id) AS loan_count
FROM MEMBER m
JOIN LOAN l
    ON m.member_id = l.member_id
GROUP BY m.member_id, m.name
ORDER BY loan_count DESC, m.member_id ASC
LIMIT 1;


-- F2.6 (a)
-- All authors including authors with zero books

SELECT
    a.author_id,
    a.name,
    COUNT(b.book_id) AS total_books
FROM AUTHOR a
LEFT JOIN BOOK b
    ON a.author_id = b.author_id
GROUP BY a.author_id, a.name
ORDER BY a.name;


-- F2.6 (b)
-- Books whose author and publisher
-- are from the same country

SELECT
    b.book_id,
    b.title,
    a.name AS author_name,
    p.name AS publisher_name,
    a.country AS common_country
FROM BOOK b
JOIN AUTHOR a
    ON b.author_id = a.author_id
JOIN PUBLISHER p
    ON b.publisher_id = p.publisher_id
WHERE a.country = p.country
ORDER BY b.title;
