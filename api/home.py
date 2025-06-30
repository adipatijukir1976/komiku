from flask import Blueprint, jsonify
import requests
from bs4 import BeautifulSoup
from functools import lru_cache

home_bp = Blueprint('home', __name__)

BASE_URL = 'https://komiku.org'
HEADERS = {
    'User-Agent': 'Mozilla/5.0'
}

SECTION_MAP = {
    'Trending_Komik': 'Komik Trending',
    'Rekomendasi_Komik': 'Rekomendasi Komik',
    'Komik_Hot_Manga': 'Hot Manga',
    'Komik_Hot_Manhwa': 'Hot Manhwa',
    'Komik_Hot_Manhua': 'Hot Manhua',
    # 'Terbaru': handled manually from 2 sources (home + /komik-terbaru/)
}


def get_soup(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except Exception:
        return None

def parse_article(article):
    try:
        title_tag = article.find('h3').find('a')
        title = title_tag.text.strip() if title_tag else ''
        link = BASE_URL + title_tag['href'] if title_tag else ''

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
    except:
        return None

def parse_section(soup, section_id, article_class='ls2'):
    section = soup.find('section', {'id': section_id})
    if not section:
        return []

    return [
        komik for article in section.find_all('article', class_=article_class)
        if (komik := parse_article(article)) is not None
    ]

def get_komik_terbaru_combined():
    # Ambil 6 dari homepage
    homepage_soup = get_soup(BASE_URL)
    items_home = []
    if homepage_soup:
        items_home = parse_section(homepage_soup, 'Terbaru', 'ls8')

    # Ambil 20+ dari halaman /komik-terbaru/
    terbaru_soup = get_soup(BASE_URL + '/komik-terbaru/')
    items_page = []
    if terbaru_soup:
        articles = terbaru_soup.find_all('article', class_='ls4')
        for article in articles:
            komik = parse_article(article)
            if komik:
                items_page.append(komik)

    # Gabungkan keduanya (hindari duplikat berdasarkan title)
    seen = set()
    combined = []
    for item in items_home + items_page:
        if item['title'] not in seen:
            combined.append(item)
            seen.add(item['title'])
    return combined

def get_all_sections():
    soup = get_soup(BASE_URL)
    if not soup:
        return {'error': 'Gagal mengambil halaman'}

    # Genre
    genres = []
    genre_select = soup.find('select', {'name': 'genre'})
    if genre_select:
        for option in genre_select.find_all('option'):
            value = option.get('value', '').strip()
            name = option.text.strip()
            if value and name.lower() != 'genre 1':
                genres.append({'slug': value, 'name': name})

    # Sections
    section_data = []

    # Sections dari peta biasa
    for section_id, label in SECTION_MAP.items():
        items = parse_section(soup, section_id)
        if items:
            section_data.append({'title': label, 'items': items})

    # Tambahkan Komik Terbaru dari 2 sumber
    terbaru_items = get_komik_terbaru_combined()
    if terbaru_items:
        section_data.append({'title': 'Komik Terbaru', 'items': terbaru_items})

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
