
DROP DATABASE IF EXISTS library_lab4;

CREATE DATABASE library_lab4
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE library_lab4;


CREATE TABLE AUTHOR (
    author_id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    country VARCHAR(80) NOT NULL,
    photo_filename VARCHAR(255),
    PRIMARY KEY (author_id)
);

CREATE TABLE PUBLISHER (
    publisher_id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    country VARCHAR(80) NOT NULL,
    PRIMARY KEY (publisher_id)
);

CREATE TABLE CATEGORY (
    category_id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    PRIMARY KEY (category_id)
);

CREATE TABLE MEMBER (
    member_id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    join_date DATE NOT NULL,
    PRIMARY KEY (member_id),
    UNIQUE (email)
);

CREATE TABLE BOOK (
    book_id INT NOT NULL AUTO_INCREMENT,
    title VARCHAR(150) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    publish_year INT NOT NULL,
    author_id INT NOT NULL,
    publisher_id INT NOT NULL,
    category_id INT NOT NULL,
    cover_filename VARCHAR(255),

    PRIMARY KEY (book_id),

    CONSTRAINT fk_book_author
        FOREIGN KEY (author_id)
        REFERENCES AUTHOR(author_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_book_publisher
        FOREIGN KEY (publisher_id)
        REFERENCES PUBLISHER(publisher_id),

    CONSTRAINT fk_book_category
        FOREIGN KEY (category_id)
        REFERENCES CATEGORY(category_id)
);

CREATE TABLE LOAN (
    loan_id INT NOT NULL AUTO_INCREMENT,
    book_id INT NOT NULL,
    member_id INT NOT NULL,
    loan_date DATE NOT NULL,
    return_date DATE DEFAULT NULL,

    PRIMARY KEY (loan_id),

    CONSTRAINT fk_loan_book
        FOREIGN KEY (book_id)
        REFERENCES BOOK(book_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_loan_member
        FOREIGN KEY (member_id)
        REFERENCES MEMBER(member_id)
);
