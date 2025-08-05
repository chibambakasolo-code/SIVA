import sqlite3
from datetime import datetime, timedelta

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self._initialize_db()
    
    def _initialize_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create inventory table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT,
                    price REAL NOT NULL,
                    quantity INTEGER NOT NULL,
                    threshold INTEGER NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create sales table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (item_id) REFERENCES inventory (id)
                )
            ''')
            
            conn.commit()
    
    def initialize_sample_data(self, sample_data):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Clear existing data
            cursor.execute('DELETE FROM inventory')
            cursor.execute('DELETE FROM sales')
            
            # Insert sample data
            for item in sample_data:
                cursor.execute('''
                    INSERT INTO inventory (name, category, price, quantity, threshold)
                    VALUES (?, ?, ?, ?, ?)
                ''', (item['name'], item['category'], item['price'], item['quantity'], item['threshold']))
            
            # Generate some sample sales data
            items = cursor.execute('SELECT id FROM inventory').fetchall()
            for i in range(30):
                for item_id in items:
                    if i % (item_id[0] + 1) == 0:  # Simple logic to vary sales
                        cursor.execute('''
                            INSERT INTO sales (item_id, quantity, price, sale_date)
                            VALUES (?, ?, ?, ?)
                        ''', (item_id[0], 1, 
                             cursor.execute('SELECT price FROM inventory WHERE id = ?', item_id).fetchone()[0],
                             (datetime.now() - timedelta(days=30-i)).strftime('%Y-%m-%d %H:%M:%S')))
            
            conn.commit()
    
    def get_inventory(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM inventory ORDER BY name')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_item(self, item_id):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM inventory WHERE id = ?', (item_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_item(self, item_id, updates):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
            values = list(updates.values())
            values.append(item_id)
            
            cursor.execute(f'''
                UPDATE inventory 
                SET {set_clause}, last_updated = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', values)
            conn.commit()
            return cursor.rowcount > 0
    
    def record_sale(self, item_id, quantity, price):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sales (item_id, quantity, price)
                VALUES (?, ?, ?)
            ''', (item_id, quantity, price))
            conn.commit()
            return cursor.lastrowid
    
    def get_recent_sales(self, limit=5):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT s.*, i.name as item_name 
                FROM sales s
                JOIN inventory i ON s.item_id = i.id
                ORDER BY s.sale_date DESC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_daily_sales_summary(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    DATE(sale_date) as day,
                    SUM(price * quantity) as total_sales,
                    COUNT(*) as items_sold
                FROM sales
                WHERE DATE(sale_date) = DATE('now')
                GROUP BY DATE(sale_date)
            ''')
            row = cursor.fetchone()
            return {
                'day': datetime.now().strftime('%Y-%m-%d'),
                'total_sales': row[1] if row else 0,
                'items_sold': row[2] if row else 0
            }
    
    def get_weekly_sales_summary(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    DATE(sale_date, 'weekday 0', '-6 days') as week_start,
                    DATE(sale_date, 'weekday 0') as week_end,
                    SUM(price * quantity) as total_sales,
                    COUNT(*) as items_sold
                FROM sales
                GROUP BY week_start
                ORDER BY week_start DESC
                LIMIT 4
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_monthly_sales_summary(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    STRFTIME('%Y-%m', sale_date) as month,
                    SUM(price * quantity) as total_sales,
                    COUNT(*) as items_sold
                FROM sales
                GROUP BY month
                ORDER BY month DESC
                LIMIT 6
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_annual_sales_summary(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    STRFTIME('%Y', sale_date) as year,
                    SUM(price * quantity) as total_sales,
                    COUNT(*) as items_sold
                FROM sales
                GROUP BY year
                ORDER BY year DESC
                LIMIT 3
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_sales_trend(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    DATE(sale_date) as date,
                    SUM(price * quantity) as total_sales
                FROM sales
                WHERE DATE(sale_date) >= DATE('now', '-30 days')
                GROUP BY DATE(sale_date)
                ORDER BY DATE(sale_date)
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_performance_data(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    i.id,
                    i.name,
                    COUNT(s.id) as sales,
                    SUM(s.price * s.quantity) as revenue
                FROM inventory i
                LEFT JOIN sales s ON i.id = s.item_id
                GROUP BY i.id, i.name
                ORDER BY revenue DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_alerts(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM inventory
                WHERE quantity < threshold
                ORDER BY quantity ASC
            ''')
            low_stock = [dict(row) for row in cursor.fetchall()]
            
            # Get poor performers (items with no sales in last 30 days)
            cursor.execute('''
                SELECT i.* FROM inventory i
                LEFT JOIN (
                    SELECT item_id FROM sales 
                    WHERE DATE(sale_date) >= DATE('now', '-30 days')
                    GROUP BY item_id
                ) s ON i.id = s.item_id
                WHERE s.item_id IS NULL
            ''')
            poor_performers = [dict(row) for row in cursor.fetchall()]
            
            return {
                'low_stock': low_stock,
                'poor_performers': poor_performers
            }