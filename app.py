import streamlit as st
import pandas as pd
import datetime
import uuid
import os
import base64
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
import base64
import warnings
import json
from datetime import date

# Suppress the ScriptRunContext warnings
warnings.filterwarnings('ignore', message='.*missing ScriptRunContext.*')

# Set page configuration
st.set_page_config(
    page_title="Hệ Thống Quản Lý Tiệm Bánh",
    page_icon="🍰",
    layout="wide"
)

def save_dataframe(df, filename):
    """Save a dataframe to a CSV file"""
    try:
        # Use the specific directory path with absolute path
        data_dir = r"C:\\Users\\Computer\\PycharmProjects\\bakery_sys\\bakery_data"
        
        # Create data directory if it doesn't exist
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            print(f"Created directory: {data_dir}")
        
        # Normalize the filepath and make it absolute
        filepath = os.path.abspath(os.path.join(data_dir, filename))
        
        # Save to CSV in the specified directory
        df.to_csv(filepath, index=False)
        print(f"Saved {len(df)} rows to {filepath}")
        return True
    except Exception as e:
        print(f"Error saving {filename}: {e}")
        st.error(f"Failed to save {filename}: {e}")
        return False

def load_dataframe(filename, default_df):
    """Load a dataframe from a CSV file or return the default if file doesn't exist"""
    try:
        # Use the specific directory path with absolute path
        data_dir = r"C:\\Users\\Computer\\PycharmProjects\\bakery_sys\\bakery_data"
        
        # Normalize the filepath and make it absolute
        filepath = os.path.abspath(os.path.join(data_dir, filename))
        
        if os.path.exists(filepath):
            # Try to read the CSV file
            df = pd.read_csv(filepath)
            print(f"Loaded {len(df)} rows from {filepath}")
            
            # Verify the dataframe has content
            if len(df) > 0:
                return df
            else:
                print(f"File {filename} exists but is empty, using default")
        else:
            print(f"File not found: {filepath}, using default")
        
        # Make a copy of the default dataframe to avoid modifying the original
        return default_df.copy()
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        st.error(f"Failed to load {filename}: {e}")
        return default_df.copy()

# Add this code at the beginning of your app to initialize the data directory
def ensure_data_directory():
    data_dir = r"C:\\Users\\Computer\\PycharmProjects\\bakery_sys\\bakery_data"
    if not os.path.exists(data_dir):
        try:
            os.makedirs(data_dir)
            print(f"Created data directory: {data_dir}")
        except Exception as e:
            print(f"Failed to create data directory: {e}")
            st.error(f"Failed to create data directory: {e}")

# Call this function after importing libraries
ensure_data_directory()

# Add this debug code at the start of your app, after imports
def check_data_files():
    """Check if data files exist and print their details"""
    data_dir = r"C:\\Users\\Computer\\PycharmProjects\\bakery_sys\\bakery_data"
    if not os.path.exists(data_dir):
        st.warning(f"Data directory does not exist: {data_dir}")
        return
    
    st.write(f"Data directory exists: {data_dir}")
    
    files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    if not files:
        st.warning("No CSV files found in data directory")
        return
    
    st.write(f"Found {len(files)} CSV files:")
    for file in files:
        filepath = os.path.join(data_dir, file)
        filesize = os.path.getsize(filepath)
        st.write(f"- {file}: {filesize} bytes")
        try:
            df = pd.read_csv(filepath)
            st.write(f"  Contains {len(df)} rows")
        except Exception as e:
            st.write(f"  Error reading file: {str(e)}")

# Add a toggle to show debug information
show_debug = st.sidebar.checkbox("Show Debug Info", value=False)
if show_debug:
    st.sidebar.write("### Debug Information")
    check_data_files()
    
# Add an explicit function to initialize data if needed
def initialize_data_if_needed():
    """Initialize data files if they don't exist yet"""
    data_dir = r"C:\\Users\\Computer\\PycharmProjects\\bakery_sys\\bakery_data"
    
    # List of expected files
    expected_files = [
        "products.csv", "materials.csv", "recipes.csv", 
        "orders.csv", "order_items.csv", "invoices.csv", 
        "income.csv", "material_costs.csv", "invoice_status.csv"
    ]
    
    # Check if any files are missing
    missing_files = []
    for filename in expected_files:
        filepath = os.path.join(data_dir, filename)
        if not os.path.exists(filepath):
            missing_files.append(filename)
    
    # If any files are missing, save the default dataframes
    if missing_files:
        print(f"Initializing missing data files: {', '.join(missing_files)}")
        
        # Save default dataframes for missing files
        if "products.csv" in missing_files and 'products' in st.session_state:
            save_dataframe(st.session_state.products, "products.csv")
        
        if "materials.csv" in missing_files and 'materials' in st.session_state:
            save_dataframe(st.session_state.materials, "materials.csv")
        
        if "recipes.csv" in missing_files and 'recipes' in st.session_state:
            save_dataframe(st.session_state.recipes, "recipes.csv")
        
        if "orders.csv" in missing_files and 'orders' in st.session_state:
            save_dataframe(st.session_state.orders, "orders.csv")
        
        if "order_items.csv" in missing_files and 'order_items' in st.session_state:
            save_dataframe(st.session_state.order_items, "order_items.csv")
        
        if "invoices.csv" in missing_files and 'invoices' in st.session_state:
            save_dataframe(st.session_state.invoices, "invoices.csv")
        
        if "income.csv" in missing_files and 'income' in st.session_state:
            save_dataframe(st.session_state.income, "income.csv")
        
        if "material_costs.csv" in missing_files and 'material_costs' in st.session_state:
            save_dataframe(st.session_state.material_costs, "material_costs.csv")
        
        if "invoice_status.csv" in missing_files and 'invoice_status' in st.session_state:
            save_dataframe(st.session_state.invoice_status, "invoice_status.csv")

# Call this function after loading data
initialize_data_if_needed()

# Default dataframes (will be used if files don't exist)
default_products = pd.DataFrame({
    'product_id': ['P001', 'P002', 'P003', 'P004'],
    'name': ['Bánh Socola', 'Bánh Sừng Bò', 'Bánh Mì', 'Bánh Cupcake'],
    'price': [575000, 80500, 138000, 57500],
    'category': ['Bánh Ngọt', 'Bánh Ngọt', 'Bánh Mì', 'Bánh Ngọt']
})

default_materials = pd.DataFrame({
    'material_id': ['M001', 'M002', 'M003', 'M004', 'M005', 'M006'],
    'name': ['Bột Mì', 'Đường', 'Trứng', 'Bơ', 'Socola', 'Tinh Chất Vani'],
    'unit': ['kg', 'kg', 'quả', 'kg', 'kg', 'ml'],
    'quantity': [50.0, 30.0, 200, 25.0, 15.0, 1000],
    'price_per_unit': [46000, 69000, 5750, 230000, 345000, 2300],
    'used_quantity': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]  
})

default_recipes = pd.DataFrame({
    'product_id': ['P001', 'P001', 'P001', 'P001', 'P001', 
                  'P002', 'P002', 'P002', 'P002',
                  'P003', 'P003', 'P003',
                  'P004', 'P004', 'P004', 'P004'],
    'material_id': ['M001', 'M002', 'M003', 'M004', 'M005',
                   'M001', 'M002', 'M004', 'M003',
                   'M001', 'M003', 'M004',
                   'M001', 'M002', 'M003', 'M004'],
    'quantity': [0.5, 0.4, 4, 0.3, 0.2,
                0.1, 0.05, 0.1, 1,
                1.0, 1, 0.1,
                0.1, 0.15, 1, 0.05]
})

default_orders = pd.DataFrame(columns=[
    'order_id', 'date', 'customer_name', 'customer_phone', 'total_amount', 'status'
])

default_order_items = pd.DataFrame(columns=[
    'order_id', 'product_id', 'quantity', 'price', 'subtotal'
])

default_invoices = pd.DataFrame(columns=[
    'invoice_id', 'order_id', 'date', 'customer_name', 'total_amount', 'payment_method'
])

default_income = pd.DataFrame(columns=[
    'date', 'total_sales', 'cost_of_goods', 'profit'
])

default_material_costs = pd.DataFrame(columns=[
    'date', 'material_id', 'quantity', 'total_cost', 'supplier'
])

default_invoice_status = pd.DataFrame(columns=[
    'invoice_id', 'is_completed', 'completion_date', 'notes', 'payment_status'
])

# Load data from files or use defaults
if 'products' not in st.session_state:
    st.session_state.products = load_dataframe("products.csv", default_products)

if 'materials' not in st.session_state:
    st.session_state.materials = load_dataframe("materials.csv", default_materials)

if 'recipes' not in st.session_state:
    st.session_state.recipes = load_dataframe("recipes.csv", default_recipes)

if 'orders' not in st.session_state:
    st.session_state.orders = load_dataframe("orders.csv", default_orders)

if 'order_items' not in st.session_state:
    st.session_state.order_items = load_dataframe("order_items.csv", default_order_items)

if 'invoices' not in st.session_state:
    st.session_state.invoices = load_dataframe("invoices.csv", default_invoices)

if 'income' not in st.session_state:
    st.session_state.income = load_dataframe("income.csv", default_income)

if 'material_costs' not in st.session_state:
    st.session_state.material_costs = load_dataframe("material_costs.csv", default_material_costs)

if 'invoice_status' not in st.session_state:
    st.session_state.invoice_status = load_dataframe("invoice_status.csv", default_invoice_status)
    
# Function to ensure we have Unicode support for Vietnamese
def setup_vietnamese_font():
    try:
        # Use relative paths for Streamlit Cloud
        roboto_base_dir = "fonts/static"
        
        try:
            regular_path = f"{roboto_base_dir}/Roboto-Regular.ttf"
            bold_path = f"{roboto_base_dir}/Roboto-Bold.ttf"
            
            # Register the regular font
            pdfmetrics.registerFont(TTFont('Roboto', regular_path))
            
            # Register the bold font
            pdfmetrics.registerFont(TTFont('Roboto-Bold', bold_path))
            
            return 'Roboto'
        except Exception as e:
            print(f"Font error: {e}")
            # Fall back to Helvetica if there's any issue
            return 'Helvetica'
            
    except Exception as e:
        print(f"Font setup error: {e}")
        # Fall back to Helvetica
        return 'Helvetica'

def save_all_data():
    """Save all dataframes to CSV files"""
    save_dataframe(st.session_state.products, "products.csv")
    save_dataframe(st.session_state.materials, "materials.csv")
    save_dataframe(st.session_state.recipes, "recipes.csv")
    save_dataframe(st.session_state.orders, "orders.csv")
    save_dataframe(st.session_state.order_items, "order_items.csv")
    save_dataframe(st.session_state.invoices, "invoices.csv")
    save_dataframe(st.session_state.income, "income.csv")
    
    if 'material_costs' in st.session_state:
        save_dataframe(st.session_state.material_costs, "material_costs.csv")
    
    if 'invoice_status' in st.session_state:
        save_dataframe(st.session_state.invoice_status, "invoice_status.csv")
    
    if 'product_costs' in st.session_state:
        save_dataframe(st.session_state.product_costs, "product_costs.csv") 

# Function to update material quantities after an order
def update_materials_after_order(order_id):
    # Get order items
    order_items_df = st.session_state.order_items[st.session_state.order_items['order_id'] == order_id]
    
    # For each order item, reduce materials according to recipe
    for _, item in order_items_df.iterrows():
        product_id = item['product_id']
        order_quantity = item['quantity']
        
        # Get recipe for this product
        product_recipe = st.session_state.recipes[st.session_state.recipes['product_id'] == product_id]
        
        # For each material in the recipe, reduce quantity and track usage
        for _, recipe_item in product_recipe.iterrows():
            material_id = recipe_item['material_id']
            material_quantity_needed = recipe_item['quantity'] * order_quantity
            
            # Update material quantity
            material_idx = st.session_state.materials[st.session_state.materials['material_id'] == material_id].index[0]
            st.session_state.materials.at[material_idx, 'quantity'] -= material_quantity_needed
            
            # Update used quantity
            st.session_state.materials.at[material_idx, 'used_quantity'] += material_quantity_needed

# Function to calculate cost of goods for an order
def calculate_cost_of_goods(order_id):
    total_cost = 0
    order_items_df = st.session_state.order_items[st.session_state.order_items['order_id'] == order_id]
    
    for _, item in order_items_df.iterrows():
        product_id = item['product_id']
        order_quantity = item['quantity']
        
        # Get recipe for this product
        product_recipe = st.session_state.recipes[st.session_state.recipes['product_id'] == product_id]
        
        # Calculate cost for each material in the recipe
        product_cost = 0
        for _, recipe_item in product_recipe.iterrows():
            material_id = recipe_item['material_id']
            material_quantity = recipe_item['quantity'] * order_quantity
            
            # Get material price
            material_price = st.session_state.materials[
                st.session_state.materials['material_id'] == material_id
            ]['price_per_unit'].values[0]
            
            product_cost += material_quantity * material_price
        
        total_cost += product_cost
    
    return total_cost

