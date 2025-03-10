from typing import Dict, List, Optional, Union, Any
import xmlrpc.client
import json
from dotenv import load_dotenv
import os

load_dotenv()

# Odoo credentials from environment variables
ODOO_URL = os.getenv('ODOO_URL')
ODOO_DB = os.getenv('ODOO_DB')
ODOO_USERNAME = os.getenv('ODOO_USERNAME')
ODOO_PASSWORD = os.getenv('ODOO_PASSWORD')

class OdooProductAPI:
    """API client for retrieving products from an Odoo database."""

    def __init__(self):
        """
        Initialize the Odoo API client.
        """
        self.url = ODOO_URL
        self.db = ODOO_DB
        self.username = ODOO_USERNAME
        self.password = ODOO_PASSWORD
        
        if not all([self.url, self.db, self.username, self.password]):
            raise ValueError("Missing Odoo credentials in environment variables.")
        
        # XML-RPC endpoints
        self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
        self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
        
        # Authenticate and get user id
        self.uid = self.common.authenticate(self.db, self.username, self.password, {})
        
        if not self.uid:
            raise ValueError("Authentication failed. Check credentials.")


    def search_products(self, 
                         limit: int = 100, 
                         offset: int = 0,
                         domain: Optional[List] = None,
                         fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Search for products in the Odoo database.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            domain: Search domain (Odoo domain format)
            fields: List of fields to fetch (None for all fields)
            
        Returns:
            List of product dictionaries
        """
        if domain is None:
            domain = [('type', '=', 'product')]
            
        if fields is None:
            fields = ['id', 'name', 'default_code', 'list_price', 'standard_price', 'categ_id', 
                     'qty_available', 'description', 'barcode']
            
        products = self.models.execute_kw(
            self.db, self.uid, self.password,
            'product.product', 'search_read',
            [domain],
            {'fields': fields, 'limit': limit, 'offset': offset}
        )
        
        return products
    
    def get_product_by_id(self, product_id: int) -> Dict[str, Any]:
        """
        Get a specific product by ID.
        
        Args:
            product_id: The Odoo product ID
            
        Returns:
            Product information dictionary
        """
        products = self.models.execute_kw(
            self.db, self.uid, self.password,
            'product.product', 'read',
            [[product_id]]
        )
        
        if not products:
            raise ValueError(f"No product found with ID {product_id}")
            
        return products[0]
    
    def get_product_by_code(self, code: str) -> Dict[str, Any]:
        """
        Get a product by its internal reference (default_code).
        
        Args:
            code: The product's internal reference code
            
        Returns:
            Product information dictionary
        """
        products = self.search_products(domain=[('default_code', '=', code)])
        
        if not products:
            raise ValueError(f"No product found with code {code}")
            
        return products[0]
    
    def get_product_stock(self, product_id: int) -> Dict[str, float]:
        """
        Get detailed stock information for a product.
        
        Args:
            product_id: The Odoo product ID
            
        Returns:
            Dictionary with stock information
        """
        stock_info = self.models.execute_kw(
            self.db, self.uid, self.password,
            'product.product', 'read',
            [[product_id]],
            {'fields': ['qty_available', 'virtual_available', 
                       'incoming_qty', 'outgoing_qty']}
        )
        
        if not stock_info:
            raise ValueError(f"No product found with ID {product_id}")
            
        return stock_info[0]
    
    def get_product_categories(self) -> List[Dict[str, Any]]:
        """
        Get all product categories.
        
        Returns:
            List of product category dictionaries
        """
        categories = self.models.execute_kw(
            self.db, self.uid, self.password,
            'product.category', 'search_read',
            [[]],
            {'fields': ['id', 'name', 'parent_id']}
        )
        
        return categories
    
    def export_products_to_json(self, filename: str, limit: int = 1000) -> None:
        """
        Export products to a JSON file.
        
        Args:
            filename: Output JSON filename
            limit: Maximum number of products to export
        """
        products = self.search_products(limit=limit)
        
        with open(filename, 'w') as f:
            json.dump(products, f, indent=4)
            
        print(f"Exported {len(products)} products to {filename}")

    def update_product_stock(self, product_id: int, new_quantity: float, location_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Update a product's stock quantity.
        
        Args:
            product_id: The Odoo product ID
            new_quantity: The new quantity to set
            location_id: Optional specific stock location ID
            
        Returns:
            Dictionary with the result of the inventory adjustment
        """
        # Create an inventory adjustment
        inventory_vals = {
            'name': f'Stock update for product ID {product_id}',
            'product_ids': [(4, product_id)],
        }
        
        # Create inventory adjustment
        inventory_id = self.models.execute_kw(
            self.db, self.uid, self.password,
            'stock.inventory', 'create',
            [inventory_vals]
        )
        
        # Get the inventory line
        self.models.execute_kw(
            self.db, self.uid, self.password,
            'stock.inventory', 'action_start',
            [[inventory_id]]
        )
        
        # Find the inventory line for our product
        domain = [
            ('inventory_id', '=', inventory_id),
            ('product_id', '=', product_id)
        ]
        
        if location_id:
            domain.append(('location_id', '=', location_id))
            
        line_ids = self.models.execute_kw(
            self.db, self.uid, self.password,
            'stock.inventory.line', 'search',
            [domain]
        )
        
        if line_ids:
            # Update existing line
            self.models.execute_kw(
                self.db, self.uid, self.password,
                'stock.inventory.line', 'write',
                [line_ids, {'product_qty': new_quantity}]
            )
        else:
            # Create a new line if not found
            location_domain = []
            if location_id:
                location_domain = [('id', '=', location_id)]
            else:
                location_domain = [('usage', '=', 'internal'), ('company_id', '=', 1)]
                
            location_ids = self.models.execute_kw(
                self.db, self.uid, self.password,
                'stock.location', 'search',
                [location_domain], {'limit': 1}
            )
            
            if not location_ids:
                raise ValueError("No suitable stock location found")
                
            location_id = location_ids[0]
            
            line_vals = {
                'inventory_id': inventory_id,
                'product_id': product_id,
                'location_id': location_id,
                'product_qty': new_quantity
            }
            
            self.models.execute_kw(
                self.db, self.uid, self.password,
                'stock.inventory.line', 'create',
                [line_vals]
            )
        
        # Validate inventory
        self.models.execute_kw(
            self.db, self.uid, self.password,
            'stock.inventory', 'action_validate',
            [[inventory_id]]
        )
        
        # Return updated product info
        return self.get_product_by_id(product_id)

    def update_product_price(self, product_id: int, list_price: Optional[float] = None, 
                            standard_price: Optional[float] = None) -> Dict[str, Any]:
        """
        Update a product's pricing (list price and/or standard price).
        
        Args:
            product_id: The Odoo product ID
            list_price: New sales price (optional)
            standard_price: New cost price (optional)
            
        Returns:
            Updated product information
        """
        if list_price is None and standard_price is None:
            raise ValueError("At least one of list_price or standard_price must be provided")
            
        update_vals = {}
        
        if list_price is not None:
            update_vals['list_price'] = list_price
            
        if standard_price is not None:
            update_vals['standard_price'] = standard_price
        
        # Update the product
        result = self.models.execute_kw(
            self.db, self.uid, self.password,
            'product.product', 'write',
            [[product_id], update_vals]
        )
        
        if not result:
            raise ValueError(f"Failed to update product ID {product_id}")
            
        # Return updated product info
        return self.get_product_by_id(product_id)
