from flask import Blueprint, jsonify
import requests
from bs4 import BeautifulSoup

home_bp = Blueprint('home', __name__)

@home_bp.route('/home', methods=['GET'])
def home():
    url = 'https://komiku.org'
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Ambil deskripsi situs
    def extract_trending():
        section = soup.find('section', id='Trending_Komik')
        desc = section.find('p').get_text(strip=True) if section else ''
        return {'description': desc}

    # Ambil daftar komik dari section ls2
    def extract_ls2(section_id):
        section = soup.find('section', id=section_id)
        result = []
        if section:
            for article in section.find_all('article', class_='ls2'):
                title_tag = article.find('h3')
                title = title_tag.get_text(strip=True) if title_tag else ''
                link = title_tag.a['href'] if title_tag and title_tag.a else ''
                genre = article.find('span', class_='ls2t')
                chapter = article.find('a', class_='ls2l')
                image = article.find('img')
                rank = article.find('span', class_='svg hot')
                result.append({
                    'title': title,
                    'link': link,
                    'genre': genre.get_text(strip=True) if genre else '',
                    'latest_chapter': chapter.get_text(strip=True) if chapter else '',
                    'chapter_link': chapter['href'] if chapter else '',
                    'thumbnail': image['data-src'] if image and image.has_attr('data-src') else '',
                    'rank': rank.get_text(strip=True) if rank else None
                })
        return result

    # Ambil daftar komik terbaru
    def extract_terbaru():
        section = soup.find('section', id='Terbaru')
        result = []
        if section:
            for article in section.find_all('article', class_='ls8'):
                title_tag = article.find('h3')
                title = title_tag.get_text(strip=True) if title_tag else ''
                link = title_tag.a['href'] if title_tag and title_tag.a else ''
                up_label = article.find('div', class_='ls84')
                image = article.find('img')
                result.append({
                    'title': title,
                    'link': link,
                    'up_info': up_label.get_text(strip=True) if up_label else '',
                    'thumbnail': image['src'] if image else ''
                })
        return result

    # Ambil info filter
    def extract_filter_info():
        section = soup.find('section', id='Filter')
        info = section.find('p').get_text(strip=True) if section else ''

        form = section.find('form') if section else None
        filters = {}

        if form:
            selects = form.find_all('select')
            for select in selects:
                name = select.get('name')
                options = [{
                    'value': opt.get('value'),
                    'text': opt.get_text(strip=True)
                } for opt in select.find_all('option')]
                filters[name] = options

        return {
            'info': info,
            'filters': filters
        }

    # Gabungkan semua data ke JSON
    data = {
        'deskripsi_situs': extract_trending(),
        'rekomendasi_komik': extract_ls2('Rekomendasi_Komik'),
        'rilisan_terbaru': extract_terbaru(),
        'filter_info': extract_filter_info(),
        'manga_populer': extract_ls2('Komik_Hot_Manga'),
        'manhwa_populer': extract_ls2('Komik_Hot_Manhwa'),
        'manhua_populer': extract_ls2('Komik_Hot_Manhua')
    }

    return jsonify(data)
