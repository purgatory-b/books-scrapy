# Selenium Book Crawler

A Python-based web scraping project for collecting book information from an online bookstore platform.

This project automates the full scraping workflow, including:

- Website login with Selenium
- CAPTCHA image handling and solving
- Keyword-based book search
- Pagination crawling
- Book detail extraction
- Cover image download
- MySQL database storage

## Highlights

- Built a real-world crawler for structured book metadata collection
- Combined browser automation and HTML parsing for dynamic pages
- Integrated CAPTCHA solving into the scraping workflow
- Designed database insertion flow for scraped records

## Features

- Automated login with Selenium
- CAPTCHA solving integration
- Search results crawling across multiple pages
- Detailed book metadata extraction
- Image download and Base64 conversion
- MySQL storage with SQLAlchemy ORM

## Tech Stack

- Python
- Selenium
- lxml
- SQLAlchemy
- Requests
- Pillow
- MySQL

## Extracted Data

The crawler collects the following book information:

- ISBN
- Title
- Detail page URL
- Cover image
- Author
- Translator
- Publisher
- Publication place
- Original price
- Discounted price
- Specification

## Project Structure

```bash
books-scrapy/
├── README.md
├── scrapy.py
├── scrapy.sql
└── image/
