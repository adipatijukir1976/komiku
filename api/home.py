from flask import Blueprint, jsonify
import requests
from bs4 import BeautifulSoup
from functools import lru_cache

home_bp = Blueprint('home', __name__)

BASE_URL = 'https://komiku.org'
HEADERS = {
    'User-Agent': 'Mozilla/5.0'
}

# ID section → class artikel
SECTION_CLASS_MAP = {
    'Rekomendasi_Komik': ('Rekomendasi Komik', 'ls2'),
    'Komik_Hot_Manga': ('Hot Manga', 'ls2'),
    'Komik_Hot_Manhwa': ('Hot Manhwa', 'ls2'),
    'Komik_Hot_Manhua': ('Hot Manhua', 'ls2'),
    'Terbaru': ('Komik Terbaru', 'ls8')
}

def get_soup(url=BASE_URL):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def parse_article(article):
    try:
        title_tag = article.find('h3').find('a')
        title = title_tag.text.strip()
        link = BASE_URL + title_tag['href']

        img_tag = article.find('img')
        image_url = img_tag.get('data-src') or img_tag.get('src') if img_tag else ''

        chapter_tag = article.find('a', class_='ls2l') or article.find('a', class_='ls24')
        chapter = chapter_tag.text.strip() if chapter_tag else ''
        chapter_link = BASE_URL + chapter_tag['href'] if chapter_tag else ''

        genre_tag = (
            article.find('span', class_='ls2t') or
            article.find('span', class_='ls4s') or
            article.find('span')
        )
        genre = genre_tag.text.strip() if genre_tag else ''

        rank_tag = article.find('span', class_='hot')
        rank = rank_tag.text.strip() if rank_tag else ''

        return {
            'title': title,
            'link': link,
            'image_url': image_url,
            'chapter': chapter,
            'chapter_link': chapter_link,
            'genre': genre,
            'rank': rank
        }
    except Exception as e:
        print(f"Error parsing article: {e}")
        return None

def parse_section(soup, section_id, article_class):
    section = soup.find('section', {'id': section_id})
    if not section:
        return []

    komik_list = []
    articles = section.find_all('article', class_=article_class)
    for article in articles:
        komik = parse_article(article)
        if komik:
            komik_list.append(komik)

    return komik_list

def get_all_sections():
    soup = get_soup()
    if not soup:
        return {'error': 'Gagal mengambil halaman'}

    # Genre dari <select name="genre">
    genres = []
    genre_select = soup.find('select', {'name': 'genre'})
    if genre_select:
        for option in genre_select.find_all('option'):
            value = option.get('value', '').strip()
            name = option.text.strip()
            if value and name.lower() != 'genre 1':
                genres.append({'slug': value, 'name': name})

    # Section Komik
    section_data = []
    for section_id, (label, article_class) in SECTION_CLASS_MAP.items():
        items = parse_section(soup, section_id, article_class)
        if items:
            section_data.append({'title': label, 'items': items})

    return {
        'sections': section_data,
        'genres': genres
    }

@lru_cache(maxsize=1)
def get_cached_home():
    return get_all_sections()

@home_bp.route('/home')
def home_endpoint():
    data = get_cached_home()
    if 'error' in data:
        return jsonify(data), 500
    return jsonify(data)
            
