from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime, timedelta
import csv
import io
from database import Database
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

app = Flask(__name__)
db = Database('instance/siva.db')

# Sample data for initial setup
SAMPLE_DATA = [
    {"name": "Milk", "category": "Dairy", "price": 15, "quantity": 20, "threshold": 5},
    {"name": "Bread", "category": "Bakery", "price": 10, "quantity": 15, "threshold": 3},
    {"name": "Eggs", "category": "Dairy", "price": 30, "quantity": 12, "threshold": 4},
    {"name": "Cookies", "category": "Snacks", "price": 25, "quantity": 8, "threshold": 2},
    {"name": "Biscuits", "category": "Snacks", "price": 20, "quantity": 5, "threshold": 2},
    {"name": "Rice", "category": "Grains", "price": 50, "quantity": 10, "threshold": 3},
    {"name": "Sugar", "category": "Groceries", "price": 40, "quantity": 7, "threshold": 2},
]

@app.route('/')
def dashboard():
    inventory = db.get_inventory()
    sales_data = db.get_recent_sales(limit=5)
    alerts = db.get_alerts()
    
    # Generate summary data
    summary = {
        'total_items': len(inventory),
        'low_stock': len([item for item in inventory if item['quantity'] < item['threshold']]),
        'daily_sales': db.get_daily_sales_summary(),
        'weekly_sales': db.get_weekly_sales_summary()
    }
    
    return render_template('dashboard.html', 
                         inventory=inventory, 
                         sales=sales_data, 
                         alerts=alerts,
                         summary=summary)

@app.route('/search')
def search():
    query = request.args.get('q', '').lower()
    inventory = db.get_inventory()
    
    # Basic search
    results = [item for item in inventory if query in item['name'].lower()]
    
    # Related items (by category)
    if results:
        category = results[0]['category']
        related = [item for item in inventory if item['category'] == category and item not in results][:3]
        results.extend(related)
    
    return jsonify(results[:10])

@app.route('/add_sale', methods=['POST'])
def add_sale():
    data = request.json
    item_id = data.get('item_id')
    quantity = data.get('quantity', 1)
    price = data.get('price')
    
    # Get item details
    item = db.get_item(item_id)
    if not item:
        return jsonify({'success': False, 'error': 'Item not found'})
    
    # Calculate total price if not provided
    if not price:
        price = item['price'] * quantity
    
    # Record sale
    sale_id = db.record_sale(item_id, quantity, price)
    
    # Update inventory
    new_quantity = item['quantity'] - quantity
    db.update_item(item_id, {'quantity': new_quantity})
    
    return jsonify({'success': True, 'sale_id': sale_id})

@app.route('/update_inventory', methods=['POST'])
def update_inventory():
    data = request.json
    item_id = data.get('item_id')
    updates = data.get('updates', {})
    
    if db.update_item(item_id, updates):
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/get_reports')
def get_reports():
    period = request.args.get('period', 'weekly')
    report_type = request.args.get('type', 'sales')
    
    if period == 'weekly':
        data = db.get_weekly_sales_summary()
    elif period == 'monthly':
        data = db.get_monthly_sales_summary()
    else:
        data = db.get_annual_sales_summary()
    
    return render_template('reports.html', data=data, period=period, report_type=report_type)

@app.route('/export_report')
def export_report():
    period = request.args.get('period', 'weekly')
    format = request.args.get('format', 'csv')
    
    if period == 'weekly':
        data = db.get_weekly_sales_summary()
    elif period == 'monthly':
        data = db.get_monthly_sales_summary()
    else:
        data = db.get_annual_sales_summary()
    
    if format == 'csv':
        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerow(['Period', 'Total Sales', 'Items Sold'])
        for row in data:
            cw.writerow([row['period'], row['total_sales'], row['items_sold']])
        
        output = io.BytesIO()
        output.write(si.getvalue().encode('utf-8'))
        output.seek(0)
        
        return send_file(output, mimetype='text/csv', as_attachment=True, download_name=f'{period}_report.csv')
    else:
        # For PDF would use something like ReportLab or WeasyPrint
        return jsonify({'success': False, 'error': 'PDF export not implemented yet'})

@app.route('/get_charts')
def get_charts():
    chart_type = request.args.get('type', 'sales_trend')
    
    if chart_type == 'sales_trend':
        data = db.get_sales_trend()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[d['date'] for d in data], 
                               y=[d['total_sales'] for d in data],
                               mode='lines+markers',
                               name='Daily Sales'))
        fig.update_layout(title='Sales Trend (Last 30 Days)',
                        xaxis_title='Date',
                        yaxis_title='Total Sales')
        
    elif chart_type == 'inventory':
        inventory = db.get_inventory()
        fig = go.Figure()
        fig.add_trace(go.Bar(x=[d['name'] for d in inventory],
                           y=[d['quantity'] for d in inventory],
                           name='Current Stock'))
        fig.update_layout(title='Current Inventory Levels',
                        xaxis_title='Product',
                        yaxis_title='Quantity')
        
    elif chart_type == 'performance':
        items = db.get_performance_data()
        fig = make_subplots(rows=1, cols=2)
        
        top_items = sorted(items, key=lambda x: x['sales'], reverse=True)[:5]
        fig.add_trace(go.Bar(x=[d['name'] for d in top_items],
                         y=[d['sales'] for d in top_items],
                         name='Top Sellers'), row=1, col=1)
        
        bottom_items = sorted(items, key=lambda x: x['sales'])[:5]
        fig.add_trace(go.Bar(x=[d['name'] for d in bottom_items],
                           y=[d['sales'] for d in bottom_items],
                           name='Poor Performers'), row=1, col=2)
        
        fig.update_layout(title='Product Performance',
                        showlegend=False)
    
    return jsonify(json.loads(fig.to_json()))

@app.route('/initialize_sample_data')
def initialize_sample_data():
    db.initialize_sample_data(SAMPLE_DATA)
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)