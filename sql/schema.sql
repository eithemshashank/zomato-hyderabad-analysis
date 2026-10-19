-- MySQL 8. Load data/processed/*.csv with the Table Data Import Wizard (or LOAD DATA).
CREATE DATABASE IF NOT EXISTS zomato_hyd;
USE zomato_hyd;

CREATE TABLE restaurants (
    restaurant            VARCHAR(100) PRIMARY KEY,
    url                   VARCHAR(255),
    collections           TEXT,
    cuisines              TEXT,
    timings               VARCHAR(255),
    cost_for_two          INT,
    n_cuisines            INT,
    has_collection        BOOLEAN,
    late_night_collection BOOLEAN,
    is_24h                BOOLEAN,
    closes_late           BOOLEAN          -- closes at midnight or later; NULL if timings missing
);

CREATE TABLE reviews (
    review_id          INT PRIMARY KEY,
    restaurant         VARCHAR(100),
    reviewer           VARCHAR(150),
    review             TEXT,
    rating             DECIMAL(2,1),
    pictures           INT,
    time               DATETIME,
    reviewer_reviews   INT,
    reviewer_followers INT,
    review_length      INT,
    has_text           BOOLEAN,
    has_pictures       BOOLEAN,
    FOREIGN KEY (restaurant) REFERENCES restaurants(restaurant)
);

CREATE TABLE restaurant_collections (restaurant VARCHAR(100), collection VARCHAR(100));
CREATE TABLE restaurant_cuisines   (restaurant VARCHAR(100), cuisine    VARCHAR(50));
