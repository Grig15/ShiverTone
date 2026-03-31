# ShiverTone - Flask Application
# v0.3 - Frontend

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, render_template, request, jsonify
from database.models import get_connection

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))


def get_stats():
    """Get database statistics for homepage."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM sold_listings')
    total = cursor.fetchone()[0]

    cursor.execute('SELECT MIN(sale_price), MAX(sale_price), AVG(sale_price) FROM sold_listings')
    row = cursor.fetchone()

    conn.close()
    return {
        'total': total,
        'min_price': round(row[0], 2) if row[0] else 0,
        'max_price': round(row[1], 2) if row[1] else 0,
        'avg_price': round(row[2], 2) if row[2] else 0,
    }


@app.route('/')
def index():
    stats = get_stats()
    return render_template('index.html', stats=stats)


@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT title, sale_price, condition, platform, listing_url, thumbnail_url, sale_date
        FROM sold_listings
        WHERE title LIKE ?
        ORDER BY sale_date DESC LIMIT 50
    ''', (f'%{query}%',))

    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        results.append({
            'title': row[0],
            'price': row[1],
            'condition': row[2],
            'platform': row[3],
            'url': row[4],
            'thumbnail': row[5],
            'date': row[6],
        })

    return jsonify(results)


@app.route('/stats')
def stats():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({})

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT sale_price, sale_date
        FROM sold_listings
        WHERE title LIKE ?
        ORDER BY sale_date ASC
    ''', (f'%{query}%',))

    rows = cursor.fetchall()
    conn.close()

    prices = [row[0] for row in rows]
    dates = [row[1] for row in rows]

    return jsonify({
        'prices': prices,
        'dates': dates,
        'avg': round(sum(prices) / len(prices), 2) if prices else 0,
        'min': min(prices) if prices else 0,
        'max': max(prices) if prices else 0,
        'count': len(prices)
    })


if __name__ == '__main__':
    app.run(debug=True, port=5001)