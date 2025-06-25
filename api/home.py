from flask import Blueprint, jsonify, request
import requests
from bs4 import BeautifulSoup
from functools import lru_cache
import time

home_bp = Blueprint('home', __name__)

BASE_URL = 'https://komiku.org'
HEADERS = {
    'User-Agent': 'Mozilla/5.0'
}

def get_soup(url=BASE_URL):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except Exception:
        return None

def parse_section(soup, section_id, article_class='ls2'):
    section = soup.find('section', {'id': section_id})
    if not section:
        return []

    komik_list = []
    for article in section.find_all('article', class_=article_class):
        try:
            title_tag = article.find('h3').find('a')
            title = title_tag.text.strip()
            link = BASE_URL + title_tag['href']
            chapter_tag = article.find('a', class_='ls2l') or article.find('a', class_='ls24')
            chapter = chapter_tag.text.strip() if chapter_tag else ''
            chapter_link = BASE_URL + chapter_tag['href'] if chapter_tag else ''
            genre_tag = article.find('span', class_='ls2t') or article.find('span', class_='ls4s') or article.find('span')
            genre = genre_tag.text.strip() if genre_tag else ''
            img_tag = article.find('img')
            image_url = img_tag.get('data-src') or img_tag.get('src')
            rank_tag = article.find('span', class_='hot')
            rank = rank_tag.text.strip() if rank_tag else ""

            komik_list.append({
                'title': title,
                'link': link,
                'genre': genre,
                'chapter': chapter,
                'chapter_link': chapter_link,
                'image_url': image_url,
                'rank': rank
            })
        except Exception:
            continue

    return komik_list

def get_all_home_data():
    soup = get_soup()
    if not soup:
        return {'error': 'Gagal mengambil halaman'}

    # Genre list
    genre_select = soup.find('select', {'name': 'genre'})
    genres = []
    if genre_select:
        for option in genre_select.find_all('option'):
            value = option.get('value', '').strip()
            name = option.text.strip()
            if value and name.lower() != 'genre 1':
                genres.append({'slug': value, 'name': name})

    return {
        'trending': parse_section(soup, 'Trending_Komik'),
        'rekomendasi': parse_section(soup, 'Rekomendasi_Komik'),
        'hot_manga': parse_section(soup, 'Komik_Hot_Manga'),
        'hot_manhwa': parse_section(soup, 'Komik_Hot_Manhwa'),
        'hot_manhua': parse_section(soup, 'Komik_Hot_Manhua'),
        'terbaru_besar': parse_section(soup, 'Terbaru', 'ls2'),
        'terbaru_mini': parse_section(soup, 'Terbaru', 'ls4'),
        'genres': genres
    }

@lru_cache(maxsize=1)
def get_cached_home():
    return get_all_home_data()

@home_bp.route('/home')
def home_combined():
    data = get_cached_home()
    if 'error' in data:
        return jsonify(data), 500
    return jsonify(data)