# Function to update income records after completing an order
def update_income(order_id):
    order_data = st.session_state.orders[st.session_state.orders['order_id'] == order_id].iloc[0]
    order_date = order_data['date']
    
    # Get product amount and shipping fee
    product_amount = order_data['total_amount']
    shipping_fee = order_data.get('shipping_fee', 0)
    
    # Calculate total with shipping
    total_amount = product_amount + shipping_fee
    
    # Calculate cost of goods (materials only, not shipping)
    cost_of_goods = calculate_cost_of_goods(order_id)
    
    # Calculate profit (including shipping as revenue)
    profit = total_amount - cost_of_goods
    
    # Check if date already exists in income DataFrame
    if order_date in st.session_state.income['date'].values:
        idx = st.session_state.income[st.session_state.income['date'] == order_date].index[0]
        st.session_state.income.at[idx, 'total_sales'] += total_amount
        st.session_state.income.at[idx, 'cost_of_goods'] += cost_of_goods
        st.session_state.income.at[idx, 'profit'] += profit
        # Track shipping revenue separately if needed
        if 'shipping_revenue' in st.session_state.income.columns:
            st.session_state.income.at[idx, 'shipping_revenue'] += shipping_fee
        else:
            st.session_state.income['shipping_revenue'] = 0
            st.session_state.income.at[idx, 'shipping_revenue'] = shipping_fee
    else:
        # Create new row for this date
        if 'shipping_revenue' not in st.session_state.income.columns:
            # Add shipping revenue column if it doesn't exist
            st.session_state.income['shipping_revenue'] = 0
            
        new_row = pd.DataFrame({
            'date': [order_date],
            'total_sales': [total_amount],
            'cost_of_goods': [cost_of_goods],
            'profit': [profit],
            'shipping_revenue': [shipping_fee]
        })
        
        st.session_state.income = pd.concat([st.session_state.income, new_row], ignore_index=True)

def generate_invoice_content(invoice_id, order_id, as_pdf=False):
    """Generate invoice content either as text or PDF to match the simplified receipt format
    with improved formatting and proper spacing"""
    order_data = st.session_state.orders[st.session_state.orders['order_id'] == order_id].iloc[0]
    order_items = st.session_state.order_items[st.session_state.order_items['order_id'] == order_id]
    
    # Get product names
    order_items = order_items.merge(
        st.session_state.products[['product_id', 'name']],
        on='product_id',
        how='left'
    )
    
    # Get shipping fee and customer address from order data (will be 0 if not specified)
    shipping_fee = order_data.get('shipping_fee', 0)
    customer_address = order_data.get('customer_address', '')
    customer_name = order_data['customer_name']
    customer_phone = order_data['customer_phone']
    
    # Calculate total amount
    total_amount = order_data['total_amount'] + shipping_fee
    
    # Store information from the original code
    store_name = "THUXUAN CAKE"
    store_address = "Đ/C: Số 10 ngõ 298 Đê La Thành, Đống Đa, Hà Nội"
    store_phone = "ĐT: 0988 159 268"
    
    if not as_pdf:
        # Text version
        invoice_content = f"""
                                {store_name}
                               {store_address}
                               {store_phone}
        
        -----------------------------------------
        
        Bill No. :                #{order_id}#
        
        Khách hàng: {customer_name}
        Số điện thoại: {customer_phone}
        Địa chỉ: {customer_address}
        
        Ngày: {order_data['date']}
        
        -----------------------------------------
        
        Item x Qty                            Price
        """
        
        for _, item in order_items.iterrows():
            invoice_content += f"\n{item['name']} x {item['quantity']}                           {item['subtotal']:,.0f}"
        
        invoice_content += f"""
        -----------------------------------------
        
        Items/Qty                              {len(order_items)}/{order_items['quantity'].sum()}
        
        Total                               {total_amount:,.0f}
        
        -----------------------------------------
        
        Payment Method                        Card
        
        
        " XIN CẢM ƠN QUY KHÁCH."
        """
        
        return invoice_content
    else:
        # Import modules - keep these inside the function to avoid import errors
        import io
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        
        # PDF version with fixed formatting
        buffer = io.BytesIO()
        width, height = A4
        
        # Create the PDF
        c = canvas.Canvas(buffer, pagesize=A4)
        
        # Set up font for Vietnamese
        font_name = setup_vietnamese_font()
        
        # Function to use proper font with fallback
        def set_font(font_style, size):
            if font_name == 'Roboto':
                try:
                    c.setFont(f"Roboto{'-Bold' if font_style == 'bold' else ''}", size)
                except:
                    c.setFont(f"Helvetica{'-Bold' if font_style == 'bold' else ''}", size)
            else:
                c.setFont(f"Helvetica{'-Bold' if font_style == 'bold' else ''}", size)
        
        # Initialize y position
        y_position = height - 2*cm
        
        # Draw store name (centered)
        set_font('bold', 34)  # Large size for store name
        c.drawCentredString(width/2, y_position, store_name)
        y_position -= 1.2*cm
        
        # Draw store address (centered)
        set_font('normal', 14)
        c.drawCentredString(width/2, y_position, store_address)
        y_position -= 0.7*cm
        c.drawCentredString(width/2, y_position, store_phone)
        y_position -= 1*cm
        
        # Draw separator line
        c.setLineWidth(1)
        c.line(2.5*cm, y_position, 19*cm, y_position)
        y_position -= 1*cm
        
        # Bill number with proper alignment
        set_font('bold', 18)
        c.drawString(2.5*cm, y_position, "Bill No. :")
        c.drawString(8*cm, y_position, f"#{order_id}#")
        y_position -= 1*cm
        
        # Customer information with proper spacing
        set_font('normal', 18)
        c.drawString(2.5*cm, y_position, f"Khách hàng: {customer_name}")
        y_position -= 0.7*cm
        
        # Phone
        set_font('normal', 18)
        c.drawString(2.5*cm, y_position, f"Số điện thoại: {customer_phone}")
        y_position -= 0.7*cm
        
        # Address
        set_font('normal', 18)
        c.drawString(2.5*cm, y_position, f"Địa chỉ: {customer_address}")
        y_position -= 1*cm
        
        # Date
        set_font('normal', 18)
        c.drawString(2.5*cm, y_position, f"Ngày: {order_data['date']}")
        y_position -= 1*cm
        
        # Draw separator line
        c.setLineWidth(1)
        c.line(2.5*cm, y_position, 19*cm, y_position)
        y_position -= 1*cm
        
        # Column headers with better alignment
        set_font('bold', 18)
        c.drawString(2.5*cm, y_position, "Item x Qty")
        c.drawRightString(19*cm, y_position, "Price")
        y_position -= 0.8*cm
        
        # Draw items with better spacing and alignment
        for _, item in order_items.iterrows():
            set_font('normal', 18)
            c.drawString(2.5*cm, y_position, f"{item['name']} x {item['quantity']}")
            # Right-align the price with consistent formatting
            c.drawRightString(19*cm, y_position, f"{item['subtotal']:,.0f}")
            y_position -= 0.8*cm
            
            # Check if we need to start a new page
            if y_position < 5*cm:
                c.showPage()
                y_position = height - 3*cm
        
        # Draw separator line
        c.setLineWidth(1)
        c.line(2.5*cm, y_position, 19*cm, y_position)
        y_position -= 1*cm
        
        # Items/Qty count with proper alignment
        set_font('normal', 18)
        c.drawString(2.5*cm, y_position, "Items/Qty")
        c.drawRightString(19*cm, y_position, f"{len(order_items)}/{order_items['quantity'].sum()}")
        y_position -= 1*cm
        
        # Total with proper alignment and emphasis
        set_font('bold', 22)
        c.drawString(2.5*cm, y_position, "Total")
        c.drawRightString(19*cm, y_position, f"{total_amount:,.0f}")
        y_position -= 1*cm
        
        # Draw separator line
        c.setLineWidth(1)
        c.line(2.5*cm, y_position, 19*cm, y_position)
        y_position -= 1*cm
        
        # Payment method with proper alignment
        set_font('normal', 18)
        c.drawString(2.5*cm, y_position, "Payment Method")
        c.drawRightString(19*cm, y_position, "Card")
        y_position -= 2.5*cm
        
        # Thank you message with proper formatting and quotes
        set_font('normal', 18)
        c.drawCentredString(width/2, y_position, '" XIN CẢM ƠN QUY KHÁCH."')
        
        # Add QR code if available
        try:
            qr_y_position = 5*cm  # Lower position for QR code
            qr_image_path = "C:\\Users\\Computer\\PycharmProjects\\bakery_sys\\assets\\qr_cua_xuan.png"
            c.drawImage(qr_image_path, 2.5*cm, qr_y_position, width=4*cm, height=4*cm)
            
            set_font('bold', 10)
            c.drawCentredString(4.5*cm, qr_y_position - 0.5*cm, "Quét để thanh toán")
            
            set_font('normal', 9)
            # Account information
            account_number = "19037177788018"
            account_name = "NGUYEN THU XUAN"
            c.drawCentredString(4.5*cm, qr_y_position - 1*cm, f"STK: {account_number}")
            c.drawCentredString(4.5*cm, qr_y_position - 1.5*cm, f"Tên: {account_name}")
        except Exception:
            # If QR code insertion fails, we don't add any note
            pass
        
        # Save the PDF
        c.save()
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return pdf_data
    
def download_link(content, filename, text, is_pdf=False):
    """Generate a link to download content as a file"""
    if is_pdf:
        # For PDF content (bytes)
        b64 = base64.b64encode(content).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">{text}</a>'
    else:
        # For text content
        b64 = base64.b64encode(content.encode()).decode()
        href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">{text}</a>'
    return href

# Function to delete a product
def delete_product(product_id):
    # Delete product from products DataFrame
    st.session_state.products = st.session_state.products[st.session_state.products['product_id'] != product_id]
    
    # Delete product's recipes from recipes DataFrame
    st.session_state.recipes = st.session_state.recipes[st.session_state.recipes['product_id'] != product_id]
    
    # Show success message
    st.success(f"Sản phẩm {product_id} đã được xóa thành công!")

# Main app navigation
st.title("Hệ Thống Quản Lý Tiệm Bánh 🍰")

# Sidebar navigation
tab_selection = st.sidebar.radio(
    "Điều hướng",
    ["Quản lý Đơn hàng", "Theo dõi Doanh thu", "Kho Nguyên liệu", "Quản lý Sản phẩm", "Quản lý Hóa đơn", "Quản lý Dữ liệu"]
)

