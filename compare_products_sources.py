import requests


def get_odoo_products_batch(limit=100, offset=0):
    url = "http://localhost:5000/api/odoo/products"
    params = {"limit": limit, "offset": offset}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data from Odoo API: {response.status_code}")
        return None


def get_all_odoo_products():
    all_products = []
    limit = 10
    offset = 0

    all_products = get_odoo_products_batch(limit=limit, offset=offset)

    # Uncomment the following block if you want to fetch all products with pagination
    # while True:
    #     products_batch = get_odoo_products_batch(limit=limit, offset=offset)
    #     if not products_batch:
    #         break  # Stop if no more products are returned

    #     all_products.extend(products_batch)
    #     if len(products_batch) < limit:
    #         break  # Stop if the batch is smaller than the limit (no more products)

    #     offset += limit  # Move to the next batch

    return all_products


def get_product_data_from_excel(code):
    url = f"http://localhost:5000/api/excel/products/code/{code}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(
            f"Failed to fetch data from Excel API for product code {code}: {response.status_code}"
        )
        return None


def update_product_price(product_id, list_price, standard_price):
    url = f"http://localhost:5000/api/odoo/products/{product_id}/price"
    data = {"list_price": list_price, "standard_price": standard_price}
    response = requests.put(url, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to update product {product_id}: {response.status_code}")
        return None


def update_product_stock(product_id, quantity, location_id=None):
    url = f"http://localhost:5000/api/odoo/products/{product_id}/stock"
    data = {"quantity": quantity}
    if location_id:
        data["location_id"] = location_id
    response = requests.put(url, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        print(
            f"Failed to update stock for product {product_id}: {response.status_code}"
        )
        return None


def compare_prices_and_stock(odoo_product, excel_data):
    if odoo_product is None or excel_data is None:
        return

    # Compare prices
    precio_neto = excel_data.get("Precio neto")
    if precio_neto is None:
        print(
            f"Precio neto not found in Excel data for product: {odoo_product['name']}"
        )
        return

    standard_price = odoo_product.get("standard_price")
    if standard_price is None:
        print(
            f"standard_price not found in Odoo data for product: {odoo_product['name']}"
        )
        return

    calculated_price = round(precio_neto / 2.14, 2)  # Round to 2 decimal places

    # Print product details
    print(f"\nOdoo code: {odoo_product['default_code']}")
    print(f"Excel code: {excel_data.get('Código')}")
    print(f"Odoo Product: {odoo_product['name']}")
    print(f"Excel Product: {excel_data.get('Producto')}")
    print(f"Odoo Stock: {odoo_product['qty_available']}")
    print(f"Excel Stock: {excel_data.get('Stock disponible', 'N/A')}")
    print(f"Odoo list_price: {odoo_product['list_price']}")
    print(f"Excel list price: {excel_data.get('Precio neto')}")
    print(f"Odoo standard_price: {standard_price}")
    print(f"Calculated price (Precio neto / 2.14): {calculated_price}")

    # Compare prices with a tolerance threshold
    tolerance = 0.01  # Allow a difference of up to 0.01
    if abs(standard_price - calculated_price) < tolerance:
        print("Prices are equal.")
    else:
        print("Prices are not equal.")
        user_input = (
            input("Do you want to update the cost and price? (y/n): ").strip().lower()
        )
        if user_input == "y":
            # Update the product's prices
            update_response = update_product_price(
                product_id=odoo_product["id"],
                list_price=precio_neto,
                standard_price=calculated_price,
            )
            if update_response:
                print(
                    f"Successfully updated product {odoo_product['name']}: {update_response}"
                )
        else:
            print("Skipping price update for this product.")

    # Compare stock quantities
    odoo_stock = odoo_product.get("qty_available")
    excel_stock = excel_data.get("Stock disponible")
    if odoo_stock is not None and excel_stock is not None:
        if (
            abs(odoo_stock - excel_stock) > 1e-6
        ):  # Allow minor floating-point differences
            print("Stock quantities are not equal.")
            user_input = (
                input("Do you want to update the stock? (y/n): ").strip().lower()
            )
            if user_input == "y":
                # Update the product's stock
                update_response = update_product_stock(
                    product_id=odoo_product["id"],
                    quantity=excel_stock,
                )
                if update_response:
                    print(
                        f"Successfully updated stock for product {odoo_product['name']}: {update_response}"
                    )
            else:
                print("Skipping stock update for this product.")
        else:
            print("Stock quantities are equal.")
    else:
        print("Stock data missing in Odoo or Excel.")


def main():
    # Fetch all products from Odoo (with pagination)
    odoo_products = get_all_odoo_products()
    if not odoo_products:
        print("No products fetched from Odoo API. Exiting.")
        return

    print(f"Total products fetched: {len(odoo_products)}")

    # Loop through each product and compare prices and stock
    for product in odoo_products:
        product_code = product.get("default_code")
        if not product_code:
            print(f"Skipping product with missing default_code: {product['name']}")
            continue

        # Fetch Excel data for the product
        excel_data = get_product_data_from_excel(product_code)
        if excel_data:
            compare_prices_and_stock(product, excel_data)


if __name__ == "__main__":
    main()
