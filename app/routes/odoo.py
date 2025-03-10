from flask import Blueprint, jsonify, request
from app.services.odoo_service import OdooProductAPI

odoo_bp = Blueprint('odoo', __name__)

# Initialize Odoo API client
odoo_api = OdooProductAPI()

@odoo_bp.route('/products', methods=['GET'])
def get_products():
    """Get all products or filter by query parameters"""
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    
    products = odoo_api.search_products(limit=limit, offset=offset)
    return jsonify(products)

@odoo_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product_by_id(product_id: int):
    """Get product by its ID"""
    try:
        product = odoo_api.get_product_by_id(product_id)
        return jsonify(product)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@odoo_bp.route('/products/code/<code>', methods=['GET'])
def get_product_by_code(code: str):
    """Get product by its internal reference code"""
    try:
        product = odoo_api.get_product_by_code(code)
        return jsonify(product)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@odoo_bp.route('/products/<int:product_id>/stock', methods=['GET'])
def get_product_stock(product_id: int):
    """Get stock information for a product"""
    try:
        stock_info = odoo_api.get_product_stock(product_id)
        return jsonify(stock_info)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    
@odoo_bp.route('/products/categories', methods=['GET'])
def get_categories():
    """Get all product categories"""
    categories = odoo_api.get_product_categories()
    return jsonify(categories)

@odoo_bp.route('/products/export', methods=['GET'])
def export_products():
    """Export products to a JSON file"""
    filename = request.args.get('filename', 'odoo_products.json')
    limit = int(request.args.get('limit', 1000))
    
    odoo_api.export_products_to_json(filename, limit)
    return jsonify({"message": f"Products exported to {filename}"})

odoo_bp.route('/products/<int:product_id>/stock', methods=['PUT'])
def update_stock(product_id):
    """Update a product's stock quantity"""
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400
        
    data = request.get_json()
    
    if 'quantity' not in data:
        return jsonify({'error': 'quantity field is required'}), 400
        
    try:
        quantity = float(data['quantity'])
        location_id = data.get('location_id')
        
        result = odoo_api.update_product_stock(
            product_id=product_id,
            new_quantity=quantity,
            location_id=location_id
        )
        
        return jsonify({
            'success': True,
            'message': f"Stock updated for product {result['name']}",
            'product': result
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f"An error occurred: {str(e)}"}), 500

@odoo_bp.route('/products/<int:product_id>/price', methods=['PUT'])
def update_price(product_id):
    """Update a product's pricing (list_price and/or standard_price)"""
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400
        
    data = request.get_json()
    
    if 'list_price' not in data and 'standard_price' not in data:
        return jsonify({'error': 'At least one of list_price or standard_price must be provided'}), 400
        
    try:
        list_price = data.get('list_price')
        standard_price = data.get('standard_price')
        
        # Convert to float if not None
        if list_price is not None:
            list_price = float(list_price)
            
        if standard_price is not None:
            standard_price = float(standard_price)
        
        result = odoo_api.update_product_price(
            product_id=product_id,
            list_price=list_price,
            standard_price=standard_price
        )
        
        return jsonify({
            'success': True,
            'message': f"Price updated for product {result['name']}",
            'product': result
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f"An error occurred: {str(e)}"}), 500