# Order Management Tab
if tab_selection == "Quản lý Đơn hàng":
    st.header("Quản lý Đơn hàng")
    
    order_tab1, order_tab2 = st.tabs(["Đơn hàng Mới", "Lịch sử Đơn hàng"])
    
    with order_tab1:
        st.subheader("Tạo Đơn hàng Mới")
        
        col1, col2 = st.columns(2)
        with col1:
            customer_name = st.text_input("Tên Khách hàng")
            customer_phone = st.text_input("Số điện thoại")
        with col2:
            customer_address = st.text_area("Địa chỉ giao hàng", height=100)
        
        # Product selection
        st.subheader("Lựa chọn Sản phẩm")
        
        # Display available products with quantity selection
        selected_products = []
        quantities = []
        
        cols = st.columns(4)
        for i, (_, product) in enumerate(st.session_state.products.iterrows()):
            with cols[i % 4]:
                st.write(f"**{product['name']}**")
                st.write(f"{product['price']:,.0f} VND")
                quantity = st.number_input(f"SL {product['name']}", min_value=0, value=0, key=f"qty_{product['product_id']}")
                if quantity > 0:
                    selected_products.append(product)
                    quantities.append(quantity)
                st.write("---")
        
        # Calculate total product amount
        total_product_amount = sum(p['price'] * q for p, q in zip(selected_products, quantities))
        
        # Shipping fee input
        st.subheader("Phí vận chuyển")
        shipping_fee = st.number_input("Phí vận chuyển (VND)", min_value=0, value=0, step=1000)
        
        # Calculate grand total
        total_amount = total_product_amount + shipping_fee
        
        # Display totals
        st.subheader("Tổng tiền")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**Tổng sản phẩm:** {total_product_amount:,.0f} VND")
        with col2:
            st.write(f"**Phí vận chuyển:** {shipping_fee:,.0f} VND")
        with col3:
            st.write(f"**Tổng cộng:** {total_amount:,.0f} VND")
        
        if st.button("Tạo Đơn hàng", key="create_order"):
            if not customer_name:
                st.error("Vui lòng nhập tên khách hàng")
            elif len(selected_products) == 0:
                st.error("Vui lòng chọn ít nhất một sản phẩm")
            else:
                # Generate order ID
                order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
                
                # Create order
                new_order = pd.DataFrame({
                    'order_id': [order_id],
                    'date': [date.today().strftime("%Y-%m-%d")],
                    'customer_name': [customer_name],
                    'customer_phone': [customer_phone],
                    'customer_address': [customer_address],
                    'total_amount': [total_product_amount],  # Store just product amount
                    'shipping_fee': [shipping_fee],  # Add shipping fee
                    'status': ['Hoàn thành']
                })
                
                # Create order items
                new_order_items = []
                for product, quantity in zip(selected_products, quantities):
                    new_order_items.append({
                        'order_id': order_id,
                        'product_id': product['product_id'],
                        'quantity': quantity,
                        'price': product['price'],
                        'subtotal': product['price'] * quantity
                    })
                
                new_order_items_df = pd.DataFrame(new_order_items)
                
                # Update session state
                st.session_state.orders = pd.concat([st.session_state.orders, new_order], ignore_index=True)
                st.session_state.order_items = pd.concat([st.session_state.order_items, new_order_items_df], ignore_index=True)
                
                # Update materials inventory
                update_materials_after_order(order_id)
                
                # Update income records
                update_income(order_id)
                
                # Create invoice
                invoice_id = f"INV-{uuid.uuid4().hex[:8].upper()}"
                new_invoice = pd.DataFrame({
                    'invoice_id': [invoice_id],
                    'order_id': [order_id],
                    'date': [date.today().strftime("%Y-%m-%d")],
                    'customer_name': [customer_name],
                    'total_amount': [total_amount],  # Use grand total (products + shipping)
                    'payment_method': ['Tiền mặt']  # Default payment method
                })
                
                st.session_state.invoices = pd.concat([st.session_state.invoices, new_invoice], ignore_index=True)
                
                st.success(f"Đơn hàng {order_id} đã được tạo thành công!")
                
                # Generate invoice download link
                pdf_data = generate_invoice_content(invoice_id, order_id, as_pdf=True)
                st.markdown(download_link(pdf_data, f"Hoadon_{invoice_id}.pdf", "Tải Hóa đơn (PDF)", is_pdf=True), unsafe_allow_html=True)

                 # Save data after creating order
                save_dataframe(st.session_state.orders, "orders.csv")
                save_dataframe(st.session_state.order_items, "order_items.csv")
                save_dataframe(st.session_state.invoices, "invoices.csv")
                save_dataframe(st.session_state.materials, "materials.csv")
                save_dataframe(st.session_state.income, "income.csv")
    
    with order_tab2:
        st.subheader("Lịch sử Đơn hàng")
        
        if len(st.session_state.orders) > 0:
            st.dataframe(st.session_state.orders.sort_values('date', ascending=False))
            
            # Order details view
            selected_order_id = st.selectbox("Chọn Đơn hàng để Xem Chi tiết", 
                                           options=st.session_state.orders['order_id'].tolist(),
                                           format_func=lambda x: f"{x} - {st.session_state.orders[st.session_state.orders['order_id'] == x]['customer_name'].iloc[0]}")
            
            if selected_order_id:
                st.write("### Chi tiết Đơn hàng")
                order_details = st.session_state.order_items[st.session_state.order_items['order_id'] == selected_order_id]
                
                # Get product names
                order_details = order_details.merge(
                    st.session_state.products[['product_id', 'name']],
                    on='product_id',
                    how='left'
                )
                
                st.dataframe(order_details[['name', 'quantity', 'price', 'subtotal']])
        else:
            st.info("Chưa có đơn hàng nào. Hãy tạo đơn hàng mới để xem ở đây.")

# Income Tracking Tab - Updated with Revenue and Cost Table
elif tab_selection == "Theo dõi Doanh thu":
    st.header("Theo dõi Doanh thu")
    
    # Initialize material import cost tracking if not exists
    if 'material_costs' not in st.session_state:
        st.session_state.material_costs = pd.DataFrame(columns=[
            'date', 'material_id', 'quantity', 'total_cost', 'supplier'
        ])
    
    income_tab1, income_tab2, income_tab3 = st.tabs(["Báo cáo Tổng quan", "Bảng Doanh thu & Chi phí", "Chi phí Nguyên liệu"])
    
    # Helper function to create monthly summary
    def create_monthly_summary(income_df, material_costs_df, start_date, end_date):
        # Ensure we have data in the correct format
        if income_df.empty and material_costs_df.empty:
            return pd.DataFrame()
            
        # Convert date strings to datetime objects for proper handling
        income_df['date_obj'] = pd.to_datetime(income_df['date'])
        if not material_costs_df.empty:
            material_costs_df['date_obj'] = pd.to_datetime(material_costs_df['date'])
        
        # Create a date range from start to end
        date_range = pd.date_range(start=start_date, end=end_date, freq='MS')  # MS = Month Start
        
        # Prepare results table
        results = []
        
        for date in date_range:
            month_name = date.strftime('%m/%Y')
            month_start = date.strftime('%Y-%m-%d')
            month_end = (date + pd.offsets.MonthEnd(1)).strftime('%Y-%m-%d')
            
            # Filter income data for this month
            month_income = income_df[(income_df['date_obj'] >= month_start) & 
                                    (income_df['date_obj'] <= month_end)]
            
            # Calculate income values
            total_sales = month_income['total_sales'].sum() if not month_income.empty else 0
            cost_of_goods = month_income['cost_of_goods'].sum() if not month_income.empty else 0
            sales_profit = month_income['profit'].sum() if not month_income.empty else 0
            
            # Calculate material costs for this month
            material_costs = 0
            if not material_costs_df.empty:
                month_costs = material_costs_df[(material_costs_df['date_obj'] >= month_start) & 
                                            (material_costs_df['date_obj'] <= month_end)]
                material_costs = month_costs['total_cost'].sum() if not month_costs.empty else 0
            
            # Calculate other costs (includes marketing, production, and other fees)
            other_costs = material_costs  # All external costs (non-COGS) go here
            
            # Recalculate the total cost as Chi phí hàng hóa + Chi phí khác
            total_cost = cost_of_goods + other_costs
            
            # Calculate net profit
            net_profit = total_sales - total_cost
            
            # Calculate profit margin
            profit_margin = (net_profit / total_sales * 100) if total_sales > 0 else 0
            
            # Add to results
            results.append({
                'Tháng': month_name,
                'Doanh thu': total_sales,
                'Chi phí Hàng bán': cost_of_goods,
                'Chi phí Khác': other_costs,
                'Tổng Chi phí': total_cost,
                'Lợi nhuận': net_profit,
                'Tỷ suất': profit_margin
            })
        
        return pd.DataFrame(results)
    
    with income_tab1:
        if len(st.session_state.income) > 0:
            # Sort by date
            income_df = st.session_state.income.sort_values('date', ascending=False)
            
            # Date filter - Handle date range safely
            try:
                # Get min and max dates from data
                min_date_str = income_df['date'].min()
                max_date_str = income_df['date'].max()
                
                min_date = datetime.datetime.strptime(min_date_str, '%Y-%m-%d').date()
                max_date = datetime.datetime.strptime(max_date_str, '%Y-%m-%d').date()
                
                # Use today's date if within range, otherwise use max_date
                today = datetime.date.today()
                if today < min_date:
                    default_end = min_date
                elif today > max_date:
                    default_end = max_date
                else:
                    default_end = today
                
                # Use first day of current month or min_date, whichever is later
                first_day_of_month = datetime.date(today.year, today.month, 1)
                if first_day_of_month < min_date:
                    default_start = min_date
                elif first_day_of_month > max_date:
                    default_start = max_date
                else:
                    default_start = first_day_of_month
                
                # Ensure the default range is valid
                if default_start > default_end:
                    default_start = default_end
                
                # Create date input with valid defaults
                date_range = st.date_input(
                    "Chọn Khoảng thời gian",
                    [default_start, default_end],
                    min_value=min_date,
                    max_value=max_date,
                    key="income_date_range"
                )
            except Exception as e:
                # Fallback if date parsing fails
                st.error(f"Lỗi khi xử lý ngày tháng: {str(e)}")
                # Use a simple date range selection without defaults
                date_range = st.date_input(
                    "Chọn Khoảng thời gian",
                    key="income_date_range_fallback"
                )
            
            # Only proceed if we have a valid date range
            if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
                start_date, end_date = date_range
                
                # Convert dates to string format for filtering
                start_date_str = start_date.strftime('%Y-%m-%d')
                end_date_str = end_date.strftime('%Y-%m-%d')
                
                # Filter income data
                filtered_income = income_df[
                    (income_df['date'] >= start_date_str) & 
                    (income_df['date'] <= end_date_str)
                ]
                
                # Check if we have data in the selected range
                if filtered_income.empty:
                    st.info(f"Không có dữ liệu doanh thu trong khoảng từ {start_date_str} đến {end_date_str}.")
                else:
                    # Get material costs for the same period
                    material_costs_in_period = 0
                    filtered_costs = pd.DataFrame()
                    if len(st.session_state.material_costs) > 0:
                        material_cost_df = st.session_state.material_costs.copy()
                        filtered_costs = material_cost_df[
                            (material_cost_df['date'] >= start_date_str) & 
                            (material_cost_df['date'] <= end_date_str)
                        ]
                        material_costs_in_period = filtered_costs['total_cost'].sum()
                    
                    # Calculate total profit with material costs considered
                    total_sales = filtered_income['total_sales'].sum()
                    cost_of_goods = filtered_income['cost_of_goods'].sum()
                    total_profit = filtered_income['profit'].sum()
                    net_profit = total_profit - material_costs_in_period
                    
                    # Display income summary
                    st.subheader("Tổng quan Doanh thu")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Tổng Doanh thu", f"{total_sales:,.0f} VND")
                    with col2:
                        st.metric("Chi phí Hàng hóa", f"{cost_of_goods:,.0f} VND")
                    with col3:
                        st.metric("Lợi nhuận Gộp", f"{total_profit:,.0f} VND")
                    
                    # Display additional costs and net profit
                    st.subheader("Chi phí & Lợi nhuận Ròng")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Chi phí Khác", f"{material_costs_in_period:,.0f} VND")
                    with col2:
                        total_costs = cost_of_goods + material_costs_in_period
                        st.metric("Tổng Chi phí", f"{total_costs:,.0f} VND")
                    with col3:
                        net_profit = total_sales - total_costs
                        st.metric("Lợi nhuận Ròng", f"{net_profit:,.0f} VND")
                    
                    # Display profit margins
                    if total_sales > 0:
                        gross_margin = (total_profit / total_sales) * 100
                        net_margin = (net_profit / total_sales) * 100
                        
                        st.subheader("Tỷ suất Lợi nhuận")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Tỷ suất Lợi nhuận Gộp", f"{gross_margin:.2f}%")
                        with col2:
                            st.metric("Tỷ suất Lợi nhuận Ròng", f"{net_margin:.2f}%")
                    
                    # Chart for income trends
                    if len(filtered_income) > 1:  # Only show chart if we have multiple data points
                        st.subheader("Biểu đồ Doanh thu")
                        chart_data = filtered_income.copy()
                        chart_data = chart_data.sort_values('date')
                        
                        # Convert date format for display
                        chart_data['formatted_date'] = chart_data['date'].apply(
                            lambda x: datetime.datetime.strptime(x, '%Y-%m-%d').strftime('%d/%m/%Y')
                        )
                        
                        # Chart data as bar chart
                        chart = {
                            'Ngày': chart_data['formatted_date'].tolist(),
                            'Doanh thu': chart_data['total_sales'].tolist(),
                            'Chi phí': chart_data['cost_of_goods'].tolist(),
                            'Lợi nhuận': chart_data['profit'].tolist()
                        }
                        
                        chart_df = pd.DataFrame(chart)
                        
                        # Use streamlit's built-in bar chart
                        st.bar_chart(
                            chart_df.set_index('Ngày')[['Doanh thu', 'Chi phí', 'Lợi nhuận']],
                            use_container_width=True
                        )
        else:
            st.info("Chưa có dữ liệu doanh thu. Hoàn thành đơn hàng để xem thông tin doanh thu.")
    
    with income_tab2:
        st.subheader("Biểu đồ Doanh thu & Chi phí")
        
        # Only create the chart if we have income data
        if len(st.session_state.income) > 0:
            income_df = st.session_state.income.copy()
            material_costs_df = st.session_state.material_costs.copy() if 'material_costs' in st.session_state else pd.DataFrame()
            
            # Date range selection
            try:
                # Get min and max dates from data
                min_date_str = income_df['date'].min()
                max_date_str = income_df['date'].max()
                
                min_date = datetime.datetime.strptime(min_date_str, '%Y-%m-%d').date()
                max_date = datetime.datetime.strptime(max_date_str, '%Y-%m-%d').date()
                
                # Create date input with valid defaults
                date_range = st.date_input(
                    "Chọn Khoảng thời gian",
                    [min_date, max_date],
                    min_value=min_date,
                    max_value=max_date,
                    key="income_chart_range"
                )
                
                if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
                    start_date, end_date = date_range
                    start_date_str = start_date.strftime('%Y-%m-%d')
                    end_date_str = end_date.strftime('%Y-%m-%d')
                    
                    # Filter income data
                    filtered_income = income_df[
                        (income_df['date'] >= start_date_str) & 
                        (income_df['date'] <= end_date_str)
                    ]
                    
                    # Filter material costs data
                    filtered_costs = pd.DataFrame()
                    if not material_costs_df.empty:
                        filtered_costs = material_costs_df[
                            (material_costs_df['date'] >= start_date_str) & 
                            (material_costs_df['date'] <= end_date_str)
                        ]
                    
                    # Group data by date
                    if not filtered_income.empty:
                        # Group income data by date
                        income_by_date = filtered_income.groupby('date').agg({
                            'total_sales': 'sum',
                            'cost_of_goods': 'sum',
                            'profit': 'sum'
                        }).reset_index()
                        
                        # Calculate material costs by date
                        costs_by_date = pd.DataFrame()
                        if not filtered_costs.empty:
                            costs_by_date = filtered_costs.groupby('date').agg({
                                'total_cost': 'sum'
                            }).reset_index()
                            costs_by_date.rename(columns={'total_cost': 'material_cost'}, inplace=True)
                        
                        # Merge the dataframes
                        chart_data = income_by_date.copy()
                        if not costs_by_date.empty:
                            chart_data = chart_data.merge(costs_by_date, on='date', how='left')
                            chart_data['material_cost'] = chart_data['material_cost'].fillna(0)
                            chart_data['total_cost'] = chart_data['cost_of_goods'] + chart_data['material_cost']
                            chart_data['net_profit'] = chart_data['profit'] - chart_data['material_cost']
                        else:
                            chart_data['material_cost'] = 0
                            chart_data['total_cost'] = chart_data['cost_of_goods']
                            chart_data['net_profit'] = chart_data['profit']
                        
                        # Add formatted date for display
                        chart_data['formatted_date'] = chart_data['date'].apply(
                            lambda x: datetime.datetime.strptime(x, '%Y-%m-%d').strftime('%d/%m/%Y')
                        )
                        
                        # Sort by date
                        chart_data = chart_data.sort_values('date')
                        
                        # Display summary metrics
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric(
                                "Tổng Doanh thu", 
                                f"{chart_data['total_sales'].sum():,.0f} VND",
                                delta=None
                            )
                        
                        with col2:
                            st.metric(
                                "Chi phí Hàng bán", 
                                f"{chart_data['cost_of_goods'].sum():,.0f} VND",
                                delta=None
                            )
                        
                        with col3:
                            st.metric(
                                "Chi phí Nguyên liệu", 
                                f"{chart_data['material_cost'].sum():,.0f} VND",
                                delta=None
                            )
                        
                        with col4:
                            st.metric(
                                "Lợi nhuận Ròng", 
                                f"{chart_data['net_profit'].sum():,.0f} VND",
                                delta=None
                            )
                        
                        # Create line chart
                        st.subheader("Biểu đồ Doanh thu theo Thời gian")
                        
                        # Option to select chart type
                        chart_type = st.radio(
                            "Loại biểu đồ",
                            ["Đường", "Cột"],
                            horizontal=True,
                            key="income_chart_type"
                        )
                        
                        # Option to select metrics to display
                        metrics = st.multiselect(
                            "Chọn các chỉ số để hiển thị",
                            ["Doanh thu", "Chi phí Hàng bán", "Chi phí Nguyên liệu", "Tổng Chi phí", "Lợi nhuận Ròng"],
                            default=["Doanh thu", "Tổng Chi phí", "Lợi nhuận Ròng"],
                            key="income_chart_metrics"
                        )
                        
                        # Map selected metrics to dataframe columns
                        metric_columns = {
                            "Doanh thu": "total_sales",
                            "Chi phí Hàng bán": "cost_of_goods",
                            "Chi phí Nguyên liệu": "material_cost",
                            "Tổng Chi phí": "total_cost",
                            "Lợi nhuận Ròng": "net_profit"
                        }
                        
                        # Create chart data
                        if metrics:
                            chart_columns = [metric_columns[m] for m in metrics if m in metric_columns]
                            if chart_columns:
                                # Create DataFrame for chart
                                display_df = pd.DataFrame()
                                display_df.index = chart_data['formatted_date']
                                
                                for metric, column in zip(metrics, chart_columns):
                                    display_df[metric] = chart_data[column]
                                
                                # Display the chart
                                if chart_type == "Đường":
                                    st.line_chart(display_df)
                                else:
                                    st.bar_chart(display_df)
                        
                        # Display data table
                        st.subheader("Dữ liệu Chi tiết")
                        
                        # Format data for display
                        display_data = []
                        for _, row in chart_data.iterrows():
                            display_data.append({
                                'Ngày': row['formatted_date'],
                                'Doanh thu': f"{row['total_sales']:,.0f} VND",
                                'Chi phí Hàng bán': f"{row['cost_of_goods']:,.0f} VND",
                                'Chi phí Nguyên liệu': f"{row['material_cost']:,.0f} VND",
                                'Tổng Chi phí': f"{row['total_cost']:,.0f} VND",
                                'Lợi nhuận Ròng': f"{row['net_profit']:,.0f} VND"
                            })
                        
                        if display_data:
                            st.dataframe(pd.DataFrame(display_data))
                    else:
                        st.info("Không có dữ liệu doanh thu trong khoảng thời gian đã chọn.")
                
            except Exception as e:
                st.error(f"Lỗi khi tạo biểu đồ doanh thu: {str(e)}")
                st.info("Vui lòng kiểm tra dữ liệu doanh thu và chi phí.")
        else:
            st.info("Chưa có dữ liệu doanh thu để hiển thị biểu đồ.")
    
    with income_tab3:
        st.subheader("Chi phí Nguyên liệu")
        
        if len(st.session_state.material_costs) > 0:
            # Display material costs
            material_costs_df = st.session_state.material_costs.copy()
            
            # Format material costs for display
            material_costs_display = pd.DataFrame({
                'Ngày': material_costs_df['date'],
                'Mã Nguyên liệu': material_costs_df['material_id'],
                'Số lượng': material_costs_df['quantity'],
                'Chi phí': material_costs_df['total_cost'].apply(lambda x: f"{x:,.0f} VND"),
                'Nhà cung cấp': material_costs_df['supplier']
            })
            
            # Date filter for material costs - with safer handling
            try:
                # Get min and max dates from data
                min_cost_date_str = material_costs_df['date'].min()
                max_cost_date_str = material_costs_df['date'].max()
                
                min_cost_date = datetime.datetime.strptime(min_cost_date_str, '%Y-%m-%d').date()
                max_cost_date = datetime.datetime.strptime(max_cost_date_str, '%Y-%m-%d').date()
                
                # Use today's date if within range, otherwise use max_date
                today = datetime.date.today()
                if today < min_cost_date:
                    default_end = min_cost_date
                elif today > max_cost_date:
                    default_end = max_cost_date
                else:
                    default_end = today
                
                # Use first day of current month or min_date, whichever is later
                first_day_of_month = datetime.date(today.year, today.month, 1)
                if first_day_of_month < min_cost_date:
                    default_start = min_cost_date
                elif first_day_of_month > max_cost_date:
                    default_start = max_cost_date
                else:
                    default_start = first_day_of_month
                
                # Ensure the default range is valid
                if default_start > default_end:
                    default_start = default_end
                
                # Create date input with valid defaults
                cost_date_range = st.date_input(
                    "Chọn Khoảng thời gian",
                    [default_start, default_end],
                    min_value=min_cost_date,
                    max_value=max_cost_date,
                    key="material_cost_date_range"
                )
            except Exception as e:
                # Fallback if date parsing fails
                st.error(f"Lỗi khi xử lý ngày tháng: {str(e)}")
                # Use a simple date range selection without defaults
                cost_date_range = st.date_input(
                    "Chọn Khoảng thời gian",
                    key="material_cost_date_range_fallback"
                )
            
            # Only proceed if we have a valid date range
            if isinstance(cost_date_range, (list, tuple)) and len(cost_date_range) == 2:
                start_date, end_date = cost_date_range
                
                # Convert dates to string format for filtering
                start_date_str = start_date.strftime('%Y-%m-%d')
                end_date_str = end_date.strftime('%Y-%m-%d')
                
                # Filter material costs
                filtered_costs_display = material_costs_display[
                    (material_costs_display['Ngày'] >= start_date_str) & 
                    (material_costs_display['Ngày'] <= end_date_str)
                ]
                
                filtered_costs_df = material_costs_df[
                    (material_costs_df['date'] >= start_date_str) & 
                    (material_costs_df['date'] <= end_date_str)
                ]
                
                # Check if we have data in the selected range
                if filtered_costs_df.empty:
                    st.info(f"Không có dữ liệu chi phí nguyên liệu trong khoảng từ {start_date_str} đến {end_date_str}.")
                else:
                    # Show total cost for period
                    total_period_cost = filtered_costs_df['total_cost'].sum()
                    st.metric("Tổng Chi phí Nguyên liệu", f"{total_period_cost:,.0f} VND")
                    
                    # Display filtered costs
                    st.dataframe(filtered_costs_display)
                    
                    # Group costs by material
                    material_grouped = filtered_costs_df.groupby('material_id').agg({
                        'quantity': 'sum',
                        'total_cost': 'sum'
                    }).reset_index()
                    
                    # Get material names (safely)
                    material_names = {}
                    if not st.session_state.materials.empty:
                        for _, material in st.session_state.materials.iterrows():
                            material_names[material['material_id']] = material['name']
                    
                    # Format for display
                    material_summary = pd.DataFrame({
                        'Mã Nguyên liệu': material_grouped['material_id'],
                        'Tên Nguyên liệu': material_grouped['material_id'].apply(
                            lambda x: material_names.get(x, x)
                        ),
                        'Tổng Số lượng': material_grouped['quantity'],
                        'Tổng Chi phí': material_grouped['total_cost'].apply(lambda x: f"{x:,.0f} VND")
                    })
                    
                    st.subheader("Chi phí theo Nguyên liệu")
                    st.dataframe(material_summary)
        else:
            st.info("Chưa có dữ liệu chi phí nguyên liệu. Vui lòng nhập nguyên liệu vào kho để theo dõi chi phí.")

