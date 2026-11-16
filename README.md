
# Database Lab 4 - Part 2

## Library Management Website

This project implements Part 2 of Database Lab 4.
We extended our previous Flask and MySQL website with
new library tables, search pages, and reports.

## Database

Database name: library_lab4

Tables:
- AUTHOR
- PUBLISHER
- CATEGORY
- BOOK
- MEMBER
- LOAN

## Features

- F2.1: Search books by title, price range, and category.
- F2.2: Catalogue with author, publisher, and category names.
- F2.3: Reports using GROUP BY and HAVING.
- F2.4: Loans, members without loans, and books never borrowed.
- F2.5: Most borrowed books and member.
- F2.6: Authors with book counts and same-country matches.

## Bonus

The search page uses parameterized SQL queries with
%s placeholders to handle user input safely.

## How to Run

1. Install MySQL and Python.
2. Open MySQL Workbench.
3. Run problem2_DDL.sql to create the library_lab4 database.
4. Run problem2_DML.sql to insert the seed data.
5. Run problem2_Queries.sql to test the search queries.
6. Make sure the Lab 2 registration database exists.
7. Create website/.env using website/.env.example.
8. Set your MySQL connection details and:
   LIBRARY_DB_NAME=library_lab4
9. Open a terminal in the website folder.
10. Install the dependencies:

   python -m pip install -r requirements.txt

11. Start the website:

   python app.py

12. Open http://127.0.0.1:5000
13. Log in and click Lab 4 Search & Reports.

## Notes

- The website keeps the registration and login features
  from previous labs.
- The original Lab 3 database was backed up separately.
- Running problem2_DDL.sql resets library_lab4.
- The .env file contains private configuration and
  must not be uploaded to GitHub.
