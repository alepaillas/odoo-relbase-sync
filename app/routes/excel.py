from flask import Blueprint, jsonify, request
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()

EXCEL_FILE_PATH = os.getenv('EXCEL_FILE_PATH')
CURRENT_STOCK_SHEET = os.getenv('CURRENT_STOCK_SHEET')
CATEGORY_STOCK_SHEET = os.getenv('CATEGORY_STOCK_SHEET')

excel_bp = Blueprint('excel', __name__)

def load_excel_data():
    """Load data from Excel file and return dataframes"""
    try:
        current_stock_df = pd.read_excel(EXCEL_FILE_PATH, sheet_name=CURRENT_STOCK_SHEET)
        category_stock_df = pd.read_excel(EXCEL_FILE_PATH, sheet_name=CATEGORY_STOCK_SHEET)
        return current_stock_df, category_stock_df
    except Exception as e:
        print(f"Error loading Excel file: {e}")
        return None, None

@excel_bp.route('/products', methods=['GET'])
def get_products():
    """Get all products or filter by query parameters"""
    current_stock_df, _ = load_excel_data()
    if current_stock_df is None:
        return jsonify({"error": "Failed to load Excel data"}), 500
    
    # Get filter parameters from request
    filters = {}
    for column in current_stock_df.columns:
        value = request.args.get(column)
        if value:
            filters[column] = value
    
    # Apply filters if any
    if filters:
        filtered_df = current_stock_df
        for column, value in filters.items():
            if column in filtered_df.columns:
                filtered_df = filtered_df[filtered_df[column].astype(str).str.contains(value, case=False)]
        result = filtered_df.to_dict(orient='records')
    else:
        result = current_stock_df.to_dict(orient='records')
    
    return jsonify(result)

@excel_bp.route('/products/code/<codigo>', methods=['GET'])
def get_product_by_code(codigo):
    """Get product by its code"""
    current_stock_df, _ = load_excel_data()
    if current_stock_df is None:
        return jsonify({"error": "Failed to load Excel data"}), 500
    
    # Find product by code
    product = current_stock_df[current_stock_df['Código'] == codigo]
    if len(product) == 0:
        return jsonify({"error": "Product not found"}), 404
    
    return jsonify(product.iloc[0].to_dict())

@excel_bp.route('/products/barcode/<barcode>', methods=['GET'])
def get_product_by_barcode(barcode):
    """Get product by its barcode"""
    current_stock_df, _ = load_excel_data()
    if current_stock_df is None:
        return jsonify({"error": "Failed to load Excel data"}), 500
    
    # Find product by barcode
    product = current_stock_df[current_stock_df['Código barra'] == barcode]
    if len(product) == 0:
        return jsonify({"error": "Product not found"}), 404
    
    return jsonify(product.iloc[0].to_dict())

@excel_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all categories or filter by query parameters"""
    _, category_stock_df = load_excel_data()
    if category_stock_df is None:
        return jsonify({"error": "Failed to load Excel data"}), 500
    
    # Get filter parameters
    filters = {}
    for column in category_stock_df.columns:
        value = request.args.get(column)
        if value:
            filters[column] = value
    
    # Apply filters if any
    if filters:
        filtered_df = category_stock_df
        for column, value in filters.items():
            if column in filtered_df.columns:
                filtered_df = filtered_df[filtered_df[column].astype(str).str.contains(value, case=False)]
        result = filtered_df.to_dict(orient='records')
    else:
        result = category_stock_df.to_dict(orient='records')
    
    return jsonify(result)

@excel_bp.route('/products/category/<category>', methods=['GET'])
def get_products_by_category(category):
    """Get all products in a specific category"""
    current_stock_df, _ = load_excel_data()
    if current_stock_df is None:
        return jsonify({"error": "Failed to load Excel data"}), 500
    
    # Find products by category
    products = current_stock_df[current_stock_df['Categoría'].str.contains(category, case=False)]
    if len(products) == 0:
        return jsonify({"error": "No products found in this category"}), 404
    
    return jsonify(products.to_dict(orient='records'))

@excel_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """Get general statistics about inventory"""
    current_stock_df, category_stock_df = load_excel_data()
    if current_stock_df is None or category_stock_df is None:
        return jsonify({"error": "Failed to load Excel data"}), 500
    
    stats = {
        "total_products": len(current_stock_df),
        "total_categories": len(category_stock_df),
        "total_stock": current_stock_df["Stock disponible"].sum(),
        "total_value": current_stock_df["Total"].sum(),
        "average_cost": current_stock_df["Costo promedio"].mean(),
        "low_stock_products": len(current_stock_df[current_stock_df["Stock disponible"] < 5])
    }
    
    return jsonify(stats)