# Materials Inventory Tab - Updated with Out-of-Stock Notifications
elif tab_selection == "Kho Nguyên liệu":
    st.header("Kho Nguyên liệu")
    
    # In the Kho Nguyên liệu tab, before displaying materials
    if 'used_quantity' not in st.session_state.materials.columns:
        st.session_state.materials['used_quantity'] = 0.0

    # Check for out-of-stock or low stock items immediately
    if not st.session_state.materials.empty:
        out_of_stock_items = []
        low_stock_items = []
        
        for _, material in st.session_state.materials.iterrows():
            if material['quantity'] <= 0:
                out_of_stock_items.append(material['name'])
            elif material['quantity'] <= 5:
                low_stock_items.append(material['name'])
        
        # Show notifications for out-of-stock items
        if out_of_stock_items:
            st.error(f"⚠️ **Cảnh báo: Các nguyên liệu đã hết hàng:** {', '.join(out_of_stock_items)}")
        
        # Show notifications for low stock items
        if low_stock_items:
            st.warning(f"⚠️ **Cảnh báo: Các nguyên liệu sắp hết hàng:** {', '.join(low_stock_items)}")
    
    # Initialize material costs tracking if not exists
    if 'material_costs' not in st.session_state:
        st.session_state.material_costs = pd.DataFrame(columns=[
            'date', 'material_id', 'quantity', 'total_cost', 'supplier'
        ])
    
    mat_tab1, mat_tab2, mat_tab3 = st.tabs(["Xem Kho", "Cập nhật Kho", "Nhập Nguyên liệu"])
    
    with mat_tab1:
        st.subheader("Kho hiện tại")
        
        # Create a safer display version without style function
        if not st.session_state.materials.empty:
            # Create a copy of the materials dataframe for display
            materials_display = st.session_state.materials.copy()
            
            # Add status column
            def get_status(quantity):
                if quantity <= 0:
                    return "Hết hàng"
                elif quantity <= 5:
                    return "Sắp hết hàng"
                elif quantity <= 15:
                    return "Hàng trung bình"
                else:
                    return "Còn hàng"
            
            materials_display['Trạng thái'] = materials_display['quantity'].apply(get_status)
            
            # Create a cleaner display version
            display_df = pd.DataFrame({
                'Mã nguyên liệu': materials_display['material_id'],
                'Tên': materials_display['name'],
                'Đơn vị': materials_display['unit'],
                'Số lượng': materials_display['quantity'],
                'Đã sử dụng': materials_display['used_quantity'],
                'Giá/Đơn vị': [f"{price:,.0f} VND" for price in materials_display['price_per_unit']],
                'Trạng thái': materials_display['Trạng thái']
            })
            
            # Display the dataframe
            st.dataframe(display_df)
            
            # Add color coding with HTML instead
            status_counts = materials_display['Trạng thái'].value_counts()
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if 'Hết hàng' in status_counts:
                    st.markdown(f"<div style='background-color:#ff8888;padding:10px;border-radius:5px;'><b>Hết hàng:</b> {status_counts.get('Hết hàng', 0)} mục</div>", unsafe_allow_html=True)
            with col2:
                if 'Sắp hết hàng' in status_counts:
                    st.markdown(f"<div style='background-color:#ffcccc;padding:10px;border-radius:5px;'><b>Sắp hết hàng:</b> {status_counts.get('Sắp hết hàng', 0)} mục</div>", unsafe_allow_html=True)
            with col3:
                if 'Hàng trung bình' in status_counts:
                    st.markdown(f"<div style='background-color:#ffffcc;padding:10px;border-radius:5px;'><b>Hàng trung bình:</b> {status_counts.get('Hàng trung bình', 0)} mục</div>", unsafe_allow_html=True)
            with col4:
                if 'Còn hàng' in status_counts:
                    st.markdown(f"<div style='background-color:#ccffcc;padding:10px;border-radius:5px;'><b>Còn hàng:</b> {status_counts.get('Còn hàng', 0)} mục</div>", unsafe_allow_html=True)
            
            # Summary metrics
            total_value = sum(m['quantity'] * m['price_per_unit'] for _, m in st.session_state.materials.iterrows() if m['quantity'] > 0)
            st.metric("Tổng Giá trị Kho", f"{total_value:,.0f} VND")
            
            # Out of stock list
            if 'Hết hàng' in status_counts or 'Sắp hết hàng' in status_counts:
                st.subheader("Danh sách cần Nhập hàng")
                needs_restock = materials_display[(materials_display['Trạng thái'] == 'Hết hàng') | 
                                                 (materials_display['Trạng thái'] == 'Sắp hết hàng')]
                
                restock_df = pd.DataFrame({
                    'Mã nguyên liệu': needs_restock['material_id'],
                    'Tên': needs_restock['name'],
                    'Đơn vị': needs_restock['unit'],
                    'Số lượng hiện tại': needs_restock['quantity'],
                    'Trạng thái': needs_restock['Trạng thái']
                })
                
                st.dataframe(restock_df)
                
                # Generate shopping list
                if st.button("Tạo Danh sách mua hàng"):
                    shopping_list = ""
                    for _, item in needs_restock.iterrows():
                        current_qty = item['quantity']
                        
                        # Calculate suggested order quantity
                        if current_qty <= 0:
                            suggested_qty = 20  # Standard restock amount for out of stock
                        else:
                            suggested_qty = 20 - current_qty  # Top up to 20 units
                            
                        shopping_list += f"- {item['name']}: {suggested_qty} {item['unit']} " + \
                                        f"(hiện tại: {current_qty}) - " + \
                                        f"Đơn giá tham khảo: {item['price_per_unit']:,.0f} VND\n"
                    
                    # Display the shopping list
                    st.subheader("Danh sách mua hàng đề xuất")
                    st.text_area("Sao chép danh sách này:", shopping_list, height=200)
        else:
            st.info("Chưa có dữ liệu nguyên liệu.")
        
    with mat_tab2:
        st.subheader("Cập nhật Kho")
        
        # Select material to update
        if not st.session_state.materials.empty:
            # Create a list of options for the selectbox
            material_options = []
            for _, material in st.session_state.materials.iterrows():
                status = ""
                if material['quantity'] <= 0:
                    status = " [HẾT HÀNG]"
                elif material['quantity'] <= 5:
                    status = " [SẮP HẾT]"
                    
                material_options.append(f"{material['material_id']} - {material['name']}{status}")
            
            selected_material = st.selectbox(
                "Chọn Nguyên liệu",
                options=material_options,
                key="update_material_select"
            )
            
            if selected_material:
                # Extract material_id from the selection
                selected_material_id = selected_material.split(' - ')[0]
                
                # Find the material data
                material_data = st.session_state.materials[st.session_state.materials['material_id'] == selected_material_id]
                
                if not material_data.empty:
                    material_idx = material_data.index[0]
                    current_quantity = st.session_state.materials.at[material_idx, 'quantity']
                    current_price = st.session_state.materials.at[material_idx, 'price_per_unit']
                    
                    # Show warning if out of stock
                    if current_quantity <= 0:
                        st.error(f"⚠️ Nguyên liệu này đã HẾT HÀNG! Số lượng hiện tại: {current_quantity}")
                    elif current_quantity <= 5:
                        st.warning(f"⚠️ Nguyên liệu này sắp hết hàng! Số lượng hiện tại: {current_quantity}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        # Allow negative values for quantity to show the actual negative balance
                        new_quantity = st.number_input("Số lượng Mới", value=float(current_quantity), step=0.1)
                    with col2:
                        new_price = st.number_input("Giá Mới trên một Đơn vị", min_value=1, value=int(current_price), step=1000)
                    
                    if st.button("Cập nhật Nguyên liệu"):
                        # Update the material
                        st.session_state.materials.at[material_idx, 'quantity'] = new_quantity
                        st.session_state.materials.at[material_idx, 'price_per_unit'] = new_price
                        
                        # Show status messages
                        if new_quantity <= 0:
                            st.error(f"Nguyên liệu {selected_material_id} đã được cập nhật nhưng hiện đã HẾT HÀNG!")
                        elif new_quantity <= 5:
                            st.warning(f"Nguyên liệu {selected_material_id} đã được cập nhật nhưng sắp hết hàng!")
                        else:
                            st.success(f"Nguyên liệu {selected_material_id} đã được cập nhật thành công!")
                        #Save materials data
                        save_dataframe(st.session_state.materials, "materials.csv")        
        else:
            st.info("Chưa có dữ liệu nguyên liệu để cập nhật.")

    with mat_tab3:
        st.subheader("Nhập Nguyên liệu")
    
        col1, col2 = st.columns(2)
        
        with col1:
            # Date of import
            import_date = st.date_input(
                "Ngày Nhập", 
                value=datetime.date.today(),
                key="material_import_date"
            ).strftime("%Y-%m-%d")
            
            # Supplier information
            supplier = st.text_input("Nhà cung cấp", key="material_supplier")
        
        # Add radio buttons to select between importing existing material or creating new material
        import_option = st.radio(
            "Lựa chọn:",
            ["Nhập kho nguyên liệu hiện có", "Thêm và nhập nguyên liệu mới"],
            key="import_option"
        )
        
        if import_option == "Nhập kho nguyên liệu hiện có":
            # OPTION 1: IMPORT EXISTING MATERIAL
            if not st.session_state.materials.empty:
                # Create a list of options for the selectbox
                material_options = []
                for _, material in st.session_state.materials.iterrows():
                    status = ""
                    if material['quantity'] <= 0:
                        status = " [HẾT HÀNG]"
                    elif material['quantity'] <= 5:
                        status = " [SẮP HẾT]"
                        
                    material_options.append(f"{material['material_id']} - {material['name']} ({material['unit']}){status}")
                
                selected_material = st.selectbox(
                    "Chọn Nguyên liệu để Nhập",
                    options=material_options,
                    key="import_material_select"
                )
                
                if selected_material:
                    # Extract material_id from the selection
                    selected_material_id = selected_material.split(' - ')[0]
                    
                    # Find the material data
                    material_data = st.session_state.materials[st.session_state.materials['material_id'] == selected_material_id]
                    
                    if not material_data.empty:
                        material_idx = material_data.index[0]
                        current_quantity = st.session_state.materials.at[material_idx, 'quantity']
                        current_unit = st.session_state.materials.at[material_idx, 'unit']
                        
                        # Show status information
                        if current_quantity <= 0:
                            st.error(f"⚠️ Nguyên liệu này hiện đang HẾT HÀNG! Số lượng hiện tại: {current_quantity} {current_unit}")
                        elif current_quantity <= 5:
                            st.warning(f"⚠️ Nguyên liệu này sắp hết hàng! Số lượng hiện tại: {current_quantity} {current_unit}")
                        else:
                            st.info(f"Số lượng hiện tại: {current_quantity} {current_unit}")
                        
                        # Input import details
                        col1, col2 = st.columns(2)
                        with col1:
                            import_quantity = st.number_input(
                                f"Số lượng Nhập ({current_unit})", 
                                min_value=0.1, 
                                value=1.0, 
                                step=0.1,
                                key="import_quantity"
                            )
                        with col2:
                            import_cost = st.number_input(
                                "Tổng Chi phí (VND)", 
                                min_value=1000, 
                                value=100000, 
                                step=1000,
                                key="import_cost"
                            )
                        
                        # Calculate unit price
                        if import_quantity > 0:
                            unit_price = import_cost / import_quantity
                            st.write(f"Giá trên một đơn vị: {unit_price:,.0f} VND/{current_unit}")
                        
                        # Additional notes
                        import_notes = st.text_area("Ghi chú", key="import_notes")
                        
                        # Confirm import
                        if st.button("Xác nhận Nhập kho"):
                            if not supplier:
                                st.error("Vui lòng nhập thông tin nhà cung cấp")
                            elif import_quantity <= 0:
                                st.error("Vui lòng nhập số lượng hợp lệ")
                            else:
                                # Update material quantity
                                new_quantity = current_quantity + import_quantity
                                st.session_state.materials.at[material_idx, 'quantity'] = new_quantity
                                
                                # Update price (weighted average)
                                current_total_value = current_quantity * st.session_state.materials.at[material_idx, 'price_per_unit']
                                new_total_value = current_total_value + import_cost
                                new_price_per_unit = new_total_value / new_quantity if new_quantity > 0 else 0
                                
                                st.session_state.materials.at[material_idx, 'price_per_unit'] = new_price_per_unit
                                
                                # Record the import cost
                                if 'material_costs' not in st.session_state:
                                    st.session_state.material_costs = pd.DataFrame(columns=[
                                        'date', 'material_id', 'quantity', 'total_cost', 'supplier'
                                    ])
                                    
                                new_import = pd.DataFrame({
                                    'date': [import_date],
                                    'material_id': [selected_material_id],
                                    'quantity': [import_quantity],
                                    'total_cost': [import_cost],
                                    'supplier': [supplier]
                                })
                                
                                st.session_state.material_costs = pd.concat([st.session_state.material_costs, new_import], ignore_index=True)
                                
                                st.success(f"Đã nhập {import_quantity} {current_unit} nguyên liệu {selected_material_id} thành công!")
                                st.write(f"Số lượng mới: {new_quantity} {current_unit}")
                                st.write(f"Giá đơn vị mới (trung bình): {new_price_per_unit:,.0f} VND/{current_unit}")
                                # Save materials and material costs data
                                save_dataframe(st.session_state.materials, "materials.csv")
                                save_dataframe(st.session_state.material_costs, "material_costs.csv")
            else:
                st.info("Chưa có dữ liệu nguyên liệu. Vui lòng thêm nguyên liệu mới.")
                
        else:
            # OPTION 2: CREATE AND IMPORT NEW MATERIAL
            st.subheader("Thêm Nguyên liệu Mới")
            
            # Generate a default material ID suggestion
            default_material_id = ""
            if not st.session_state.materials.empty:
                existing_ids = st.session_state.materials['material_id'].tolist()
                # Extract numeric parts from existing IDs that start with "M"
                numeric_parts = []
                for id in existing_ids:
                    if id.startswith("M") and id[1:].isdigit():
                        numeric_parts.append(int(id[1:]))
                
                if numeric_parts:
                    # Suggest next ID number
                    next_id = max(numeric_parts) + 1
                    default_material_id = f"M{next_id:03d}"
                else:
                    default_material_id = "M001"
            else:
                default_material_id = "M001"
            
            new_material_id = st.text_input("Mã Nguyên liệu", value=default_material_id, key="new_material_id")
            new_material_name = st.text_input("Tên Nguyên liệu", key="new_material_name")
            
            # Suggest common units
            unit_options = ["kg", "g", "lít", "ml", "cái", "túi", "gói", "thùng", "hộp", "chai", "Khác"]
            selected_unit_option = st.selectbox("Đơn vị", options=unit_options, key="unit_select")
            
            if selected_unit_option == "Khác":
                new_material_unit = st.text_input("Nhập đơn vị mới:", key="custom_unit")
            else:
                new_material_unit = selected_unit_option
            
            col1, col2 = st.columns(2)
            with col1:
                new_material_quantity = st.number_input("Số lượng nhập", min_value=0.1, value=1.0, step=0.1, key="new_material_quantity")
            with col2:
                new_material_cost = st.number_input("Tổng chi phí (VND)", min_value=1000, value=100000, step=1000, key="new_material_cost")
            
            # Calculate unit price for new material
            if new_material_quantity > 0:
                unit_price = new_material_cost / new_material_quantity
                st.write(f"Giá trên một đơn vị: {unit_price:,.0f} VND/{new_material_unit or selected_unit_option}")
            
            # Additional notes
            new_material_notes = st.text_area("Ghi chú", key="new_material_notes")
            
            if st.button("Thêm và Nhập kho Nguyên liệu Mới"):
                if not new_material_id or not new_material_name or not (new_material_unit or selected_unit_option != "Khác"):
                    st.error("Vui lòng điền đầy đủ thông tin nguyên liệu")
                elif not supplier:
                    st.error("Vui lòng nhập thông tin nhà cung cấp")
                elif new_material_id in st.session_state.materials['material_id'].values:
                    st.error(f"Mã nguyên liệu {new_material_id} đã tồn tại")
                else:
                    # Calculate the price per unit
                    price_per_unit = new_material_cost / new_material_quantity if new_material_quantity > 0 else 0
                    
                    # Add new material
                    new_material = pd.DataFrame({
                        'material_id': [new_material_id],
                        'name': [new_material_name],
                        'unit': [new_material_unit if selected_unit_option == "Khác" else selected_unit_option],
                        'quantity': [new_material_quantity],
                        'price_per_unit': [price_per_unit],
                        'used_quantity': [0.0]
                    })
                    
                    # If materials DataFrame does not exist yet, create it
                    if 'materials' not in st.session_state or st.session_state.materials.empty:
                        st.session_state.materials = new_material
                    else:
                        st.session_state.materials = pd.concat([st.session_state.materials, new_material], ignore_index=True)
                    
                    # Record the initial inventory
                    if 'material_costs' not in st.session_state:
                        st.session_state.material_costs = pd.DataFrame(columns=[
                            'date', 'material_id', 'quantity', 'total_cost', 'supplier'
                        ])
                    
                    initial_import = pd.DataFrame({
                        'date': [import_date],
                        'material_id': [new_material_id],
                        'quantity': [new_material_quantity],
                        'total_cost': [new_material_cost],
                        'supplier': [supplier]
                    })
                    
                    st.session_state.material_costs = pd.concat([st.session_state.material_costs, initial_import], ignore_index=True)
                    
                    unit_display = new_material_unit if selected_unit_option == "Khác" else selected_unit_option
                    st.success(f"Nguyên liệu mới {new_material_id} - {new_material_name} đã được thêm và nhập kho thành công!")
                    st.write(f"Đã nhập: {new_material_quantity} {unit_display}")
                    st.write(f"Giá đơn vị: {price_per_unit:,.0f} VND/{unit_display}")

                    # Save materials and material costs data
                    save_dataframe(st.session_state.materials, "materials.csv")
                    save_dataframe(st.session_state.material_costs, "material_costs.csv")

# Product Management Tab
elif tab_selection == "Quản lý Sản phẩm":
    st.header("Quản lý Sản phẩm")
    
    price_tab1, price_tab2, price_tab3, price_tab4 = st.tabs(["Xem Sản phẩm", "Cập nhật Giá", "Thêm Sản phẩm Mới", "Xóa Sản phẩm"])
    
    with price_tab1:
        st.subheader("Sản phẩm Hiện tại")
        
        if not st.session_state.products.empty:
            # Display products in a cleaner format
            products_display = pd.DataFrame({
                'Mã sản phẩm': st.session_state.products['product_id'],
                'Tên sản phẩm': st.session_state.products['name'],
                'Giá': [f"{price:,.0f} VND" for price in st.session_state.products['price']],
                'Phân loại': st.session_state.products['category']
            })
            
            st.dataframe(products_display)
            
            # Calculate profitability in a safer way
            if not st.session_state.recipes.empty and not st.session_state.materials.empty:
                st.subheader("Lợi nhuận Sản phẩm")
                
                profit_data = []
                
                for _, product in st.session_state.products.iterrows():
                    product_id = product['product_id']
                    product_recipes = st.session_state.recipes[st.session_state.recipes['product_id'] == product_id]
                    
                    # Calculate cost
                    cost = 0
                    if not product_recipes.empty:
                        for _, recipe in product_recipes.iterrows():
                            material_id = recipe['material_id']
                            quantity = recipe['quantity']
                            
                            material_price_data = st.session_state.materials[st.session_state.materials['material_id'] == material_id]
                            if not material_price_data.empty:
                                material_price = material_price_data['price_per_unit'].iloc[0]
                                cost += quantity * material_price
                    
                    # Calculate profit margin
                    price = product['price']
                    profit = price - cost
                    profit_margin = (profit / price) * 100 if price > 0 else 0
                    
                    profit_data.append({
                        'Mã sản phẩm': product_id,
                        'Tên sản phẩm': product['name'],
                        'Giá bán': f"{price:,.0f} VND",
                        'Chi phí': f"{cost:,.0f} VND",
                        'Lợi nhuận': f"{profit:,.0f} VND",
                        'Tỷ suất LN': f"{profit_margin:.2f}%"
                    })
                
                if profit_data:
                    st.dataframe(pd.DataFrame(profit_data))
                else:
                    st.info("Không thể tính toán dữ liệu lợi nhuận.")
            else:
                st.info("Chưa có đủ dữ liệu công thức hoặc nguyên liệu để tính lợi nhuận.")
        else:
            st.info("Chưa có dữ liệu sản phẩm.")
    
    with price_tab2:
        st.subheader("Cập nhật Giá Sản phẩm")
        
        if not st.session_state.products.empty:
            # Create a list of options for the selectbox
            product_options = []
            for _, product in st.session_state.products.iterrows():
                product_options.append(f"{product['product_id']} - {product['name']}")
            
            selected_product = st.selectbox(
                "Chọn Sản phẩm",
                options=product_options,
                key="update_product_select"
            )
            
            if selected_product:
                # Extract product_id from the selection
                selected_product_id = selected_product.split(' - ')[0]
                
                # Find the product data
                product_data = st.session_state.products[st.session_state.products['product_id'] == selected_product_id]
                
                if not product_data.empty:
                    product_idx = product_data.index[0]
                    current_price = st.session_state.products.at[product_idx, 'price']
                    
                    new_price = st.number_input("Giá Mới", min_value=1000, value=int(current_price), step=1000)
                    
                    if st.button("Cập nhật Giá"):
                        st.session_state.products.at[product_idx, 'price'] = new_price
                        st.success(f"Giá sản phẩm {selected_product_id} đã được cập nhật thành công!")
                        
                        # Save products data
                        save_dataframe(st.session_state.products, "products.csv")
        else:
            st.info("Chưa có dữ liệu sản phẩm để cập nhật.")

    with price_tab3:
        st.subheader("Thêm Sản phẩm Mới")
        
        # New product form
        new_product_id = st.text_input("Mã Sản phẩm (vd: P005)", key="new_product_id")
        new_product_name = st.text_input("Tên Sản phẩm", key="new_product_name")
        new_product_category = st.text_input("Phân loại", key="new_product_category")
        
        # Add direct production fee and other costs inputs
        col1, col2 = st.columns(2)
        with col1:
            production_fee = st.number_input("Chi phí sản xuất (VND)", min_value=0, value=10000, step=1000, key="production_fee")
            st.caption("Chi phí liên quan đến quá trình sản xuất")
        with col2:
            other_fee = st.number_input("Chi phí khác (VND)", min_value=0, value=5000, step=1000, key="other_fee")
            st.caption("Các chi phí phát sinh khác")
        
        st.write("### Công thức")
        st.write("Chọn nguyên liệu và số lượng cần thiết cho sản phẩm này:")
        
        # Materials for recipe
        recipe_materials = []
        total_material_cost = 0
        
        if not st.session_state.materials.empty:
            for _, material in st.session_state.materials.iterrows():
                col1, col2, col3 = st.columns([3, 1, 2])
                with col1:
                    st.write(f"{material['name']} ({material['unit']})")
                with col2:
                    quantity = st.number_input(
                        f"SL",
                        min_value=0.0,
                        value=0.0,
                        step=0.1,
                        key=f"new_recipe_{material['material_id']}"
                    )
                with col3:
                    if quantity > 0:
                        material_cost = quantity * material['price_per_unit']
                        st.write(f"{material_cost:,.0f} VND")
                        total_material_cost += material_cost
                    else:
                        st.write("0 VND")
                
                if quantity > 0:
                    recipe_materials.append({
                        'material_id': material['material_id'],
                        'quantity': quantity
                    })
        else:
            st.warning("Không có nguyên liệu nào trong kho. Vui lòng thêm nguyên liệu trước.")
        
        # Calculate total cost and suggested price
        total_cost = total_material_cost + production_fee + other_fee
        markup_percentage = 66.66
        markup_multiplier = 1 + (markup_percentage / 100)
        suggested_price = total_cost * markup_multiplier
        
        # Display cost breakdown and suggested price
        st.write("### Chi phí và Giá đề xuất")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"Chi phí nguyên liệu: **{total_material_cost:,.0f} VND**")
            st.write(f"Chi phí sản xuất: **{production_fee:,.0f} VND**")
            st.write(f"Chi phí khác: **{other_fee:,.0f} VND**")
            st.write(f"**Tổng chi phí: {total_cost:,.0f} VND**")
        with col2:
            st.write(f"Tỷ lệ lợi nhuận: **{markup_percentage:.2f}%**")
            st.write(f"Giá đề xuất: **{suggested_price:,.0f} VND**")
        
        # Allow user to use suggested price or enter a custom price
        use_suggested_price = st.checkbox("Sử dụng giá đề xuất", value=True, key="use_suggested_price")
        
        if use_suggested_price:
            new_product_price = int(suggested_price)
            st.write(f"Giá sản phẩm: **{new_product_price:,.0f} VND**")
        else:
            new_product_price = st.number_input("Giá tùy chỉnh", min_value=1000, value=int(suggested_price), step=1000, key="new_product_price")
        
        # Add product cost info for future reference
        product_cost_info = {
            'material_cost': total_material_cost,
            'production_fee': production_fee,
            'other_fee': other_fee,
            'total_cost': total_cost
        }
        
        if st.button("Thêm Sản phẩm"):
            if not new_product_id or not new_product_name or not new_product_category:
                st.error("Vui lòng điền đầy đủ thông tin sản phẩm")
            elif len(recipe_materials) == 0:
                st.error("Vui lòng thêm ít nhất một nguyên liệu vào công thức")
            elif new_product_id in st.session_state.products['product_id'].values:
                st.error(f"Mã sản phẩm {new_product_id} đã tồn tại")
            else:
                # Add new product
                new_product = pd.DataFrame({
                    'product_id': [new_product_id],
                    'name': [new_product_name],
                    'price': [new_product_price],
                    'category': [new_product_category]
                })
                
                st.session_state.products = pd.concat([st.session_state.products, new_product], ignore_index=True)
                
                # Add recipe
                recipe_rows = []
                for material in recipe_materials:
                    recipe_rows.append({
                        'product_id': new_product_id,
                        'material_id': material['material_id'],
                        'quantity': material['quantity']
                    })
                
                new_recipes = pd.DataFrame(recipe_rows)
                st.session_state.recipes = pd.concat([st.session_state.recipes, new_recipes], ignore_index=True)
                
                # Store cost info (optional, if you want to track this information)
                if 'product_costs' not in st.session_state:
                    st.session_state.product_costs = pd.DataFrame(columns=[
                        'product_id', 'material_cost', 'production_fee', 'other_fee', 'total_cost', 'price'
                    ])
                
                new_cost_info = pd.DataFrame({
                    'product_id': [new_product_id],
                    'material_cost': [total_material_cost],
                    'production_fee': [production_fee],
                    'other_fee': [other_fee],
                    'total_cost': [total_cost],
                    'price': [new_product_price]
                })
                
                st.session_state.product_costs = pd.concat([st.session_state.product_costs, new_cost_info], ignore_index=True)
                
                # Save products, recipes, and product costs data
                st.success(f"Sản phẩm {new_product_id} đã được thêm thành công!")
                save_dataframe(st.session_state.products, "products.csv")
                save_dataframe(st.session_state.recipes, "recipes.csv")
                if 'product_costs' in st.session_state:
                    save_dataframe(st.session_state.product_costs, "product_costs.csv")
    
    # Add new Delete Products tab
    with price_tab4:
        st.subheader("Xóa Sản phẩm")
        
        if not st.session_state.products.empty:
            # Create a list of options for the selectbox
            product_options = []
            for _, product in st.session_state.products.iterrows():
                product_options.append(f"{product['product_id']} - {product['name']}")
            
            selected_product = st.selectbox(
                "Chọn Sản phẩm để Xóa",
                options=product_options,
                key="delete_product_select"
            )
            
            if selected_product:
                # Extract product_id from the selection
                selected_product_id = selected_product.split(' - ')[0]
                
                # Find the product data
                product_data = st.session_state.products[st.session_state.products['product_id'] == selected_product_id]
                
                if not product_data.empty:
                    product_info = product_data.iloc[0]
                    
                    st.write(f"**Tên sản phẩm:** {product_info['name']}")
                    st.write(f"**Giá:** {product_info['price']:,.0f} VND")
                    st.write(f"**Phân loại:** {product_info['category']}")
                    
                    # Check if product is used in any order
                    product_in_orders = selected_product_id in st.session_state.order_items['product_id'].values
                    
                    if product_in_orders:
                        st.warning("Sản phẩm này đã được sử dụng trong các đơn hàng. Xóa sản phẩm có thể ảnh hưởng đến dữ liệu lịch sử.")
                    
                    # Delete confirmation
                    delete_confirmed = st.checkbox("Tôi hiểu rằng hành động này không thể hoàn tác", key="delete_confirm")
                    
                    if st.button("Xóa Sản phẩm") and delete_confirmed:
                        # Delete product from products DataFrame
                        st.session_state.products = st.session_state.products[st.session_state.products['product_id'] != selected_product_id]
                        
                        # Delete product's recipes from recipes DataFrame
                        st.session_state.recipes = st.session_state.recipes[st.session_state.recipes['product_id'] != selected_product_id]
                        
                        st.success(f"Sản phẩm {selected_product_id} đã được xóa thành công!")
        
                        # Save products and recipes data
                        save_dataframe(st.session_state.products, "products.csv")
                        save_dataframe(st.session_state.recipes, "recipes.csv")
        
        else:
            st.info("Chưa có dữ liệu sản phẩm để xóa.")

# Invoice Management Tab - Updated with Completion Status
elif tab_selection == "Quản lý Hóa đơn":
    st.header("Quản lý Hóa đơn")
    
    # Initialize invoice status tracking if not exists
    if 'invoice_status' not in st.session_state:
        st.session_state.invoice_status = pd.DataFrame(columns=[
            'invoice_id', 'is_completed', 'completion_date', 'notes'
        ])
    
    # Make sure all invoices have a status entry
    if not st.session_state.invoices.empty:
        for _, invoice in st.session_state.invoices.iterrows():
            invoice_id = invoice['invoice_id']
            if invoice_id not in st.session_state.invoice_status['invoice_id'].values:
                new_status = pd.DataFrame({
                    'invoice_id': [invoice_id],
                    'is_completed': [False],
                    'completion_date': [''],
                    'notes': [''],
                    'payment_status': ['Chưa thanh toán']  # Add default payment status
                })
                st.session_state.invoice_status = pd.concat([st.session_state.invoice_status, new_status], ignore_index=True)
            # Add payment_status column to existing records if it doesn't exist
            elif 'payment_status' not in st.session_state.invoice_status.columns:
                st.session_state.invoice_status['payment_status'] = 'Chưa thanh toán'
    
    invoice_tab1, invoice_tab2 = st.tabs(["Danh sách Hóa đơn", "Hóa đơn Chưa hoàn thành"])
    
    with invoice_tab1:
        if len(st.session_state.invoices) > 0:
            st.subheader("Tất cả Hóa đơn")
            
            # Create a display version of the invoices with formatted values and status
            invoices_with_status = st.session_state.invoices.merge(
                st.session_state.invoice_status[['invoice_id', 'is_completed']],
                on='invoice_id',
                how='left'
            )
            
            # Fill NaN values from merge
            invoices_with_status['is_completed'] = invoices_with_status['is_completed'].fillna(False)
            
            # Format for display
            display_invoices = pd.DataFrame({
                'ID Hóa đơn': invoices_with_status['invoice_id'],
                'Ngày': invoices_with_status['date'],
                'Khách hàng': invoices_with_status['customer_name'],
                'Tổng tiền': invoices_with_status['total_amount'].apply(lambda x: f"{x:,.0f} VND"),
                'Thanh toán': invoices_with_status['payment_method'],
                'Trạng thái': invoices_with_status['is_completed'].apply(
                    lambda x: "✅ Hoàn thành" if x else "⏳ Chưa hoàn thành"
                ),
                'Trạng thái TT': invoices_with_status['payment_status'] if 'payment_status' in invoices_with_status.columns else "Chưa thanh toán"
            })
            
            # Show the invoices sorted by date
            st.dataframe(display_invoices.sort_values('Ngày', ascending=False))
            
            # Filter options
            st.subheader("Lọc Hóa đơn")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                filter_status = st.radio(
                    "Trạng thái hoàn thành",
                    ["Tất cả", "Hoàn thành", "Chưa hoàn thành"],
                    key="invoice_status_filter"
                )
            
            with col2:
                # Get unique dates
                unique_dates = sorted(st.session_state.invoices['date'].unique(), reverse=True)
                filter_date = st.selectbox(
                    "Ngày",
                    ["Tất cả"] + unique_dates,
                    key="invoice_date_filter"
                )
            
            with col3:
                # Get payment methods
                payment_methods = ["Tất cả"] + list(st.session_state.invoices['payment_method'].unique())
                filter_payment = st.selectbox(
                    "Phương thức thanh toán",
                    payment_methods,
                    key="invoice_payment_filter"
                )
            
            # Apply filters
            filtered_invoices = invoices_with_status.copy()
            
            if filter_status == "Hoàn thành":
                filtered_invoices = filtered_invoices[filtered_invoices['is_completed'] == True]
            elif filter_status == "Chưa hoàn thành":
                filtered_invoices = filtered_invoices[filtered_invoices['is_completed'] == False]
            
            if filter_date != "Tất cả":
                filtered_invoices = filtered_invoices[filtered_invoices['date'] == filter_date]
            
            if filter_payment != "Tất cả":
                filtered_invoices = filtered_invoices[filtered_invoices['payment_method'] == filter_payment]
            
            # Select invoice to view
            if not filtered_invoices.empty:
                invoice_options = []
                for _, invoice in filtered_invoices.iterrows():
                    status_emoji = "✅" if invoice['is_completed'] else "⏳"
                    invoice_options.append(f"{invoice['invoice_id']} - {invoice['customer_name']} ({status_emoji})")
                
                selected_invoice = st.selectbox(
                    "Chọn Hóa đơn để Xem",
                    options=invoice_options,
                    key="view_invoice_select"
                )
                
                if selected_invoice:
                    # Extract invoice_id from the selection
                    selected_invoice_id = selected_invoice.split(' - ')[0]
                    
                    # Find the invoice data
                    invoice_data = st.session_state.invoices[st.session_state.invoices['invoice_id'] == selected_invoice_id]
                    status_data = st.session_state.invoice_status[st.session_state.invoice_status['invoice_id'] == selected_invoice_id]
                    
                    if not invoice_data.empty and not status_data.empty:
                        invoice_data = invoice_data.iloc[0]
                        status_data = status_data.iloc[0]
                        order_id = invoice_data['order_id']
                        
                        # Display invoice details
                        st.write("### Chi tiết Hóa đơn")
                        
                        # Invoice header in columns
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**Hóa đơn #:** {selected_invoice_id}")
                            st.write(f"**Ngày:** {invoice_data['date']}")
                        with col2:
                            st.write(f"**Khách hàng:** {invoice_data['customer_name']}")
                            st.write(f"**Tổng tiền:** {invoice_data['total_amount']:,.0f} VND")
                        with col3:
                            st.write(f"**Thanh toán:** {invoice_data['payment_method']}")
                            status_text = "✅ Hoàn thành" if status_data['is_completed'] else "⏳ Chưa hoàn thành"
                            st.write(f"**Trạng thái:** {status_text}")
                            payment_status = status_data.get('payment_status', "Chưa thanh toán")
                            st.write(f"**Trạng thái TT:** {payment_status}")
                        
                        # Completion status toggle and notes
                        st.write("### Cập nhật Trạng thái")
                        completion_col1, completion_col2 = st.columns(2)
                        
                        with completion_col1:
                            new_status = st.checkbox(
                                "Đánh dấu đã hoàn thành",
                                value=status_data['is_completed'],
                                key=f"complete_{selected_invoice_id}"
                            )
                            
                            # Only show date input if completed
                            if new_status:
                                completion_date = status_data['completion_date']
                                if not completion_date:
                                    completion_date = datetime.date.today().strftime("%Y-%m-%d")
                                
                                new_completion_date = st.date_input(
                                    "Ngày hoàn thành",
                                    value=datetime.datetime.strptime(completion_date, "%Y-%m-%d").date() if completion_date else datetime.date.today(),
                                    key=f"completion_date_{selected_invoice_id}"
                                ).strftime("%Y-%m-%d")
                            else:
                                new_completion_date = ""

                            # Add payment status selector
                            payment_status_options = ["Chưa thanh toán", "Đã thanh toán một phần", "Đã thanh toán"]
                            current_payment_status = status_data.get('payment_status', "Chưa thanh toán")
                            new_payment_status = st.selectbox(
                                "Trạng thái thanh toán",
                                options=payment_status_options,
                                index=payment_status_options.index(current_payment_status) if current_payment_status in payment_status_options else 0,
                                key=f"payment_status_{selected_invoice_id}"
                            )

                        with completion_col2:
                            new_notes = st.text_area(
                                "Ghi chú",
                                value=status_data['notes'],
                                key=f"notes_{selected_invoice_id}"
                            )
                        
                        # Save status changes
                        if st.button("Lưu trạng thái", key=f"save_status_{selected_invoice_id}"):
                            status_idx = st.session_state.invoice_status[
                                st.session_state.invoice_status['invoice_id'] == selected_invoice_id
                            ].index[0]
                            
                            # Update status values
                            st.session_state.invoice_status.at[status_idx, 'is_completed'] = new_status
                            st.session_state.invoice_status.at[status_idx, 'completion_date'] = new_completion_date
                            st.session_state.invoice_status.at[status_idx, 'notes'] = new_notes
                            
                            # Add payment status update
                            if 'payment_status' not in st.session_state.invoice_status.columns:
                                st.session_state.invoice_status['payment_status'] = "Chưa thanh toán"
                            st.session_state.invoice_status.at[status_idx, 'payment_status'] = new_payment_status

                            st.success(f"Trạng thái hóa đơn {selected_invoice_id} đã được cập nhật!")
                            # Save invoice status data
                            save_dataframe(st.session_state.invoice_status, "invoice_status.csv")
                            st.rerun()  # Changed from experimental_rerun to rerun
                        
                        # Order items
                        st.write("### Các Mặt hàng")
                        order_items = st.session_state.order_items[st.session_state.order_items['order_id'] == order_id]
                        
                        if not order_items.empty:
                            # Get product names
                            order_items_with_names = order_items.copy()
                            if not st.session_state.products.empty:
                                order_items_with_names = order_items.merge(
                                    st.session_state.products[['product_id', 'name']],
                                    on='product_id',
                                    how='left'
                                )
                            
                            # Handle cases where products might be missing
                            if 'name' not in order_items_with_names.columns:
                                order_items_with_names['name'] = order_items_with_names['product_id'].apply(
                                    lambda pid: f"Sản phẩm {pid}"
                                )
                            
                            # Format for display
                            display_items = pd.DataFrame({
                                'Tên sản phẩm': order_items_with_names['name'],
                                'Số lượng': order_items_with_names['quantity'],
                                'Đơn giá': order_items_with_names['price'].apply(lambda x: f"{x:,.0f} VND"),
                                'Thành tiền': order_items_with_names['subtotal'].apply(lambda x: f"{x:,.0f} VND")
                            })
                            
                            # Display the items
                            st.dataframe(display_items)
                        else:
                            st.info("Không tìm thấy chi tiết đơn hàng.")
                        
                        # Invoice download link
                        st.subheader("Tải xuống Hóa đơn")
                        try:
                            pdf_data = generate_invoice_content(selected_invoice_id, order_id, as_pdf=True)
                            st.markdown(download_link(pdf_data, f"Hoadon_{selected_invoice_id}.pdf", "Tải Hóa đơn (PDF)", is_pdf=True), unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"Lỗi khi tạo hóa đơn: {str(e)}")
            else:
                st.info("Không có hóa đơn nào phù hợp với bộ lọc đã chọn.")
        else:
            st.info("Chưa có hóa đơn nào. Tạo đơn hàng để tạo hóa đơn.")
            
            # Add demo invoice button for testing
            if st.button("Tạo hóa đơn mẫu (Để kiểm tra)"):
                # Create a demo order and invoice
                order_id = f"ORD-DEMO-{uuid.uuid4().hex[:4].upper()}"
                invoice_id = f"INV-DEMO-{uuid.uuid4().hex[:4].upper()}"
                
                # Create order
                demo_order = pd.DataFrame({
                    'order_id': [order_id],
                    'date': [datetime.date.today().strftime("%Y-%m-%d")],
                    'customer_name': ["Khách hàng Mẫu"],
                    'customer_phone': ["0123456789"],
                    'total_amount': [150000],
                    'status': ['Hoàn thành']
                })
                
                # Create order items
                demo_item = pd.DataFrame({
                    'order_id': [order_id],
                    'product_id': ['P001'],
                    'quantity': [1],
                    'price': [150000],
                    'subtotal': [150000]
                })
                
                # Create invoice
                demo_invoice = pd.DataFrame({
                    'invoice_id': [invoice_id],
                    'order_id': [order_id],
                    'date': [datetime.date.today().strftime("%Y-%m-%d")],
                    'customer_name': ["Khách hàng Mẫu"],
                    'total_amount': [150000],
                    'payment_method': ['Tiền mặt']
                })
                
                # Create invoice status
                demo_status = pd.DataFrame({
                    'invoice_id': [invoice_id],
                    'is_completed': [False],
                    'completion_date': [''],
                    'notes': ['Hóa đơn mẫu để kiểm thử']
                })
                
                # Update session state
                st.session_state.orders = pd.concat([st.session_state.orders, demo_order], ignore_index=True)
                st.session_state.order_items = pd.concat([st.session_state.order_items, demo_item], ignore_index=True)
                st.session_state.invoices = pd.concat([st.session_state.invoices, demo_invoice], ignore_index=True)
                st.session_state.invoice_status = pd.concat([st.session_state.invoice_status, demo_status], ignore_index=True)
                
                st.success("Đã tạo hóa đơn mẫu thành công!")
                # Save orders, order items, invoices, and invoice status data
                save_dataframe(st.session_state.orders, "orders.csv")
                save_dataframe(st.session_state.order_items, "order_items.csv")
                save_dataframe(st.session_state.invoices, "invoices.csv")
                save_dataframe(st.session_state.invoice_status, "invoice_status.csv")

                st.rerun()  # Changed from experimental_rerun to rerun
    
    with invoice_tab2:
        st.subheader("Hóa đơn Chưa hoàn thành")
        
        # Get incomplete invoices
        if not st.session_state.invoices.empty and not st.session_state.invoice_status.empty:
            incomplete_status = st.session_state.invoice_status[st.session_state.invoice_status['is_completed'] == False]
            
            if not incomplete_status.empty:
                incomplete_invoices = st.session_state.invoices.merge(
                    incomplete_status[['invoice_id']],
                    on='invoice_id',
                    how='inner'
                )
                
                if not incomplete_invoices.empty:
                    # Format for display
                    display_incomplete = pd.DataFrame({
                        'ID Hóa đơn': incomplete_invoices['invoice_id'],
                        'Ngày': incomplete_invoices['date'],
                        'Khách hàng': incomplete_invoices['customer_name'],
                        'Tổng tiền': incomplete_invoices['total_amount'].apply(lambda x: f"{x:,.0f} VND"),
                        'Thanh toán': incomplete_invoices['payment_method']
                    })
                    
                    # Show the incomplete invoices
                    st.dataframe(display_incomplete.sort_values('Ngày', ascending=False))
                    
                    # Quick completion tools
                    st.subheader("Hoàn thành Nhanh")
                    
                    incomplete_options = []
                    for _, invoice in incomplete_invoices.iterrows():
                        incomplete_options.append(f"{invoice['invoice_id']} - {invoice['customer_name']}")
                    
                    selected_to_complete = st.multiselect(
                        "Chọn hóa đơn để đánh dấu hoàn thành",
                        options=incomplete_options,
                        key="batch_complete_select"
                    )
                    
                    if selected_to_complete:
                        if st.button("Đánh dấu đã hoàn thành", key="batch_complete_button"):
                            completion_date = datetime.date.today().strftime("%Y-%m-%d")
                            completion_note = "Đánh dấu hoàn thành theo lô"
                            
                            for invoice_string in selected_to_complete:
                                invoice_id = invoice_string.split(' - ')[0]
                                
                                # Find status entry
                                status_idxs = st.session_state.invoice_status[
                                    st.session_state.invoice_status['invoice_id'] == invoice_id
                                ].index
                                
                                if not status_idxs.empty:
                                    status_idx = status_idxs[0]
                                    
                                    # Update status
                                    st.session_state.invoice_status.at[status_idx, 'is_completed'] = True
                                    st.session_state.invoice_status.at[status_idx, 'completion_date'] = completion_date
                                    
                                    # Only update notes if empty
                                    if not st.session_state.invoice_status.at[status_idx, 'notes']:
                                        st.session_state.invoice_status.at[status_idx, 'notes'] = completion_note
                            
                            st.success(f"Đã cập nhật {len(selected_to_complete)} hóa đơn!")
                            # Save invoice status data
                            save_dataframe(st.session_state.invoice_status, "invoice_status.csv")
                            
                            st.rerun()  # Changed from experimental_rerun to rerun
                else:
                    st.info("Không có hóa đơn nào chưa hoàn thành.")
            else:
                st.info("Không có hóa đơn nào chưa hoàn thành.")
        else:
            st.info("Chưa có hóa đơn nào để hiển thị.")

# Data Management and Debug Tab
elif tab_selection == "Quản lý Dữ liệu":
    st.header("Quản lý Dữ liệu")
    
    data_tab1, data_tab2, data_tab3 = st.tabs(["Sao lưu & Phục hồi", "Xóa Dữ liệu", "Thông tin Dữ liệu"])
    
    with data_tab1:
        st.subheader("Sao lưu & Phục hồi Dữ liệu")
        
        data_dir = r"C:\\Users\\Computer\\PycharmProjects\\bakery_sys\\bakery_data"
        
        # Backup section
        st.write("### Sao lưu Dữ liệu")
        st.write("Tạo bản sao lưu cho tất cả dữ liệu của hệ thống.")
        
        if st.button("Lưu Tất cả Dữ liệu"):
            try:
                # Save all current data
                save_all_data()
                st.success("Đã lưu tất cả dữ liệu thành công!")
            except Exception as e:
                st.error(f"Lỗi khi lưu dữ liệu: {str(e)}")
                
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Tạo Backup"):
                try:
                    # Create backup directory if it doesn't exist
                    backup_dir = os.path.join(data_dir, "backup")
                    if not os.path.exists(backup_dir):
                        os.makedirs(backup_dir)
                    
                    # Get current timestamp for backup name
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_zip = os.path.join(backup_dir, f"backup_{timestamp}.zip")
                    
                    # Create a zip file containing all CSVs
                    import zipfile
                    with zipfile.ZipFile(backup_zip, 'w') as zip_file:
                        for file in os.listdir(data_dir):
                            if file.endswith('.csv'):
                                file_path = os.path.join(data_dir, file)
                                zip_file.write(file_path, arcname=file)
                    
                    st.success(f"Đã tạo backup thành công: {backup_zip}")
                except Exception as e:
                    st.error(f"Lỗi khi tạo backup: {str(e)}")
        
        with col2:
            if st.button("Tải lại Dữ liệu"):
                try:
                    # Force reload all data from disk
                    st.session_state.products = load_dataframe("products.csv", default_products)
                    st.session_state.materials = load_dataframe("materials.csv", default_materials)
                    st.session_state.recipes = load_dataframe("recipes.csv", default_recipes)
                    st.session_state.orders = load_dataframe("orders.csv", default_orders)
                    st.session_state.order_items = load_dataframe("order_items.csv", default_order_items)
                    st.session_state.invoices = load_dataframe("invoices.csv", default_invoices)
                    st.session_state.income = load_dataframe("income.csv", default_income)
                    st.session_state.material_costs = load_dataframe("material_costs.csv", default_material_costs)
                    st.session_state.invoice_status = load_dataframe("invoice_status.csv", default_invoice_status)
                    
                    st.success("Đã tải lại dữ liệu thành công!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Lỗi khi tải lại dữ liệu: {str(e)}")
    
    with data_tab2:
        st.subheader("Xóa Dữ liệu")
        st.warning("⚠️ **Cảnh báo**: Các hành động ở đây có thể làm mất dữ liệu vĩnh viễn!")
        
        reset_options = st.radio(
            "Chọn loại dữ liệu để xóa:",
            ["Không xóa gì", "Xóa dữ liệu đơn hàng và hóa đơn", "Xóa dữ liệu kho", "Xóa dữ liệu sản phẩm", "Xóa tất cả dữ liệu"]
        )
        
        if reset_options != "Không xóa gì":
            st.write(f"**Bạn đã chọn:** {reset_options}")
            
            # Display what will be deleted
            if reset_options == "Xóa dữ liệu đơn hàng và hóa đơn":
                st.write("Các dữ liệu sau sẽ bị xóa:")
                st.write("- Đơn hàng")
                st.write("- Chi tiết đơn hàng")
                st.write("- Hóa đơn")
                st.write("- Trạng thái hóa đơn")
                st.write("- Doanh thu")
            elif reset_options == "Xóa dữ liệu kho":
                st.write("Các dữ liệu sau sẽ bị xóa:")
                st.write("- Nguyên liệu (sẽ được thiết lập lại về mặc định)")
                st.write("- Chi phí nguyên liệu")
            elif reset_options == "Xóa dữ liệu sản phẩm":
                st.write("Các dữ liệu sau sẽ bị xóa:")
                st.write("- Sản phẩm (sẽ được thiết lập lại về mặc định)")
                st.write("- Công thức (sẽ được thiết lập lại về mặc định)")
            else:  # Xóa tất cả
                st.write("**Tất cả dữ liệu** sẽ bị xóa và thiết lập lại về mặc định!")
            
            # Multiple confirmations for safety
            confirm1 = st.checkbox("Tôi muốn xóa dữ liệu đã chọn", key="confirm_delete_1")
            confirm2 = st.checkbox("Tôi hiểu rằng dữ liệu bị xóa sẽ không thể khôi phục (trừ khi có bản sao lưu)", key="confirm_delete_2")
            
            delete_password = st.text_input("Nhập 'XOA' để xác nhận:", type="password", key="delete_password")
            
            if st.button("Xóa Dữ liệu") and confirm1 and confirm2 and delete_password == "XOA":
                try:
                    # Create automatic backup before deletion
                    backup_dir = os.path.join(data_dir, "backup")
                    if not os.path.exists(backup_dir):
                        os.makedirs(backup_dir)
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_zip = os.path.join(backup_dir, f"auto_backup_before_deletion_{timestamp}.zip")
                    
                    # Create a zip file containing all CSVs
                    import zipfile
                    with zipfile.ZipFile(backup_zip, 'w') as zip_file:
                        for file in os.listdir(data_dir):
                            if file.endswith('.csv'):
                                file_path = os.path.join(data_dir, file)
                                zip_file.write(file_path, arcname=file)
                    
                    if reset_options == "Xóa dữ liệu đơn hàng và hóa đơn":
                        # Reset order-related data
                        st.session_state.orders = default_orders.copy()
                        st.session_state.order_items = default_order_items.copy()
                        st.session_state.invoices = default_invoices.copy()
                        st.session_state.invoice_status = default_invoice_status.copy()
                        st.session_state.income = default_income.copy()
                        
                        # Save the reset data
                        save_dataframe(st.session_state.orders, "orders.csv")
                        save_dataframe(st.session_state.order_items, "order_items.csv")
                        save_dataframe(st.session_state.invoices, "invoices.csv")
                        save_dataframe(st.session_state.invoice_status, "invoice_status.csv")
                        save_dataframe(st.session_state.income, "income.csv")
                        
                    elif reset_options == "Xóa dữ liệu kho":
                        # Reset materials data
                        st.session_state.materials = default_materials.copy()
                        st.session_state.material_costs = default_material_costs.copy()
                        
                        # Save the reset data
                        save_dataframe(st.session_state.materials, "materials.csv")
                        save_dataframe(st.session_state.material_costs, "material_costs.csv")
                        
                    elif reset_options == "Xóa dữ liệu sản phẩm":
                        # Reset product data
                        st.session_state.products = default_products.copy()
                        st.session_state.recipes = default_recipes.copy()
                        
                        # Save the reset data
                        save_dataframe(st.session_state.products, "products.csv")
                        save_dataframe(st.session_state.recipes, "recipes.csv")
                        
                    else:  # Xóa tất cả
                        # Reset all data
                        st.session_state.products = default_products.copy()
                        st.session_state.materials = default_materials.copy()
                        st.session_state.recipes = default_recipes.copy()
                        st.session_state.orders = default_orders.copy()
                        st.session_state.order_items = default_order_items.copy()
                        st.session_state.invoices = default_invoices.copy()
                        st.session_state.invoice_status = default_invoice_status.copy()
                        st.session_state.income = default_income.copy()
                        st.session_state.material_costs = default_material_costs.copy()
                        
                        # Save all reset data
                        save_all_data()
                    
                    st.success(f"Đã xóa dữ liệu thành công! Backup tự động được lưu tại: {backup_zip}")
                    st.info("Ứng dụng sẽ tải lại sau 5 giây...")
                    import time
                    time.sleep(5)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Lỗi khi xóa dữ liệu: {str(e)}")
    
    with data_tab3:
        st.subheader("Thông tin Dữ liệu")
        
        data_dir = r"C:\\Users\\Computer\\PycharmProjects\\bakery_sys\\bakery_data"
        
        # Check if data directory exists
        if not os.path.exists(data_dir):
            st.error(f"Thư mục dữ liệu không tồn tại: {data_dir}")
        else:
            st.write(f"Thư mục dữ liệu: {data_dir}")
            
            # List CSV files
            files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
            if not files:
                st.warning("Không tìm thấy file CSV nào trong thư mục dữ liệu.")
            else:
                st.write(f"Tìm thấy {len(files)} file CSV:")
                
                file_info = []
                for file in files:
                    filepath = os.path.join(data_dir, file)
                    size = os.path.getsize(filepath)
                    modified = datetime.datetime.fromtimestamp(os.path.getmtime(filepath)).strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Count rows
                    try:
                        df = pd.read_csv(filepath)
                        rows = len(df)
                    except:
                        rows = "Lỗi đọc file"
                    
                    file_info.append({
                        "Tên file": file,
                        "Kích thước": f"{size:,} bytes",
                        "Số dòng": rows,
                        "Lần sửa cuối": modified
                    })
                
                st.table(pd.DataFrame(file_info))
        
        # Show session state data sizes
        st.subheader("Dữ liệu trong phiên hiện tại")
        
        session_data = []
        for key in [
            'products', 'materials', 'recipes', 'orders', 'order_items', 
            'invoices', 'income', 'material_costs', 'invoice_status'
        ]:
            if key in st.session_state:
                rows = len(st.session_state[key])
                columns = len(st.session_state[key].columns) if rows > 0 else 0
                session_data.append({
                    "Tên dữ liệu": key,
                    "Số dòng": rows,
                    "Số cột": columns
                })
        
        st.table(pd.DataFrame(session_data))
        
        # Add a force save button
        if st.button("Lưu lại tất cả dữ liệu"):
            save_all_data()
            st.success("Đã lưu lại tất cả dữ liệu thành công!")